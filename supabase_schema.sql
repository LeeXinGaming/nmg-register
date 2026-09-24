-- ==============================================================================
-- NMC SERVER - SUPABASE POSTGRESQL DATABASE SCHEMA
-- DISCORD REGISTRATION & AUTOMATIC ROLE ASSIGNMENT SYSTEM
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    discord_id VARCHAR(64) UNIQUE,
    discord_username VARCHAR(100),
    discord_global_name VARCHAR(100),
    discord_avatar VARCHAR(255),
    discord_linked BOOLEAN DEFAULT FALSE,
    fivem_identifier VARCHAR(100) UNIQUE,
    fivem_linked BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for high speed lookups
CREATE INDEX IF NOT EXISTS idx_users_discord_id ON public.users(discord_id);
CREATE INDEX IF NOT EXISTS idx_users_fivem_identifier ON public.users(fivem_identifier);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- 2. DISCORD LINKS TABLE (Stores encrypted OAuth2 tokens)
CREATE TABLE IF NOT EXISTS public.discord_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    discord_id VARCHAR(64) UNIQUE NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_discord_links_user_id ON public.discord_links(user_id);
CREATE INDEX IF NOT EXISTS idx_discord_links_discord_id ON public.discord_links(discord_id);

-- 3. DISCORD ROLES TABLE
CREATE TABLE IF NOT EXISTS public.discord_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discord_role_id VARCHAR(64) UNIQUE NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    role_type VARCHAR(50) NOT NULL, -- 'CITIZEN', 'PLAYER', 'SERVER_TEAM', 'ADMIN'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pre-populate default NMC Server roles
INSERT INTO public.discord_roles (discord_role_id, role_name, role_type)
VALUES 
    ('1549854919148965898', '𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍', 'CITIZEN'),
    ('1549514937834012784', '𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑', 'PLAYER'),
    ('1549492423326179458', '𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌', 'SERVER_TEAM')
ON CONFLICT (discord_role_id) DO NOTHING;

-- 4. ROLE ASSIGNMENTS TABLE (Tracks active & historical role assignments)
CREATE TABLE IF NOT EXISTS public.role_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    discord_id VARCHAR(64) NOT NULL,
    role_id VARCHAR(64) NOT NULL,
    status VARCHAR(50) DEFAULT 'ASSIGNED', -- 'ASSIGNED', 'REMOVED', 'FAILED'
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    removed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_role_assignments_discord_id ON public.role_assignments(discord_id);
CREATE INDEX IF NOT EXISTS idx_role_assignments_role_id ON public.role_assignments(role_id);

-- 5. AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    admin_discord_id VARCHAR(64),
    target_discord_id VARCHAR(64),
    role_id VARCHAR(64),
    reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON public.audit_logs(target_discord_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);

-- Automatic updated_at trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
DROP TRIGGER IF EXISTS trigger_update_users_timestamp ON public.users;
CREATE TRIGGER trigger_update_users_timestamp
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trigger_update_discord_links_timestamp ON public.discord_links;
CREATE TRIGGER trigger_update_discord_links_timestamp
    BEFORE UPDATE ON public.discord_links
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Row Level Security (RLS) policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow Service Role full access to all tables
CREATE POLICY "Service Role Full Access Users" ON public.users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Discord Links" ON public.discord_links FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Roles" ON public.discord_roles FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Role Assignments" ON public.role_assignments FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access Audit Logs" ON public.audit_logs FOR ALL TO service_role USING (true) WITH CHECK (true);
