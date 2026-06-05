"""LangSmith tracing configuration for OpenAI API calls."""
import os
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

if settings.langsmith_api_key:
    os.environ["LANGSMITH_TRACING"] = "true" if settings.langsmith_tracing else "false"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
else:
    logger.warning("LangSmith API key not configured - tracing disabled")

import langsmith
from langsmith.wrappers import wrap_openai
from openai import OpenAI, AsyncOpenAI

if settings.langsmith_api_key:
    api_key_preview = settings.langsmith_api_key[:8] + "..." if len(settings.langsmith_api_key) > 8 else "***"
    logger.info(f"LangSmith SDK version: {langsmith.__version__}")
    logger.info(f"LangSmith project: {settings.langsmith_project}")
    logger.info(f"LangSmith endpoint: {os.environ.get('LANGSMITH_ENDPOINT')}")
    logger.info(f"LangSmith API key: {api_key_preview}")


def get_traced_openai_client() -> OpenAI:
    """Get an OpenAI client wrapped with LangSmith tracing."""
    client = OpenAI(api_key=settings.openai_api_key)

    if settings.langsmith_api_key:
        wrapped = wrap_openai(client)
        logger.info("OpenAI client wrapped with LangSmith tracing")
        return wrapped

    return client


def get_traced_async_openai_client() -> AsyncOpenAI:
    """Get an AsyncOpenAI client wrapped with LangSmith tracing."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    if settings.langsmith_api_key:
        wrapped = wrap_openai(client)
        logger.info("AsyncOpenAI client wrapped with LangSmith tracing")
        return wrapped

    return client
