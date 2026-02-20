# middleware/auth_middleware.py
# Role: FastAPI dependency for protected routes. Extracts and validates the Bearer token.
# Returns the user_id (str) on success. Raises HTTP 401 on any failure.
# Import and use as: user_id: str = Depends(get_current_user_id)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Validates the Bearer JWT from the Authorization header.
    Returns the user_id (sub claim) if valid. Raises 401 otherwise.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid access token"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired access token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
