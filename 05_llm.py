"""Run a validation pilot, then identical zero-shot LLM on frozen tests."""
import argparse
import json
from pathlib import Path
import time
from urllib.parse import urlsplit

from common import INVALID, read_csv, write_csv, write_json
from experiment_utils import (ROOT, environment, evaluate_to_directory, model_inputs,
                              object_hash, sha256, utc_now, validate_rows)
from llm_support import (estimate_cost, load_journal, ollama_identity, run_pending, select_pilot)
from llm_support import compatible_signature, model_signature


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/llm_local.json")
    p.add_argument("--language", choices=("en", "tr"), required=True)
    p.add_argument("--stage", choices=("pilot", "test"), required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--data", default="data")
    p.add_argument("--pilot-per-class", type=int, default=10)
    p.add_argument("--pilot-root", default="runs", help="Must contain en_llm_pilot and tr_llm_pilot")
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--allow-runtime-version-change", action="store_true",
                   help="Permit a logged Ollama runtime update only; weights, template and prompt must match")
    p.add_argument("--estimate-only", action="store_true")
    p.add_argument("--input-usd-per-million", type=float)
    p.add_argument("--output-usd-per-million", type=float)
    p.add_argument("--approve-estimate-sha256", help="Explicit human approval of the displayed cost estimate hash")
    args = p.parse_args()
    if args.workers < 1 or args.pilot_per_class < 1:
        p.error("Workers and pilot-per-class must be positive")
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if config["provider"] not in ("ollama", "openai-compatible"):
        p.error("Provider must be ollama or openai-compatible")
    url = urlsplit(config["base_url"])
    if url.username or url.password or url.query:
        p.error("Do not place credentials in URLs; use an environment variable")
    if config["provider"] == "ollama" and url.hostname not in ("127.0.0.1", "localhost", "::1"):
        p.error("The free local runner requires a loopback Ollama endpoint")
    prompt = (ROOT / config["prompt_file"]).read_text(encoding="utf-8")
    experiment = {"config": config, "prompt": prompt}
    experiment_hash = object_hash(experiment)
    data = Path(args.data) / args.language
    input_path = data / ("validation.csv" if args.stage == "pilot" else "test.csv")
    rows = validate_rows(read_csv(input_path))
    if args.stage == "pilot":
        rows = select_pilot(rows, args.pilot_per_class, config["seed"])
    safe_rows = model_inputs(rows)
    run = Path(args.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    if config["provider"] == "openai-compatible":
        if args.input_usd_per_million is None or args.output_usd_per_million is None:
            p.error("API requires current input/output prices to show a cost estimate before any request")
        estimate = estimate_cost(safe_rows, prompt, config, args.input_usd_per_million, args.output_usd_per_million)
        estimate["experiment_hash"] = experiment_hash
        estimate["input_sha256"] = sha256(input_path)
        estimate_hash = object_hash(estimate)
        write_json(run / "cost_estimate.json", {**estimate, "approval_hash": estimate_hash})
        print(json.dumps({**estimate, "approval_hash": estimate_hash}, indent=2), flush=True)
        if args.estimate_only:
            return
        if args.approve_estimate_sha256 != estimate_hash:
            p.error("Paid API has not been approved. Review cost_estimate.json and obtain explicit approval first.")
    elif args.estimate_only:
        print("Local Ollama: no provider API fee; electricity/hardware costs not measured.")
        return
    identity = ollama_identity(config) if config["provider"] == "ollama" else {
        "model": config["model"], "revision": config.get("model_revision", "provider-managed; not immutable")}
    if args.stage == "test":
        for language in ("en", "tr"):
            pilot = Path(args.pilot_root) / f"{language}_llm_pilot" / "complete.json"
            if not pilot.exists():
                p.error(f"First complete the validation pilot for {language}")
            pilot_metadata = json.loads(pilot.read_text(encoding="utf-8"))
            same_identity = (model_signature(pilot_metadata["model_identity"]) == model_signature(identity)
                             if args.allow_runtime_version_change else pilot_metadata["model_identity"] == identity)
            if pilot_metadata["experiment_hash"] != experiment_hash or not same_identity:
                p.error("Pilot/test prompt, model, digest or settings differ")
    signature = {"experiment_hash": experiment_hash, "model_identity": identity, "language": args.language,
                 "stage": args.stage, "input_sha256": sha256(input_path),
                 "selected_ids_hash": object_hash([r["id"] for r in safe_rows])}
    config_path = run / "run_config.json"
    if config_path.exists():
        if not args.resume:
            p.error("Existing run: use --resume; original logs are preserved")
        prior_run = json.loads(config_path.read_text(encoding="utf-8"))
        if not compatible_signature(prior_run["signature"], signature, args.allow_runtime_version_change):
            p.error("Input/prompt/model/settings changed; cannot resume this run")
    else:
        write_json(config_path, {"signature": signature, "experiment": experiment,
                                "started_at_utc": utc_now(), "environment": environment(), "workers": args.workers})
    existing = load_journal(run / "records.jsonl", [r["id"] for r in safe_rows], repair_tail=args.resume)
    if (run / "complete.json").exists():
        if len(existing) != len(safe_rows):
            p.error("Complete marker contradicts journal coverage")
        print("Already complete; preserving predictions and results.")
        return
    start = time.perf_counter()
    runtime_config = {**config, "_runtime_version": identity.get("ollama_version")}
    records = run_pending(safe_rows, prompt, runtime_config, run / "records.jsonl", args.workers, existing)
    seconds = time.perf_counter() - start
    if len(records) != len(safe_rows):
        raise ValueError("Incomplete prediction coverage")
    predictions = [{"id": row["id"], "prediction": records[row["id"]]["prediction"],
                    "raw_response": records[row["id"]]["raw_response"], "seconds": records[row["id"]]["seconds"],
                    "input_tokens": records[row["id"]]["input_tokens"], "output_tokens": records[row["id"]]["output_tokens"]}
                   for row in safe_rows]
    output = run / "predictions.csv"
    write_csv(output, predictions, ("id", "prediction", "raw_response", "seconds", "input_tokens", "output_tokens"))
    # Pilot scoring uses the selected validation subset, never a shortened test.
    gold_path = input_path
    if args.stage == "pilot":
        gold_path = run / "pilot_gold.csv"
        write_csv(gold_path, rows, ("id", "text", "label", "source_split"))
    initial_identity = json.loads(config_path.read_text(encoding="utf-8"))["signature"]["model_identity"]
    from collections import Counter
    runtime_counts = Counter(r.get("runtime_version") or initial_identity.get("ollama_version", "provider-managed") for r in records.values())
    metadata = {**signature, "n": len(records), "completed_at_utc": utc_now(),
                "resumed_from_records": len(existing), "runtime_version_record_counts": dict(runtime_counts),
                "runtime_version_change_explicitly_allowed": args.allow_runtime_version_change,
                "current_session_wall_seconds": seconds, "workers": args.workers,
                "summed_request_seconds": sum(r["seconds"] for r in records.values()),
                "invalid_predictions": sum(r["prediction"] == INVALID for r in records.values()),
                "input_tokens": sum(r["input_tokens"] for r in records.values()),
                "output_tokens": sum(r["output_tokens"] for r in records.values()),
                "api_fee_usd": 0 if config["provider"] == "ollama" else None,
                "note": "Wall time with concurrent requests differs from sum of request latencies."}
    write_json(output.with_suffix(".metadata.json"), metadata)
    if not (run / "evaluation" / "metrics.json").exists():
        evaluate_to_directory(gold_path, output, run / "evaluation", "LLM_zero_shot", args.language, metadata)
    write_json(run / "complete.json", metadata)
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
