from fastapi import APIRouter, Response
from pydantic import BaseModel

from typing import Optional
from ..config import settings

router = APIRouter(prefix="", tags=["freeagent"])


class TokenExchangeResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: Optional[str] = None


@router.get("/authorize")
def authorize():
    """Redirect to FreeAgent to authorize the app (read-only scope)."""
    from urllib.parse import urlencode

    params = {
        "client_id": settings.FREEAGENT_CLIENT_ID,
        "redirect_uri": settings.FREEAGENT_REDIRECT_URI,
        "response_type": "code",
        "state": settings.SECRET_KEY,
    }
    auth_url = f"https://api.freeagent.com/v2/approve_app?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.post("/callback", response_model=TokenExchangeResponse)
def oauth_callback(code: str, state: str, redirect_uri: Optional[str] = None):
    """
    Exchange the authorization code for an access token.
    Uses HTTP Basic auth (client_id:client_secret) to the token endpoint.
    """
    import httpx

    token_url = "https://api.freeagent.com/v2/token_endpoint"
    headers = {"Accept": "application/json"}

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.FREEAGENT_REDIRECT_URI,
    }
    if redirect_uri:
        payload["redirect_uri"] = redirect_uri

    with httpx.Client() as client:
        resp = client.post(
            token_url,
            headers=headers,
            auth=(settings.FREEAGENT_CLIENT_ID, settings.FREEAGENT_CLIENT_SECRET),
            data=payload,
        )
        resp.raise_for_status()
        return resp.json()
