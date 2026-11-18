"""Strict ID alignment and class-wise error counts for every method."""
import argparse
from collections import Counter
import hashlib
from pathlib import Path

from common import INVALID, LABELS, read_csv, unique_index, write_csv, write_json


def evaluate(gold_rows, prediction_rows):
    gold = unique_index(gold_rows, "id", "Gold data")
    predictions = unique_index(prediction_rows, "id", "Predictions")
    if not gold:
        raise ValueError("Gold data is empty")
    if gold.keys() != predictions.keys():
        missing = len(gold.keys() - predictions.keys())
        extra = len(predictions.keys() - gold.keys())
        raise ValueError(f"Prediction coverage mismatch: {missing} missing, {extra} extra IDs")
    matrix = {label: Counter({pred: 0 for pred in (*LABELS, INVALID)}) for label in LABELS}
    errors = []
    for identifier, row in gold.items():
        truth, prediction = row.get("label"), predictions[identifier].get("prediction")
        if truth not in LABELS:
            raise ValueError(f"Unknown gold label: {truth!r}")
        if prediction not in (*LABELS, INVALID):
            raise ValueError(f"Unknown prediction {prediction!r}; explicitly use {INVALID} for failed outputs")
        matrix[truth][prediction] += 1
        if prediction != truth:
            errors.append({"id": identifier, "text": row.get("text", ""),
                           "label": truth, "prediction": prediction})
    per_class = []
    for label in LABELS:
        support = sum(matrix[label].values())
        correct = matrix[label][label]
        incorrect = support - correct
        predicted_count = sum(matrix[truth][label] for truth in LABELS)
        false_positive = predicted_count - correct
        precision = correct / predicted_count if predicted_count else 0.0
        recall = correct / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({"class": label, "support": support, "correct": correct,
                          "incorrect": incorrect, "false_negative": incorrect,
                          "false_positive": false_positive,
                          "invalid_predictions": matrix[label][INVALID],
                          "error_rate": incorrect / support if support else None,
                          "precision": precision, "recall": recall, "f1": f1})
    summary = {"n": len(gold), "correct": len(gold) - len(errors), "incorrect": len(errors),
               "accuracy": (len(gold) - len(errors)) / len(gold),
               "macro_f1": sum(row["f1"] for row in per_class) / len(LABELS),
               "invalid_predictions": sum(matrix[label][INVALID] for label in LABELS),
               "label_order": LABELS, "confusion_rows": "gold", "confusion_columns": "prediction"}
    return summary, per_class, matrix, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True, help="New report directory")
    parser.add_argument("--method", required=True)
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists() and any(out.iterdir()):
        parser.error("Report directory must be empty")
    summary, per_class, matrix, errors = evaluate(read_csv(args.gold), read_csv(args.predictions))
    summary.update({"method": args.method, "language": args.language,
                    "gold_sha256": hashlib.sha256(Path(args.gold).read_bytes()).hexdigest(),
                    "predictions_sha256": hashlib.sha256(Path(args.predictions).read_bytes()).hexdigest()})
    write_json(out / "metrics.json", summary)
    write_csv(out / "class_errors.csv", per_class, list(per_class[0]))
    write_csv(out / "confusion_matrix.csv",
              [{"true_class": label, **dict(matrix[label])} for label in LABELS],
              ("true_class", *LABELS, INVALID))
    write_csv(out / "misclassified.csv", errors, ("id", "text", "label", "prediction"))
    print(summary)


if __name__ == "__main__":
    main()
