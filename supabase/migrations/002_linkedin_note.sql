-- Add linkedin_note column to applications table
ALTER TABLE applications ADD COLUMN IF NOT EXISTS linkedin_note TEXT;
