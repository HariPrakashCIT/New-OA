-- New OsteoCare tables are isolated from any older application tables.
-- Run once in the Supabase SQL editor. Auth is provided by Supabase Auth.
create table public.osteocare_profiles (id uuid primary key references auth.users on delete cascade, name text not null default '', daily_goal integer not null default 20 check(daily_goal between 1 and 240));
create table public.osteocare_devices (id text primary key, user_id uuid not null references auth.users on delete cascade, name text not null, key_hash text not null, created_at timestamptz not null default now());
create table public.osteocare_readings (id bigint generated always as identity primary key, device_id text not null references public.osteocare_devices on delete cascade, timestamp timestamptz not null, received_at timestamptz not null default now(), heel_pressure integer not null check(heel_pressure between 0 and 4095), ball_pressure integer not null check(ball_pressure between 0 and 4095), toe_pressure integer not null check(toe_pressure between 0 and 4095), unique(device_id,timestamp));
create index osteocare_readings_device_time on public.osteocare_readings(device_id,timestamp desc);
create table public.osteocare_sessions (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade, device_id text not null references public.osteocare_devices on delete cascade, started_at timestamptz not null default now(), ended_at timestamptz);
create unique index osteocare_one_active_session on public.osteocare_sessions(user_id) where ended_at is null;
create table public.osteocare_reports (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade, period text not null check(period in ('day','week','month')), created_at timestamptz not null default now(), analysis jsonb not null);
alter table public.osteocare_profiles enable row level security;
alter table public.osteocare_devices enable row level security;
alter table public.osteocare_readings enable row level security;
alter table public.osteocare_sessions enable row level security;
alter table public.osteocare_reports enable row level security;
-- No browser table policies: all data passes through authenticated FastAPI endpoints.
-- Service-role key belongs ONLY on the backend. Browser/mobile use the anon key for Auth.

-- Explicit privileges avoid depending on project-wide default grants.
revoke all on public.osteocare_profiles, public.osteocare_devices, public.osteocare_readings, public.osteocare_sessions, public.osteocare_reports from anon, authenticated, public;
grant select, insert, update, delete on public.osteocare_profiles, public.osteocare_devices, public.osteocare_readings, public.osteocare_sessions, public.osteocare_reports to service_role;
grant usage, select on sequence public.osteocare_readings_id_seq to service_role;
create index osteocare_devices_user_id on public.osteocare_devices(user_id);
create index osteocare_sessions_device_id on public.osteocare_sessions(device_id);
create index osteocare_reports_user_id on public.osteocare_reports(user_id);
