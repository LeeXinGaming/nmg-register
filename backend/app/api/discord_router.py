import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.utils.logger import logger
from app.utils.crypto import encrypt_token
from app.auth.security import get_current_user
from app.database import (
    UserModel,
    update_user_discord,
    save_discord_link,
    delete_discord_link,
    get_user_by_id,
    get_user_by_discord_id,
    add_audit_log
)
from app.discord.oauth import (
    generate_oauth_url,
    verify_oauth_state,
    exchange_code_for_token,
    fetch_discord_user
)
from app.discord.service import DiscordRoleService
from app.discord.roles import ROLE_CONFIGS
from app.models.schemas import (
    DiscordStatusResponse,
    DiscordRoleInfo,
    SyncRolesResponse,
    DiscordLinkRequest
)

router = APIRouter(prefix="/api/discord", tags=["Discord"])

@router.get("/login")
async def discord_login(user_id: Optional[str] = Query(None)):
    """
    Generate Discord OAuth2 authorization URL with signed CSRF state.
    """
    url, state = generate_oauth_url(user_id=user_id)
    return {"url": url, "state": state}

@router.get("/callback")
async def discord_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """
    Discord OAuth2 redirect callback:
    1. Validate state and error.
    2. Exchange authorization code for Discord tokens.
    3. Fetch Discord user profile.
    4. Link to user account.
    5. Check NMC SERVER guild membership.
    6. Automatically assign 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role if member.
    7. Redirect to frontend with status.
    """
    if error:
        logger.warning(f"Discord OAuth cancelled or failed: {error} - {error_description}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?discord_error={error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state in OAuth callback")

    state_data = verify_oauth_state(state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    user_id = state_data.get("uid")

    try:
        # 1. Exchange code
        token_data = await exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 604800)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # 2. Fetch Discord user identity
        d_user = await fetch_discord_user(access_token)
        discord_id = str(d_user["id"])
        discord_username = d_user.get("username", "")
        discord_global_name = d_user.get("global_name")
        discord_avatar = d_user.get("avatar")

        # 3. Find or link user
        target_user = None
        if user_id and user_id != "anonymous":
            target_user = await get_user_by_id(user_id)
        if not target_user:
            # Check if an existing website user has this discord_id
            target_user = await get_user_by_discord_id(discord_id)

        if target_user:
            # Encrypt tokens securely before saving
            enc_access = encrypt_token(access_token)
            enc_refresh = encrypt_token(refresh_token)

            await save_discord_link(
                user_id=target_user.id,
                discord_id=discord_id,
                access_token_encrypted=enc_access,
                refresh_token_encrypted=enc_refresh,
                expires_at=expires_at
            )

            await update_user_discord(
                user_id=target_user.id,
                discord_id=discord_id,
                discord_username=discord_username,
                discord_global_name=discord_global_name,
                discord_avatar=discord_avatar,
                discord_linked=True
            )

            # 4. Check guild membership & automatically assign 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role
            is_member = await DiscordRoleService.isGuildMember(discord_id)
            citizen_assigned = False

            if is_member:
                ok, msg = await DiscordRoleService.assignCitizenRole(discord_id)
                citizen_assigned = ok

                # If user already had FiveM linked, also give 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑
                if target_user.fivem_linked:
                    await DiscordRoleService.assignPlayerRole(discord_id)

            await add_audit_log(
                action="DISCORD_LINKED",
                target_discord_id=discord_id,
                reason="User linked Discord account via OAuth2",
                metadata={
                    "user_id": target_user.id,
                    "discord_username": discord_username,
                    "is_guild_member": is_member,
                    "citizen_assigned": citizen_assigned
                }
            )

            # Redirect to frontend dashboard with success
            redirect_url = f"{settings.FRONTEND_URL}/dashboard?discord_linked=true&is_member={str(is_member).lower()}&citizen_assigned={str(citizen_assigned).lower()}"
            return RedirectResponse(url=redirect_url)
        else:
            # Anonymous OAuth registration - pass info to frontend to complete register
            redirect_url = f"{settings.FRONTEND_URL}/register?discord_id={discord_id}&discord_username={discord_username}"
            return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"Error handling Discord OAuth callback: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?discord_error=oauth_failed")

@router.post("/link")
async def link_discord_account(
    req: DiscordLinkRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Direct POST endpoint to link Discord using authorization code.
    """
    token_data = await exchange_code_for_token(req.code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 604800)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    d_user = await fetch_discord_user(access_token)
    discord_id = str(d_user["id"])
    discord_username = d_user.get("username", "")
    discord_global_name = d_user.get("global_name")
    discord_avatar = d_user.get("avatar")

    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token)

    await save_discord_link(
        user_id=current_user.id,
        discord_id=discord_id,
        access_token_encrypted=enc_access,
        refresh_token_encrypted=enc_refresh,
        expires_at=expires_at
    )

    await update_user_discord(
        user_id=current_user.id,
        discord_id=discord_id,
        discord_username=discord_username,
        discord_global_name=discord_global_name,
        discord_avatar=discord_avatar,
        discord_linked=True
    )

    is_member = await DiscordRoleService.isGuildMember(discord_id)
    citizen_assigned = False
    if is_member:
        ok, msg = await DiscordRoleService.assignCitizenRole(discord_id)
        citizen_assigned = ok

    return {
        "success": True,
        "discord_id": discord_id,
        "discord_username": discord_username,
        "is_guild_member": is_member,
        "citizen_assigned": citizen_assigned
    }

@router.post("/unlink")
async def unlink_discord_account(current_user: UserModel = Depends(get_current_user)):
    """
    Unlink Discord account from website profile.
    """
    if not current_user.discord_linked or not current_user.discord_id:
        raise HTTPException(status_code=400, detail="No Discord account is currently linked.")

    discord_id = current_user.discord_id
    await delete_discord_link(current_user.id)
    await update_user_discord(
        user_id=current_user.id,
        discord_id=None,
        discord_username=None,
        discord_global_name=None,
        discord_avatar=None,
        discord_linked=False
    )

    await add_audit_log(
        action="DISCORD_UNLINKED",
        target_discord_id=discord_id,
        reason="User unlinked Discord account from website dashboard",
        metadata={"user_id": current_user.id}
    )

    return {"success": True, "message": "Discord account unlinked successfully."}

@router.get("/status", response_model=DiscordStatusResponse)
async def get_discord_status(current_user: UserModel = Depends(get_current_user)):
    """
    Check Discord connection, NMC SERVER guild membership, and active role statuses.
    """
    if not current_user.discord_linked or not current_user.discord_id:
        # Return unlinked template
        roles_list = [
            DiscordRoleInfo(
                id=c["id"],
                name=c["name"],
                type=c["type"],
                assigned=False,
                description=c["description"]
            )
            for c in ROLE_CONFIGS
        ]
        return DiscordStatusResponse(
            connected=False,
            is_guild_member=False,
            roles=roles_list,
            message="Please connect your Discord account first."
        )

    discord_id = current_user.discord_id
    is_member = await DiscordRoleService.isGuildMember(discord_id)

    # Check which roles are assigned
    roles_list = []
    for c in ROLE_CONFIGS:
        has_r = False
        if is_member:
            has_r = await DiscordRoleService.hasRole(discord_id, c["id"])
        roles_list.append(DiscordRoleInfo(
            id=c["id"],
            name=c["name"],
            type=c["type"],
            assigned=has_r,
            description=c["description"]
        ))

    avatar_url = None
    if current_user.discord_avatar and current_user.discord_id:
        avatar_url = f"https://cdn.discordapp.com/avatars/{current_user.discord_id}/{current_user.discord_avatar}.png"

    msg = None
    if not is_member:
        msg = "Please join the NMC SERVER Discord before verification."

    return DiscordStatusResponse(
        connected=True,
        discord_user_id=current_user.discord_id,
        discord_username=current_user.discord_username,
        discord_global_name=current_user.discord_global_name,
        avatar_url=avatar_url,
        is_guild_member=is_member,
        guild_name="NMC SERVER",
        roles=roles_list,
        message=msg
    )

@router.post("/sync", response_model=SyncRolesResponse)
async def sync_user_roles(current_user: UserModel = Depends(get_current_user)):
    """
    Trigger on-demand role synchronization between website account and Discord.
    """
    if not current_user.discord_linked or not current_user.discord_id:
        raise HTTPException(status_code=400, detail="Please connect your Discord account first.")

    res = await DiscordRoleService.syncRoles(current_user.discord_id)
    return SyncRolesResponse(
        success=res["success"],
        message=res["message"],
        is_guild_member=res["is_guild_member"],
        assigned_roles=res.get("assigned_roles", []),
        current_roles=res.get("current_roles", [])
    )

@router.get("/roles")
async def get_roles_list():
    """
    Get public list of configured NMC roles.
    """
    return {"roles": ROLE_CONFIGS}
