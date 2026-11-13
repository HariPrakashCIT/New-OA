# Free Gemma deployment

The selected model is **Gemma 4 26B A4B (free)** through OpenRouter,
`google/gemma-4-26b-a4b-it:free`, approved in place of the original E4B model.
The website is live at https://hariprakashcit.github.io/New-OA/.
**AI is not active until the accounts, secrets and database below are configured.**

## 1. Create a free Supabase project

Use https://supabase.com/dashboard and select the Free plan. Run
`database/schema.sql` once in the new project's SQL editor. It creates profiles,
devices, readings, walking sessions and reports with row-level security enabled.
Do not rerun it over an existing database without inspecting its schema.
Set the Auth site URL to `https://hariprakashcit.github.io/New-OA/` and add that
URL to allowed redirect URLs. Keep email confirmation enabled and complete it
when creating the demo user.

Retain the project URL and public/anon key for the website. The legacy
service-role key is used only by FastAPI and must be entered in Render's secret
environment settings, never the website, GitHub, or chat.

## 2. Create a free OpenRouter API key

Create your account/key at https://openrouter.ai/settings/keys. Do not add
credits or enable auto-top-up for this free-only setup. Store the key only as
`GEMMA_API_KEY` in Render. The backend fixes requests to the approved `:free`
model while `GEMMA_FREE_ONLY=true`, sets input/output price ceilings to zero,
disables provider fallback and disables reasoning for these short summaries.
A missing key, a paid model alias or a different API host fails configuration
before any inference request. Model availability and free quotas are controlled
by the provider; an error does not switch to paid inference.

Only aggregate sensor statistics are sent, after the signed-in user consents.
Review the provider's privacy/data-use settings before transmitting real records.
Account IDs, device IDs and raw readings are not included in the prompt.

## 3. Deploy the free FastAPI service

[Deploy from this repository on Render](https://render.com/deploy?repo=https://github.com/HariPrakashCIT/New-OA)

Sign in, connect the repository, review `render.yaml`, and retain the **Free**
service plan. No GPU service or Render database is included. Supply:

| Render environment key | Value |
| --- | --- |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret service-role key from your project |
| `GEMMA_API_KEY` | Secret OpenRouter API key |

The blueprint already sets the GitHub Pages CORS origin,
`GEMMA_API_BASE_URL=https://openrouter.ai/api/v1`, the selected free model, and
`GEMMA_FREE_ONLY=true`. Wait for `/ready` to return HTTP 200; it queries Supabase
and fails if the schema, URL or secret is wrong. `/health` alone does not prove
database readiness. If the service name is already taken, choose another name
and use its actual Render URL below.

Free Render services sleep after 15 minutes of inactivity and can take about a
minute to wake. Free Supabase projects can pause after a week of inactivity.
The provider's quotas apply. Avoid adding a payment method or paid upgrades;
review workspace spend controls because bandwidth/build usage may have charges
when a payment method is present. These are demo services, not an always-on SLA.

## 4. Connect the website

Open the website's connection settings and enter the actual Render HTTPS URL,
Supabase URL and **public/anon** key. Sign up, confirm your email and sign in.
Pair the real ESP32 insole, record three-FSR readings, and create a report.
In **AI workspace**, select the report, consent to sending its aggregate
statistics and select **Explain with Gemma**. Empty reports cannot generate AI.
The website shows the model returned by the backend, and saved explanations
retain their original model provenance.

## 5. Verify

Run `scripts/check_deployment.py` with `API_BASE_URL` set to the deployed Render
URL. Optionally provide `SMOKE_ACCESS_TOKEN` through your environment for
read-only authenticated checks. Never paste tokens into command arguments.
Perform a real report generation after deployment and verify saved output and
PDF export. A configured model status only confirms configuration, not a real
inference success. No real completion has been tested before accounts are connected.

## Source and legacy GPU recipe

`backend/` implements authentication, persistence, rule-based calculations and
the model adapter. `web/` contains editable frontend source; `docs/` is the
GitHub Pages build. `model-hosting/` retains the earlier E4B GPU server recipe
for reference only. It is **not** deployed, used or required by this free setup.
Do not launch paid GPU resources under the free-only authorization.

## Current checks

28 backend tests and 13 frontend tests pass; TypeScript and the production build
pass. Model responses are mocked in tests. Live database/ESP32/model integration
still requires the services and a real hardware rehearsal. AI explanations are
descriptive, can be wrong, and are not medical diagnoses.

Sources checked on 2026-11-13:
- https://openrouter.ai/google/gemma-4-26b-a4b-it:free
- https://openrouter.ai/docs/guides/routing/provider-selection
- https://openrouter.ai/docs/api-reference/limits
- https://render.com/docs/free
- https://supabase.com/pricing
