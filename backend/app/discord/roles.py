"""
Role constants and DiscordRoleService exports
"""
from app.discord.service import DiscordRoleService
from app.config import settings

CITIZEN_ROLE_NAME = "𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍"
PLAYER_ROLE_NAME = "𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑"
SERVER_TEAM_ROLE_NAME = "𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌"

ROLE_CONFIGS = [
    {
        "id": settings.NMC_CITIZEN_ROLE_ID,
        "name": CITIZEN_ROLE_NAME,
        "type": "CITIZEN",
        "description": "Assigned automatically upon website registration & Discord account linking."
    },
    {
        "id": settings.NMC_PLAYER_ROLE_ID,
        "name": PLAYER_ROLE_NAME,
        "type": "PLAYER",
        "description": "Assigned automatically when FiveM player account is linked."
    },
    {
        "id": settings.NMC_SERVER_TEAM_ROLE_ID,
        "name": SERVER_TEAM_ROLE_NAME,
        "type": "SERVER_TEAM",
        "description": "Restricted administrative staff role. Assigned only manually by server admins."
    }
]
