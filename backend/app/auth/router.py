from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.database import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    UserModel
)
from app.auth.security import hash_password, verify_password, create_access_token, get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def serialize_user(user: UserModel) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        discord_id=user.discord_id,
        discord_username=user.discord_username,
        discord_global_name=user.discord_global_name,
        discord_avatar=user.discord_avatar,
        discord_linked=user.discord_linked,
        fivem_identifier=user.fivem_identifier,
        fivem_linked=user.fivem_linked,
        is_admin=user.is_admin,
        created_at=user.created_at
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest):
    """
    Register a new user account.
    Auto-working system: Account is created, user receives JWT token,
    and can immediately link Discord to receive the 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role.
    """
    # Check if email already registered
    existing_email = await get_user_by_email(req.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Check if username already taken
    existing_username = await get_user_by_username(req.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken. Please choose another."
        )

    # Hash password securely
    hashed_pwd = hash_password(req.password)
    
    # First user or admin check
    is_admin = False

    new_user = await create_user(
        email=req.email,
        username=req.username,
        password_hash=hashed_pwd,
        is_admin=is_admin
    )

    logger.info(f"New user registered: {new_user.username} ({new_user.id})")

    token = create_access_token(data={"sub": new_user.id, "username": new_user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=serialize_user(new_user)
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest):
    """
    Authenticate an existing user via username or email.
    """
    identifier = req.username_or_email.strip()
    user = None
    if "@" in identifier:
        user = await get_user_by_email(identifier)
    if not user:
        user = await get_user_by_username(identifier)

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=serialize_user(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get current logged-in user profile and linking status.
    """
    return serialize_user(current_user)
