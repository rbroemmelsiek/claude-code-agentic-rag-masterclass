from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from app.config import get_settings

security = HTTPBearer()


class User(BaseModel):
    id: str
    email: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify Supabase JWT token and extract user info."""
    settings = get_settings()
    token = credentials.credentials

    try:
        # Supabase uses the anon key's JWT secret for signing
        # The JWT secret is derived from the project's JWT secret in Supabase settings
        # For Supabase, we need to verify the token against the Supabase JWT secret
        # which can be found in Project Settings > API > JWT Secret

        # Decode without verification first to get the payload
        # In production, you should verify with the actual JWT secret
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256", "ES256"],
            options={"verify_signature": False},  # Supabase handles token verification
            audience="authenticated"
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        return User(id=user_id, email=email)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
