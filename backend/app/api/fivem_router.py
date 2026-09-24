from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import FiveMLinkRequest, FiveMLinkResponse
from app.auth.security import get_current_user
from app.database import (
    UserModel,
    update_user_fivem,
    get_user_by_fivem,
    add_audit_log
)
from app.discord.service import DiscordRoleService
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/api/fivem", tags=["FiveM"])

@router.post("/link", response_model=FiveMLinkResponse)
async def link_fivem(
    req: FiveMLinkRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Link FiveM player account:
    1. Validates identifier format.
    2. Check if already linked to another account.
    3. Update user profile.
    4. Automatically assigns 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role on Discord!
    """
    ident = req.identifier.strip()
    if len(ident) < 4:
        raise HTTPException(status_code=400, detail="Invalid FiveM identifier.")

    # Check uniqueness
    existing = await get_user_by_fivem(ident)
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="This FiveM identifier is already linked to another registered account."
        )

    await update_user_fivem(current_user.id, ident, True)
    logger.info(f"User {current_user.username} linked FiveM identifier: {ident}")

    player_role_assigned = False
    # If Discord is linked and member of guild, automatically assign 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑!
    if current_user.discord_linked and current_user.discord_id:
        is_member = await DiscordRoleService.isGuildMember(current_user.discord_id)
        if is_member:
            ok, msg = await DiscordRoleService.assignPlayerRole(current_user.discord_id)
            player_role_assigned = ok

    await add_audit_log(
        action="FIVEM_LINKED",
        target_discord_id=current_user.discord_id,
        reason=f"FiveM account {ident} linked to user {current_user.username}",
        metadata={"fivem_identifier": ident, "player_role_assigned": player_role_assigned}
    )

    return FiveMLinkResponse(
        success=True,
        message="FiveM account successfully linked! 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role assigned." if player_role_assigned else "FiveM account linked! Connect Discord to receive your 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role.",
        fivem_identifier=ident,
        player_role_assigned=player_role_assigned
    )

@router.post("/unlink")
async def unlink_fivem(current_user: UserModel = Depends(get_current_user)):
    """
    Unlink FiveM identifier and remove 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role.
    """
    if not current_user.fivem_linked:
        raise HTTPException(status_code=400, detail="No FiveM account is currently linked.")

    old_ident = current_user.fivem_identifier
    await update_user_fivem(current_user.id, None, False)

    if current_user.discord_linked and current_user.discord_id:
        await DiscordRoleService.removeRole(
            discord_user_id=current_user.discord_id,
            role_id=settings.NMC_PLAYER_ROLE_ID,
            reason="FiveM account unlinked by user"
        )

    await add_audit_log(
        action="FIVEM_UNLINKED",
        target_discord_id=current_user.discord_id,
        reason=f"FiveM account {old_ident} unlinked",
        metadata={"previous_identifier": old_ident}
    )

    return {"success": True, "message": "FiveM account unlinked successfully."}
