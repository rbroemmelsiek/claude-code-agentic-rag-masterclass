"""OpenAI Responses API service for chat completions with RAG."""
from typing import Generator, AsyncGenerator, Any

from openai import OpenAI, AsyncOpenAI
from app.config import get_settings
from app.services.langsmith import get_traced_openai_client, get_traced_async_openai_client

settings = get_settings()
client = get_traced_openai_client()
async_client = get_traced_async_openai_client()

SYSTEM_PROMPT = """You are a helpful assistant for the RAG Masterclass application.
You can answer questions and help users with their queries.
When relevant, search through the uploaded documents to provide accurate information.
Always cite your sources when using information from documents."""

DEFAULT_MODEL = "gpt-4o"
ASSISTANT_NAME = "RAG Masterclass Assistant"


def create_thread() -> str:
    """Create a new thread using the OpenAI Conversations API."""
    thread = client.conversations.create()
    return thread.id


def delete_thread(thread_id: str):
    """Delete a thread using the OpenAI Conversations API."""
    client.conversations.delete(thread_id)


def get_or_create_assistant() -> str:
    """Get or create the RAG assistant using the OpenAI Skills API."""
    skills = client.skills.list()
    for skill in skills.data:
        if skill.name == ASSISTANT_NAME:
            return skill.id

    # Create if not found
    skill = client.skills.create(
        name=ASSISTANT_NAME,
        instructions=SYSTEM_PROMPT,
        model=DEFAULT_MODEL,
        tools=_get_tools() or []
    )
    return skill.id


def _get_tools() -> list[dict] | None:
    """Get the tools configuration including file_search if vector store is configured."""
    current_settings = get_settings()
    if current_settings.openai_vector_store_id:
        return [{
            "type": "file_search",
            "vector_store_ids": [current_settings.openai_vector_store_id],
        }]
    return None


async def astream_chat_response(
    thread_id: str,
    content: str,
    model: str = DEFAULT_MODEL,
) -> AsyncGenerator[dict[str, Any], None]:
    """Async stream a chat response using the stateful OpenAI Responses API."""
    request_kwargs = {
        "model": model,
        "conversation": {"id": thread_id},
        "input": content,
        "stream": True,
        "store": True,
        "instructions": SYSTEM_PROMPT,
    }

    tools = _get_tools()
    if tools:
        request_kwargs["tools"] = tools

    try:
        stream = await async_client.responses.create(**request_kwargs)

        full_response = ""
        response_id = None
        openai_message_id = None

        async for event in stream:
            event_type = getattr(event, 'type', None)

            if event_type == "response.created":
                response_id = event.response.id
            elif event_type == "response.output_text.delta":
                delta = event.delta
                if delta:
                    full_response += delta
                    yield {
                        "type": "text_delta",
                        "content": delta,
                    }
            elif event_type == "response.completed":
                # Extract message ID from output if available in this event
                if hasattr(event, 'response') and hasattr(event.response, 'output'):
                    for item in event.response.output:
                        if hasattr(item, 'id'):
                            openai_message_id = item.id
                            break

                yield {
                    "type": "response_completed",
                    "response_id": response_id,
                    "openai_message_id": openai_message_id,
                    "content": full_response,
                }
            elif event_type == "error":
                yield {
                    "type": "error",
                    "error": str(event.error) if hasattr(event, 'error') else "Unknown error",
                }

    except Exception as e:
        yield {
            "type": "error",
            "error": str(e),
        }


def get_chat_response(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
) -> str:
    """Get a non-streaming chat response (legacy stateless)."""
    input_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages
    ]

    request_kwargs = {
        "model": model,
        "input": input_messages,
    }

    tools = _get_tools()
    if tools:
        request_kwargs["tools"] = tools

    response = client.responses.create(**request_kwargs)

    return response.output_text
