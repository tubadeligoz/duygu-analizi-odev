"""Small synthetic fixtures verify contracts; never used as experiment observations."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from common import INVALID, LABELS
from experiment_utils import load_script, model_inputs
from llm_support import classify, estimate_cost, load_journal, messages_for, parse_label, select_pilot
from llm_support import compatible_signature


class ExperimentContractTests(unittest.TestCase):
    def test_runtime_update_requires_opt_in_and_never_allows_model_or_input_change(self):
        old = {"model_identity": {"digest": "same", "ollama_version": "1"}, "input_sha256": "gold"}
        new = {"model_identity": {"digest": "same", "ollama_version": "2"}, "input_sha256": "gold"}
        self.assertFalse(compatible_signature(old, new))
        self.assertTrue(compatible_signature(old, new, True))
        new["model_identity"]["digest"] = "different"
        self.assertFalse(compatible_signature(old, new, True))
        new["model_identity"]["digest"] = "same"
        new["input_sha256"] = "changed"
        self.assertFalse(compatible_signature(old, new, True))

    def test_inference_inputs_and_prompts_never_contain_gold_fields(self):
        rows = [{"id": "opaque", "text": "A review", "label": "negative", "score": 1, "source_split": "test"}]
        self.assertEqual(model_inputs(rows), [{"id": "opaque", "text": "A review"}])
        message = json.loads(messages_for(rows[0]["text"], "frozen prompt")[1]["content"])
        self.assertEqual(message, {"review": "A review"})

    def test_strict_parser_does_not_infer_neutral_from_invalid(self):
        for text in ("", "Neutral", "The label is neutral", '"neutral"', "negative\npositive", None):
            self.assertEqual(parse_label(text), INVALID)
        for label in LABELS:
            self.assertEqual(parse_label(" \n" + label + " \n"), label)

    def test_timeout_and_invalid_retries_keep_all_raw_responses(self):
        responses = iter([TimeoutError(), ("not a label", {}), ("positive", {"input_tokens": 4})])
        def request(*_):
            result = next(responses)
            if isinstance(result, Exception):
                raise result
            return result
        record = classify({"id": "a", "text": "fixture"}, "prompt", {"max_attempts": 3}, request, lambda _: None)
        self.assertEqual(record["prediction"], "positive")
        self.assertEqual(len(record["attempts"]), 3)
        self.assertEqual(record["attempts"][1]["raw_response"], "not a label")
        self.assertEqual(record["input_tokens"], 4)

    def test_exhausted_response_is_invalid_and_counts_in_denominator(self):
        record = classify({"id": "a", "text": "fixture"}, "prompt", {"max_attempts": 2},
                          lambda *_: ("unknown", {}), lambda _: None)
        evaluate = load_script("03_evaluate.py").evaluate
        summary, classes, _, _ = evaluate([{"id": "a", "label": "neutral"}], [record])
        self.assertEqual(record["prediction"], INVALID)
        self.assertEqual(summary["n"], 1)
        self.assertEqual(summary["accuracy"], 0)
        self.assertEqual(classes[1]["incorrect"], 1)

    def test_resume_rejects_duplicate_and_foreign_ids_and_repairs_only_torn_tail(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "journal.jsonl"
            row = {"id": "a", "prediction": "positive"}
            path.write_text(json.dumps(row) + '\n{"id":', encoding="utf-8")
            records = load_journal(path, ["a", "b"], repair_tail=True)
            self.assertEqual(set(records), {"a"})
            self.assertTrue(path.read_bytes().endswith(b"\n"))
            with self.assertRaises(ValueError):
                load_journal(path, ["b"])
            path.write_text((json.dumps(row) + "\n") * 2, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_journal(path, ["a"])
            path.write_text('{bad}\n' + json.dumps(row) + '\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_journal(path, ["a"], repair_tail=True)

    def test_pilot_is_balanced_reproducible_and_validation_only(self):
        rows = [{"id": f"{c}_{i}", "text": "fixture", "label": c, "source_split": "validation"}
                for c in LABELS for i in range(8)]
        selected = select_pilot(rows, 3)
        self.assertEqual(selected, select_pilot(list(reversed(rows)), 3))
        self.assertEqual([sum(r["label"] == c for r in selected) for c in LABELS], [3, 3, 3])

    def test_training_disjointness_checks_text_and_id(self):
        check = load_script("04_bert.py").assert_disjoint
        with self.assertRaises(AssertionError):
            check([{"id": "a", "text": "same text"}], [{"id": "b", "text": "same   text"}])

    def test_cost_budget_includes_retries(self):
        config = {"model": "fixture", "max_attempts": 3, "max_output_tokens": 16}
        estimate = estimate_cost([{"text": "fixture"}], "prompt", config, 2, 8)
        self.assertEqual(estimate["output_token_budget"], 48)
        self.assertGreater(estimate["conservative_usd"], 0)


if __name__ == "__main__":
    unittest.main()
