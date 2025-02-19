from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import SECRET_KEY

security = HTTPBearer()

def create_token(data: dict):
    """Create JWT token with expiration"""
    expiration = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    to_encode = data.copy()
    to_encode.update({"exp": expiration})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expiration.isoformat()
    }

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """ Verify JWT token """
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
