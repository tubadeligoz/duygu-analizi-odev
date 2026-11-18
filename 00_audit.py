"""Independently verify the frozen data and old results without rewriting them."""
import argparse
from collections import Counter
import json
from pathlib import Path
from itertools import combinations

from common import LABELS, clean_text, fingerprint, read_csv, unique_index, write_json
from experiment_utils import ROOT, environment, load_script, sha256, utc_now, validate_rows


def audit_data(data_root):
    data_root = Path(data_root)
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    result = {"checked_at_utc": utc_now(), "manifest_sha256": sha256(data_root / "manifest.json"),
              "languages": {}, "all_checks_passed": True}
    across_languages = {}
    for language in ("en", "tr"):
        spec = manifest["datasets"][language]
        assert all(spec["raw_class_counts"][c] >= 1000 for c in LABELS), "Insufficient source data"
        assert all(spec["clean_class_counts"][c] >= 1000 for c in LABELS), "Insufficient clean data"
        assert len(spec["revision"]) == 40, "Unpinned dataset revision"
        partitions, text_sets = {}, {}
        details = {"source": spec["repo"], "revision": spec["revision"],
                   "source_class_counts": spec["raw_class_counts"],
                   "clean_class_counts": spec["clean_class_counts"], "files": {}, "overlaps": {}}
        all_labels = {}
        for split in ("train", "validation", "test"):
            path = data_root / language / f"{split}.csv"
            rows = validate_rows(read_csv(path))
            unique_index(rows, "id", f"{language}/{split}")
            counts = {c: sum(r["label"] == c for r in rows) for c in LABELS}
            assert counts == dict.fromkeys(LABELS, manifest["targets_per_class"][split]), "Wrong balance"
            expected = spec["files"][split]
            assert counts == expected["class_counts"] and len(rows) == expected["rows"]
            assert sha256(path) == expected["sha256"], f"Changed frozen file {path}"
            hashes = [fingerprint(row["text"]) for row in rows]
            assert len(hashes) == len(set(hashes)), "Duplicate normalized text"
            for row, text_hash in zip(rows, hashes):
                assert row["id"] == language + "_" + text_hash, "Text/ID mismatch"
                if language == "en":
                    assert row["source_split"] == split, "Official English split changed"
                if text_hash in all_labels:
                    assert all_labels[text_hash] == row["label"], "Conflicting gold label"
                all_labels[text_hash] = row["label"]
            partitions[split] = {r["id"] for r in rows}
            text_sets[split] = set(hashes)
            details["files"][split] = {"rows": len(rows), "class_counts": counts, "sha256": sha256(path),
                                        "second_html_decode_would_change": sum(r["text"] != clean_text(r["text"]) for r in rows)}
        for a, b in combinations(partitions, 2):
            overlap = len(partitions[a] & partitions[b]) + len(text_sets[a] & text_sets[b])
            assert overlap == 0, "Cross-split leakage"
            details["overlaps"][a + "/" + b] = 0
        conflicts = read_csv(data_root / language / "excluded_label_conflicts.csv")
        excluded_ids = {r["id"] for r in conflicts}
        assert not excluded_ids & set.union(*partitions.values()), "Excluded conflicts returned"
        details["excluded_conflict_rows"] = len(conflicts)
        assert len(conflicts) == spec["audit"]["conflicting_rows_removed"]
        across_languages[language] = set.union(*text_sets.values())
        result["languages"][language] = details
    result["cross_language_exact_text_overlap"] = len(across_languages["en"] & across_languages["tr"])
    result["limits"] = ["Near duplicates and user/product leakage cannot be ruled out without identifiers.",
                        "Raw source counts are inherited from the pinned manifest; raw corpus was not redownloaded.",
                        "Eight English training rows contain nested HTML entities. Frozen bytes and IDs are preserved; normalization is not reapplied before inference."]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data")
    parser.add_argument("--output", default="audit")
    args = parser.parse_args()
    out = Path(args.output)
    audit = audit_data(args.data)
    evaluator = load_script("03_evaluate.py")
    audit["preserved_results_verified"] = []
    for language, stem in (("en", "en_vader"), ("tr", "tr_vader_diagnostic")):
        gold = Path(args.data) / language / "test.csv"
        predictions = ROOT / "predictions" / f"{stem}.csv"
        original = json.loads((ROOT / "results" / stem / "metrics.json").read_text())
        summary, _, _, _ = evaluator.evaluate(read_csv(gold), read_csv(predictions))
        for key in ("n", "correct", "incorrect", "accuracy", "macro_f1", "invalid_predictions"):
            assert summary[key] == original[key], f"Original metric mismatch {stem}/{key}"
        assert sha256(predictions) == original["predictions_sha256"]
        assert sha256(gold) == original["gold_sha256"]
        audit["preserved_results_verified"].append(stem)
    write_json(out / "data_integrity.json", audit)
    write_json(out / "environment.json", environment())
    print(json.dumps({"all_checks_passed": True, "rows_verified": 30000,
                      "preserved_results": audit["preserved_results_verified"]}, indent=2))


if __name__ == "__main__":
    main()
