import json
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.schemas import RoleOperationRequest, AuditLogItem
from app.auth.security import get_current_admin
from app.database import UserModel, get_recent_audit_logs
from app.discord.service import DiscordRoleService
from app.config import settings

router = APIRouter(prefix="/api/admin/discord", tags=["Admin Operations"])

@router.post("/assign-role")
async def admin_assign_role(
    req: RoleOperationRequest,
    current_admin: UserModel = Depends(get_current_admin)
):
    """
    SECURE ADMIN ENDPOINT: Manually assign Discord roles (including 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌).
    Enforces authorization, records audit logs, and validates role hierarchy.
    """
    admin_identifier = current_admin.discord_id or f"web_admin:{current_admin.username}"

    if req.role_id == settings.NMC_SERVER_TEAM_ROLE_ID:
        # Staff role assignment
        success, msg = await DiscordRoleService.assignServerTeamRole(
            discord_user_id=req.discord_user_id,
            admin_discord_id=admin_identifier,
            reason=req.reason
        )
    elif req.role_id == settings.NMC_CITIZEN_ROLE_ID:
        success, msg = await DiscordRoleService.assignCitizenRole(req.discord_user_id)
    elif req.role_id == settings.NMC_PLAYER_ROLE_ID:
        success, msg = await DiscordRoleService.assignPlayerRole(req.discord_user_id)
    else:
        # Generic role assignment
        success, msg = await DiscordRoleService._assign_role_internal(
            discord_user_id=req.discord_user_id,
            role_id=req.role_id,
            role_name_display="Custom Role",
            reason=req.reason,
            admin_discord_id=admin_identifier
        )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg}

@router.post("/remove-role")
async def admin_remove_role(
    req: RoleOperationRequest,
    current_admin: UserModel = Depends(get_current_admin)
):
    """
    SECURE ADMIN ENDPOINT: Remove a Discord role.
    """
    admin_identifier = current_admin.discord_id or f"web_admin:{current_admin.username}"
    success, msg = await DiscordRoleService.removeRole(
        discord_user_id=req.discord_user_id,
        role_id=req.role_id,
        admin_discord_id=admin_identifier,
        reason=req.reason
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg}

@router.get("/logs", response_model=List[AuditLogItem])
async def get_audit_log_list(current_admin: UserModel = Depends(get_current_admin)):
    """
    Retrieve recent audit logs for role assignments, joins, leaves, and staff actions.
    """
    logs = await get_recent_audit_logs(limit=50)
    result = []
    for l in logs:
        meta = {}
        if l.meta_json:
            try:
                meta = json.loads(l.meta_json)
            except Exception:
                meta = {}
        result.append(AuditLogItem(
            id=l.id,
            action=l.action,
            admin_discord_id=l.admin_discord_id,
            target_discord_id=l.target_discord_id,
            role_id=l.role_id,
            reason=l.reason,
            metadata=meta,
            created_at=l.created_at
        ))
    return result
