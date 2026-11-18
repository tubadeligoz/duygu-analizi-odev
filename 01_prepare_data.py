"""Download, audit and freeze balanced splits without touching sentiment signals."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import importlib.metadata
from pathlib import Path
import platform
import random

from common import LABELS, clean_text, fingerprint, write_csv, write_json

SOURCES = {
    "en": {"repo": "cardiffnlp/tweet_eval", "config": "sentiment"},
    "tr": {"repo": "maydogan/Turkish_SentimentAnalysis_TRSAv1", "config": None},
}


def counts(rows):
    counter = Counter(row["label"] for row in rows)
    return {label: counter[label] for label in LABELS}


def canonical_rows(dataset, language):
    result = []
    for split, partition in dataset.items():
        for item in partition:
            if language == "en":
                raw_label = item["label"]
                if raw_label not in (0, 1, 2):
                    raise ValueError(f"Unexpected TweetEval label: {raw_label!r}")
                label, text = LABELS[raw_label], item["text"]
            else:
                label = str(item["score"]).strip().lower()
                text = item["review"]
            if label not in LABELS:
                raise ValueError(f"Unknown label: {label!r}; check the source schema")
            text = clean_text(text)
            result.append({"id": language + "_" + fingerprint(text),
                           "text": text, "label": label, "source_split": split})
    return result


def deduplicate(rows):
    """Remove contradictory exact duplicates; preserve official test priority."""
    groups = defaultdict(list)
    empty = 0
    for row in rows:
        if not row["text"]:
            empty += 1
        else:
            groups[row["id"]].append(row)
    clean = []
    conflicts = []
    removed_duplicates = 0
    priority = {"test": 0, "validation": 1, "train": 2}
    for group in groups.values():
        if len({row["label"] for row in group}) > 1:
            conflicts.extend(group)
            continue
        representative = min(group, key=lambda row: priority.get(row["source_split"], 3))
        clean.append(representative)
        removed_duplicates += len(group) - 1
    return clean, conflicts, {"empty_rows": empty,
                              "duplicate_rows_removed": removed_duplicates,
                              "conflicting_rows_removed": len(conflicts)}


def select_splits(rows, language, targets, seed):
    rng = random.Random(seed)
    output = {split: [] for split in targets}
    for label in LABELS:
        if language == "en":
            for split, target in targets.items():
                pool = sorted((row for row in rows if row["label"] == label
                               and row["source_split"] == split), key=lambda row: row["id"])
                if len(pool) < target:
                    raise ValueError(f"{language}/{split}/{label}: {len(pool)} available, {target} required")
                output[split].extend(rng.sample(pool, target))
        else:
            pool = sorted((row for row in rows if row["label"] == label), key=lambda row: row["id"])
            needed = sum(targets.values())
            if len(pool) < needed:
                raise ValueError(f"{language}/{label}: {len(pool)} available, {needed} required")
            rng.shuffle(pool)
            offset = 0
            for split, target in targets.items():
                output[split].extend(pool[offset:offset + target])
                offset += target
    for partition in output.values():
        rng.shuffle(partition)
    identifiers = [row["id"] for partition in output.values() for row in partition]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate text leaked across selected splits")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-per-class", type=int, default=3800)
    parser.add_argument("--validation-per-class", type=int, default=200)
    parser.add_argument("--test-per-class", type=int, default=1000)
    parser.add_argument("--en-revision", help="Optional pinned source commit")
    parser.add_argument("--tr-revision", help="Optional pinned source commit")
    args = parser.parse_args()
    targets = {"train": args.train_per_class, "validation": args.validation_per_class,
               "test": args.test_per_class}
    if min(targets.values()) < 1 or args.test_per_class < 1000:
        parser.error("All targets must be positive; test-per-class must be at least 1000")
    out = Path(args.output)
    if out.exists() and any(out.iterdir()):
        parser.error("Output directory must be empty; use a new directory to preserve frozen splits")

    from datasets import load_dataset
    from huggingface_hub import HfApi

    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "seed": args.seed,
                "targets_per_class": targets, "labels": LABELS,
                "python": platform.python_version(),
                "packages": {name: importlib.metadata.version(name)
                             for name in ("datasets", "huggingface-hub")}, "datasets": {}}
    for language, spec in SOURCES.items():
        requested_revision = getattr(args, language + "_revision")
        revision = HfApi().dataset_info(spec["repo"], revision=requested_revision).sha
        dataset = load_dataset(spec["repo"], name=spec["config"], revision=revision)
        raw = canonical_rows(dataset, language)
        clean, conflicts, audit = deduplicate(raw)
        if any(n < 1000 for n in counts(clean).values()):
            raise ValueError(f"{language}: fewer than 1000 clean texts in at least one class")
        selected = select_splits(clean, language, targets, args.seed)
        files = {}
        for split, partition in selected.items():
            path = out / language / f"{split}.csv"
            write_csv(path, partition, ("id", "text", "label", "source_split"))
            import hashlib
            files[split] = {"rows": len(partition), "class_counts": counts(partition),
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        write_csv(out / language / "excluded_label_conflicts.csv", conflicts,
                  ("id", "text", "label", "source_split"))
        manifest["datasets"][language] = {
            **spec, "revision": revision, "raw_class_counts": counts(raw),
            "clean_class_counts": counts(clean), "audit": audit, "files": files,
            "original_splits_preserved": language == "en",
        }
        print(language, {split: item["class_counts"] for split, item in files.items()})
    write_json(out / "manifest.json", manifest)
    print("Frozen data and source revisions saved to", out.resolve())


if __name__ == "__main__":
    main()
