import asyncio
import discord
from typing import Optional, Dict, Any, List, Tuple
from app.config import settings
from app.utils.logger import logger
from app.discord.bot import bot, create_nmc_embed, send_to_log_channel, COLOR_SUCCESS, COLOR_DANGER, COLOR_GOLD, COLOR_INFO
from app.database import (
    get_user_by_discord_id,
    record_role_assignment,
    mark_role_removed,
    add_audit_log,
    UserModel
)

class DiscordRoleService:
    """
    Centralized, idempotent Discord Role Assignment & Verification Service
    Enforces security, rate-limit backoff, role hierarchy checks, and audit logging.
    """

    @classmethod
    def get_guild(cls) -> Optional[discord.Guild]:
        if settings.DISCORD_GUILD_ID and settings.DISCORD_GUILD_ID.isdigit():
            guild = bot.get_guild(int(settings.DISCORD_GUILD_ID))
            if guild:
                return guild
        # Fallback to the first connected guild if only 1 guild
        if bot.guilds:
            return bot.guilds[0]
        return None

    @classmethod
    async def get_member(cls, discord_user_id: str) -> Optional[discord.Member]:
        guild = cls.get_guild()
        if not guild:
            return None
        try:
            uid = int(discord_user_id)
        except ValueError:
            return None

        # Check local cache first
        member = guild.get_member(uid)
        if member:
            return member
        # Fallback to API fetch
        try:
            member = await guild.fetch_member(uid)
            return member
        except (discord.NotFound, discord.HTTPException):
            return None

    @classmethod
    async def isGuildMember(cls, discord_user_id: str) -> bool:
        """Check if user is currently in the NMC SERVER Discord guild"""
        member = await cls.get_member(discord_user_id)
        return member is not None

    @classmethod
    async def hasRole(cls, discord_user_id: str, role_id: str) -> bool:
        """Check if member currently has a specific Discord role"""
        member = await cls.get_member(discord_user_id)
        if not member:
            return False
        try:
            rid = int(role_id)
            return any(r.id == rid for r in member.roles)
        except ValueError:
            return False

    @classmethod
    async def _assign_role_internal(
        cls,
        discord_user_id: str,
        role_id: str,
        role_name_display: str,
        reason: str,
        admin_discord_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Internal robust role assignment with:
        - Guild & member check
        - Idempotency check
        - Bot role hierarchy validation
        - Discord 429 rate limit backoff retry
        - Database tracking & audit log
        """
        guild = cls.get_guild()
        if not guild:
            err = "NMC SERVER Discord Guild not found or bot not in guild. Please check DISCORD_GUILD_ID."
            logger.error(err)
            return False, err

        member = await cls.get_member(discord_user_id)
        if not member:
            err = "User is not a member of NMC SERVER. Please join the Discord server first."
            logger.warning(f"Role assign failed: {err} (User ID: {discord_user_id})")
            return False, err

        # 1. Search role by ID
        role = None
        if role_id and role_id.isdigit():
            role = guild.get_role(int(role_id))

        # 2. Fallback: Search role by name
        if not role:
            for r in guild.roles:
                if r.name.strip() == role_name_display.strip() or role_name_display in r.name:
                    role = r
                    break

        if not role:
            err = f"Discord role '{role_name_display}' (ID: {role_id}) not found on server."
            logger.error(err)
            return False, err

        # IDEMPOTENCY: Check if user already has this role
        if role in member.roles:
            logger.info(f"User {member.name} ({discord_user_id}) already has role {role.name}. Skipping assignment.")
            await record_role_assignment(discord_user_id, str(role.id), status="ASSIGNED")
            return True, f"User already has role {role.name}."

        # Assign role with 429 rate limit retry
        max_retries = 3
        backoff = 1.0
        success = False

        for attempt in range(max_retries):
            try:
                await member.add_roles(role, reason=reason)
                success = True
                break
            except discord.RateLimited as rl:
                retry_after = getattr(rl, 'retry_after', backoff)
                logger.warning(f"Discord 429 Rate limited. Waiting {retry_after}s (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(retry_after)
                backoff *= 2
            except discord.Forbidden:
                bot_member = guild.me
                bot_top_name = bot_member.top_role.name if bot_member and bot_member.top_role else "NMG REGISTER"
                err = (
                    f"Discord Permission Notice: Bot lacks permission to assign '{role.name}'. "
                    f"Please drag the '{bot_top_name}' role ABOVE '{role.name}' in Server Settings -> Roles."
                )
                logger.warning(err)
                return False, err
            except Exception as e:
                logger.error(f"Unexpected error assigning role: {e}")
                return False, f"Discord API error: {str(e)}"

        if not success:
            return False, "Failed to assign role due to rate limiting or connection failure."

        # Persist to database
        user = await get_user_by_discord_id(discord_user_id)
        user_id = user.id if user else None
        await record_role_assignment(discord_user_id, str(role.id), user_id=user_id, status="ASSIGNED")

        # Record audit log
        await add_audit_log(
            action="ROLE_ASSIGNED",
            admin_discord_id=admin_discord_id,
            target_discord_id=discord_user_id,
            role_id=str(role.id),
            reason=reason,
            metadata={"role_name": role.name, "member_username": member.name}
        )

        # Dispatch log embed
        embed = create_nmc_embed(
            title="Discord Role Assigned",
            description=f"Role **{role.name}** was assigned to <@{discord_user_id}>.",
            color=COLOR_SUCCESS,
            fields=[
                {"name": "Target Member", "value": f"**{member.name}** (`{discord_user_id}`)", "inline": True},
                {"name": "Role", "value": f"**{role.name}**", "inline": True},
                {"name": "Assigned By", "value": f"<@{admin_discord_id}>" if admin_discord_id else "System Automation", "inline": True},
                {"name": "Reason", "value": reason, "inline": False}
            ]
        )
        await send_to_log_channel(embed)

        logger.info(f"Successfully assigned role '{role.name}' to {member.name} ({discord_user_id})")
        return True, f"Role {role.name} successfully assigned."

    @classmethod
    async def assignCitizenRole(cls, discord_user_id: str) -> Tuple[bool, str]:
        """
        Assign 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role automatically upon website registration & Discord verification.
        """
        role_id = settings.NMC_CITIZEN_ROLE_ID
        return await cls._assign_role_internal(
            discord_user_id=discord_user_id,
            role_id=role_id,
            role_name_display="𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍",
            reason="Automated website registration & Discord account verification"
        )

    @classmethod
    async def assignPlayerRole(cls, discord_user_id: str) -> Tuple[bool, str]:
        """
        Assign 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role automatically when FiveM account is linked.
        """
        role_id = settings.NMC_PLAYER_ROLE_ID
        return await cls._assign_role_internal(
            discord_user_id=discord_user_id,
            role_id=role_id,
            role_name_display="𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑",
            reason="Automated FiveM account linking"
        )

    @classmethod
    async def assignServerTeamRole(
        cls,
        discord_user_id: str,
        admin_discord_id: str,
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        SECURE ADMIN ONLY: Assign 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 role.
        Never called automatically during registration.
        """
        role_id = settings.NMC_SERVER_TEAM_ROLE_ID
        action_reason = reason or "Manual administrator role assignment via /staffrole"
        return await cls._assign_role_internal(
            discord_user_id=discord_user_id,
            role_id=role_id,
            role_name_display="𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌",
            reason=action_reason,
            admin_discord_id=admin_discord_id
        )

    @classmethod
    async def removeRole(
        cls,
        discord_user_id: str,
        role_id: str,
        admin_discord_id: Optional[str] = None,
        reason: Optional[str] = "Manual role removal"
    ) -> Tuple[bool, str]:
        """Remove a Discord role and record audit history"""
        guild = cls.get_guild()
        if not guild:
            return False, "Guild not found"

        member = await cls.get_member(discord_user_id)
        if not member:
            return False, "Member not found in guild"

        try:
            target_role_id = int(role_id)
        except ValueError:
            return False, "Invalid role ID"

        role = guild.get_role(target_role_id)
        if not role:
            return False, "Role not found in guild"

        if role not in member.roles:
            return True, f"Member does not have role {role.name}."

        try:
            await member.remove_roles(role, reason=reason)
            await mark_role_removed(discord_user_id, str(role.id))
            await add_audit_log(
                action="ROLE_REMOVED",
                admin_discord_id=admin_discord_id,
                target_discord_id=discord_user_id,
                role_id=str(role.id),
                reason=reason,
                metadata={"role_name": role.name, "member_username": member.name}
            )

            embed = create_nmc_embed(
                title="Discord Role Removed",
                description=f"Role **{role.name}** was removed from <@{discord_user_id}>.",
                color=COLOR_DANGER,
                fields=[
                    {"name": "Target Member", "value": f"**{member.name}** (`{discord_user_id}`)", "inline": True},
                    {"name": "Role Removed", "value": f"**{role.name}**", "inline": True},
                    {"name": "Removed By", "value": f"<@{admin_discord_id}>" if admin_discord_id else "System", "inline": True},
                    {"name": "Reason", "value": reason, "inline": False}
                ]
            )
            await send_to_log_channel(embed)

            return True, f"Role {role.name} successfully removed."
        except Exception as e:
            logger.error(f"Failed to remove role: {e}")
            return False, f"Failed to remove role: {str(e)}"

    @classmethod
    async def syncRoles(cls, discord_user_id: str) -> Dict[str, Any]:
        """
        Synchronize user roles between website database state and Discord:
        1. Check if user is in NMC SERVER.
        2. If website registered & linked -> ensure 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 is assigned.
        3. If FiveM linked -> ensure 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 is assigned.
        4. NEVER grant 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 automatically.
        """
        is_member = await cls.isGuildMember(discord_user_id)
        if not is_member:
            return {
                "success": False,
                "is_guild_member": False,
                "message": "Please join the NMC SERVER Discord before role synchronization.",
                "assigned_roles": [],
                "current_roles": []
            }

        user = await get_user_by_discord_id(discord_user_id)
        assigned = []

        if user and user.discord_linked:
            # Citizen role check
            has_citizen = await cls.hasRole(discord_user_id, settings.NMC_CITIZEN_ROLE_ID)
            if not has_citizen:
                ok, msg = await cls.assignCitizenRole(discord_user_id)
                if ok:
                    assigned.append("𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍")

            # Player role check
            if user.fivem_linked:
                has_player = await cls.hasRole(discord_user_id, settings.NMC_PLAYER_ROLE_ID)
                if not has_player:
                    ok, msg = await cls.assignPlayerRole(discord_user_id)
                    if ok:
                        assigned.append("𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑")

        # Get all current NMC roles for the user
        member = await cls.get_member(discord_user_id)
        current = []
        if member:
            for r in member.roles:
                if str(r.id) in {settings.NMC_CITIZEN_ROLE_ID, settings.NMC_PLAYER_ROLE_ID, settings.NMC_SERVER_TEAM_ROLE_ID}:
                    current.append(r.name)

        return {
            "success": True,
            "is_guild_member": True,
            "message": "Roles synchronized successfully.",
            "assigned_roles": assigned,
            "current_roles": current
        }
