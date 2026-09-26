from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import httpx
import os
from models import User

SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_jwks_cache = None


async def get_jwks(force_refresh: bool = False):
    global _jwks_cache
    if _jwks_cache is None or force_refresh:
        last_error = None
        for _ in range(2):  # one retry: a cold-started container's first outbound request can time out
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(SUPABASE_JWKS_URL)
                    resp.raise_for_status()
                    _jwks_cache = resp.json()
                    break
            except httpx.HTTPError as exc:
                last_error = exc
        else:
            # A proper HTTPException (not an unhandled 500) keeps CORS headers, so the browser sees the real error.
            raise HTTPException(status_code=503, detail="Authentication service is unreachable, please try again") from last_error
    return _jwks_cache


async def decode_token(token: str):
    try:
        unverified_header = jwt.get_unverified_header(token)  # malformed tokens fail here, without a network call
        kid = unverified_header.get("kid")
        jwks = await get_jwks()
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if key is None:  # Supabase rotated its signing key since we cached the set
            jwks = await get_jwks(force_refresh=True)
            key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if key is None:
            raise HTTPException(status_code=401, detail="Invalid token key")

        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256"],   # use ["HS256"] + SUPABASE_JWT_SECRET if your project is still on legacy
            audience="authenticated",
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = await decode_token(token)
    user_uuid = payload.get("sub")
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid token")

    return User(user_uuid=user_uuid, email=payload.get("email"))
