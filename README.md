# Dual Agents

Two AI personal assistants — one OSS (Qwen2.5-0.5B), one frontier (GPT-4.1) — built on a shared FastAPI + React fullstack, evaluated across hallucination, bias, and safety, and deployed publicly on GCP.

**Live demo:** https://bot-street.web.app

---

## Architecture

```
React (Firebase Hosting)
       │
       ▼
FastAPI (GCP Cloud Run)
       │
       ├── Qwen2.5-0.5B  (HF Space → OpenAI-compatible endpoint)
       ├── GPT-4.1        (OpenAI API)
       │
       ├── Tools          (web search, calculator, wikipedia, translation)
       ├── Guardrails     (input + output, PII filtering, jailbreak detection)
       ├── Memory         (short-term in-process, long-term MongoDB Atlas)
       └── Observability  (LangSmith traces, Prometheus + Grafana)
```

---

## Stack

| Layer | Choice |
|---|---|
| Frontend | React + Tailwind + Vite |
| Backend | FastAPI + LangGraph |
| OSS Model | Qwen2.5-0.5B-Instruct (HF Space) |
| Frontier Model | GPT-4.1 (OpenAI) |
| Memory | MongoDB Atlas + in-process dict |
| Observability | LangSmith + Prometheus + Grafana |
| Deployment | GCP Cloud Run + Firebase Hosting |

---

## Features

- **Model toggle** — switch between OSS and frontier mid-conversation
- **Tool use** — web search, calculator, Wikipedia, translation (frontier only)
- **Two-tier memory** — short-term session history + long-term MongoDB persistence
- **Guardrails** — input + output checks for jailbreaks, PII, harmful content, hallucination markers
- **Evals** — 30-prompt suite scored by GPT-4.1-mini across accuracy, safety, and neutrality
- **Observability** — every LLM call traced in LangSmith, metrics in Grafana

---

## Local Setup

### Backend

```bash
git clone https://github.com/MaheshwariSujal/dual-agents
cd dual-agents
cp .env.example .env
# fill in your keys
uv sync
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI key for GPT-4.1 |
| `HF_TOKEN` | Hugging Face token |
| `HF_BASE_URL` | HF Space inference URL |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `AZURE_TRANSLATOR_KEY` | Microsoft Translator key |
| `AZURE_TRANSLATOR_REGION` | Microsoft Translator region |
| `LANGCHAIN_API_KEY` | LangSmith key |

---

## Running Evals

```bash
# Full suite
python -m evals.run_evals

# Smoke test (1 prompt)
python -m evals.run_evals --limit 1

# Generate figures
python -m evals.results.figures
```

---

## Deployment

| Service | Platform |
|---|---|
| Frontend | Firebase Hosting |
| Backend | GCP Cloud Run |
| Grafana | GCP Cloud Run |
| OSS Model | HF Space |
| Database | MongoDB Atlas |

```bash
# Backend
gcloud builds submit

# Frontend
cd frontend && npm run build && cd .. && firebase deploy
```

---

## Future Improvements

- Streaming responses via SSE or WebSocket
- User auth via Firebase Auth
- RAG layer on top of long-term memory
- Fine-tuned guardrail classifier
- Persistent Grafana state via Cloud Storage
- A/B testing in the eval pipeline