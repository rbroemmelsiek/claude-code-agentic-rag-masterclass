"""Thread lookups scoped to the authenticated user."""

from fastapi import HTTPException, status
from supabase import Client


def get_thread_for_user(
    supabase: Client,
    thread_id: str,
    user_id: str,
    *,
    columns: str = "*",
) -> dict:
    """Return one thread row or raise 404 (never leaks existence via 500)."""
    result = (
        supabase.table("threads")
        .select(columns)
        .eq("id", thread_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    return result.data[0]
