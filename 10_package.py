"""Package reproducibility records without caches or large model weights."""
import argparse
from pathlib import Path
import zipfile
from common import write_json
from experiment_utils import ROOT, sha256, utc_now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", default="../Duygu_Analizi_Teslim_Paketi.zip")
    args = p.parse_args()
    target = Path(args.output).resolve()
    if target.exists():
        p.error("Package exists; choose a new output name")
    files = []
    folders = {"data", "predictions", "results", "configs", "prompts", "tools", "provenance", "audit", "deliverables", "runs"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == target:
            continue
        relative = path.relative_to(ROOT)
        if "__pycache__" in relative.parts or any("smoke" in s for s in relative.parts):
            continue
        if path.suffix in (".pt", ".safetensors", ".log"):
            continue
        if len(relative.parts) == 1:
            if path.suffix not in (".py", ".md", ".txt") or path.name == "environment-ml-lock.txt":
                continue
        elif relative.parts[0] not in folders:
            continue
        if path.name == "package_manifest.json":
            continue
        files.append(path)
    manifest_path = ROOT / "deliverables/package_manifest.json"
    manifest = {"created_at_utc": utc_now(), "files": [{"path": str(p.relative_to(ROOT)).replace('\\', '/'),
                 "bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(files)],
                "excluded": ["runtime_cache", "qa", "smoke runs", "large *.pt and *.safetensors weights", "unrelated full environment snapshot", "server logs"],
                "model_artifacts_reference": "audit/model_artifacts.json",
                "note": "Fine-tuned weights remain in the original workspace. Reproduce them with pinned revisions and training commands."}
    write_json(manifest_path, manifest)
    files.append(manifest_path)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, "sentiment_baslangic/" + str(path.relative_to(ROOT)).replace('\\', '/'))
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC check failed")
    print({"archive": str(target), "files": len(files), "bytes": target.stat().st_size, "sha256": sha256(target)})


if __name__ == "__main__":
    main()
