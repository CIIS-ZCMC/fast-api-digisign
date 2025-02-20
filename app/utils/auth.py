"""
Authentication Utility Module

This module provides JWT (JSON Web Token) based authentication functionality for the FastAPI
application. It includes token creation and verification mechanisms with proper error
handling and security measures.

The module uses PyJWT for token handling and FastAPI's security utilities for
HTTP Bearer token authentication.
"""

from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import SECRET_KEY

security = HTTPBearer()

def create_token(data: dict) -> dict:
    """
    Create a new JWT token with expiration time.

    This function creates a new JSON Web Token that includes the provided data
    and an expiration timestamp set to 24 hours from creation.

    Args:
        data (dict): The payload data to be encoded in the token

    Returns:
        dict: A dictionary containing:
            - access_token: The JWT token string
            - token_type: The type of token (bearer)
            - expires_at: ISO format timestamp of token expiration

    Example:
        >>> token_data = create_token({"user_id": 123})
        >>> print(token_data["access_token"])
    """
    expiration = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    to_encode = data.copy()
    to_encode.update({"exp": expiration})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expiration.isoformat()
    }

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify and decode a JWT token.

    This function verifies the authenticity and validity of a JWT token provided
    in the HTTP Authorization header. It checks for token expiration and validity
    of the signature.

    Args:
        credentials (HTTPAuthorizationCredentials): The credentials extracted from
            the Authorization header by FastAPI's security system

    Returns:
        dict: The decoded payload from the token if verification is successful

    Raises:
        HTTPException: With status code 401 in the following cases:
            - Missing credentials
            - Invalid token
            - Expired token
            - Invalid signature or corrupted token

    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(payload: dict = Depends(verify_token)):
        >>>     return {"message": "Access granted", "user_data": payload}
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, 
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
