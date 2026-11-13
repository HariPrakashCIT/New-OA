# OsteoCare AI

Website: https://hariprakashcit.github.io/New-OA/

The frontend and AI workspace are public on GitHub Pages. **The backend,
Supabase database and live AI generation still need account configuration.**

## Activate the free backend and AI

Follow [the free hosting setup](GEMMA_SETUP.md). The selected AI model is
**Gemma 4 26B A4B (free)** through OpenRouter. The backend rejects paid model
aliases and requires a secret API key; it does not silently use paid inference.

[Deploy the free FastAPI service on Render](https://render.com/deploy?repo=https://github.com/HariPrakashCIT/New-OA)

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

Latest validation: 29 backend tests, 13 frontend tests, TypeScript and Vite build
passed. Live AI inference, database integration and hardware still need testing
after account setup. No real sensor data or credentials are stored here.
