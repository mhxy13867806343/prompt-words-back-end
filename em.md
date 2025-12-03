# Project Docs

## Overview
- Backend for Prompt Words platform (FastAPI + SQLAlchemy + Redis)
- Features: auth, email binding, password reset, prompt CRUD, like/favorite, view stats, user center, global stats

## Stack
- Python 3.11+
- FastAPI, SQLAlchemy (async)
- PostgreSQL, Redis
- JWT authentication

## Setup & Dependencies
- With uv (recommended):
  - `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - `uv sync`
- With pip:
  - `pip install -r requirements.txt`

## Environment Variables
- `DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname`
- `REDIS_URL=redis://host:6379/0`
- `SECRET_KEY=your-secret`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`

## Run
- Dev: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Docker build: `docker build -t prompt-words-back-end .`
- Docker run: `docker run --rm -p 8000:8000 --env-file .env prompt-words-back-end`

## Useful Scripts
- Init DB: `python init_db.py`
- Start script: `bash run.sh`
- Simple API test: `uv run python test_api.py`

## API Quick Reference
- Auth:
  - `POST /auth/register`
  - `POST /auth/login`
- Prompts:
  - `POST /prompts`
  - `GET /prompts?page=1&page_size=10`
  - `GET /prompts/{promptId}`
  - `PUT /prompts/{promptId}`
  - `DELETE /prompts/{promptId}`
  - `GET /prompts/user/my-prompts`
  - `GET /prompts/stats/global`

## Notes
- Swagger: `http://localhost:8000/docs`
- Response shape: `{code:200, data: {}, msg:"成功"}` with camelCase fields
