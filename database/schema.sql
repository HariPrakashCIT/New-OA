-- Run once in the Supabase SQL editor. Auth is provided by Supabase Auth.
create table public.profiles (id uuid primary key references auth.users on delete cascade, name text not null default '', daily_goal integer not null default 20 check(daily_goal between 1 and 240));
create table public.devices (id text primary key, user_id uuid not null references auth.users on delete cascade, name text not null, key_hash text not null, created_at timestamptz not null default now());
create table public.readings (id bigint generated always as identity primary key, device_id text not null references public.devices on delete cascade, timestamp timestamptz not null, received_at timestamptz not null default now(), heel_pressure integer not null check(heel_pressure between 0 and 4095), ball_pressure integer not null check(ball_pressure between 0 and 4095), toe_pressure integer not null check(toe_pressure between 0 and 4095), unique(device_id,timestamp));
create index readings_device_time on public.readings(device_id,timestamp desc);
create table public.sessions (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade, device_id text not null references public.devices on delete cascade, started_at timestamptz not null default now(), ended_at timestamptz);
create unique index one_active_session on public.sessions(user_id) where ended_at is null;
create table public.reports (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade, period text not null check(period in ('day','week','month')), created_at timestamptz not null default now(), analysis jsonb not null);
alter table public.profiles enable row level security;
alter table public.devices enable row level security;
alter table public.readings enable row level security;
alter table public.sessions enable row level security;
alter table public.reports enable row level security;
-- No browser table policies: all data passes through authenticated FastAPI endpoints.
-- Service-role key belongs ONLY on the backend. Browser/mobile use the anon key for Auth.
