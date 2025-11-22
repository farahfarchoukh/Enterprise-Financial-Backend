from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from src.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_admin(key: str = Security(api_key_header)):
    settings = get_settings()
    if key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials"
        )
    return key