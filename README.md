# OsteoCare AI

Website: https://hariprakashcit.github.io/New-OA/

The frontend and AI workspace are public on GitHub Pages. The free backend is deployed at https://osteocare-new-oa-api.onrender.com
and the Supabase tables are created. The deployed backend passes its database
readiness check and detects the AI configuration. Real AI generation and physical
sensor operation still require a signed-in hardware rehearsal.

## Connect an ESP32 over Wi-Fi

Use **Wi-Fi connection** on the website. The supplied Knee Health Arduino code
has been adapted to send three baseline-adjusted FSR readings to the hosted API.
Download the firmware ZIP, enter your Wi-Fi/device credentials locally, and upload
once. Sensor transfer uses Wi-Fi only. See [Wi-Fi setup and file analysis](WIFI_SETUP.md).
The earlier USB implementation remains in source for reference but is not part of
the current website workflow.

## Configure the free backend and AI

Follow [the free hosting setup](GEMMA_SETUP.md). The selected AI model is
**Gemma 4 26B A4B (free)** through OpenRouter. The backend rejects paid model
aliases and requires a secret API key; it does not silently use paid inference.

[Configure the existing backend on Render](https://dashboard.render.com/web/srv-dbr9n9c9v7es73bv1ki0/env)

The existing Supabase project is prepared with separate `osteocare_` tables.
Supply its service-role key and your OpenRouter key in Render's environment settings.
Never commit real keys or put server secrets into the browser.

## Saved source

- `web/`: editable React/TypeScript frontend, AI workspace and frontend tests.
- `backend/`: FastAPI, authenticated REST/WebSockets, analysis, PDF reports and Gemma adapter.
- `database/`: Supabase schema and row-level security configuration.
- `mobile/`: Expo/React Native application source.
- `firmware/`: ESP32 Arduino firmware for heel, ball and toe FSRs.
- `tests/`: backend access, validation, persistence and AI adapter tests.
- `render.yaml`: free backend deployment blueprint.
- `model-hosting/`: earlier E4B GPU recipe, retained but not used by the free configuration.
- `docs/`: published GitHub Pages build, served from `main:/docs`.

The root ZIP, `website/` and standalone HTML are the earlier downloadable
frontend snapshot. The current frontend is `web/` and the current published
build is `docs/`.

## Build and test

Frontend: `npm ci`, `npm test`, `npm run build`.
Backend: create a Python 3.12 virtual environment, install
`backend/requirements.txt`, then run `python -m pytest tests -q`.
Copy `backend/.env.example` to a local untracked `backend/.env` for development.
Set its values securely and run `scripts/start.sh` from the repository root.

For GitHub Pages updates, build with `npm run build -- --base=./`, copy `dist/`
into `docs/`, retain `docs/.nojekyll`, then commit. GitHub Pages automatically
publishes `main:/docs`.

Latest validation: 35 backend tests, 22 frontend tests, TypeScript and Vite build
passed. Local Chromium checks cover USB live preview, disconnect/reconnect,
firmware download and unsupported browsers. No real sensor data or credentials
are stored here. Physical hardware and live AI generation still need a rehearsal.

The website includes only the public Supabase key and service URLs. Server and
model keys must remain in Render. Supabase schema migration:
`osteocare_isolated_mobility_tables`. The existing unprefixed tables are preserved.
