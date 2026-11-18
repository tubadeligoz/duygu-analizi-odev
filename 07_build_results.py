"""Recompute every reported metric, verify common test IDs, then build real tables/plots."""
import argparse
import json
from pathlib import Path
import random
import re

from common import INVALID, LABELS, read_csv, write_csv, write_json
from experiment_utils import ROOT, load_script, sha256, utc_now

NAMES = {"vader": "VADER", "vader_diagnostic": "VADER tanısal", "bert": "BERT", "llm": "Qwen 2.5 7B"}
LABEL_TR = {"negative": "Negatif", "neutral": "Nötr", "positive": "Pozitif", INVALID: "Geçersiz"}


def collect():
    runs, unavailable = [], []
    evaluator = load_script("03_evaluate.py")
    for lang in ("en", "tr"):
        vader = "en_vader" if lang == "en" else "tr_vader_diagnostic"
        specs = [("vader" if lang == "en" else "vader_diagnostic", ROOT / "results" / vader,
                  ROOT / "predictions" / (vader + ".csv")),
                 ("bert", ROOT / "runs" / (lang + "_bert_seed42") / "evaluation",
                  ROOT / "runs" / (lang + "_bert_seed42") / "test_predictions.csv"),
                 ("llm", ROOT / "runs" / (lang + "_llm_test") / "evaluation",
                  ROOT / "runs" / (lang + "_llm_test") / "predictions.csv")]
        for key, result_dir, predictions in specs:
            metrics_path = result_dir / "metrics.json"
            if not metrics_path.exists():
                unavailable.append({"language": lang, "method": key, "status": "not_completed"})
                continue
            recorded = json.loads(metrics_path.read_text(encoding="utf-8"))
            gold_path = ROOT / "data" / lang / "test.csv"
            gold = read_csv(gold_path)
            predictions_rows = read_csv(predictions)
            summary, classes, matrix, errors = evaluator.evaluate(gold, predictions_rows)
            if sha256(gold_path) != recorded["gold_sha256"] or sha256(predictions) != recorded["predictions_sha256"]:
                raise ValueError("Reported data or predictions changed")
            for metric in ("n", "correct", "incorrect", "accuracy", "macro_f1", "invalid_predictions"):
                if summary[metric] != recorded[metric]:
                    raise ValueError(f"Recorded/recomputed metric mismatch: {lang}/{key}/{metric}")
            sidecar = predictions.with_suffix(".metadata.json")
            metadata = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
            runs.append({"language": lang, "method": key, "display_name": NAMES[key], "metrics": summary,
                         "classes": classes, "matrix": matrix, "errors": errors,
                         "gold_sha256": sha256(gold_path), "predictions_sha256": sha256(predictions),
                         "predictions_path": str(predictions.relative_to(ROOT)), "result_path": str(result_dir.relative_to(ROOT)),
                         "metadata": metadata})
    identities = [r["metadata"].get("model_identity") for r in runs if r["method"] == "llm"]
    from llm_support import model_signature
    if len(identities) == 2 and model_signature(identities[0]) != model_signature(identities[1]):
        raise ValueError("The two languages used different LLM identities")
    return runs, unavailable


def make_plots(runs, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 200})
    colors = {"vader": "#577590", "vader_diagnostic": "#577590", "bert": "#24786D", "llm": "#BC7540"}
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1), layout="constrained")
    labels = [r["language"].upper() + "\n" + r["display_name"] for r in runs]
    for ax, metric, title in zip(axes, ("accuracy", "macro_f1"), ("Accuracy", "Macro F1")):
        values = [r["metrics"][metric] for r in runs]
        ax.bar(range(len(runs)), values, color=[colors[r["method"]] for r in runs], width=.7)
        ax.set_xticks(range(len(runs)), labels, fontsize=8)
        ax.set_ylim(0, 1)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
        for i, value in enumerate(values):
            ax.text(i, value + .018, f"{value:.3f}", ha="center", fontsize=9)
    fig.savefig(output / "comparison.png", bbox_inches="tight")
    plt.close(fig)
    for lang in ("en", "tr"):
        subset = [r for r in runs if r["language"] == lang]
        fig, axes = plt.subplots(1, len(subset), figsize=(11, 3.6), squeeze=False, layout="constrained")
        for ax, run in zip(axes[0], subset):
            matrix = np.array([[run["matrix"][c][p] for p in (*LABELS, INVALID)] for c in LABELS])
            ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1000)
            ax.set_xticks(range(4), ["Neg.", "Nötr", "Poz.", "Geçersiz"], rotation=30, ha="right", fontsize=9)
            ax.set_yticks(range(3), [LABEL_TR[c] for c in LABELS], fontsize=9)
            ax.set_title(run["display_name"], fontsize=11)
            ax.set_xlabel("Tahmin")
            ax.set_ylabel("Gerçek sınıf")
            for i in range(3):
                for j in range(4):
                    ax.text(j, i, str(matrix[i, j]), ha="center", va="center",
                            color="white" if matrix[i, j] > 500 else "#222222", fontsize=10)
        fig.savefig(output / f"confusion_{lang}.png", bbox_inches="tight")
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for ax, lang in zip(axes, ("en", "tr")):
        subset = [r for r in runs if r["language"] == lang]
        width = .24
        for i, run in enumerate(subset):
            x = np.arange(3) + (i - (len(subset)-1)/2) * width
            values = [r["incorrect"] for r in run["classes"]]
            ax.bar(x, values, width, label=run["display_name"], color=colors[run["method"]])
        ax.set_xticks(range(3), [LABEL_TR[c] for c in LABELS])
        ax.set_ylim(0, 1100)
        ax.set_title(lang.upper() + " gerçek sınıf başına yanlış")
        ax.set_ylabel("Yanlış / 1000")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
    fig.savefig(output / "class_errors.png", bbox_inches="tight")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", default="deliverables")
    p.add_argument("--allow-partial", action="store_true")
    args = p.parse_args()
    out = Path(args.output)
    runs, unavailable = collect()
    if unavailable and not args.allow_partial:
        p.error(f"Incomplete experiments: {unavailable}; --allow-partial explicitly marks missing results")
    summary, class_rows, directions, sample, candidates = [], [], [], [], []
    patterns = {"olumsuzluk": r"\b(not|never|no|isn't|don't|değil|yok|hiç)\b|beğenmed|olmadı",
                "ironi_adayi": r"yeah right|thanks.*(nothing|ruin)|great.*(not|hate)|(!{2,})|sanki|sağolsun",
                "karisik_duygu": r"\b(but|however|although|ama|fakat|ancak)\b",
                "notr_siniri": r"\b(ok|okay|average|normal|idare|orta|eh|fena)\b",
                "etiket_gurultusu_adayi": r"mükemmel|tavsiye|berbat|excellent|awful|harika"}
    for run in runs:
        m = run["metrics"]
        row = {"language": run["language"], "method": run["display_name"], "n": m["n"],
               **{c["class"] + "_incorrect": c["incorrect"] for c in run["classes"]},
               "incorrect": m["incorrect"], "accuracy": m["accuracy"], "macro_f1": m["macro_f1"],
               "invalid_predictions": m["invalid_predictions"], "gold_sha256": run["gold_sha256"],
               "inference_seconds": run["metadata"].get("inference_seconds"),
               "llm_wall_seconds_current_session": run["metadata"].get("current_session_wall_seconds"),
               "llm_summed_request_seconds": run["metadata"].get("summed_request_seconds")}
        summary.append(row)
        class_rows.extend({"language": run["language"], "method": run["display_name"], **c} for c in run["classes"])
        for truth in LABELS:
            for pred in (*LABELS, INVALID):
                if truth != pred:
                    directions.append({"language": run["language"], "method": run["display_name"],
                                       "gold": truth, "prediction": pred, "count": run["matrix"][truth][pred]})
        rng = random.Random(42)
        for c in LABELS:
            pool = sorted((r for r in run["errors"] if r["label"] == c), key=lambda r: r["id"])
            for error in rng.sample(pool, min(5, len(pool))):
                sample.append({"language": run["language"], "method": run["display_name"], **error,
                               "category": "", "reviewer_1": "", "reviewer_2": "", "interpretation": ""})
        for category, pattern in patterns.items():
            pool = [r for r in sorted(run["errors"], key=lambda r: r["id"])
                    if re.search(pattern, r["text"], flags=re.IGNORECASE)]
            for error in pool[:4]:
                candidates.append({"language": run["language"], "method": run["display_name"],
                                   "candidate_category": category, **error})
    write_csv(out / "comparison.csv", summary, list(summary[0]))
    write_csv(out / "class_metrics.csv", class_rows, list(class_rows[0]))
    write_csv(out / "error_directions.csv", directions, list(directions[0]))
    write_csv(out / "error_review_sample.csv", sample, list(sample[0]))
    write_csv(out / "error_candidates.csv", candidates, list(candidates[0]))
    make_plots(runs, out / "figures")
    serializable = [{k: v for k, v in r.items() if k != "errors"} for r in runs]
    write_json(out / "report_data.json", {"built_at_utc": utc_now(), "runs": serializable, "unavailable": unavailable,
                                         "all_common_test_checks_passed": True,
                                         "manual_review_sample_n": len(sample)})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
