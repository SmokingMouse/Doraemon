"""JWT authentication for Web API."""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from config import config


security = HTTPBearer()


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(days=7)  # Default 7 days

    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": user_id, "exp": expire}

    encoded_jwt = jwt.encode(to_encode, config.WEB_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> str:
    """Decode JWT token and return user_id."""
    try:
        payload = jwt.decode(token, config.WEB_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Get current user from JWT token."""
    token = credentials.credentials
    user_id = decode_access_token(token)
    logger.debug(f"Authenticated user: {user_id}")
    return user_id


# Simple user database (for demo, replace with real database)
USERS_DB = {
    "admin": "admin123",  # username: password
}


def verify_user(username: str, password: str) -> bool:
    """Verify username and password."""
    return USERS_DB.get(username) == password
