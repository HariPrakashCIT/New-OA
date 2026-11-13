#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f backend/.env ]; then
  echo 'Create backend/.env from backend/.env.example and configure Supabase first.' >&2
  exit 1
fi
set -a
. ./backend/.env
set +a
: "${SUPABASE_URL:?Set SUPABASE_URL in backend/.env}"
: "${SUPABASE_SERVICE_ROLE_KEY:?Set SUPABASE_SERVICE_ROLE_KEY in backend/.env}"
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
npm run dev
