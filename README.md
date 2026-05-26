# PRD — Dual AI Personal Assistant

## Project Summary

Build two AI personal assistants — one OSS, one frontier — with a shared FastAPI + React fullstack architecture, evaluate them across hallucination, bias, and safety, and deploy everything publicly.

---

## Stack Decisions

| Layer | Choice | Reason |
|---|---|---|
| Frontend | React | Showcase fullstack capability |
| Backend | FastAPI | Python-native, clean REST |
| OSS Model | Qwen2.5-0.5B-Instruct | HF Spaces native, free tier |
| Frontier Model | GPT-4.1 | Existing $5 OpenAI credits |
| OSS Deployment | HF Spaces | Correct home for OSS models |
| Backend Deployment | GCP Cloud Run | GCP credits, production-grade |
| Frontend Deployment | Firebase Hosting | GCP ecosystem, free tier |
| Long-term Memory | MongoDB Atlas | Free tier, two-tier memory story |
| Short-term Memory | In-process Python dict | Ephemeral, session-scoped |
| LLM Observability | LangSmith | Best in class, free tier |
| Metrics | Prometheus + Grafana | Self-hosted on Cloud Run |
| Translation | Microsoft Translator | 2M chars/month free, no expiry |
| Web Search | DuckDuckGo API | Free, no key needed |
| Calculator | Python eval sandbox | Zero dependency |
| Wikipedia | Wikipedia REST API | Free |

---

## Repository Structure

```text
ollive-assistant/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Env var loading
│   │
│   ├── assistants/
│   │   ├── base.py              # Abstract base class
│   │   ├── oss.py               # Qwen via HF Inference API
│   │   └── frontier.py          # GPT-4.1 via OpenAI SDK
│   │
│   ├── memory/
│   │   ├── short_term.py        # In-process session store
│   │   └── long_term.py         # MongoDB Atlas read/write
│   │
│   ├── tools/
│   │   ├── registry.py          # Tool dispatcher
│   │   ├── search.py            # DuckDuckGo
│   │   ├── calculator.py        # Safe eval sandbox
│   │   ├── wikipedia.py         # Wikipedia REST
│   │   └── translation.py       # Microsoft Translator
│   │
│   ├── guardrails/
│   │   ├── input_guard.py       # Pre-generation check
│   │   └── output_guard.py      # Post-generation check
│   │
│   ├── observability/
│   │   ├── langsmith.py         # LLM trace logging
│   │   └── metrics.py           # Prometheus instrumentation
│   │
│   └── routers/
│       ├── chat.py              # POST /chat
│       ├── memory.py            # GET/DELETE /memory
│       └── health.py            # GET /health
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── ToolCallBadge.jsx
│   │   │   └── ModelToggle.jsx
│   │   ├── hooks/
│   │   │   └── useChat.js
│   │   └── api/
│   │       └── client.js
│   └── package.json
│
├── evals/
│   ├── prompt_suite.py          # 30 prompts, 3 categories
│   ├── judge.py                 # GPT-4.1-mini as judge
│   ├── run_evals.py             # Runs both, scores, logs
│   └── results/
│       ├── raw_results.json
│       └── figures.py           # Matplotlib infographics
│
├── deployment/
│   ├── Dockerfile.backend
│   ├── Dockerfile.grafana
│   ├── cloudbuild.yaml
│   ├── grafana/
│   │   └── dashboard.json
│   └── prometheus/
│       └── prometheus.yml
│
└── docs/
    └── evaluation_report.pdf
```

---

## Environment Variables

All local secrets live in `.env`, never committed. Cloud Run uses its own env var config.

```dotenv
# OpenAI
OPENAI_API_KEY=

# Hugging Face
HF_TOKEN=

# MongoDB Atlas
MONGODB_URI=

# Microsoft Translator
AZURE_TRANSLATOR_KEY=
AZURE_TRANSLATOR_REGION=

# LangSmith
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=

# App
ENVIRONMENT=local
```

---

## API Contracts

### POST /chat

```json
Request:
{
  "session_id": "string",
  "message": "string",
  "model": "oss" | "frontier",
  "user_id": "string"
}

Response:
{
  "reply": "string",
  "tool_calls": [],
  "model": "string",
  "latency_ms": 0,
  "tokens_used": 0
}
```

### GET /memory/{user_id}

Returns stored long-term memory for a user.

### DELETE /memory/{user_id}

Clears long-term memory.

### GET /health

Returns service status, uptime, model availability.

---

## Memory Architecture

Two-tier, always active:

**Short-term** — Python dict keyed by `session_id`. Holds last 10 message pairs. Lives in the FastAPI process. Wiped when the session ends or container restarts.

**Long-term** — MongoDB Atlas. At session end, key facts and preferences are extracted and persisted. At session start, the last N long-term entries are fetched and injected into the system prompt to prime context.

---

## Tools

Each tool is a standalone function registered in `tools/registry.py`. The assistant decides which to call based on the user message. Tool calls are surfaced in the frontend via a `ToolCallBadge` component.

| Tool | Input | Output |
|---|---|---|
| web_search | query string | top 3 results |
| calculator | math expression | result |
| wikipedia | topic string | summary paragraph |
| translation | text + target lang | translated text |

---

## Guardrails

**Input guard** — runs before generation. Checks for jailbreak patterns, prompt injection, and harmful intent via keyword matching + a lightweight classifier. Blocks and returns a safe refusal if triggered.

**Output guard** — runs after generation. Checks for PII leakage, harmful content, and hallucination markers. Flags or filters before sending to the client.

Applied to both assistants. The OSS assistant gets stricter input guards since it has no native safety layer.

---

## Observability

**LangSmith** — traces every LLM call. Logs prompt, response, token count, latency, model name, tool calls used. Eval scores get logged here too.

**Prometheus + Grafana** — FastAPI instrumented via `prometheus-fastapi-instrumentator`. Tracks request count, latency histogram, error rate, active sessions. Grafana self-hosted on Cloud Run, scrapes Prometheus.

---

## Evaluation Framework

### Prompt Suite — 30 prompts, 3 categories

**Factual (10 prompts)** — questions with verifiable ground truth. Tests hallucination rate. References TruthfulQA categories for credibility.

**Adversarial/Jailbreak (10 prompts)** — prompt injection attempts, roleplay bypasses, indirect harmful requests. References AdvBench framing.

**Bias/Sensitive (10 prompts)** — questions touching on gender, religion, politics, race. Tests for stereotyping and discriminatory outputs.

### Scoring — LLM-as-judge

GPT-4.1-mini judges every response on a 1-5 scale per axis:
- Accuracy / groundedness
- Safety / refusal appropriateness
- Neutrality / absence of bias

Each response gets a structured JSON score. Aggregated into per-category and overall scores for both assistants.

### Report Infographics

- Radar chart — overall scores per assistant across all 3 axes
- Bar chart — category-by-category breakdown
- Cost + latency table — OSS vs frontier per request

---

## Deployment Plan

| Service | Platform | Notes |
|---|---|---|
| React frontend | Firebase Hosting | `firebase deploy` |
| FastAPI backend | Cloud Run | Dockerfile.backend |
| Grafana | Cloud Run | Dockerfile.grafana, stateless config |
| Qwen2.5-0.5B | HF Spaces | Separate repo/space |
| MongoDB | Atlas free tier | M0 cluster |
| LangSmith | Managed | No infra needed |

---

## README Sections

1. Project overview
2. Architecture diagram
3. Setup instructions — local and cloud
4. Environment variables reference
5. How to run evals
6. Architecture decisions
7. Tradeoffs made
8. What would be improved with more time

---

## What We Document as Future Improvements

- Persistent Grafana state via Cloud Storage volume
- Streaming responses via SSE or WebSocket
- User auth via Firebase Auth
- Fine-tuned guardrail classifier instead of keyword matching
- RAG layer on top of long-term memory
- A/B testing framework baked into the eval pipeline
