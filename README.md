# OneAI Hub FastAPI backend

This service is the internal AI execution layer for OneAI Hub.
Public clients should call the Fastify backend only.

The Fastify backend owns:

- authentication
- sessions
- users
- payments
- notifications
- public API contracts for mobile and web

`ai-agent` should focus on:

- chat generation
- model routing
- voice
- RAG
- agents
- file processing
- background AI work

## Deployment boundary

```text
React / React Native
        |
API Gateway (Fastify)
        |
        +-- Authentication / Payments / Users / Notifications
        |
        +-- AI Service (FastAPI / ai-agent)
              +-- Chat generation
              +-- Model Router
              +-- Voice
              +-- RAG
              +-- Agents
              +-- File Processing
              +-- Background Workers
```

Use the backend as the only public entry point.
Do not call `ai-agent` directly from mobile or dashboard.

The backend already has an internal proxy route:

- Fastify: `/api/v1/ai-service/*`
- FastAPI: `/api/v1/*`

Example:

- Fastify `/api/v1/ai-service/chat/responses`
- forwards to FastAPI `/api/v1/chat/responses`

## Current env contract

For the current internal AI-service setup, `ai-agent` only needs provider API keys in `.env`:

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `GEMINI_API_KEY`
- `PERPLEXITY_API_KEY`
- `ANTHROPIC_API_KEY`
- `XAI_API_KEY`

Base URLs and default model names already fall back to code defaults in `app/core/config.py`.
When all six keys are configured, `GET /api/v1/chat/models` exposes all six models:

| App model | Provider | Default provider model |
| --- | --- | --- |
| ChatGPT | OpenAI | `gpt-5.6-sol` |
| DeepSeek | DeepSeek | `deepseek-v4-flash` |
| Gemini | Google | `gemini-3.6-flash` |
| Perplexity | Perplexity | `sonar` |
| Claude | Anthropic | `claude-sonnet-5` |
| Grok | xAI | `grok-4.5` |

## Run locally

Install the service once, then start it before the Fastify backend:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host localhost --port 8000 --reload
```

`requirements.txt` is the only dependency file. It contains runtime, worker, testing,
linting, and type-checking packages. `pyproject.toml` contains only package metadata and
tool configuration.

Keep `backend/.env` configured with:

```dotenv
AI_SERVICE_BASE_URL=http://localhost:8000/api/v1
```

Mobile calls Fastify on port 4000. Fastify authenticates the user, owns conversation
history and memory, and forwards model generation to this service. Provider keys never
need to be placed in the mobile app or sent through the public API.

## Project structure

```text
ai-agent/
|-- app/
|   |-- api/v1/endpoints/   FastAPI route handlers
|   |-- core/               Pydantic settings, security, and infrastructure
|   |-- repositories/       Persistence boundaries
|   |-- schemas/            Pydantic request and response models
|   |-- services/           Model routing and AI business logic
|   |-- workers/            Background task entry points
|   |-- dependencies.py     Shared FastAPI dependency providers
|   `-- main.py             Application factory
|-- tests/                  Unit and API contract tests
|-- .dockerignore           Docker build exclusions, including secrets
|-- .gitignore              Local and secret-file exclusions
|-- compose.yaml            Local/container deployment definition
|-- Dockerfile              Non-root production image
|-- requirements.txt        All Python dependencies
`-- pyproject.toml          Package metadata and tool configuration
```

All HTTP payloads inherit from the shared Pydantic `ApiModel`. It rejects unknown fields,
accepts camelCase JSON aliases used by Fastify, trims input strings, and validates assignment.
Environment configuration uses Pydantic Settings and reads provider secrets from `.env`.

## Active route surface

- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/chat/models`
- `POST /api/v1/chat/responses`
- `POST /api/v1/voice/ws`
- `POST /api/v1/rag/ingest`
- `POST /api/v1/rag/search`
- `POST /api/v1/agents/run`
- `POST /api/v1/files/upload`

Conversation persistence is intentionally owned by Fastify. FastAPI receives prepared
conversation context through `POST /api/v1/chat/responses` and generates the response.

## Docker deployment

The image runs as a non-root user, excludes `.env`, stores uploads in a mounted volume,
and includes a liveness health check. Start it with:

```powershell
docker compose up --build -d
docker compose ps
```

The service is published only on `127.0.0.1:8000`, so it is not directly exposed on the
machine's public interfaces. Keep Fastify configured as follows when Fastify runs on the host:

```dotenv
AI_SERVICE_BASE_URL=http://localhost:8000/api/v1
```

If Fastify runs in the same Docker network, use the service DNS name instead:

```dotenv
AI_SERVICE_BASE_URL=http://ai-agent:8000/api/v1
```

For a registry deployment:

```powershell
docker build -t your-registry/oneai-hub-ai-agent:latest .
docker push your-registry/oneai-hub-ai-agent:latest
```

Provide provider keys through your deployment platform's secret manager or `--env-file`.
Never copy `.env` into an image or place provider keys in mobile/dashboard builds.

## Notes

- Mobile already points to the backend API, which is the correct public path.
- Both `/api/v1/ai` and `/api/v1/conversations` use this AI service. Fastify no longer
  stores provider keys or calls AI providers directly.
