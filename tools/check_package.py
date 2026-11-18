"""Verify every packaged file, then extract safely to a fresh QA directory."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

p = argparse.ArgumentParser()
p.add_argument("archive")
p.add_argument("--output", default="qa/delivery_unpack")
args = p.parse_args()
target = Path(args.output).resolve()
if target.exists() and any(target.iterdir()):
    raise ValueError("QA output directory is not empty")
with zipfile.ZipFile(args.archive) as archive:
    if archive.testzip() is not None:
        raise ValueError("CRC mismatch")
    manifest = json.loads(archive.read("sentiment_baslangic/deliverables/package_manifest.json"))
    for row in manifest["files"]:
        data = archive.read("sentiment_baslangic/" + row["path"])
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("Manifest mismatch: " + row["path"])
    for item in archive.infolist():
        path = (target / item.filename).resolve()
        if not path.is_relative_to(target):
            raise ValueError("Unsafe ZIP path")
    archive.extractall(target)
print(json.dumps({"all_packaged_hashes_verified": True, "files": len(manifest["files"]),
                  "extracted_to": str(target)}, indent=2))
