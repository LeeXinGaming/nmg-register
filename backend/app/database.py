import os
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Text, select, update, delete, desc, func
from app.config import settings
from app.utils.logger import logger

# Initialize Supabase client if credentials are configured
supabase_client = None
if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
    try:
        from supabase import create_client, Client
        supabase_client: Optional[Client] = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to SQL engine.")

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    discord_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    discord_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    discord_global_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    discord_avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    discord_linked: Mapped[bool] = mapped_column(Boolean, default=False)
    fivem_identifier: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    fivem_linked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class DiscordLinkModel(Base):
    __tablename__ = "discord_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    discord_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class DiscordRoleModel(Base):
    __tablename__ = "discord_roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discord_role_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class RoleAssignmentModel(Base):
    __tablename__ = "role_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    discord_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    role_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ASSIGNED") # 'ASSIGNED', 'REMOVED', 'FAILED'
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    admin_discord_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_discord_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    role_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_json: Mapped[Optional[str]] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

# Determine database engine
db_url = settings.DATABASE_URL
if not db_url:
    db_url = "sqlite+aiosqlite:///./nmc_server.db"

engine = create_async_engine(db_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    """Create tables if they don't exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

# --- Database Helper Functions ---

async def get_user_by_id(user_id: str) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalars().first()

async def get_user_by_email(email: str) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.email == email.lower().strip()))
        return result.scalars().first()

async def get_user_by_username(username: str) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.username == username.strip()))
        return result.scalars().first()

async def get_user_by_discord_id(discord_id: str) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.discord_id == discord_id))
        return result.scalars().first()

async def get_user_by_fivem(identifier: str) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.fivem_identifier == identifier))
        return result.scalars().first()

async def create_user(email: str, username: str, password_hash: str, is_admin: bool = False) -> UserModel:
    async with async_session_factory() as session:
        user = UserModel(
            email=email.lower().strip(),
            username=username.strip(),
            password_hash=password_hash,
            is_admin=is_admin
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Sync to Supabase if configured
        if supabase_client:
            try:
                supabase_client.table("users").upsert({
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "password_hash": user.password_hash,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat()
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to sync user to Supabase: {e}")

        return user

async def register_discord_user(
    discord_id: str,
    username: str,
    email: Optional[str] = None,
    fivem_identifier: Optional[str] = None,
    discord_global_name: Optional[str] = None,
    discord_avatar: Optional[str] = None
) -> Tuple[UserModel, bool]:
    """
    Direct registration from Discord Bot.
    Returns (user, is_new_account)
    """
    async with async_session_factory() as session:
        # Check if user already exists with this discord_id
        result = await session.execute(select(UserModel).where(UserModel.discord_id == discord_id))
        user = result.scalars().first()
        is_new = False

        if user:
            # Existing account, update profile and FiveM if provided
            if fivem_identifier and not user.fivem_linked:
                user.fivem_identifier = fivem_identifier.strip()
                user.fivem_linked = True
            user.discord_username = username
            user.discord_global_name = discord_global_name or user.discord_global_name
            user.discord_avatar = discord_avatar or user.discord_avatar
            user.discord_linked = True
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(user)
        else:
            is_new = True
            # Build unique username if collision
            clean_username = username.strip().replace(" ", "_")
            existing_name = await session.execute(select(UserModel).where(UserModel.username == clean_username))
            if existing_name.scalars().first():
                clean_username = f"{clean_username}_{discord_id[-4:]}"

            # Build email if not provided
            clean_email = email.strip().lower() if email and "@" in email else f"{clean_username.lower()}@discord.nmcserver.net"
            existing_email = await session.execute(select(UserModel).where(UserModel.email == clean_email))
            if existing_email.scalars().first():
                clean_email = f"user_{discord_id}@discord.nmcserver.net"

            # Random secure default password hash
            import secrets
            temp_pwd = secrets.token_urlsafe(16)
            import bcrypt
            pwd_hash = bcrypt.hashpw(temp_pwd.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')

            user = UserModel(
                email=clean_email,
                username=clean_username,
                password_hash=pwd_hash,
                discord_id=discord_id,
                discord_username=username,
                discord_global_name=discord_global_name,
                discord_avatar=discord_avatar,
                discord_linked=True,
                fivem_identifier=fivem_identifier.strip() if fivem_identifier else None,
                fivem_linked=bool(fivem_identifier and fivem_identifier.strip()),
                is_admin=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Sync to Supabase if configured
        if supabase_client:
            try:
                supabase_client.table("users").upsert({
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "discord_id": user.discord_id,
                    "discord_username": user.discord_username,
                    "discord_linked": user.discord_linked,
                    "fivem_identifier": user.fivem_identifier,
                    "fivem_linked": user.fivem_linked,
                    "updated_at": user.updated_at.isoformat()
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to sync discord registered user to Supabase: {e}")

        # Record audit log for registration tracking
        meta_str = json.dumps({"is_new": is_new, "username": user.username, "fivem": user.fivem_identifier})
        session.add(AuditLogModel(
            action="DISCORD_REGISTER",
            target_discord_id=discord_id,
            reason="User registered via Discord Bot",
            meta_json=meta_str
        ))
        await session.commit()

        return user, is_new

async def count_discord_daily_registrations(discord_id: str, hours: int = 24) -> int:
    """
    Count how many registrations this Discord ID has performed in the last 24 hours.
    """
    async with async_session_factory() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await session.execute(
            select(func.count()).select_from(AuditLogModel).where(
                AuditLogModel.target_discord_id == discord_id,
                AuditLogModel.action.in_(["DISCORD_REGISTER", "USER_REGISTERED", "DISCORD_LINKED"]),
                AuditLogModel.created_at >= cutoff
            )
        )
        return result.scalar() or 0

async def can_register_today(discord_id: str, max_limit: Optional[int] = None) -> Tuple[bool, int, str]:
    """
    Verify if a user can register today (Max 3 registrations per day / 24 hours).
    Returns (allowed, current_count, error_message)
    """
    limit = max_limit or settings.MAX_REGISTRATIONS_PER_DAY
    count = await count_discord_daily_registrations(discord_id, hours=24)
    if count >= limit:
        return False, count, f"Daily registration limit reached ({count}/{limit} registered in the past 24 hours). Maximum is 3 registrations per day. Please try again tomorrow."
    return True, count, ""

async def update_user_discord(
    user_id: str,
    discord_id: str,
    discord_username: str,
    discord_global_name: Optional[str],
    discord_avatar: Optional[str],
    discord_linked: bool = True
) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalars().first()
        if not user:
            return None
        user.discord_id = discord_id
        user.discord_username = discord_username
        user.discord_global_name = discord_global_name
        user.discord_avatar = discord_avatar
        user.discord_linked = discord_linked
        user.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)

        if supabase_client:
            try:
                supabase_client.table("users").update({
                    "discord_id": discord_id,
                    "discord_username": discord_username,
                    "discord_global_name": discord_global_name,
                    "discord_avatar": discord_avatar,
                    "discord_linked": discord_linked,
                    "updated_at": user.updated_at.isoformat()
                }).eq("id", user_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update user Discord in Supabase: {e}")

        return user

async def update_user_fivem(user_id: str, fivem_identifier: Optional[str], fivem_linked: bool) -> Optional[UserModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalars().first()
        if not user:
            return None
        user.fivem_identifier = fivem_identifier
        user.fivem_linked = fivem_linked
        user.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)

        if supabase_client:
            try:
                supabase_client.table("users").update({
                    "fivem_identifier": fivem_identifier,
                    "fivem_linked": fivem_linked,
                    "updated_at": user.updated_at.isoformat()
                }).eq("id", user_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update user FiveM in Supabase: {e}")

        return user

async def save_discord_link(
    user_id: str,
    discord_id: str,
    access_token_encrypted: str,
    refresh_token_encrypted: str,
    expires_at: Optional[datetime]
) -> DiscordLinkModel:
    async with async_session_factory() as session:
        # Check if existing link for discord_id
        result = await session.execute(select(DiscordLinkModel).where(DiscordLinkModel.discord_id == discord_id))
        link = result.scalars().first()
        if link:
            link.user_id = user_id
            link.access_token_encrypted = access_token_encrypted
            link.refresh_token_encrypted = refresh_token_encrypted
            link.expires_at = expires_at
            link.updated_at = datetime.now(timezone.utc)
        else:
            link = DiscordLinkModel(
                user_id=user_id,
                discord_id=discord_id,
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                expires_at=expires_at
            )
            session.add(link)
        await session.commit()
        await session.refresh(link)
        return link

async def get_discord_link_by_user(user_id: str) -> Optional[DiscordLinkModel]:
    async with async_session_factory() as session:
        result = await session.execute(select(DiscordLinkModel).where(DiscordLinkModel.user_id == user_id))
        return result.scalars().first()

async def delete_discord_link(user_id: str):
    async with async_session_factory() as session:
        await session.execute(delete(DiscordLinkModel).where(DiscordLinkModel.user_id == user_id))
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalars().first()
        if user:
            user.discord_linked = False
            user.updated_at = datetime.now(timezone.utc)
        await session.commit()

async def record_role_assignment(
    discord_id: str,
    role_id: str,
    user_id: Optional[str] = None,
    status: str = "ASSIGNED"
) -> RoleAssignmentModel:
    async with async_session_factory() as session:
        # Check if active assignment exists
        result = await session.execute(
            select(RoleAssignmentModel).where(
                RoleAssignmentModel.discord_id == discord_id,
                RoleAssignmentModel.role_id == role_id,
                RoleAssignmentModel.status == "ASSIGNED"
            )
        )
        existing = result.scalars().first()
        if existing and status == "ASSIGNED":
            return existing

        assignment = RoleAssignmentModel(
            user_id=user_id,
            discord_id=discord_id,
            role_id=role_id,
            status=status,
            assigned_at=datetime.now(timezone.utc) if status == "ASSIGNED" else datetime.now(timezone.utc),
            removed_at=datetime.now(timezone.utc) if status == "REMOVED" else None
        )
        session.add(assignment)
        await session.commit()
        await session.refresh(assignment)

        if supabase_client:
            try:
                supabase_client.table("role_assignments").insert({
                    "id": assignment.id,
                    "user_id": user_id,
                    "discord_id": discord_id,
                    "role_id": role_id,
                    "status": status,
                    "assigned_at": assignment.assigned_at.isoformat()
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to record role assignment in Supabase: {e}")

        return assignment

async def mark_role_removed(discord_id: str, role_id: str):
    async with async_session_factory() as session:
        result = await session.execute(
            select(RoleAssignmentModel).where(
                RoleAssignmentModel.discord_id == discord_id,
                RoleAssignmentModel.role_id == role_id,
                RoleAssignmentModel.status == "ASSIGNED"
            )
        )
        assignment = result.scalars().first()
        if assignment:
            assignment.status = "REMOVED"
            assignment.removed_at = datetime.now(timezone.utc)
            await session.commit()

async def get_active_role_assignments(discord_id: str) -> List[RoleAssignmentModel]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(RoleAssignmentModel).where(
                RoleAssignmentModel.discord_id == discord_id,
                RoleAssignmentModel.status == "ASSIGNED"
            )
        )
        return list(result.scalars().all())

async def add_audit_log(
    action: str,
    admin_discord_id: Optional[str] = None,
    target_discord_id: Optional[str] = None,
    role_id: Optional[str] = None,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLogModel:
    async with async_session_factory() as session:
        meta_str = json.dumps(metadata or {})
        log_entry = AuditLogModel(
            action=action,
            admin_discord_id=admin_discord_id,
            target_discord_id=target_discord_id,
            role_id=role_id,
            reason=reason,
            meta_json=meta_str
        )
        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)

        if supabase_client:
            try:
                supabase_client.table("audit_logs").insert({
                    "id": log_entry.id,
                    "action": action,
                    "admin_discord_id": admin_discord_id,
                    "target_discord_id": target_discord_id,
                    "role_id": role_id,
                    "reason": reason,
                    "metadata": metadata or {},
                    "created_at": log_entry.created_at.isoformat()
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to record audit log in Supabase: {e}")

        return log_entry

async def get_recent_audit_logs(limit: int = 50) -> List[AuditLogModel]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLogModel).order_by(desc(AuditLogModel.created_at)).limit(limit)
        )
        return list(result.scalars().all())
