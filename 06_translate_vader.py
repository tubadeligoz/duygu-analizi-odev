"""Optional separate TR -> EN translation + VADER experiment; never plain TR VADER."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import time

from common import LABELS, read_csv, write_csv, write_json
from experiment_utils import (configure_cache, environment, evaluate_to_directory, load_script,
                              model_inputs, object_hash, sha256, utc_now)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="data/tr/test.csv")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--model", default="Helsinki-NLP/opus-mt-tr-en")
    p.add_argument("--revision")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()
    configure_cache()
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from huggingface_hub import HfApi
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from llm_support import load_journal

    run = Path(args.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    config_path = run / "config.json"
    prior = json.loads(config_path.read_text()) if config_path.exists() else None
    if prior and not args.resume:
        p.error("Existing run: use --resume or a new directory")
    revision = prior["revision"] if prior else HfApi().model_info(args.model, revision=args.revision).sha
    config = {"model": args.model, "revision": revision, "input_sha256": sha256(args.input),
              "batch_size": args.batch_size, "device": args.device, "max_input_length": 512,
              "max_new_tokens": 512, "num_beams": 4, "do_sample": False}
    if prior and prior != config:
        p.error("Changed configuration cannot resume")
    write_json(config_path, config)
    if (run / "complete.json").exists():
        print("Translation experiment already complete; preserving it.")
        return
    safe_rows = model_inputs(read_csv(args.input))
    journal = run / "translations.jsonl"
    records = load_journal(journal, [r["id"] for r in safe_rows], repair_tail=args.resume)
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=revision)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model, revision=revision).to(args.device).eval()
    analyzer = SentimentIntensityAnalyzer()
    compound_label = load_script("02_vader.py").compound_label
    pending = [r for r in safe_rows if r["id"] not in records]
    import os
    with journal.open("a", encoding="utf-8", newline="\n") as stream:
        for offset in range(0, len(pending), args.batch_size):
            batch = pending[offset:offset + args.batch_size]
            started = time.perf_counter()
            inputs = tokenizer([r["text"] for r in batch], return_tensors="pt", padding=True,
                               truncation=True, max_length=512).to(args.device)
            with torch.inference_mode():
                generated = model.generate(**inputs, do_sample=False, num_beams=4, max_new_tokens=512)
            translations = tokenizer.batch_decode(generated, skip_special_tokens=True)
            seconds = time.perf_counter() - started
            for row, translated in zip(batch, translations):
                score = analyzer.polarity_scores(translated)["compound"]
                record = {"id": row["id"], "original_text": row["text"], "translation": translated,
                          "prediction": compound_label(score), "compound": score,
                          "batch_translation_seconds": seconds, "batch_size_actual": len(batch)}
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                records[row["id"]] = record
            print(f"Translated {len(records)}/{len(safe_rows)}", flush=True)
    ordered = [records[r["id"]] for r in safe_rows]
    write_csv(run / "translated_texts.csv", ordered,
              ("id", "original_text", "translation", "batch_translation_seconds", "batch_size_actual"))
    write_csv(run / "predictions.csv", ordered, ("id", "prediction", "compound"))
    metadata = {"method": "TR_EN_translation_plus_VADER", "config": config, "environment": environment(),
                "translation_seconds": sum(r["batch_translation_seconds"] / r["batch_size_actual"] for r in ordered),
                "vader_version": importlib.metadata.version("vaderSentiment"), "completed_at_utc": utc_now(),
                "note": "Translation can change sentiment. Input is truncated at 512 source tokens."}
    evaluate_to_directory(args.input, run / "predictions.csv", run / "evaluation", metadata["method"], "tr", metadata)
    write_json(run / "complete.json", metadata)


if __name__ == "__main__":
    main()
