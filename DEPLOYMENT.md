# Deployment Guide

This project is set up for:

- Supabase for PostgreSQL + pgvector
- Render for the FastAPI backend
- Vercel for the React frontend

## 1. Supabase

1. Create a Supabase project.
2. Open the SQL Editor.
3. Run the SQL in `infra/init_pgvector.sql`.
4. Copy the direct Postgres connection string and append `?sslmode=require`.

Example:

```env
DATABASE_URL=postgresql+psycopg2://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres?sslmode=require
```

## 2. Render Backend

Render can use `render.yaml` from the repository root.

Required environment variables:

- `DATABASE_URL`
- `GEMINI_API_KEY`
- `CORS_ORIGINS`

Recommended values:

- `ROOT_PATH=` (leave empty for Render)
- `UPLOAD_DIR=/tmp/uploads`
- `CHAT_MODEL=gemini-2.0-flash`

Set `CORS_ORIGINS` to your Vercel domain, for example:

```env
CORS_ORIGINS=https://your-frontend.vercel.app
```

The backend health check is:

```text
/health
```

## 3. Vercel Frontend

Deploy the repository root to Vercel. The root `vercel.json` now builds the frontend and serves the Vite output as a SPA.

Set this environment variable in Vercel:

```env
VITE_API_URL=https://your-render-service.onrender.com
```

If your Render service URL changes, update `VITE_API_URL` and redeploy Vercel.

## 4. Notes

- On Render free tier, uploaded files are stored in `/tmp/uploads` and can disappear after restart or redeploy.
- If you want uploaded files to persist on Render, switch to a paid plan and attach a persistent disk.
- The backend can still run locally with a local Postgres instance by changing only `DATABASE_URL`.
