"""Shared data contract. Label order is always negative, neutral, positive."""
import csv
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

LABELS = ("negative", "neutral", "positive")
INVALID = "__invalid__"


def clean_text(value):
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFC", html.unescape(value))
    return re.sub(r"\s+", " ", value).strip()


def fingerprint(text):
    return hashlib.sha256(clean_text(text).encode("utf-8")).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def unique_index(rows, key, context):
    index = {}
    for row in rows:
        value = row.get(key)
        if not value or value in index:
            raise ValueError(f"{context}: missing or duplicate {key}: {value!r}")
        index[value] = row
    return index
