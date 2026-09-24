from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    discord_id: Optional[str] = None
    discord_username: Optional[str] = None
    discord_global_name: Optional[str] = None
    discord_avatar: Optional[str] = None
    discord_linked: bool = False
    fivem_identifier: Optional[str] = None
    fivem_linked: bool = False
    is_admin: bool = False
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Discord Schemas ---
class DiscordRoleInfo(BaseModel):
    id: str
    name: str
    type: str # 'CITIZEN', 'PLAYER', 'SERVER_TEAM'
    assigned: bool
    description: str

class DiscordStatusResponse(BaseModel):
    connected: bool
    discord_user_id: Optional[str] = None
    discord_username: Optional[str] = None
    discord_global_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_guild_member: bool = False
    guild_name: Optional[str] = None
    roles: List[DiscordRoleInfo] = []
    message: Optional[str] = None

class DiscordLinkRequest(BaseModel):
    code: str
    state: Optional[str] = None

class RoleOperationRequest(BaseModel):
    discord_user_id: str
    role_id: str
    reason: Optional[str] = "Manual administrative role assignment"

class SyncRolesResponse(BaseModel):
    success: bool
    message: str
    is_guild_member: bool
    assigned_roles: List[str] = []
    current_roles: List[str] = []

# --- FiveM Schemas ---
class FiveMLinkRequest(BaseModel):
    identifier: str = Field(..., description="FiveM identifier (license:, steam:, cfx:, live:, xbl:, or fivem:ID)")

class FiveMLinkResponse(BaseModel):
    success: bool
    message: str
    fivem_identifier: str
    player_role_assigned: bool

# --- Audit Logs Schemas ---
class AuditLogItem(BaseModel):
    id: str
    action: str
    admin_discord_id: Optional[str] = None
    target_discord_id: Optional[str] = None
    role_id: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
