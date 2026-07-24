"""
Keycloak JWT валидация для admin endpoints.
"""
import time
import httpx
import jwt
from fastapi import HTTPException, Depends, Request
from functools import lru_cache

JWKS_URL = "https://auth.makotools.ru/realms/MAKO/protocol/openid-connect/certs"
ISSUER = "https://auth.makotools.ru/realms/MAKO"
REQUIRED_ROLE = "agents-admin"

_jwks_cache = {"keys": None, "expires": 0}


async def _get_jwks() -> dict:
    now = time.time()
    if _jwks_cache["keys"] and _jwks_cache["expires"] > now:
        return _jwks_cache["keys"]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(JWKS_URL)
        if resp.status_code != 200:
            raise HTTPException(502, "Cannot fetch JWKS")
        _jwks_cache["keys"] = resp.json()
        _jwks_cache["expires"] = now + 300
    return _jwks_cache["keys"]


async def require_admin(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")

    token = auth_header[7:]
    try:
        jwks = await _get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        key_data = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key_data = k
                break
        if not key_data:
            raise HTTPException(401, "Unknown key ID")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="ai-platform",
            issuer=ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f"Invalid token: {e}")

    roles = payload.get("realm_access", {}).get("roles", [])
    if REQUIRED_ROLE not in roles:
        raise HTTPException(403, f"Role '{REQUIRED_ROLE}' required")

    return payload