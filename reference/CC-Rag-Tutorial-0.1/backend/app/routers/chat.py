import json
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import StreamingResponse
from datetime import datetime

from app.dependencies import get_current_user, User
from app.db.supabase import get_supabase_client
from app.models.schemas import MessageCreate, MessageResponse
from app.services.openai_service import astream_chat_response

router = APIRouter(prefix="/threads/{thread_id}", tags=["chat"])


async def verify_thread_access(thread_id: str, user_id: str) -> dict:
    """Verify the user has access to the thread and return thread data."""
    supabase = get_supabase_client()
    result = supabase.table("threads").select("*").eq("id", thread_id).eq("user_id", user_id).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    return result.data


def get_thread_messages(thread_id: str) -> list[dict[str, str]]:
    """Get all messages for a thread formatted for the API."""
    supabase = get_supabase_client()
    result = supabase.table("messages").select("role, content").eq("thread_id", thread_id).order("created_at").execute()

    return [{"role": msg["role"], "content": msg["content"]} for msg in result.data]


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
    await verify_thread_access(thread_id, current_user.id)
    supabase = get_supabase_client()

    # Store user message in database
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

    # Get full message history for context
    messages = get_thread_messages(thread_id)

    async def generate():
        """Generate SSE events for the streaming response."""
        full_response = ""

        try:
            async for event in astream_chat_response(messages):
                if event["type"] == "text_delta":
                    full_response += event["content"]
                    data = json.dumps({"content": event["content"]})
                    yield f"event: text_delta\ndata: {data}\n\n"
                elif event["type"] == "response_completed":
                    # Save assistant message to database
                    if full_response:
                        supabase.table("messages").insert({
                            "thread_id": thread_id,
                            "user_id": current_user.id,
                            "role": "assistant",
                            "content": full_response,
                            "created_at": datetime.utcnow().isoformat(),
                        }).execute()

                        # Update thread's updated_at
                        supabase.table("threads").update({
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", thread_id).execute()

                    data = json.dumps({"response_id": event.get("response_id")})
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
