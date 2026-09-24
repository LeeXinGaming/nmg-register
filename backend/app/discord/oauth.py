import httpx
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import jwt, JWTError
from app.config import settings
from app.utils.logger import logger

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = f"{DISCORD_API_BASE}/oauth2/token"

def generate_oauth_url(user_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Generate Discord OAuth2 authorization URL with signed state token for CSRF defense.
    """
    state_payload = {
        "uid": user_id or "anonymous",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    state = jwt.encode(state_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    params = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds guilds.members.read",
        "state": state,
        "prompt": "consent"
    }

    url = f"{DISCORD_OAUTH_URL}?{urllib.parse.urlencode(params)}"
    return url, state

def verify_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Verify signed OAuth2 state parameter"""
    try:
        payload = jwt.decode(state, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for Discord access and refresh tokens.
    """
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.DISCORD_REDIRECT_URI
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(DISCORD_TOKEN_URL, data=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to exchange OAuth code: status={response.status_code}, body={response.text}")
            raise Exception(f"Discord OAuth token exchange failed: {response.text}")
        return response.json()

async def refresh_discord_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an expired Discord access token.
    """
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(DISCORD_TOKEN_URL, data=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to refresh Discord token: {response.text}")
            raise Exception(f"Discord OAuth token refresh failed: {response.text}")
        return response.json()

async def fetch_discord_user(access_token: str) -> Dict[str, Any]:
    """
    Fetch the authorized Discord user's profile.
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch Discord user: {response.text}")
            raise Exception(f"Failed to fetch Discord user: {response.text}")
        return response.json()

async def fetch_guild_member_oauth(access_token: str, guild_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch guild member info using user's access token if guilds.members.read scope was granted.
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{DISCORD_API_BASE}/users/@me/guilds/{guild_id}/member", headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None # Not a member of the guild
        else:
            logger.warning(f"Guild member fetch returned status {response.status_code}: {response.text}")
            return None
