from pydantic import BaseModel
from datetime import datetime


class ThreadCreate(BaseModel):
    title: str | None = "New Chat"


class ThreadResponse(BaseModel):
    id: str
    user_id: str
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
    role: str
    content: str
    created_at: datetime
