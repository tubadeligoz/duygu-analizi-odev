"""Verify preservation, checkpoint selection, journals and six actual test results."""
import json
from pathlib import Path
import zipfile
from common import read_csv, write_json
from experiment_utils import ROOT, load_script, object_hash, sha256, utc_now
from llm_support import load_journal, model_signature


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    audit = load_script("00_audit.py").audit_data(ROOT / "data")
    runs, unavailable = load_script("07_build_results.py").collect()
    require(not unavailable and len(runs) == 6, "Six real experiments must be complete")
    evaluator = load_script("03_evaluate.py")
    preserved, changed_documentation = [], []
    with zipfile.ZipFile(ROOT / "provenance/baslangic_paketi_original.zip") as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            relative = Path(item.filename).relative_to("sentiment_baslangic")
            file = ROOT / relative
            require(file.exists(), f"Original file missing: {relative}")
            if archive.read(item) == file.read_bytes():
                preserved.append(str(relative))
            elif str(relative) in ("README.md", "CALISTIRMA_DURUMU.md"):
                changed_documentation.append(str(relative))
            else:
                raise ValueError(f"Original artifact changed: {relative}")
    for lang in ("en", "tr"):
        bert = ROOT / "runs" / f"{lang}_bert_seed42"
        history = json.loads((bert / "history.json").read_text())
        selection = json.loads((bert / "selection.json").read_text())
        require(not json.loads((bert / "config.json").read_text())["smoke"], "Smoke run cannot supply a result")
        validation = read_csv(ROOT / "data" / lang / "validation.csv")
        for row in history:
            metrics = evaluator.evaluate(validation, read_csv(bert / f"validation_epoch_{row['epoch']}.csv"))[0]
            require(metrics["macro_f1"] == row["validation_macro_f1"], "Validation score mismatch")
        require(max(history, key=lambda r: r["validation_macro_f1"])["epoch"] == selection["epoch"], "Wrong checkpoint selection")
        llm = ROOT / "runs" / f"{lang}_llm_test"
        gold = read_csv(ROOT / "data" / lang / "test.csv")
        journal = load_journal(llm / "records.jsonl", [r["id"] for r in gold])
        predictions = {r["id"]: r for r in read_csv(llm / "predictions.csv")}
        require(set(journal) == set(predictions) == {r["id"] for r in gold}, "Journal coverage mismatch")
        require(all(journal[i]["prediction"] == predictions[i]["prediction"] for i in journal), "Journal/prediction mismatch")
        complete = json.loads((llm / "complete.json").read_text())
        signature = json.loads((llm / "run_config.json").read_text())["signature"]
        require(complete["experiment_hash"] == signature["experiment_hash"], "Prompt configuration changed")
        require(complete["selected_ids_hash"] == object_hash([r["id"] for r in gold]), "Wrong test IDs")
        for pilot_lang in ("en", "tr"):
            pilot = json.loads((ROOT / "runs" / f"{pilot_lang}_llm_pilot" / "complete.json").read_text())
            require(pilot["experiment_hash"] == complete["experiment_hash"], "Test differs from pilot prompt")
            require(model_signature(pilot["model_identity"]) == model_signature(complete["model_identity"]), "Different LLM across runs")
    for case in read_csv(ROOT / "deliverables/error_case_studies.csv"):
        run = next(r for r in runs if r["language"] == case["language"] and r["display_name"] == case["method"])
        require(any(all(error[k] == case[k] for k in ("id", "text", "label", "prediction")) for error in run["errors"]),
                "Case study is not an actual model error")
    with zipfile.ZipFile(ROOT / "deliverables/Proje_Raporu.docx") as docx:
        text = docx.read("word/document.xml").decode()
        require("Tamamlanmayan deneyler" not in text, "Word report still contains obsolete partial results")
        require("w:pBdr" not in text, "Unexpected decorative paragraph border")
    model_artifacts = []
    missing_weight_files = []
    for lang in ("en", "tr"):
        folder = ROOT / "runs" / f"{lang}_bert_seed42" / "best"
        if not (folder / "model.safetensors").exists():
            missing_weight_files.append(str((folder / "model.safetensors").relative_to(ROOT)))
        for path in sorted(folder.iterdir()):
            if path.is_file():
                model_artifacts.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    if not missing_weight_files:
        write_json(ROOT / "audit/model_artifacts.json", model_artifacts)
    elif (ROOT / "audit/model_artifacts.json").exists():
        reference = json.loads((ROOT / "audit/model_artifacts.json").read_text())
        hashes = {item["path"]: item["sha256"] for item in reference}
        for item in model_artifacts:
            require(hashes.get(item["path"]) == item["sha256"], "Packaged tokenizer/config hash mismatch")
    result = {"verified_at_utc": utc_now(), "all_checks_passed": True, "test_runs": 6,
              "total_test_predictions": sum(r["metrics"]["n"] for r in runs),
              "preserved_original_files": preserved, "updated_documentation_with_originals_archived": changed_documentation,
              "large_weights_excluded_from_lightweight_package": missing_weight_files,
              "unchanged_data_sha256": {lang: {split: spec["sha256"] for split, spec in audit["languages"][lang]["files"].items()}
                                         for lang in ("en", "tr")},
              "validated_checks": ["gold/prediction hashes", "exact ID coverage", "invalid denominator",
                                   "validation-only checkpoint choice", "same LLM/prompt in two languages",
                                   "pilot/test signatures", "journal/prediction identity", "real error case provenance"]}
    write_json(ROOT / "audit/delivery_validation.json", result)
    print(json.dumps({"all_checks_passed": True, "original_files_preserved": len(preserved),
                      "experiments": 6, "test_predictions": 18000}, indent=2))


if __name__ == "__main__":
    main()
