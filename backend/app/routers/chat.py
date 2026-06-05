import json
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import StreamingResponse
from datetime import datetime

from app.dependencies import get_current_user, User
from app.db.supabase import get_supabase_client
from app.db.threads import get_thread_for_user
from app.models.schemas import MessageCreate, MessageResponse
from app.services import openai_service

router = APIRouter(prefix="/threads/{thread_id}", tags=["chat"])


async def verify_thread_access(thread_id: str, user_id: str) -> dict:
    """Verify the user has access to the thread and return thread data."""
    supabase = get_supabase_client()
    return get_thread_for_user(supabase, thread_id, user_id)


@router.get("/messages", response_model=list[MessageResponse])
async def get_messages(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a thread from database."""
    await verify_thread_access(thread_id, current_user.id)

    supabase = get_supabase_client()
    result = supabase.table("messages").select("*").eq("thread_id", thread_id).order("created_at").execute()

    return result.data


@router.post("/messages")
async def send_message(
    thread_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message and stream the assistant's response via SSE."""
    thread = await verify_thread_access(thread_id, current_user.id)
    openai_thread_id = thread.get("openai_thread_id")
    
    supabase = get_supabase_client()

    # Ensure we have an OpenAI thread ID
    if not openai_thread_id:
        openai_thread_id = openai_service.create_thread()
        supabase.table("threads").update({
            "openai_thread_id": openai_thread_id
        }).eq("id", thread_id).execute()

    # Save user message to database
    now = datetime.utcnow().isoformat()
    user_message_result = supabase.table("messages").insert({
        "thread_id": thread_id,
        "user_id": current_user.id,
        "role": "user",
        "content": message_data.content,
        "created_at": now,
    }).execute()

    if not user_message_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save user message"
        )

    async def generate():
        """Generate SSE events for the streaming response."""
        full_response = ""

        try:
            async for event in openai_service.astream_chat_response(openai_thread_id, message_data.content):
                if event["type"] == "text_delta":
                    full_response += event["content"]
                    data = json.dumps({"content": event["content"]})
                    yield f"event: text_delta\ndata: {data}\n\n"
                elif event["type"] == "response_completed":
                    if full_response:
                        supabase.table("messages").insert({
                            "thread_id": thread_id,
                            "user_id": current_user.id,
                            "role": "assistant",
                            "content": full_response,
                            "openai_message_id": event.get("openai_message_id"),
                            "created_at": datetime.utcnow().isoformat(),
                        }).execute()

                        supabase.table("threads").update({
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", thread_id).execute()

                    data = json.dumps({
                        "response_id": event.get("response_id"),
                        "openai_message_id": event.get("openai_message_id")
                    })
                    yield f"event: done\ndata: {data}\n\n"
                elif event["type"] == "error":
                    data = json.dumps({"error": event["error"]})
                    yield f"event: error\ndata: {data}\n\n"
        except Exception as e:
            data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
