"""Synthetic fixtures test software only; they are not project data or results."""
import importlib.util
from pathlib import Path
import unittest

from common import INVALID, LABELS, fingerprint


def load_module(filename):
    spec = importlib.util.spec_from_file_location("module_" + filename[:2], Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load_module("01_prepare_data.py")
vader = load_module("02_vader.py")
evaluator = load_module("03_evaluate.py")


class PipelineTests(unittest.TestCase):
    def test_error_counts_and_id_alignment(self):
        gold = [{"id": str(i), "text": "test", "label": LABELS[i // 2]} for i in range(6)]
        predictions = [{"id": str(i), "prediction": p} for i, p in enumerate(
            ("negative", "neutral", "neutral", "positive", "positive", INVALID))]
        summary, rows, matrix, errors = evaluator.evaluate(gold, list(reversed(predictions)))
        self.assertEqual(summary["correct"], 3)
        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual(summary["invalid_predictions"], 1)
        self.assertEqual([r["incorrect"] for r in rows], [1, 1, 1])
        self.assertEqual(len(errors), 3)
        self.assertEqual(sum(sum(c.values()) for c in matrix.values()), 6)

    def test_rejects_missing_extra_duplicate_and_unknown_predictions(self):
        gold = [{"id": "a", "label": "neutral"}]
        cases = [[], [{"id": "b", "prediction": "neutral"}],
                 [{"id": "a", "prediction": "neutral"}] * 2,
                 [{"id": "a", "prediction": "unknown"}]]
        for predictions in cases:
            with self.subTest(predictions=predictions), self.assertRaises(ValueError):
                evaluator.evaluate(gold, predictions)

    def test_conflicting_duplicates_and_test_priority(self):
        rows = [{"id": "a", "text": "test A", "label": "positive", "source_split": "train"},
                {"id": "a", "text": "test A", "label": "positive", "source_split": "test"},
                {"id": "b", "text": "test B", "label": "positive", "source_split": "train"},
                {"id": "b", "text": "test B", "label": "negative", "source_split": "test"}]
        clean, conflicts, audit = prepare.deduplicate(rows)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["source_split"], "test")
        self.assertEqual(len(conflicts), 2)
        self.assertEqual(audit["duplicate_rows_removed"], 1)

    def test_deterministic_selection_without_cross_split_leakage(self):
        rows = []
        for label in LABELS:
            for split in ("train", "validation", "test"):
                for i in range(5):
                    text = f"fixture {label} {split} {i}"
                    rows.append({"id": fingerprint(text), "text": text,
                                 "label": label, "source_split": split})
        targets = {"train": 2, "validation": 1, "test": 2}
        for language in ("en", "tr"):
            selected = prepare.select_splits(rows, language, targets, 42)
            self.assertEqual(selected, prepare.select_splits(rows, language, targets, 42))
            identifiers = [r["id"] for partition in selected.values() for r in partition]
            self.assertEqual(len(identifiers), len(set(identifiers)))
            for split, partition in selected.items():
                self.assertEqual(prepare.counts(partition), dict.fromkeys(LABELS, targets[split]))
                if language == "en":
                    self.assertTrue(all(row["source_split"] == split for row in partition))

    def test_vader_threshold_boundaries(self):
        self.assertEqual(vader.compound_label(-0.05), "negative")
        self.assertEqual(vader.compound_label(0.05), "positive")
        self.assertEqual(vader.compound_label(0), "neutral")


if __name__ == "__main__":
    unittest.main()
