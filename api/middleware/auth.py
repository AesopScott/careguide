from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.firebase import verify_token

bearer = HTTPBearer()

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

def require_practitioner(user: dict = Depends(require_auth)) -> dict:
    if user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Practitioner access required",
        )
    return user
