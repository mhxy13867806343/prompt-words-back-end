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
  - `POST /auth/send-code`
  - `POST /auth/bind-email`
  - `POST /auth/reset-password`
  - `POST /auth/logout`
- Prompts:
  - `POST /prompts`
  - `GET /prompts?page=1&page_size=10`
  - `GET /prompts/{promptId}`
  - `PUT /prompts/{promptId}`
  - `DELETE /prompts/{promptId}`
  - `GET /prompts/user/my-prompts`
  - `GET /prompts/stats/global`

## API Examples

### Register & Login
Request:
```json
POST /auth/register
{"username":"testuser","password":"123456"}
```
Response:
```json
{"code":200,"data":{"accessToken":"...","tokenType":"bearer","user":{"id":1,"username":"testuser","email":null,"state":0,"createdAt":"..."}},"msg":"成功"}
```

```json
POST /auth/login
{"username":"testuser","password":"123456"}
```

### Email Code & Binding
Send code:
```json
POST /auth/send-code
{"email":"user@example.com"}
```
Bind email:
```json
POST /auth/bind-email (Bearer token)
{"email":"user@example.com","code":"123456"}
```

Reset password:
```json
POST /auth/reset-password
{"email":"user@example.com","code":"123456","newPassword":"654321"}
```

Logout:
```json
POST /auth/logout (Bearer token)
{}
```

### Prompts CRUD
Create:
```json
POST /prompts (Bearer token)
{"title":"Sample","content":"..."}
```
List:
```text
GET /prompts?page=1&page_size=10
```
Detail (IP-based view tracking):
```text
GET /prompts/123
```
Update:
```json
PUT /prompts/123 (owner + token)
{"title":"New","content":"Updated"}
```
Delete (soft delete):
```text
DELETE /prompts/123 (owner + token)
```

### Like & Favorite toggle
```text
POST /prompts/123/like (token)     # call again to undo
POST /prompts/123/favorite (token) # call again to undo
```

### My lists
```text
GET /prompts/user/my-prompts (token)
GET /prompts/user/favorites  (token)
GET /prompts/user/likes      (token)
```

### Global stats
```text
GET /prompts/stats/global
```

## Notes
- Swagger: `http://localhost:8000/docs`
- Response shape: `{code:200, data: {}, msg:"成功"}` with camelCase fields

## Front-end Integration
- Repo: `https://github.com/mhxy13867806343/prompt-words-front-end`
- Prefix: both `/{...}` and `/api/{...}` are supported; prefer `/api`
- Vite proxy example:
  ```ts
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
  ```
