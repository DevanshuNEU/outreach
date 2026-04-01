-- ============================================================
-- Cold Outreach Platform - Complete Schema
-- ============================================================

-- Users
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Profiles
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
  full_name TEXT NOT NULL,
  background TEXT,
  sign_off_block TEXT NOT NULL,
  links_block TEXT NOT NULL DEFAULT '',
  projects JSONB DEFAULT '[]',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Role Templates
CREATE TABLE IF NOT EXISTS role_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  slug TEXT NOT NULL,
  title TEXT NOT NULL,
  color TEXT DEFAULT '#3b82f6',
  tagline TEXT,
  system_prompt TEXT NOT NULL DEFAULT '',
  role_prompt_addition TEXT NOT NULL,
  example_email TEXT,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, slug)
);

-- Companies (shared across users)
CREATE TABLE IF NOT EXISTS companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  domain TEXT,
  location TEXT,
  apollo_org_id TEXT,
  employee_count INT,
  industry TEXT,
  website TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Applications (per-user)
CREATE TABLE IF NOT EXISTS applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  role_template_id UUID REFERENCES role_templates(id),
  job_title TEXT,
  job_url TEXT,
  job_description TEXT,
  email_subject TEXT,
  email_body TEXT,
  email_status TEXT DEFAULT 'draft' CHECK (email_status IN ('draft','confirmed','sent')),
  status TEXT DEFAULT 'drafting' CHECK (status IN (
    'drafting','ready','outreach_in_progress','waiting','replied','closed'
  )),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contacts (shared across users)
CREATE TABLE IF NOT EXISTS contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  apollo_person_id TEXT UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  title TEXT,
  seniority TEXT,
  email TEXT,
  email_status TEXT,
  linkedin_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outreach (per-user)
CREATE TABLE IF NOT EXISTS outreach (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  personalized_greeting TEXT,
  sent_at TIMESTAMPTZ,
  followup_1_sent_at TIMESTAMPTZ,
  followup_2_sent_at TIMESTAMPTZ,
  replied BOOLEAN DEFAULT FALSE,
  reply_date TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(application_id, contact_id)
);

-- API Usage Tracking
CREATE TABLE IF NOT EXISTS api_usage (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  service TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  tokens_in INT,
  tokens_out INT,
  estimated_cost_cents REAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Target Companies (ATS Job Watcher)
CREATE TABLE IF NOT EXISTS target_companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  company_name TEXT NOT NULL,
  ats_type TEXT NOT NULL CHECK (ats_type IN ('greenhouse', 'lever', 'ashby')),
  ats_slug TEXT NOT NULL,
  keywords TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_target_companies_user ON target_companies(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_date ON api_usage(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_user ON outreach(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_app ON outreach(application_id);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company_id);
