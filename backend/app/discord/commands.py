import discord
from discord import app_commands
from typing import Optional
from app.config import settings
from app.utils.logger import logger
from app.discord.bot import (
    bot,
    create_nmc_embed,
    create_verification_success_embed,
    send_to_log_channel,
    COLOR_SUCCESS,
    COLOR_DANGER,
    COLOR_GOLD,
    COLOR_INFO
)
from app.discord.service import DiscordRoleService
from app.database import (
    get_user_by_discord_id,
    get_recent_audit_logs,
    register_discord_user,
    update_user_fivem,
    add_audit_log,
    can_register_today,
    count_discord_daily_registrations,
    UserModel
)

def is_staff_member(interaction: discord.Interaction) -> bool:
    """Check if the user invoking the command is a staff member or administrator"""
    if not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    admin_roles = {settings.NMC_ADMIN_ROLE_ID, settings.NMC_SERVER_TEAM_ROLE_ID}
    user_role_ids = {str(r.id) for r in interaction.user.roles}
    return bool(admin_roles.intersection(user_role_ids))

# Global tree error handler to prevent "application did not respond"
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f"Global slash command error: {error}")
    try:
        msg = f"❌ An error occurred: {error}"
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to send error response to interaction: {e}")

# ==============================================================================
# DISCORD INTERACTIVE MODALS FOR IN-BOT REGISTRATION
# ==============================================================================

class NMCRegisterModal(discord.ui.Modal, title="NMC SERVER — Member Registration"):
    username_input = discord.ui.TextInput(
        label="Player Username / Character Name",
        placeholder="Enter your unique player username",
        min_length=3,
        max_length=32,
        required=True
    )
    email_input = discord.ui.TextInput(
        label="Email Address (Optional)",
        placeholder="user@example.com (or leave blank)",
        required=False
    )
    fivem_input = discord.ui.TextInput(
        label="FiveM Identifier / CFX ID (Optional)",
        placeholder="e.g. license:4a88f7..., steam:1100..., or CFX username",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Acknowledge immediately to prevent Discord interaction timeout
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)

        # 0. Check daily registration limit (Max 3 on 1 day)
        allowed, count, limit_msg = await can_register_today(discord_id)
        if not allowed:
            embed = create_nmc_embed(
                title="⚠️ Daily Registration Limit Reached",
                description=(
                    f"{interaction.user.mention}, you have already registered **{count}/3 accounts** today.\n\n"
                    f"**Server Rule:** Maximum 3 registrations per 24 hours.\n"
                    f"Please wait until tomorrow to register another account."
                ),
                color=COLOR_DANGER
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        raw_username = self.username_input.value.strip()
        raw_email = self.email_input.value.strip() if self.email_input.value else None
        raw_fivem = self.fivem_input.value.strip() if self.fivem_input.value else None

        avatar_url = interaction.user.display_avatar.url if interaction.user.display_avatar else None
        avatar_hash = interaction.user.avatar.key if interaction.user.avatar else None

        try:
            # 1. Register or update account in database
            user, is_new = await register_discord_user(
                discord_id=discord_id,
                username=raw_username,
                email=raw_email,
                fivem_identifier=raw_fivem,
                discord_global_name=interaction.user.global_name,
                discord_avatar=avatar_hash
            )

            # 2. Automatically assign 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role
            citizen_ok, citizen_msg = await DiscordRoleService.assignCitizenRole(discord_id)

            # 3. If FiveM identifier provided, automatically assign 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role
            player_ok = False
            player_msg = ""
            if raw_fivem:
                player_ok, player_msg = await DiscordRoleService.assignPlayerRole(discord_id)

            # 4. Generate the exact NMC SERVER — Registration Verified embed
            has_fivem = bool(raw_fivem or user.fivem_linked)
            notice = None
            if not citizen_ok and "permission" in citizen_msg.lower():
                notice = citizen_msg

            embed = create_verification_success_embed(
                fivem_linked=has_fivem,
                avatar_url=avatar_url,
                extra_note=notice,
                daily_count=count + 1
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send rich notification to audit log channel
            log_embed = create_nmc_embed(
                title="Member Registered via Discord Bot",
                description=f"<@{discord_id}> registered in NMC SERVER.",
                color=COLOR_SUCCESS,
                fields=[
                    {"name": "Username", "value": f"`{user.username}`", "inline": True},
                    {"name": "FiveM Identifier", "value": f"`{raw_fivem or 'None'}`", "inline": True},
                    {"name": "Roles", "value": "✅ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍" + ("\n✅ 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑" if has_fivem else ""), "inline": False}
                ]
            )
            await send_to_log_channel(log_embed)

        except Exception as e:
            logger.error(f"Error during in-bot registration submit: {e}")
            await interaction.followup.send(f"❌ Registration failed: {str(e)}", ephemeral=True)

class NMCFiveMLinkModal(discord.ui.Modal, title="Link FiveM Player Account"):
    fivem_id_input = discord.ui.TextInput(
        label="FiveM Identifier / License / CFX ID",
        placeholder="e.g. license:4a88f7..., steam:1100..., or CFX username",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)
        raw_fivem = self.fivem_id_input.value.strip()

        try:
            user: Optional[UserModel] = await get_user_by_discord_id(discord_id)
            if not user:
                user, _ = await register_discord_user(
                    discord_id=discord_id,
                    username=interaction.user.name,
                    fivem_identifier=raw_fivem,
                    discord_global_name=interaction.user.global_name,
                    discord_avatar=interaction.user.avatar.key if interaction.user.avatar else None
                )
                await DiscordRoleService.assignCitizenRole(discord_id)
            else:
                await update_user_fivem(user.id, raw_fivem, True)

            ok, msg = await DiscordRoleService.assignPlayerRole(discord_id)

            embed = create_verification_success_embed(
                fivem_linked=True,
                avatar_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
                extra_note=None if ok else msg
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error linking FiveM: {e}")
            await interaction.followup.send(f"❌ Failed to link FiveM identifier: {str(e)}", ephemeral=True)

# ==============================================================================
# PERSISTENT REGISTRATION VIEW WITH BUTTONS
# ==============================================================================

class RegistrationPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Register Account",
        style=discord.ButtonStyle.primary,
        custom_id="nmc_panel_register_btn"
    )
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(NMCRegisterModal())
        except Exception as e:
            logger.error(f"Error sending register modal: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Could not open registration modal. Please try `/register` directly.", ephemeral=True)

    @discord.ui.button(
        label="🎮 Link FiveM",
        style=discord.ButtonStyle.success,
        custom_id="nmc_panel_fivem_btn"
    )
    async def fivem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(NMCFiveMLinkModal())
        except Exception as e:
            logger.error(f"Error sending FiveM modal: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Could not open FiveM modal.", ephemeral=True)

    @discord.ui.button(
        label="🔄 Sync Roles",
        style=discord.ButtonStyle.secondary,
        custom_id="nmc_panel_sync_btn"
    )
    async def sync_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            res = await DiscordRoleService.syncRoles(discord_id)
            user: Optional[UserModel] = await get_user_by_discord_id(discord_id)
            count = await count_discord_daily_registrations(discord_id)
            
            embed = create_verification_success_embed(
                fivem_linked=bool(user and user.fivem_linked),
                avatar_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
                daily_count=count
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error during sync button: {e}")
            await interaction.followup.send(f"❌ Sync failed: {e}", ephemeral=True)

    @discord.ui.button(
        label="📋 My Roles & Status",
        style=discord.ButtonStyle.secondary,
        custom_id="nmc_panel_myroles_btn"
    )
    async def myroles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            user: Optional[UserModel] = await get_user_by_discord_id(discord_id)
            count = await count_discord_daily_registrations(discord_id)

            nmc_role_map = {
                settings.NMC_CITIZEN_ROLE_ID: "✅ **𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍**",
                settings.NMC_PLAYER_ROLE_ID: "✅ **𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑**",
                settings.NMC_SERVER_TEAM_ROLE_ID: "👑 **𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌**"
            }
            active_roles = []
            if isinstance(interaction.user, discord.Member):
                for r in interaction.user.roles:
                    if str(r.id) in nmc_role_map:
                        active_roles.append(nmc_role_map[str(r.id)])

            roles_display = "\n".join(active_roles) if active_roles else "❌ *No NMC roles assigned yet.*"

            embed = create_nmc_embed(
                title=f"📋 Member Status — {interaction.user.display_name}",
                description=f"Here is your current role and verification status in **NMC SERVER**:",
                color=COLOR_SUCCESS if active_roles else COLOR_GOLD,
                fields=[
                    {"name": "Active Roles", "value": roles_display, "inline": False},
                    {"name": "Website Account", "value": f"`{user.username}`" if user else "⚪ *Not Registered (Click 'Register Account')*", "inline": True},
                    {"name": "FiveM Status", "value": f"🟢 `{user.fivem_identifier}`" if user and user.fivem_linked else "⚪ *Not Linked (Click 'Link FiveM')*", "inline": True},
                    {"name": "Daily Registrations", "value": f"**{count}/3** today", "inline": True}
                ],
                thumbnail_url=interaction.user.display_avatar.url
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error during myroles button: {e}")
            await interaction.followup.send(f"❌ Failed to retrieve role status: {e}", ephemeral=True)

# ==============================================================================
# DISCORD SLASH COMMANDS
# ==============================================================================

# 1. /register
@bot.tree.command(name="register", description="Register your NMC SERVER account directly in Discord and get automated roles.")
@app_commands.describe(
    username="Your desired username (defaults to Discord username if omitted)",
    fivem_identifier="Your FiveM identifier or CFX ID (Optional)"
)
async def register_command(
    interaction: discord.Interaction,
    username: Optional[str] = None,
    fivem_identifier: Optional[str] = None
):
    try:
        if not username:
            # Open interactive modal directly without defer
            await interaction.response.send_modal(NMCRegisterModal())
            return

        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)

        # Check daily registration limit (Max 3 on 1 day)
        allowed, count, limit_msg = await can_register_today(discord_id)
        if not allowed:
            embed = create_nmc_embed(
                title="⚠️ Daily Registration Limit Reached",
                description=(
                    f"{interaction.user.mention}, you have already registered **{count}/3 accounts** today.\n\n"
                    f"**Server Rule:** Maximum 3 registrations per 24 hours.\n"
                    f"Please wait until tomorrow to register another account."
                ),
                color=COLOR_DANGER
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        user, is_new = await register_discord_user(
            discord_id=discord_id,
            username=username.strip(),
            fivem_identifier=fivem_identifier.strip() if fivem_identifier else None,
            discord_global_name=interaction.user.global_name,
            discord_avatar=interaction.user.avatar.key if interaction.user.avatar else None
        )

        citizen_ok, citizen_msg = await DiscordRoleService.assignCitizenRole(discord_id)
        player_ok = False
        if fivem_identifier:
            player_ok, player_msg = await DiscordRoleService.assignPlayerRole(discord_id)

        has_fivem = bool(fivem_identifier or user.fivem_linked)
        notice = None
        if not citizen_ok and "permission" in citizen_msg.lower():
            notice = citizen_msg

        embed = create_verification_success_embed(
            fivem_linked=has_fivem,
            avatar_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
            extra_note=notice,
            daily_count=count + 1
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in register command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Registration error: {e}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Registration error: {e}", ephemeral=True)

# 2. /linkfivem command
@bot.tree.command(name="linkfivem", description="Link your FiveM account to automatically receive the 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role.")
@app_commands.describe(identifier="Your FiveM identifier (license:, steam:, cfx:, etc.)")
async def linkfivem_command(interaction: discord.Interaction, identifier: str):
    try:
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)
        raw_ident = identifier.strip()

        user: Optional[UserModel] = await get_user_by_discord_id(discord_id)
        if not user:
            user, _ = await register_discord_user(
                discord_id=discord_id,
                username=interaction.user.name,
                fivem_identifier=raw_ident,
                discord_global_name=interaction.user.global_name,
                discord_avatar=interaction.user.avatar.key if interaction.user.avatar else None
            )
            await DiscordRoleService.assignCitizenRole(discord_id)
        else:
            await update_user_fivem(user.id, raw_ident, True)

        ok, msg = await DiscordRoleService.assignPlayerRole(discord_id)
        embed = create_verification_success_embed(
            fivem_linked=True,
            avatar_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
            extra_note=None if ok else msg
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in linkfivem command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 3. /setup-panel (Admin only)
@bot.tree.command(name="setup-panel", description="Post or refresh the NMC Registration panel in this channel or default channel. (Admin)")
@app_commands.describe(channel="Optional: Specific text channel to post the registration panel into")
async def setuppanel_command(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    try:
        if not is_staff_member(interaction):
            await interaction.response.send_message("❌ **Permission Denied:** Administrator privileges required.", ephemeral=True)
            return

        target_channel = channel or interaction.channel
        from app.discord.bot import deploy_registration_panel
        await interaction.response.defer(ephemeral=True)
        ok = await deploy_registration_panel(target_channel_id=target_channel.id)
        if ok:
            await interaction.followup.send(f"✅ Registration & Role Verification Panel deployed successfully to {target_channel.mention}!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Failed to deploy registration panel to {target_channel.mention}.", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in setup-panel command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 4. /verify command
@bot.tree.command(name="verify", description="Verify your website account link and sync your NMC SERVER roles.")
async def verify_command(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)

        user: Optional[UserModel] = await get_user_by_discord_id(discord_id)
        if not user or not user.discord_linked:
            embed = create_nmc_embed(
                title="Verification Notice",
                description="❌ **You are not registered yet.**\n\nClick below to register or type `/register` to create your account immediately in Discord!",
                color=COLOR_DANGER,
                fields=[
                    {"name": "Quick Register", "value": "Type `/register` directly in Discord to create your account in 3 seconds!", "inline": False},
                    {"name": "Web Dashboard", "value": f"[Open Registration Website]({settings.FRONTEND_URL})", "inline": False}
                ]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        sync_result = await DiscordRoleService.syncRoles(discord_id)
        if not sync_result["is_guild_member"]:
            embed = create_nmc_embed(
                title="Verification Notice",
                description="❌ **Please join the NMC SERVER Discord before verification.**",
                color=COLOR_DANGER
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        count = await count_discord_daily_registrations(discord_id)
        embed = create_verification_success_embed(
            fivem_linked=bool(user.fivem_linked),
            avatar_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
            daily_count=count
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in verify command: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 5. /sync command (User self-service or Staff for others)
@bot.tree.command(name="sync", description="Synchronize your NMC SERVER roles (or synchronize another member if Staff).")
@app_commands.describe(user="Optional: Discord member to synchronize (Staff only if targeting another member)")
async def sync_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
    try:
        target_member = user or interaction.user
        is_self = target_member.id == interaction.user.id

        if not is_self and not is_staff_member(interaction):
            await interaction.response.send_message(
                "❌ **Permission Denied:** Only Staff members can synchronize roles for other members.\n"
                "💡 *Tip:* Run `/sync` without selecting a user to synchronize your own roles!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        res = await DiscordRoleService.syncRoles(str(target_member.id))
        db_user: Optional[UserModel] = await get_user_by_discord_id(str(target_member.id))
        count = await count_discord_daily_registrations(str(target_member.id))

        if is_self:
            has_fivem = bool(db_user and db_user.fivem_linked)
            notice = None
            if not res["success"]:
                notice = res.get("message")
            embed = create_verification_success_embed(
                fivem_linked=has_fivem,
                avatar_url=target_member.display_avatar.url if target_member.display_avatar else None,
                extra_note=notice,
                daily_count=count
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = create_nmc_embed(
                title="NMC Role Synchronization",
                description=f"Role sync completed for {target_member.mention}.",
                color=COLOR_SUCCESS if res["success"] else COLOR_DANGER,
                fields=[
                    {"name": "Newly Assigned", "value": ", ".join(res["assigned_roles"]) if res["assigned_roles"] else "None (Already up to date)", "inline": False},
                    {"name": "Current NMC Roles", "value": ", ".join(res["current_roles"]) if res["current_roles"] else "None", "inline": False}
                ],
                thumbnail_url=target_member.display_avatar.url
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in sync command: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 6. /roles command (User self-service or Staff for others)
@bot.tree.command(name="roles", description="Show active NMC SERVER roles and registration status.")
@app_commands.describe(user="Optional: Discord member to inspect (Staff only if targeting another member)")
async def roles_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
    try:
        target_member = user or interaction.user
        is_self = target_member.id == interaction.user.id

        if not is_self and not is_staff_member(interaction):
            await interaction.response.send_message(
                "❌ **Permission Denied:** Only Staff members can inspect roles for other members.\n"
                "💡 *Tip:* Run `/roles` or `/myroles` to check your own roles!",
                ephemeral=True
            )
            return

        nmc_role_map = {
            settings.NMC_CITIZEN_ROLE_ID: "✅ **𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍**",
            settings.NMC_PLAYER_ROLE_ID: "✅ **𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑**",
            settings.NMC_SERVER_TEAM_ROLE_ID: "👑 **𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌**"
        }
        active_roles = [nmc_role_map[str(r.id)] for r in target_member.roles if str(r.id) in nmc_role_map]

        db_user: Optional[UserModel] = await get_user_by_discord_id(str(target_member.id))
        count = await count_discord_daily_registrations(str(target_member.id))

        embed = create_nmc_embed(
            title=f"NMC Roles — {target_member.display_name}",
            description=f"Active server roles for {target_member.mention}:",
            color=COLOR_SUCCESS if active_roles else COLOR_GOLD,
            fields=[
                {"name": "Active NMC Roles", "value": "\n".join(active_roles) if active_roles else "❌ *No NMC roles assigned yet.*", "inline": False},
                {"name": "Registered Account", "value": f"`{db_user.username}`" if db_user else "⚪ *Not Registered*", "inline": True},
                {"name": "FiveM Linked", "value": f"🟢 `{db_user.fivem_identifier}`" if db_user and db_user.fivem_linked else "⚪ *Not Linked*", "inline": True},
                {"name": "Daily Registrations", "value": f"**{count}/3** today", "inline": True}
            ],
            thumbnail_url=target_member.display_avatar.url
        )
        if not active_roles and is_self:
            embed.add_field(
                name="💡 How to get roles:",
                value=(
                    "• Use `/register` or click **`📝 Register Account`** to get **`✅ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍`**\n"
                    "• Use `/linkfivem` or click **`🎮 Link FiveM`** to get **`✅ 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑`**"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in roles command: {e}")

# 7. /myroles command (Instant self-check)
@bot.tree.command(name="myroles", description="Instantly view your active NMC SERVER roles and registration status.")
async def myroles_command(interaction: discord.Interaction):
    await roles_command(interaction, user=None)

# 8. /staffrole command (Admin only - assigns 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌)
@bot.tree.command(name="staffrole", description="Assign the 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 role to a member. (Admin only)")
@app_commands.describe(
    user="The target Discord member",
    reason="Reason for staff promotion"
)
async def staffrole_command(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: Optional[str] = "Manual staff role promotion"
):
    try:
        if not is_staff_member(interaction):
            await interaction.response.send_message("❌ **Security Alert:** Only authorized administrators can assign the 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 role.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        admin_id = str(interaction.user.id)
        target_id = str(user.id)

        success, msg = await DiscordRoleService.assignServerTeamRole(
            discord_user_id=target_id,
            admin_discord_id=admin_id,
            reason=reason
        )

        if success:
            embed = create_nmc_embed(
                title="👑 Staff Promotion Executed",
                description=f"{user.mention} has been officially assigned the **𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌** role.",
                color=COLOR_GOLD,
                fields=[
                    {"name": "Promoted Member", "value": f"{user.name} (`{target_id}`)", "inline": True},
                    {"name": "Authorizing Admin", "value": f"{interaction.user.name} (`{admin_id}`)", "inline": True},
                    {"name": "Reason", "value": reason, "inline": False}
                ],
                thumbnail_url=user.display_avatar.url
            )
            await interaction.followup.send(embed=embed)
        else:
            embed = create_nmc_embed(
                title="Role Assignment Failed",
                description=f"❌ Failed to assign 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 to {user.mention}.\n\n`{msg}`",
                color=COLOR_DANGER
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in staffrole command: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 9. /removestaff command (Admin only)
@bot.tree.command(name="removestaff", description="Remove 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 role from a user. (Admin only)")
@app_commands.describe(
    user="The target Discord member",
    reason="Reason for removal"
)
async def removestaff_command(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: Optional[str] = "Staff role revoked by administrator"
):
    try:
        if not is_staff_member(interaction):
            await interaction.response.send_message("❌ **Permission Denied:** Administrator privileges required.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        admin_id = str(interaction.user.id)
        target_id = str(user.id)

        success, msg = await DiscordRoleService.removeRole(
            discord_user_id=target_id,
            role_id=settings.NMC_SERVER_TEAM_ROLE_ID,
            admin_discord_id=admin_id,
            reason=reason
        )

        if success:
            embed = create_nmc_embed(
                title="Staff Role Revoked",
                description=f"**𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌** role was removed from {user.mention}.",
                color=COLOR_DANGER,
                fields=[
                    {"name": "Target Member", "value": f"{user.name} (`{target_id}`)", "inline": True},
                    {"name": "Admin", "value": f"{interaction.user.name} (`{admin_id}`)", "inline": True},
                    {"name": "Reason", "value": reason, "inline": False}
                ]
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Error: {msg}", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in removestaff command: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 10. /verifyuser command (User self-service or Staff for others)
@bot.tree.command(name="verifyuser", description="Inspect registration and FiveM linking status for yourself or another member.")
@app_commands.describe(user="Optional: Discord member to inspect (Staff only if inspecting others)")
async def verifyuser_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
    try:
        target_member = user or interaction.user
        is_self = target_member.id == interaction.user.id

        if not is_self and not is_staff_member(interaction):
            await interaction.response.send_message("❌ **Permission Denied:** Only Staff members can inspect other members.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        db_user: Optional[UserModel] = await get_user_by_discord_id(str(target_member.id))
        count = await count_discord_daily_registrations(str(target_member.id))

        if not db_user:
            embed = create_nmc_embed(
                title=f"User Status — {target_member.display_name}",
                description=(
                    f"{target_member.mention} has not registered or linked an account yet.\n\n"
                    f"Use `/register` or click **`📝 Register Account`** on the panel to create an account!"
                ),
                color=COLOR_DANGER,
                fields=[
                    {"name": "Daily Registrations", "value": f"**{count}/3** today", "inline": True}
                ],
                thumbnail_url=target_member.display_avatar.url
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = create_nmc_embed(
            title=f"User Status — {db_user.username}",
            description=f"Account verification details for {target_member.mention}:",
            color=COLOR_SUCCESS,
            fields=[
                {"name": "Website Username", "value": f"`{db_user.username}`", "inline": True},
                {"name": "Registered Email", "value": f"`{db_user.email or 'None'}`", "inline": True},
                {"name": "Discord Linked", "value": "🟢 Yes", "inline": True},
                {"name": "FiveM Linked", "value": f"🟢 `{db_user.fivem_identifier}`" if db_user.fivem_linked else "⚪ No", "inline": True},
                {"name": "Admin Privilege", "value": "⭐ Admin" if db_user.is_admin else "Normal User", "inline": True},
                {"name": "Daily Registrations", "value": f"**{count}/3** today", "inline": True}
            ],
            thumbnail_url=target_member.display_avatar.url
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in verifyuser command: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 11. /help command (All members)
@bot.tree.command(name="help", description="Show all available NMC SERVER bot commands and role system guide.")
async def help_command(interaction: discord.Interaction):
    try:
        embed = create_nmc_embed(
            title="🏛️ NMC SERVER — Automated Role & Verification System",
            description=(
                "Welcome to **NMC SERVER** automated bot system!\n"
                "All members can register, link their FiveM identity, and receive server roles automatically."
            ),
            color=COLOR_GOLD,
            fields=[
                {
                    "name": "🎭 Server Roles",
                    "value": (
                        "• **`✅ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍`** — Auto-granted on account registration (`/register`)\n"
                        "• **`✅ 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑`** — Auto-granted on FiveM linking (`/linkfivem`)\n"
                        "• **`👑 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌`** — Staff/Admin only (Protected manual assignment)"
                    ),
                    "inline": False
                },
                {
                    "name": "👤 Member Commands (Everyone)",
                    "value": (
                        "• `/register` — Register your account and receive **`✅ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍`**\n"
                        "• `/linkfivem <license>` — Link your FiveM identifier and receive **`✅ 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑`**\n"
                        "• `/roles` or `/myroles` — Check your active server roles and verification status\n"
                        "• `/sync` — Synchronize and refresh your server roles\n"
                        "• `/verify` — Check your web account link and refresh roles\n"
                        "• `/verifyuser` — View your registered account profile\n"
                        "• `/help` — Display this command reference"
                    ),
                    "inline": False
                },
                {
                    "name": "🛡️ Staff Commands (Admin/Staff Only)",
                    "value": (
                        "• `/setup-panel` — Post the interactive registration panel\n"
                        "• `/sync @user` — Synchronize roles for another member\n"
                        "• `/roles @user` — Inspect roles for another member\n"
                        "• `/verifyuser @user` — Inspect registration details for another member\n"
                        "• `/staffrole @user` — Assign **`𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌`** role (Admin only)\n"
                        "• `/removestaff @user` — Revoke **`𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌`** role (Admin only)\n"
                        "• `/logs` — View recent role assignment audit history"
                    ),
                    "inline": False
                },
                {
                    "name": "⚡ Rules & Limits",
                    "value": "• Limit: Maximum 3 registrations per 24 hours per user.",
                    "inline": False
                }
            ]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in help command: {e}")

# 12. /logs command (Staff only)
@bot.tree.command(name="logs", description="Show recent NMC role assignment audit logs. (Staff only)")
async def logs_command(interaction: discord.Interaction):
    try:
        if not is_staff_member(interaction):
            await interaction.response.send_message("❌ **Permission Denied.**", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        logs = await get_recent_audit_logs(limit=8)

        if not logs:
            await interaction.followup.send("No audit logs recorded yet.", ephemeral=True)
            return

        lines = []
        for l in logs:
            timestamp = l.created_at.strftime("%m-%d %H:%M") if l.created_at else ""
            target = f"<@{l.target_discord_id}>" if l.target_discord_id else "N/A"
            admin = f"<@{l.admin_discord_id}>" if l.admin_discord_id else "System"
            lines.append(f"`{timestamp}` **{l.action}** on {target} by {admin} ({l.reason or 'No reason'})")

        embed = create_nmc_embed(
            title="NMC Server Audit Logs",
            description="\n\n".join(lines),
            color=COLOR_INFO
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in logs command: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
