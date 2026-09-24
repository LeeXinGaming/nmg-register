# NMC SERVER — Discord Registration & Automatic Role Assignment System

Automated, production-ready FiveM server registration portal and Discord bot for **NMC SERVER**. 

This system automatically links player accounts, verifies Discord guild membership, and assigns role permissions instantly without requiring manual staff intervention—while keeping administrative staff roles strictly secured.

---

## 🎯 Role Hierarchy & Automated Assignment Logic

| Discord Role | Assignment Trigger | Protection Level |
| :--- | :--- | :--- |
| **🏛️ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍** | Website Registration + Discord OAuth2 Link + Guild Member | **Automated** |
| **🎮 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑** | Linked FiveM Player Identifier (`license:`, `cfx:`, etc.) | **Automated** |
| **👑 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌** | Assigned manually by administrators via `/staffrole @user` | **Restricted / Staff Only** |

### Critical Security Rule
- ⚠️ **Normal website registration NEVER grants 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌**.
- The staff role can only be assigned by authorized administrators through the `/staffrole @user` slash command or the authenticated Staff Console.
- All staff assignments record: `admin_discord_id`, `target_discord_id`, `role_id`, `timestamp`, and `reason` in the audit log.

---

## 🚀 Automated Registration Flow

```
USER OPENS WEBSITE
       │
       ▼
REGISTER WEBSITE ACCOUNT
       │
       ▼
CONNECT DISCORD (OAuth2)
       │
       ▼
VERIFY NMC SERVER MEMBERSHIP ──[ Not in Guild ]──> Prompt: "Please join the NMC SERVER Discord"
       │
       ▼ [ Member Confirmed ]
AUTO-ASSIGN: 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍
       │
       ▼
LINK FIVEM ACCOUNT (Identifier / CFX ID)
       │
       ▼
AUTO-ASSIGN: 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+ / FastAPI, discord.py 2.x, SQLAlchemy / asyncpg / aiosqlite, Supabase Python SDK, Python-Jose (JWT), Cryptography (Fernet AES token encryption), Bcrypt.
- **Frontend**: React 18, Vite, Lucide Icons, Glassmorphic responsive dark theme tailored for gaming communities.
- **Database**: Supabase PostgreSQL (with direct SQL migration schema and local SQLite fallback for dev).

---

## 📁 Project Structure

```
.
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py               # FastAPI entrypoint, CORS, Discord Bot lifespan
│       ├── config.py             # Pydantic environment configuration
│       ├── database.py           # Unified SQLAlchemy & Supabase data repository
│       ├── auth/
│       │   ├── security.py       # Password hashing & JWT token verification
│       │   └── router.py         # Register, login, user profile endpoints
│       ├── discord/
│       │   ├── bot.py            # Discord Bot, event listeners, NMC embeds
│       │   ├── oauth.py          # OAuth2 flow, code exchange, profile fetcher
│       │   ├── roles.py          # Role definitions & constants
│       │   ├── service.py        # Idempotent DiscordRoleService (rate limits & audit)
│       │   └── commands.py       # Slash commands (/verify, /staffrole, /sync, /logs)
│       ├── api/
│       │   ├── discord_router.py # /api/discord endpoints (login, callback, sync)
│       │   ├── fivem_router.py   # /api/fivem endpoints (link, unlink)
│       │   └── admin_router.py   # Secure admin endpoints for staff role operations
│       ├── models/
│       │   └── schemas.py        # Pydantic validation models
│       ├── services/
│       │   └── role_service.py   # Service exports
│       └── utils/
│           ├── crypto.py         # AES Fernet token encryption
│           └── logger.py         # Structured logging
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # Branding, live bot status indicator, user menu
│   │   │   ├── RoleCard.jsx      # Role visual status (Citizen, Player, Server Team)
│   │   │   ├── FiveMLinkModal.jsx# FiveM account linking modal
│   │   │   └── AdminPanelModal.jsx # Staff console for manual role & audit logs
│   │   ├── pages/
│   │   │   ├── AuthPage.jsx      # Registration, Login, & 1-click Discord flow
│   │   │   └── DashboardPage.jsx # Full status cards, sync triggers, role statuses
│   │   ├── services/
│   │   │   └── api.js            # API client with token storage
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css             # High-aesthetics glassmorphism CSS
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── .env.example
├── .env
├── supabase_schema.sql           # Complete Supabase PostgreSQL schema
├── Dockerfile                    # Multi-stage production container build
├── docker-compose.yml
├── requirements.txt
├── run_dev.py                    # Dual-process local development runner
└── start.bat                     # Windows 1-click launcher
```

---

## ⚙️ Configuration (.env)

Create or update your `.env` file with your credentials:

```env
# Discord Bot & Application
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=1552671732421107772
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_GUILD_ID=1549490376195309661

# Discord Role IDs
NMC_CITIZEN_ROLE_ID=1550320871128957018
NMC_PLAYER_ROLE_ID=1550320871128957019
NMC_SERVER_TEAM_ROLE_ID=1550320871128957020
NMC_ADMIN_ROLE_ID=1550320871128957021

# Optional Log Channel
DISCORD_LOG_CHANNEL_ID=

# OAuth2 Redirect URI
DISCORD_REDIRECT_URI=http://localhost:8000/api/discord/callback

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Security
JWT_SECRET=nmc_super_secret_jwt_key_change_in_production_32charsmin!
ENCRYPTION_KEY=W3o8GqD7q34_vN8sBq0M4Lg6wX9Z1Y2t5R8u4E7w0A1=
```

---

## 🤖 Discord Developer Portal Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Select your application (`NMG REGISTER` / ID `1552671732421107772`).
3. Under **Bot**:
   - Enable **Server Members Intent** (Privileged Gateway Intent).
   - Enable **Message Content Intent**.
4. Under **OAuth2 -> General**:
   - Add Redirect URI: `http://localhost:8000/api/discord/callback` (or your production URL).
   - Copy **Client Secret** and paste it into `.env` under `DISCORD_CLIENT_SECRET`.
5. **Invite Bot to NMC SERVER**:
   Use this invite link:
   ```
   https://discord.com/oauth2/authorize?client_id=1552671732421107772&permissions=268435456&scope=bot%20applications.commands
   ```
6. **Role Hierarchy in Discord Server Settings**:
   - In Discord: Open **Server Settings -> Roles**.
   - Ensure the bot's role (`NMG REGISTER`) is moved **ABOVE** `𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍`, `𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑`, and `𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌`.
   - Discord's permission model requires the bot's highest role to be higher than any role it assigns!

---

## 🗄️ Supabase Database Setup

1. Open your [Supabase Dashboard](https://supabase.com).
2. Go to the **SQL Editor**.
3. Paste the contents of [`supabase_schema.sql`](file:///c:/Users/rosv2/NMG%20REGISTER/supabase_schema.sql) and click **Run**.
4. Copy your project URL and `service_role` secret into `.env`.

---

## ⚡ Quick Start (Local Development)

### Option 1: One-Click Windows Launcher
Double-click `start.bat` in the root folder.

### Option 2: Command Line
```powershell
python run_dev.py
```
This automatically starts:
- **FastAPI Backend**: `http://localhost:8000` (API Docs at `/docs`)
- **React Frontend**: `http://localhost:5173`

---

## 🎮 Discord Slash Commands

| Command | Permission | Description |
| :--- | :--- | :--- |
| **`/register`** | **Everyone** | **Opens Discord Registration Modal or directly registers in Discord & grants roles automatically!** |
| **`/linkfivem <id>`** | **Everyone** | **Links FiveM identifier directly in Discord & auto-assigns 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑.** |
| **`/setup-panel`** | **Admin Only** | **Posts persistent Interactive Verification Panel with buttons in the channel.** |
| `/verify` | Everyone | Verifies linked website account & syncs NMC SERVER roles. |
| `/sync @user` | Staff / Admin | Manually synchronizes all eligible roles for a target member. |
| `/roles @user` | Staff / Admin | Displays all active NMC SERVER roles for a member. |
| `/staffrole @user [reason]` | **Admin Only** | **Safely assigns 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 and records an audit log.** |
| `/removestaff @user [reason]`| **Admin Only** | Revokes 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 role and logs reason. |
| `/verifyuser @user` | Staff / Admin | Inspects website username, email, and FiveM linking status. |
| `/logs` | Staff / Admin | Shows recent role assignment audit events. |

---

## 🔒 Security Best Practices Implemented

- **Idempotent Role Assignments**: Verifies existing roles before firing Discord API calls, preventing duplicate events and API rate limits.
- **Exponential Backoff**: Handles Discord HTTP 429 rate limits smoothly with retry logic.
- **AES-Fernet Token Encryption**: All Discord OAuth2 access and refresh tokens stored in the database are encrypted at rest.
- **State CSRF Defense**: OAuth2 authorization URLs contain cryptographically signed, short-lived JWT state tokens.
- **Auditing**: Every role assignment, join event, and staff command is immutably logged with the executing user, target user, timestamp, and justification.
