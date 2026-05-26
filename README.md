# Dual Agents

A dual-model AI personal assistant platform comparing an open-source LLM against a frontier foundation model under the same application stack, memory system, guardrails, and evaluation pipeline.

The project implements:

- An OSS assistant powered by Qwen2.5-0.5B-Instruct
- A frontier assistant powered by GPT-4.1
- Multi-turn conversational memory
- Tool calling
- Guardrails and safety filters
- Evaluation workflows for hallucination, bias, and jailbreak robustness
- Observability using LangSmith, Prometheus, and Grafana
- Public deployment on GCP + Firebase

---

# Live Demo

Frontend: `https://dualagents.web.app`

---

# System Architecture

```text
React + Tailwind Frontend
           │
           ▼
      FastAPI Backend
           │
 ┌─────────┴─────────┐
 │                   │
 ▼                   ▼
OSS Assistant     Frontier Assistant
(Qwen2.5-0.5B)    (GPT-4.1)
 │                   │
 └─────────┬─────────┘
           ▼
      Shared Services
  - Guardrails
  - Memory
  - Tool Registry
  - Evaluations
  - Observability
```

---

# Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TailwindCSS, Vite |
| Backend | FastAPI, LangGraph |
| OSS Model | Qwen2.5-0.5B-Instruct |
| Frontier Model | GPT-4.1 |
| Memory | MongoDB Atlas + in-process session memory |
| Tooling | LangChain Tools |
| Observability | LangSmith, Prometheus, Grafana |
| Deployment | Firebase Hosting + GCP Cloud Run |
| Evaluations | Custom eval suite + LLM-as-judge |

---

# Features

## Dual Assistant Comparison

The application allows switching between:
- Open-source assistant
- Frontier hosted assistant

Both assistants operate through the same backend pipeline for fair evaluation.

---

## Multi-turn Conversations

Supports:
- Session-based conversational history
- Context retention across turns
- Shared interaction flow across both models

Short-term memory is maintained in-process using rolling conversation windows.

---

## Long-Term Memory

Persistent user memory is stored using MongoDB Atlas.

Examples:
- user preferences
- remembered facts
- conversational metadata

---

## Tool Use

The frontier assistant supports tool calling through LangGraph orchestration.

Implemented tools:
- Web search
- Wikipedia lookup
- Calculator
- Translation

---

## Guardrails and Safety

Implemented protections include:
- jailbreak detection
- prompt injection filtering
- harmful request blocking
- self-harm filtering
- PII redaction
- unsafe output filtering
- hallucination marker detection

Separate input and output guardrail layers are used.

---

## Observability

Integrated monitoring stack:
- LangSmith tracing
- Prometheus metrics
- Grafana dashboards

Tracked metrics:
- latency
- token usage
- tool calls
- guardrail triggers
- active sessions
- memory writes

---

# Evaluation Framework

The project evaluates both assistants across:

| Category | Description |
|---|---|
| Hallucination | Factual consistency and confidence |
| Bias | Harmful stereotypes or discriminatory outputs |
| Jailbreak Resistance | Resistance to prompt injection and adversarial prompts |
| Safety | Harmful content refusal behavior |
| Neutrality | Tone and response stability |

Evaluation pipeline:
- custom prompt suite
- adversarial prompts
- factual prompts
- LLM-as-judge scoring using GPT-4.1-mini

---

# Repository Structure

```text
backend/
├── assistants/
├── guardrails/
├── memory/
├── observability/
├── routers/
└── tools/

frontend/
├── components/
├── hooks/
└── api/

evals/
├── prompt_suite.py
├── judge.py
└── run_evals.py

deployment/
├── Dockerfiles
├── Grafana
└── Prometheus
```

---

# Local Setup

## 1. Clone Repository

```bash
git clone https://github.com/<your-username>/dual-agents
cd dual-agents
```

---

## 2. Backend Setup

```bash
cp .env.example .env
```

Fill in environment variables.

Install dependencies:

```bash
uv sync
```

Run backend:

```bash
python main.py
```

Backend runs on:

```text
http://127.0.0.1:8000
```

---

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

# Environment Variables

```env
OPENAI_API_KEY=
HF_TOKEN=
MONGODB_URI=
LANGCHAIN_API_KEY=
AZURE_TRANSLATOR_KEY=
AZURE_TRANSLATOR_REGION=
```

---

# Running Evaluations

Run complete evaluation suite:

```bash
python -m evals.run_evals
```

Run smoke test:

```bash
python -m evals.run_evals --limit 1
```

Generate evaluation figures:

```bash
python -m evals.results.figures
```

---

# Deployment

## Frontend

```bash
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

---

## Backend

```bash
gcloud builds submit
```

---

# Deployment Stack

| Service | Platform |
|---|---|
| Frontend | Firebase Hosting |
| Backend | GCP Cloud Run |
| OSS Model Hosting | Hugging Face Spaces |
| Database | MongoDB Atlas |
| Monitoring | Grafana + Prometheus |

---

# Design Decisions

## Why Qwen2.5-0.5B?

Chosen because:
- lightweight deployment
- inexpensive hosting
- fast inference
- deployable on free/low-cost infrastructure

Tradeoff:
- weaker reasoning and factual reliability compared to frontier models

---

## Why GPT-4.1?

Used as the frontier baseline because:
- strong reasoning performance
- reliable instruction following
- robust tool calling support

---

## Why LangGraph?

LangGraph was used instead of simple chains to support:
- tool orchestration
- graph-based execution
- expandable workflows
- production-style agent routing

---

# Limitations

Current limitations include:
- no streaming responses
- limited evaluation dataset size
- lightweight OSS model capability constraints
- no authentication layer
- in-memory short-term session storage

---

# Future Improvements

Potential improvements:
- SSE/WebSocket streaming
- Firebase authentication
- vector memory / RAG layer
- stronger OSS model deployment
- automated benchmark integration
- persistent observability storage
- A/B testing framework
- tool use for OSS assistant

---