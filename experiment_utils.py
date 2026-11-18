"""Reproducibility helpers; uses the original evaluator without changing it."""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

from common import LABELS, read_csv, unique_index, write_csv, write_json

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_script(filename):
    spec = importlib.util.spec_from_file_location("project_" + filename.replace(".", "_"), ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment():
    names = ("torch", "transformers", "datasets", "huggingface-hub", "numpy",
             "scikit-learn", "vaderSentiment", "matplotlib", "safetensors")
    packages = {}
    for name in names:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    try:
        gpu = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            text=True, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        gpu = None
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "cpu_count": os.cpu_count(), "gpu": gpu, "packages": packages}


def validate_rows(rows, labelled=True):
    unique_index(rows, "id", "Input")
    if not rows or any(not row.get("text", "").strip() for row in rows):
        raise ValueError("Empty data or text")
    if labelled and any(row.get("label") not in LABELS for row in rows):
        raise ValueError("Invalid gold label")
    return rows


def model_inputs(rows):
    """Only text and opaque IDs leave the data layer; labels never enter inference."""
    validate_rows(rows, labelled=False)
    return [{"id": row["id"], "text": row["text"]} for row in rows]


def evaluate_to_directory(gold_path, predictions_path, output, method, language, metadata=None):
    out = Path(output)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"Refusing to overwrite existing results: {out}")
    evaluator = load_script("03_evaluate.py")
    summary, classes, matrix, errors = evaluator.evaluate(read_csv(gold_path), read_csv(predictions_path))
    summary.update({"method": method, "language": language, "gold_sha256": sha256(gold_path),
                    "predictions_sha256": sha256(predictions_path), "conditions": metadata or {}})
    write_json(out / "metrics.json", summary)
    write_csv(out / "class_errors.csv", classes, list(classes[0]))
    from common import INVALID
    write_csv(out / "confusion_matrix.csv", [{"true_class": c, **dict(matrix[c])} for c in LABELS],
              ("true_class", *LABELS, INVALID))
    write_csv(out / "misclassified.csv", errors, ("id", "text", "label", "prediction"))
    return summary


def configure_cache():
    os.environ.setdefault("HF_HOME", str(ROOT / "runtime_cache" / "huggingface"))
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
