from pydantic import BaseModel
from datetime import datetime


class ThreadCreate(BaseModel):
    title: str | None = "New Chat"


class ThreadResponse(BaseModel):
    id: str
    user_id: str
    openai_thread_id: str | None = None
    title: str
    created_at: datetime
    updated_at: datetime


class ThreadUpdate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    thread_id: str
    user_id: str
    openai_message_id: str | None = None
    role: str
    content: str
    created_at: datetime
