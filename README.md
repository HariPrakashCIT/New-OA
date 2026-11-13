# OsteoCare AI

Responsive mobility-monitoring frontend with a dedicated **AI workspace**.

The published frontend is served by GitHub Pages from `main:/docs`.
`docs/` contains the built website extracted from `OsteoCare-new-version.zip`.
Asset URLs are relative so the website works under this repository's `/New-OA/` path.

## Current functionality

Navigation, the AI workspace, connection settings and empty states are available.
Authentication, saved reports, live ESP32 readings and Gemma explanations require
a deployed FastAPI backend, a configured Supabase project and a hosted Gemma endpoint.
Those services are not included in GitHub Pages hosting and are not yet configured.

Use **Connect your workspace** to enter the backend URL, Supabase project URL and
Supabase public/anon key. Never enter a service-role key in the frontend. Configure
the backend to allow the GitHub Pages origin in its CORS settings and configure
the frontend URL in the Supabase authentication redirect settings.

## Local preview

Download and extract `OsteoCare-new-version.zip`, then open
`OsteoCare-preview.html`. Alternatively, run the included `start.py` with Python 3
and open `http://localhost:4173`.

## Publish updates

Replace the built files in `docs/`, keep asset links relative, and commit to `main`.
GitHub Pages automatically republishes the contents of `docs/`.
