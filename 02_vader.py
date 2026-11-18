"""Run original VADER; Turkish execution is explicitly a diagnostic baseline."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
from pathlib import Path
import time

from common import LABELS, read_csv, unique_index, write_csv, write_json


def compound_label(score):
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--turkish-diagnostic", action="store_true",
                        help="Acknowledge that original VADER has no native Turkish adaptation")
    args = parser.parse_args()
    if args.language == "tr" and not args.turkish_diagnostic:
        parser.error("For direct Turkish VADER use --turkish-diagnostic and report its limitations")
    output = Path(args.output)
    if output.exists() or output.with_suffix(".metadata.json").exists():
        parser.error("Output exists; choose a new filename to preserve prior runs")
    rows = read_csv(args.input)
    unique_index(rows, "id", "Input")
    if not rows or any(not row.get("text") or row.get("label") not in LABELS for row in rows):
        parser.error("Input must contain nonempty text and valid labels")
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    start = time.perf_counter()
    predictions = []
    for row in rows:
        score = analyzer.polarity_scores(row["text"])["compound"]
        predictions.append({"id": row["id"], "prediction": compound_label(score),
                            "compound": score})
    elapsed = time.perf_counter() - start
    write_csv(output, predictions, ("id", "prediction", "compound"))
    write_json(output.with_suffix(".metadata.json"), {
        "method": "VADER_original_TR_diagnostic" if args.language == "tr" else "VADER_original_EN",
        "language": args.language, "package_version": importlib.metadata.version("vaderSentiment"),
        "thresholds": {"negative_max": -0.05, "positive_min": 0.05},
        "input_sha256": hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(rows), "inference_seconds": elapsed,
        "note": "Direct Turkish use is a diagnostic, not a native Turkish sentiment system"
                if args.language == "tr" else "English original VADER",
    })
    print("Saved", len(predictions), "predictions to", output)


if __name__ == "__main__":
    main()
