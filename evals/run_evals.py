import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.routers.chat import create_chat_completion
from backend.schemas import AssistantModel, ChatRequest, ChatResponse
from evals.judge import ResponseJudge
from evals.prompt_suite import EvalCategory, EvalPrompt, get_prompt_suite


DEFAULT_OUTPUT = Path("evals/results/raw_results.json")


@dataclass(frozen=True, slots=True)
class EvalRunConfig:
    models: tuple[AssistantModel, ...]
    limit: int | None
    output_path: Path
    skip_judge: bool = False


async def run_evaluations(config: EvalRunConfig) -> dict[str, Any]:
    prompts = get_prompt_suite(config.limit)
    judge = ResponseJudge()
    rows: list[dict[str, Any]] = []

    for model in config.models:
        for prompt in prompts:
            response = await _run_single_assistant(model, prompt)
            score = (
                await judge.score(prompt, response.reply)
                if not config.skip_judge
                else None
            )
            rows.append(
                {
                    "prompt": prompt.to_dict(),
                    "assistant": {
                        "requested_model": model.value,
                        "provider_model": response.model,
                        "reply": response.reply,
                        "tool_calls": [tool_call.model_dump() for tool_call in response.tool_calls],
                        "guardrail_flags": [
                            flag.model_dump() for flag in response.guardrail_flags
                        ],
                        "latency_ms": response.latency_ms,
                        "tokens_used": response.tokens_used,
                    },
                    "score": score.to_dict() if score else None,
                }
            )

    payload = {
        "run": {
            "created_at": datetime.now(UTC).isoformat(),
            "prompt_count": len(prompts),
            "assistant_count": len(config.models),
            "skip_judge": config.skip_judge,
        },
        "results": rows,
        "summary": summarize_results(rows),
    }
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "overall": {},
        "by_category": {},
        "cost_latency": {},
    }
    scored_rows = [row for row in rows if row.get("score")]

    for model in sorted({row["assistant"]["requested_model"] for row in rows}):
        model_rows = [row for row in rows if row["assistant"]["requested_model"] == model]
        model_scored = [row for row in scored_rows if row["assistant"]["requested_model"] == model]
        summary["overall"][model] = _average_scores(model_scored)
        summary["cost_latency"][model] = _cost_latency(model_rows)

    for category in EvalCategory:
        category_key = category.value
        summary["by_category"][category_key] = {}
        for model in sorted({row["assistant"]["requested_model"] for row in rows}):
            category_rows = [
                row
                for row in scored_rows
                if row["assistant"]["requested_model"] == model
                and row["prompt"]["category"] == category_key
            ]
            summary["by_category"][category_key][model] = _average_scores(category_rows)

    return summary


async def _run_single_assistant(model: AssistantModel, prompt: EvalPrompt) -> ChatResponse:
    session_id = f"eval-{model.value}-{prompt.id}"
    request = ChatRequest(
        session_id=session_id,
        user_id="eval-user",
        model=model,
        message=prompt.prompt,
    )
    return await create_chat_completion(request)


def _average_scores(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    if not rows:
        return {"accuracy": 0.0, "safety": 0.0, "neutrality": 0.0, "count": 0}

    axes = ("accuracy", "safety", "neutrality")
    return {
        axis: round(sum(row["score"][axis] for row in rows) / len(rows), 3)
        for axis in axes
    } | {"count": len(rows)}


def _cost_latency(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    if not rows:
        return {
            "avg_latency_ms": 0.0,
            "total_tokens": 0,
            "avg_tokens": 0.0,
            "estimated_cost_usd": 0.0,
        }

    total_tokens = sum(row["assistant"]["tokens_used"] for row in rows)
    return {
        "avg_latency_ms": round(
            sum(row["assistant"]["latency_ms"] for row in rows) / len(rows),
            3,
        ),
        "total_tokens": total_tokens,
        "avg_tokens": round(total_tokens / len(rows), 3),
        "estimated_cost_usd": _estimate_cost(rows[0]["assistant"]["requested_model"], total_tokens),
    }


def _estimate_cost(model: str, total_tokens: int) -> float:
    # Rough PRD-facing estimate only. Exact provider billing should be computed externally.
    per_1m_tokens = {"frontier": 2.0, "oss": 0.0}
    return round((total_tokens / 1_000_000) * per_1m_tokens.get(model, 0.0), 6)


def parse_args() -> EvalRunConfig:
    parser = argparse.ArgumentParser(description="Run dual assistant evaluations.")
    parser.add_argument("--limit", type=int, default=None, help="Limit prompts for smoke runs.")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=[model.value for model in AssistantModel],
        default=[AssistantModel.OSS.value, AssistantModel.FRONTIER.value],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write raw eval JSON.",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Run assistants but omit judge scoring.",
    )
    args = parser.parse_args()
    return EvalRunConfig(
        models=tuple(AssistantModel(model) for model in args.models),
        limit=args.limit,
        output_path=args.output,
        skip_judge=args.skip_judge,
    )


def main() -> None:
    payload = asyncio.run(run_evaluations(parse_args()))
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
