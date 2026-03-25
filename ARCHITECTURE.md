# System Architecture Document
**RAG Chatbot Workshop**
Gemini RAG + SQL RAG + Agentic RAG

## 1. Overview
A Client-Server architecture web application designed to allow users to converse with an AI Chatbot using data from uploaded documents and structured business SQL databases.

## 2. RAG System
- **Document RAG:** Vector search via Cosine Similarity powered by `pgvector` and `gemini-embedding-001`.
- **SQL RAG:** Automated Text-to-SQL function calling capabilities restricted to `SELECT` operations.
- **Agentic RAG / Auto:** An intent router executing a State Graph to analyze user inputs, determine whether to fetch Document Vectors or SQL schemas, evaluate the sufficiency of responses, and rewrite queries if necessary.

## 3. Tech Stack
- **Frontend:** React + Vite + Tailwind CSS + Lucide React
- **Backend:** Python + FastAPI + SQLAlchemy + Uvicorn
- **Database:** PostgreSQL 16 + pgvector
- **AI Models:** Google Gemini 2.5 Flash, Gemini Embeddings 001

## 4. API Definition
- `POST /chat` - Standard JSON messaging endpoint
- `POST /chat/stream` - SSE Endpoint for real-time word generation
- `POST /ingest/file` - File upload processor

## 5. Deployment
Recommended production deployment:

- Supabase for PostgreSQL + pgvector
- Render for the FastAPI backend
- Vercel for the React frontend

See `DEPLOYMENT.md` for the exact environment variables and deployment steps.
