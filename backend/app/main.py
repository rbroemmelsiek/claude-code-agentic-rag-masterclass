from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from app.config import get_settings
from app.routers import auth, threads, chat
from app.services.openai_service import get_or_create_assistant

settings = get_settings()

app = FastAPI(
    title="RAG Masterclass API",
    description="Backend API for the RAG Masterclass application",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    try:
        assistant_id = get_or_create_assistant()
        print(f"RAG Assistant ready: {assistant_id}")
    except Exception as e:
        print(f"Warning: Failed to initialize RAG Assistant: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(threads.router)
app.include_router(chat.router)
