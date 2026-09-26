# Make My Resume

Portfolio & resume platform: a React frontend and a FastAPI backend (Supabase auth/Postgres + Groq AI) that
manages profile data, answers questions about it, and generates job-tailored DOCX resumes.

```
backend/    FastAPI API (auth, profile CRUD, AI chat, resume generation)
frontend/   React + Vite + Tailwind single-page app
docs/       API reference and Supabase schema
Dockerfile  API image (default target, used by Render); `full` target also bundles the frontend
render.yaml Render Blueprint for the backend
```

## Run with Docker

```bash
cp .env.example .env    # then fill in your Groq and Supabase values
docker compose up --build
```

Open http://localhost:8000 for the app, http://localhost:8000/docs for Swagger, and
http://localhost:8000/health for the health check.

The frontend is served from the same origin as the API, so no CORS or API URL configuration is needed in Docker.

## Deploy: backend on Render, frontend on Vercel

**1. Backend (Render)**
1. Push the repo to GitHub.
2. In Render choose **New > Blueprint** and select the repo; `render.yaml` creates the `make-my-resume-api` Docker service.
3. Fill in the secret env vars it asks for (see `.env.example`). `SUPABASE_DB_URL` must be the Supabase **pooler**
   connection string (port 6543): Render has no IPv6, so the direct `db.<ref>.supabase.co` host can't be reached.
4. After the deploy, check `https://<your-service>.onrender.com/health` returns `{"status":"ok"}`.

**2. Frontend (Vercel)**
1. **Add New > Project**, import the repo and set **Root Directory** to `frontend` (framework preset: Vite).
2. Add the env var `VITE_API_BASE_URL=https://<your-service>.onrender.com` (no trailing slash) and deploy.
   It is read at build time, so redeploy after changing it.

**3. Connect them**
Set `CORS_ALLOWED_ORIGINS` on Render to the Vercel URL (e.g. `https://make-my-resume.vercel.app`, no trailing slash).
For preview deployments also set `CORS_ALLOWED_ORIGIN_REGEX`, e.g. `https://make-my-resume-.*\.vercel\.app`.

Notes: Render's free plan sleeps after 15 idle minutes, so the first request can take ~50 s (the login page says so).
Resumes are rebuilt from the database on download, so nothing is lost when Render restarts the container.

## Local development

Backend (Python 3.11+):

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn mains:dapp --reload --port 8000
```

The backend reads `.env` from the directory it runs in, so copy the root `.env` into `backend/` for local runs.

Frontend (Node 20.19+):

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on http://localhost:5173 and calls the API at http://localhost:8000. Set `VITE_API_BASE_URL` to point
it elsewhere, and add the frontend origin to `CORS_ALLOWED_ORIGINS` on the backend.

## Tests

```bash
cd backend
python -m unittest discover -s tests -t .
```

## Database

Run [docs/supabase_schema.sql](docs/supabase_schema.sql) in the Supabase SQL editor to create the tables and RLS policies.
See [docs/API.md](docs/API.md) for the endpoint reference.
