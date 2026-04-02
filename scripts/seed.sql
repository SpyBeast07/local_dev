-- DevBeast Baseline Seed Script
-- This script initializes the database schema and populates it with robust sample data.
-- Ideal for quick development setup and testing.

-- 1. CLEANUP (Optional: Only if you want to ensure a strictly clean start within this script)
-- DROP TABLE IF EXISTS deployments;
-- DROP TABLE IF EXISTS projects;
-- DROP TABLE IF EXISTS users;

-- 2. SCHEMA DEFINITION
-- Create Users Table
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'developer',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url TEXT,
    stack VARCHAR(100),
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Deployments Table
CREATE TABLE IF NOT EXISTS public.deployments (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES public.projects(id) ON DELETE CASCADE,
    environment VARCHAR(50) NOT NULL, -- 'production', 'staging', 'preview'
    status VARCHAR(50) NOT NULL, -- 'running', 'failed', 'stopped'
    version VARCHAR(50),
    logs_url TEXT,
    last_deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. SAMPLE DATA SEEDING
-- Seed Users
INSERT INTO public.users (name, email, role, status) VALUES 
('Kushagra', 'kush@devbeast.io', 'admin', 'active'),
('Alice Smith', 'alice@example.com', 'developer', 'active'),
('Bob Johnson', 'bob@example.com', 'developer', 'active'),
('Charlie Brown', 'charlie@example.com', 'tester', 'away'),
('Diana Prince', 'diana@amazon.com', 'manager', 'active')
ON CONFLICT (email) DO NOTHING;

-- Seed Projects
INSERT INTO public.projects (owner_id, name, description, stack, repository_url) VALUES 
(1, 'Local Dev UI', 'Advanced management interface for local development environments.', 'SvelteKit + FastAPI', 'https://github.com/kushagra/local_dev_ui'),
(1, 'Is It Open?', 'Real-time campus stall status tracker.', 'Vanilla JS + Python', 'https://github.com/kushagra/is-it-open'),
(2, 'Drive ReBAC', 'Local file management with fine-grained access control.', 'Go + OpenFGA', 'https://github.com/alice/drive-rebac'),
(3, 'LMS Portal', 'Learning management system for university students.', 'React + Node.js', 'https://github.com/bob/lms-portal')
ON CONFLICT DO NOTHING;

-- Seed Deployments
INSERT INTO public.deployments (project_id, environment, status, version) VALUES 
(1, 'production', 'running', 'v2.4.0'),
(1, 'staging', 'running', 'v2.5.0-beta.1'),
(2, 'production', 'running', 'v1.0.2'),
(3, 'production', 'failed', 'v0.9.0-rc1'),
(4, 'staging', 'stopped', 'v1.1.0')
ON CONFLICT DO NOTHING;

-- Verification
SELECT 'Database Initialized and Seeded Successfully' as status;
