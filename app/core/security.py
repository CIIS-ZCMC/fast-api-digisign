from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import settings

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """ Verify JWT token """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Use jwt.decode with the correct error types
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET, 
            algorithms=["HS256"]
        )
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, 
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
