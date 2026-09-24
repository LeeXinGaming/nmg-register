import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.logger import logger
from app.database import init_db
from app.auth.router import router as auth_router
from app.api.discord_router import router as discord_router
from app.api.fivem_router import router as fivem_router
from app.api.admin_router import router as admin_router
from app.discord.bot import bot
import app.discord.commands  # Register slash commands

bot_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    logger.info("Initializing NMC SERVER Backend...")
    await init_db()

    # Launch Discord Bot
    global bot_task
    if settings.DISCORD_BOT_TOKEN:
        logger.info("Starting NMC Discord Bot...")
        bot_task = asyncio.create_task(bot.start(settings.DISCORD_BOT_TOKEN))
    else:
        logger.warning("DISCORD_BOT_TOKEN not provided. Discord bot will not run.")

    yield

    # Shutdown:
    logger.info("Shutting down NMC SERVER Backend...")
    if bot_task and not bot.is_closed():
        await bot.close()
        bot_task.cancel()

app = FastAPI(
    title="NMC SERVER — Discord Registration & Role Assignment API",
    description="Automated Discord Role Management & FiveM Verification System for NMC SERVER",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(discord_router)
app.include_router(fivem_router)
app.include_router(admin_router)

@app.get("/api/health")
async def health_check():
    guild_id = int(settings.DISCORD_GUILD_ID) if settings.DISCORD_GUILD_ID.isdigit() else None
    guild = bot.get_guild(guild_id) if guild_id else None
    return {
        "status": "online",
        "server": "NMC SERVER",
        "bot_ready": bot.is_ready(),
        "bot_user": str(bot.user) if bot.user else None,
        "guild_connected": guild is not None,
        "guild_name": guild.name if guild else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
