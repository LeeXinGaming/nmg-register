import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.config import settings
from app.utils.logger import logger
from app.database import (
    get_user_by_discord_id,
    record_role_assignment,
    add_audit_log,
    UserModel
)

intents = discord.Intents.default()
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# Colors for Embeds
COLOR_SUCCESS = 0x10B981 # Emerald Green
COLOR_GOLD = 0xF59E0B    # NMC Gold/Amber
COLOR_DANGER = 0xEF4444  # Crimson Red
COLOR_INFO = 0x06B6D4    # Cyan

def create_nmc_embed(
    title: str,
    description: str,
    color: int = COLOR_GOLD,
    fields: Optional[List[Dict[str, Any]]] = None,
    thumbnail_url: Optional[str] = None
) -> discord.Embed:
    """Create a standardized high-aesthetics NMC SERVER embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    if fields:
        for f in fields:
            embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="NMC SERVER — Automated Verification System", icon_url=bot.user.display_avatar.url if bot.user else None)
    return embed

def create_verification_success_embed(
    fivem_linked: bool = False,
    avatar_url: Optional[str] = None,
    extra_note: Optional[str] = None,
    daily_count: Optional[int] = None
) -> discord.Embed:
    """
    Exact requested registration verified embed:
    Title: NMC SERVER — Registration Verified
    Description: Your NMC SERVER account has been successfully verified.
    Roles:
    ✅ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍
    If FiveM linked:
    ✅ 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑
    Footer: NMC SERVER • Daily Registrations: X/3
    """
    roles_lines = ["✅ **𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍**"]
    if fivem_linked:
        roles_lines.append("✅ **𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑**")

    voice_ch_id = getattr(settings, "NMC_REGISTERED_VOICE_CHANNEL_ID", "1550320871128957018")
    desc = (
        "Your NMC SERVER account has been successfully verified.\n"
        f"🔊 **Voice Channel Access Unlocked:** You can now join <#{voice_ch_id}> (**🎙️・𝐍𝐈𝐆𝐇𝐓𝐌𝐀𝐑𝐄 𝐅𝐀𝐌**)."
    )

    embed = discord.Embed(
        title="NMC SERVER — Registration Verified",
        description=desc,
        color=COLOR_SUCCESS,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(
        name="Roles:",
        value="\n".join(roles_lines),
        inline=False
    )
    if extra_note:
        embed.add_field(name="Notice:", value=extra_note, inline=False)
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    footer_text = "NMC SERVER"
    if daily_count is not None:
        footer_text += f" • Daily Registrations: {daily_count}/3"
    embed.set_footer(text=footer_text)
    return embed

async def send_to_log_channel(embed: discord.Embed):
    """Dispatch an embed to the configured DISCORD_LOG_CHANNEL_ID"""
    if not settings.DISCORD_LOG_CHANNEL_ID:
        return
    try:
        channel_id = int(settings.DISCORD_LOG_CHANNEL_ID)
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
    except Exception as e:
        logger.warning(f"Could not send log to Discord channel: {e}")

async def deploy_registration_panel(target_channel_id: Optional[int] = None) -> bool:
    """
    Deploys or updates the official NMC SERVER interactive registration panel
    with buttons: Register Account, Link FiveM, Sync Roles, My Roles & Status.
    """
    ch_id = target_channel_id
    if not ch_id and getattr(settings, "DISCORD_REGISTER_CHANNEL_ID", None):
        if settings.DISCORD_REGISTER_CHANNEL_ID.isdigit():
            ch_id = int(settings.DISCORD_REGISTER_CHANNEL_ID)

    if not ch_id:
        return False

    channel = bot.get_channel(ch_id)
    if not channel:
        try:
            channel = await bot.fetch_channel(ch_id)
        except Exception as e:
            logger.warning(f"Could not fetch registration channel {ch_id}: {e}")
            return False

    from app.discord.commands import RegistrationPanelView
    panel_view = RegistrationPanelView()
    embed = create_nmc_embed(
        title="🏛️ NMC SERVER — Official Registration & Role Verification",
        description=(
            "Welcome to **NMC SERVER**!\n\n"
            "Use the interactive buttons below to register your account, link your FiveM identity, "
            "and automatically receive your server roles:\n\n"
            "• Click **`📝 Register Account`** to create your account & receive **`✅ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍`**.\n"
            "• Click **`🎮 Link FiveM`** to link your in-game identity & receive **`✅ 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑`**.\n"
            "• Click **`🔄 Sync Roles`** to refresh your active permissions at any time.\n"
            "• Click **`📋 My Roles & Status`** to view your active roles and verification status.\n\n"
            "🔒 *Note: 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 is protected and assigned only by server administrators.*"
        ),
        color=COLOR_GOLD,
        fields=[
            {"name": "Web Registration Portal", "value": f"[Open Web Dashboard]({settings.FRONTEND_URL})", "inline": False},
            {"name": "Daily Registration Limit", "value": "Maximum **3 accounts per 24 hours** per member.", "inline": False}
        ]
    )

    try:
        found_msg = None
        async for msg in channel.history(limit=10):
            if msg.author.id == bot.user.id and msg.components:
                found_msg = msg
                break

        if found_msg:
            await found_msg.edit(embed=embed, view=panel_view)
            logger.info(f"Updated active registration panel in #{channel.name} ({channel.id})")
        else:
            await channel.send(embed=embed, view=panel_view)
            logger.info(f"Deployed new registration panel to #{channel.name} ({channel.id})")
        return True
    except Exception as e:
        logger.error(f"Error deploying registration panel in #{channel.name}: {e}")
        return False

async def ensure_voice_channel_permissions():
    """Ensure registered citizens and players have connect and view permissions on the designated voice channel"""
    voice_id = getattr(settings, "NMC_REGISTERED_VOICE_CHANNEL_ID", None)
    if not voice_id or not voice_id.isdigit():
        return

    guild_id = int(settings.DISCORD_GUILD_ID) if settings.DISCORD_GUILD_ID.isdigit() else None
    if not guild_id:
        return

    guild = bot.get_guild(guild_id)
    if not guild:
        return

    ch = guild.get_channel(int(voice_id))
    if not ch:
        try:
            ch = await bot.fetch_channel(int(voice_id))
        except Exception as e:
            logger.warning(f"Could not fetch voice channel {voice_id}: {e}")
            return

    citizen_role = guild.get_role(int(settings.NMC_CITIZEN_ROLE_ID)) if settings.NMC_CITIZEN_ROLE_ID.isdigit() else None
    player_role = guild.get_role(int(settings.NMC_PLAYER_ROLE_ID)) if settings.NMC_PLAYER_ROLE_ID.isdigit() else None

    overwrite = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
    category_overwrite = discord.PermissionOverwrite(view_channel=True)

    try:
        if citizen_role:
            await ch.set_permissions(citizen_role, overwrite=overwrite, reason="Allow registered NMC Citizens to join voice channel")
        if player_role:
            await ch.set_permissions(player_role, overwrite=overwrite, reason="Allow linked NMC Players to join voice channel")

        if ch.category:
            if citizen_role:
                await ch.category.set_permissions(citizen_role, overwrite=category_overwrite, reason="Allow registered NMC Citizens to view voice category")
            if player_role:
                await ch.category.set_permissions(player_role, overwrite=category_overwrite, reason="Allow linked NMC Players to view voice category")

        logger.info(f"Voice channel #{ch.name} ({ch.id}) permissions configured for registered members.")
    except Exception as e:
        logger.error(f"Error configuring voice channel permissions: {e}")

@bot.event
async def on_ready():
    logger.info(f"Discord Bot connected as: {bot.user} (ID: {bot.user.id})")
    logger.info(f"Bot connected to {len(bot.guilds)} guild(s)")

    # Check guild presence
    guild_id = int(settings.DISCORD_GUILD_ID) if settings.DISCORD_GUILD_ID.isdigit() else None
    if guild_id:
        target_guild = bot.get_guild(guild_id)
        if target_guild:
            logger.info(f"Found target guild: '{target_guild.name}' (ID: {target_guild.id})")
            
            # Check configured roles
            citizen_role = target_guild.get_role(int(settings.NMC_CITIZEN_ROLE_ID)) if settings.NMC_CITIZEN_ROLE_ID.isdigit() else None
            player_role = target_guild.get_role(int(settings.NMC_PLAYER_ROLE_ID)) if settings.NMC_PLAYER_ROLE_ID.isdigit() else None
            team_role = target_guild.get_role(int(settings.NMC_SERVER_TEAM_ROLE_ID)) if settings.NMC_SERVER_TEAM_ROLE_ID.isdigit() else None

            logger.info(f"Role Check -> CITIZEN: {citizen_role.name if citizen_role else 'NOT FOUND'}")
            logger.info(f"Role Check -> PLAYER: {player_role.name if player_role else 'NOT FOUND'}")
            logger.info(f"Role Check -> SERVER TEAM: {team_role.name if team_role else 'NOT FOUND'}")

            # Check bot role hierarchy
            if target_guild.me and citizen_role:
                bot_top = target_guild.me.top_role
                if bot_top.position <= citizen_role.position:
                    logger.warning(
                        f"CRITICAL ROLE HIERARCHY NOTICE: Bot role '{bot_top.name}' (position {bot_top.position}) "
                        f"is below '{citizen_role.name}' (position {citizen_role.position}). "
                        f"Please open Discord Server Settings -> Roles and drag '{bot_top.name}' ABOVE '{citizen_role.name}' "
                        f"so the bot has permission to assign it!"
                    )
        else:
            logger.warning(
                f"Target Guild ID {settings.DISCORD_GUILD_ID} not found in bot's guilds."
            )

    # Register persistent interactive button view
    try:
        from app.discord.commands import RegistrationPanelView
        bot.add_view(RegistrationPanelView())
        logger.info("Persistent RegistrationPanelView registered.")
    except Exception as e:
        logger.warning(f"Could not register persistent view: {e}")

    # Sync slash commands with guild or globally
    try:
        if guild_id:
            guild_obj = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild_obj)
            synced = await bot.tree.sync(guild=guild_obj)
            logger.info(f"Synchronized {len(synced)} slash commands to NMC SERVER guild.")
        else:
            synced = await bot.tree.sync()
            logger.info(f"Synchronized {len(synced)} slash commands globally.")
    except Exception as e:
        logger.warning(f"Error syncing slash commands: {e}")

    # Automatically deploy / refresh registration panel in configured registration channel (1549509737060638751)
    try:
        await deploy_registration_panel()
    except Exception as e:
        logger.warning(f"Error in initial deploy_registration_panel: {e}")

    # Ensure voice channel permissions for registered members (1550320871128957018)
    try:
        await ensure_voice_channel_permissions()
    except Exception as e:
        logger.warning(f"Error configuring voice channel permissions: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    """
    Automatic verification when a member joins NMC SERVER:
    1. Check whether their Discord account is linked to a website account.
    2. If linked, automatically assign 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍.
    3. If FiveM is also linked, automatically assign 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑.
    4. Log result to audit logs and log channel.
    """
    discord_id = str(member.id)
    logger.info(f"Member joined NMC SERVER: {member.name} ({discord_id})")

    user: Optional[UserModel] = await get_user_by_discord_id(discord_id)
    if not user or not user.discord_linked:
        logger.info(f"User {member.name} joined but is not linked to any website account yet.")
        return

    # User is linked! Auto-assign 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍
    roles_to_add = []
    assigned_names = []

    citizen_role_id = int(settings.NMC_CITIZEN_ROLE_ID) if settings.NMC_CITIZEN_ROLE_ID.isdigit() else None
    if citizen_role_id:
        citizen_role = member.guild.get_role(citizen_role_id)
        if citizen_role and citizen_role not in member.roles:
            roles_to_add.append(citizen_role)
            assigned_names.append("𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍")

    # If FiveM linked, also give 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑
    if user.fivem_linked:
        player_role_id = int(settings.NMC_PLAYER_ROLE_ID) if settings.NMC_PLAYER_ROLE_ID.isdigit() else None
        if player_role_id:
            player_role = member.guild.get_role(player_role_id)
            if player_role and player_role not in member.roles:
                roles_to_add.append(player_role)
                assigned_names.append("𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑")

    if roles_to_add:
        try:
            await member.add_roles(*roles_to_add, reason="Automatic role assignment on member join (linked website account)")
            for role in roles_to_add:
                await record_role_assignment(discord_id, str(role.id), user_id=user.id)
            
            await add_audit_log(
                action="MEMBER_JOIN_AUTO_ROLE",
                target_discord_id=discord_id,
                reason="Automatic assignment on join from website verification",
                metadata={"roles": [r.name for r in roles_to_add], "username": user.username}
            )

            # Send rich log embed
            embed = create_nmc_embed(
                title="Member Joined — Roles Auto-Assigned",
                description=f"Member <@{discord_id}> joined and was automatically verified with their website account **{user.username}**.",
                color=COLOR_SUCCESS,
                fields=[
                    {"name": "Assigned Roles", "value": "\n".join([f"✅ {name}" for name in assigned_names]), "inline": False},
                    {"name": "Website Account", "value": f"`{user.username}` (`{user.email}`)", "inline": True},
                    {"name": "FiveM Linked", "value": "Yes" if user.fivem_linked else "No", "inline": True}
                ]
            )
            await send_to_log_channel(embed)
            logger.info(f"Successfully auto-assigned roles to joining member {member.name}: {assigned_names}")
        except discord.Forbidden:
            logger.error(f"Missing permissions to assign roles to {member.name}. Check bot role hierarchy!")
        except Exception as e:
            logger.error(f"Failed to auto-assign roles on member join: {e}")

@bot.event
async def on_member_remove(member: discord.Member):
    """
    When member leaves NMC SERVER:
    Do not delete website account. Mark membership inactive and record audit log.
    """
    discord_id = str(member.id)
    logger.info(f"Member left NMC SERVER: {member.name} ({discord_id})")

    await add_audit_log(
        action="MEMBER_LEFT_GUILD",
        target_discord_id=discord_id,
        reason="Member left or was removed from Discord guild",
        metadata={"discord_username": member.name}
    )

    embed = create_nmc_embed(
        title="Member Left Guild",
        description=f"Discord user **{member.name}** (`{discord_id}`) left the server.",
        color=COLOR_DANGER
    )
    await send_to_log_channel(embed)

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """Audit role changes happening in the guild"""
    if before.roles != after.roles:
        added_roles = [r for r in after.roles if r not in before.roles]
        removed_roles = [r for r in before.roles if r not in after.roles]

        target_ids = {settings.NMC_CITIZEN_ROLE_ID, settings.NMC_PLAYER_ROLE_ID, settings.NMC_SERVER_TEAM_ROLE_ID}

        for r in added_roles:
            if str(r.id) in target_ids:
                await add_audit_log(
                    action="ROLE_ADDED_DISCORD",
                    target_discord_id=str(after.id),
                    role_id=str(r.id),
                    reason=f"Role {r.name} added in Discord",
                    metadata={"role_name": r.name}
                )

        for r in removed_roles:
            if str(r.id) in target_ids:
                await add_audit_log(
                    action="ROLE_REMOVED_DISCORD",
                    target_discord_id=str(after.id),
                    role_id=str(r.id),
                    reason=f"Role {r.name} removed in Discord",
                    metadata={"role_name": r.name}
                )

@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Discord command error: {error}")
