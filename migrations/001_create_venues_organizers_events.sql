-- Migration: Create venues, organizer_users, and events tables
-- Run this once against your Postgres database before using the app in production.
-- Relationships:
--  - events.venue_id -> venues.id (FK)
--  - events.created_by -> organizer_users.id (FK)

BEGIN;

-- Venues: durable place metadata used for GEO discovery in Redis
CREATE TABLE IF NOT EXISTS venues (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    address VARCHAR NULL,
    metadata JSONB NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Organizers: authenticated users who can create durable events
CREATE TABLE IF NOT EXISTS organizer_users (
    id UUID PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Events: durable event metadata backed by Postgres. Ephemeral runtime joins/chats live in Redis.
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY,
    venue_id UUID REFERENCES venues(id) ON DELETE RESTRICT,
    title VARCHAR NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    capacity INT,
    created_by UUID REFERENCES organizer_users(id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_venue_id ON events(venue_id);

COMMIT;

-- Notes:
--  - This migration intentionally keeps FK actions conservative. Adjust ON DELETE behavior as needed.
--  - The app keeps ephemeral joins/messages in Redis; `events` is durable metadata only.
