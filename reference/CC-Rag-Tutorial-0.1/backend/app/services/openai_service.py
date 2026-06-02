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


def _get_tools() -> list[dict] | None:
    """Get the tools configuration including file_search if vector store is configured."""
    # Get fresh settings to avoid caching issues
    current_settings = get_settings()
    if current_settings.openai_vector_store_id:
        return [{
            "type": "file_search",
            "vector_store_ids": [current_settings.openai_vector_store_id],
        }]
    return None


def stream_chat_response(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
) -> Generator[dict[str, Any], None, None]:
    """
    Stream a chat response using the OpenAI Responses API with file search.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: The model to use (default: gpt-4o)

    Yields:
        Event dicts with 'type' and additional data
    """
    # Build input with system prompt
    input_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages
    ]

    # Build request kwargs
    request_kwargs = {
        "model": model,
        "input": input_messages,
        "stream": True,
    }

    # Add tools if vector store is configured
    tools = _get_tools()
    if tools:
        request_kwargs["tools"] = tools

    try:
        stream = client.responses.create(**request_kwargs)

        full_response = ""
        response_id = None

        for event in stream:
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
                yield {
                    "type": "response_completed",
                    "response_id": response_id,
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


async def astream_chat_response(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Async stream a chat response using the OpenAI Responses API.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: The model to use (default: gpt-4o)

    Yields:
        Event dicts with 'type' and additional data
    """
    input_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages
    ]

    request_kwargs = {
        "model": model,
        "input": input_messages,
        "stream": True,
    }

    tools = _get_tools()
    if tools:
        request_kwargs["tools"] = tools

    try:
        stream = await async_client.responses.create(**request_kwargs)

        full_response = ""
        response_id = None

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
                yield {
                    "type": "response_completed",
                    "response_id": response_id,
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
    """
    Get a non-streaming chat response with file search.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: The model to use (default: gpt-4o)

    Returns:
        The assistant's response text
    """
    input_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages
    ]

    # Build request kwargs
    request_kwargs = {
        "model": model,
        "input": input_messages,
    }

    # Add tools if vector store is configured
    tools = _get_tools()
    if tools:
        request_kwargs["tools"] = tools

    response = client.responses.create(**request_kwargs)

    return response.output_text
