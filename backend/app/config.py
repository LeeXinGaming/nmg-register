import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Discord Bot & Application
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_CLIENT_ID: str = "1552671732421107772"
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_GUILD_ID: str = "1549490376195309661"

    # Discord Role IDs
    NMC_CITIZEN_ROLE_ID: str = "1549854919148965898"
    NMC_PLAYER_ROLE_ID: str = "1549514937834012784"
    NMC_SERVER_TEAM_ROLE_ID: str = "1549492423326179458"
    NMC_ADMIN_ROLE_ID: str = "1549503438461607957"

    # Discord Channels
    DISCORD_LOG_CHANNEL_ID: Optional[str] = None
    DISCORD_REGISTER_CHANNEL_ID: str = "1549509737060638751"
    NMC_REGISTERED_VOICE_CHANNEL_ID: str = "1550320871128957018"

    # Daily Registration Limit
    MAX_REGISTRATIONS_PER_DAY: int = 3

    # OAuth2 Configuration
    DISCORD_REDIRECT_URI: str = "http://localhost:8000/api/discord/callback"

    # Database
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    DATABASE_URL: str = "sqlite+aiosqlite:///./nmc_server.db"

    # Security & JWT
    JWT_SECRET: str = "nmc_super_secret_jwt_key_change_in_production_32charsmin!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ENCRYPTION_KEY: str = "W3o8GqD7q34_vN8sBq0M4Lg6wX9Z1Y2t5R8u4E7w0A1="

    # App Settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    FRONTEND_URL: str = "http://localhost:5173"
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
