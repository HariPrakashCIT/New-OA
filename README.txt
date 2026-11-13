OSTEOCARE AI — NEW FRONTEND WITH AI WORKSPACE
Source commit: 9217c30139a77b8954ef2935e70bc246caea17a7

QUICK FRONTEND PREVIEW (no installation):
Open OsteoCare-preview.html in Chrome, Edge or Firefox.
Click AI workspace in the left sidebar.

LOCAL WEBSITE:
Install Python 3 from python.org if needed, then extract this entire ZIP.
Windows: double-click Start-Windows.bat.
Mac/Linux: run python3 start.py from this folder in Terminal.
Open http://localhost:4173 while the launcher is running.
This address runs on your own laptop, not the ChatGPT cloud machine.

STATUS:
This is the real newer frontend, not a working cloud deployment.
Supabase, FastAPI and Gemma hosting are still unconfigured. Login,
live ESP32 readings, stored reports and AI generation need those services.
Do not enter a Supabase service-role key in the website.
For backend integration, use the local HTTP website instead of the file preview;
the backend must allow http://localhost:4173 in its CORS origins.
Public deployment remains blocked by Sites authentication.
