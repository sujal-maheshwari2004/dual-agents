import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("evals/results/raw_results.json")
DEFAULT_OUTPUT_DIR = Path("evals/results")


def generate_figures(input_path: Path = DEFAULT_INPUT, output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    summary = payload["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_cost_latency_table(summary, output_dir / "cost_latency_table.csv")

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        _write_text_fallback(summary, output_dir / "figures_summary.md")
        return

    _plot_radar(summary, output_dir / "radar_scores.png", plt)
    _plot_category_breakdown(summary, output_dir / "category_breakdown.png", plt)


def _plot_radar(summary: dict[str, Any], output_path: Path, plt: Any) -> None:
    axes = ("accuracy", "safety", "neutrality")
    models = sorted(summary["overall"])
    angles = [index / len(axes) * 2 * math.pi for index in range(len(axes))]
    angles += angles[:1]

    figure = plt.figure(figsize=(7, 7))
    axis = figure.add_subplot(111, polar=True)
    for model in models:
        values = [summary["overall"][model].get(axis_name, 0) for axis_name in axes]
        values += values[:1]
        axis.plot(angles, values, linewidth=2, label=model)
        axis.fill(angles, values, alpha=0.12)

    axis.set_xticks(angles[:-1])
    axis.set_xticklabels([axis_name.title() for axis_name in axes])
    axis.set_ylim(0, 5)
    axis.set_yticks([1, 2, 3, 4, 5])
    axis.set_title("Overall Assistant Scores", pad=24)
    axis.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def _plot_category_breakdown(summary: dict[str, Any], output_path: Path, plt: Any) -> None:
    categories = sorted(summary["by_category"])
    models = sorted(summary["overall"])
    axes = ("accuracy", "safety", "neutrality")
    width = 0.35

    figure, axis = plt.subplots(figsize=(10, 6))
    x_positions = list(range(len(categories)))
    for model_index, model in enumerate(models):
        values = []
        for category in categories:
            category_scores = summary["by_category"][category].get(model, {})
            axis_mean = sum(category_scores.get(axis_name, 0) for axis_name in axes) / len(axes)
            values.append(axis_mean)
        offset = (model_index - (len(models) - 1) / 2) * width
        axis.bar([position + offset for position in x_positions], values, width, label=model)

    axis.set_ylabel("Average Score")
    axis.set_ylim(0, 5)
    axis.set_title("Category-by-Category Breakdown")
    axis.set_xticks(x_positions)
    axis.set_xticklabels([category.replace("_", " ").title() for category in categories])
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def _write_cost_latency_table(summary: dict[str, Any], output_path: Path) -> None:
    rows = []
    for model, values in sorted(summary["cost_latency"].items()):
        rows.append(
            {
                "model": model,
                "avg_latency_ms": values.get("avg_latency_ms", 0),
                "total_tokens": values.get("total_tokens", 0),
                "avg_tokens": values.get("avg_tokens", 0),
                "estimated_cost_usd": values.get("estimated_cost_usd", 0),
            }
        )

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=(
                "model",
                "avg_latency_ms",
                "total_tokens",
                "avg_tokens",
                "estimated_cost_usd",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_text_fallback(summary: dict[str, Any], output_path: Path) -> None:
    lines = ["# Evaluation Figure Summary", ""]
    lines.append("Matplotlib is not installed, so PNG figures were skipped.")
    lines.append("")
    lines.append("## Overall Scores")
    for model, scores in sorted(summary["overall"].items()):
        lines.append(
            f"- {model}: accuracy={scores.get('accuracy', 0)}, "
            f"safety={scores.get('safety', 0)}, neutrality={scores.get('neutrality', 0)}"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate evaluation figures.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_figures(args.input, args.output_dir)


if __name__ == "__main__":
    main()
