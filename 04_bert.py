"""Fine-tune pinned base BERT; choose epochs only with validation Macro-F1."""
import argparse
from contextlib import nullcontext
import json
import math
from pathlib import Path
import random
import time

from common import LABELS, read_csv, write_csv, write_json
from experiment_utils import (ROOT, configure_cache, environment, evaluate_to_directory,
                              load_script, model_inputs, sha256, utc_now, validate_rows)

MODELS = {"en": "google-bert/bert-base-uncased", "tr": "dbmdz/bert-base-turkish-cased"}


def assert_disjoint(train, validation):
    from common import fingerprint
    assert not {r["id"] for r in train} & {r["id"] for r in validation}, "ID leakage"
    assert not {fingerprint(r["text"]) for r in train} & {fingerprint(r["text"]) for r in validation}, "Text leakage"


def main():
    run_started = time.perf_counter()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", choices=("en", "tr"), required=True)
    p.add_argument("--data", default="data")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--revision", help="Hub commit; resolved and recorded if omitted")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--gradient-accumulation", type=int, default=1)
    p.add_argument("--max-length", type=int, default=256)
    p.add_argument("--learning-rate", type=float, default=2e-5)
    p.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--predict-only", action="store_true")
    p.add_argument("--smoke", action="store_true", help="One train batch and validation; never a project result")
    args = p.parse_args()
    if not (1 <= args.epochs <= 3) or min(args.batch_size, args.gradient_accumulation, args.max_length) < 1:
        p.error("Use 1..3 epochs and positive batch/accumulation/length")
    configure_cache()
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, DataCollatorWithPadding
    from huggingface_hub import HfApi

    torch.set_num_threads(args.threads)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    run = Path(args.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    config_path = run / "config.json"
    if config_path.exists() and not (args.resume or args.predict_only):
        p.error("Existing run requires --resume or --predict-only")
    if args.predict_only and not (run / "training_complete.json").exists():
        p.error("No completed fine-tuning; refusing random-head predictions")
    model_name = MODELS[args.language]
    prior = json.loads(config_path.read_text()) if config_path.exists() else None
    revision = prior["model_revision"] if prior else HfApi().model_info(model_name, revision=args.revision).sha
    data = Path(args.data) / args.language
    config = {"language": args.language, "model": model_name, "model_revision": revision,
              "tokenizer_revision": revision, "seed": args.seed, "epochs": args.epochs,
              "batch_size": args.batch_size, "gradient_accumulation": args.gradient_accumulation,
              "effective_batch_size": args.batch_size * args.gradient_accumulation,
              "learning_rate": args.learning_rate, "weight_decay": 0.01,
              "max_length": args.max_length, "scheduler": "linear_no_warmup", "clip_grad_norm": 1.0,
              "selection": "validation_macro_f1; earliest epoch breaks ties",
              "precision": "fp16_autocast" if device == "cuda" else "float32",
              "train_sha256": sha256(data / "train.csv"),
              "validation_sha256": sha256(data / "validation.csv"), "smoke": args.smoke}
    if prior and prior != config:
        p.error("Run configuration differs; use a new directory")
    write_json(config_path, config)
    write_json(run / "environment.json", environment())
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=False)
    collator = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8 if device == "cuda" else None)
    evaluator = load_script("03_evaluate.py")

    def encode(rows, include_labels):
        safe_rows = model_inputs(rows)
        tokens = tokenizer([r["text"] for r in safe_rows], truncation=True, max_length=args.max_length)
        examples = [{key: values[i] for key, values in tokens.items()} for i in range(len(rows))]
        if include_labels:
            for example, row in zip(examples, rows):
                example["labels"] = LABELS.index(row["label"])
        lengths = tokenizer([r["text"] for r in safe_rows], truncation=False, return_length=True)["length"]
        return examples, {"n": len(rows), "truncated": sum(n > args.max_length for n in lengths),
                          "truncation_rate": sum(n > args.max_length for n in lengths) / len(rows)}

    def infer(rows, output):
        examples, truncation = encode(rows, False)
        loader = DataLoader(examples, batch_size=args.batch_size, shuffle=False, collate_fn=collator)
        model.eval()
        predictions = []
        start = time.perf_counter()
        with torch.inference_mode():
            for batch in loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                with torch.autocast("cuda", dtype=torch.float16) if device == "cuda" else nullcontext():
                    ids = model(**batch).logits.argmax(-1).cpu().tolist()
                predictions.extend(LABELS[i] for i in ids)
        seconds = time.perf_counter() - start
        write_csv(output, [{"id": r["id"], "prediction": pred} for r, pred in zip(rows, predictions)],
                  ("id", "prediction"))
        return seconds, truncation

    training_seconds = 0.0
    if not args.predict_only:
        train = validate_rows(read_csv(data / "train.csv"))
        validation = validate_rows(read_csv(data / "validation.csv"))
        assert_disjoint(train, validation)
        if args.smoke:
            train, validation = train[:args.batch_size], validation[:12]
        train_examples, train_truncation = encode(train, True)
        loader = DataLoader(train_examples, batch_size=args.batch_size, shuffle=True, collate_fn=collator,
                            generator=torch.Generator().manual_seed(args.seed), pin_memory=device == "cuda")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, revision=revision, num_labels=3, id2label=dict(enumerate(LABELS)),
            label2id={c: i for i, c in enumerate(LABELS)}, use_safetensors=True, trust_remote_code=False).to(device)
        decay = [param for name, param in model.named_parameters() if param.requires_grad and not any(x in name for x in ("bias", "LayerNorm.weight"))]
        no_decay = [param for name, param in model.named_parameters() if param.requires_grad and any(x in name for x in ("bias", "LayerNorm.weight"))]
        optimizer = torch.optim.AdamW([{"params": decay, "weight_decay": 0.01}, {"params": no_decay, "weight_decay": 0.0}], lr=args.learning_rate)
        total_steps = math.ceil(len(loader) / args.gradient_accumulation) * (1 if args.smoke else args.epochs)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: max(0.0, 1.0 - step / total_steps))
        scaler = torch.amp.GradScaler("cuda", enabled=device == "cuda")
        best, start_epoch, history, val_truncation = -1.0, 0, [], None
        if args.resume and (run / "resume.pt").exists():
            state = torch.load(run / "resume.pt", map_location=device, weights_only=False)
            model.load_state_dict(state["model"])
            optimizer.load_state_dict(state["optimizer"])
            scheduler.load_state_dict(state["scheduler"])
            scaler.load_state_dict(state["scaler"])
            start_epoch, best, history = state["epoch"], state["best"], state["history"]
            training_seconds = state["training_seconds"]
            random.setstate(state["random"])
            np.random.set_state(state["numpy"])
            torch.set_rng_state(state["torch_rng"].cpu())
            loader.generator.set_state(state["loader_rng"].cpu())
            if device == "cuda":
                torch.cuda.set_rng_state_all([x.cpu() for x in state["cuda_rng"]])
        for epoch in range(start_epoch, 1 if args.smoke else args.epochs):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            started = time.perf_counter()
            loss_sum = 0.0
            for step, batch in enumerate(loader):
                batch = {k: v.to(device) for k, v in batch.items()}
                group_size = min(args.gradient_accumulation, len(loader) - (step // args.gradient_accumulation) * args.gradient_accumulation)
                with torch.autocast("cuda", dtype=torch.float16) if device == "cuda" else nullcontext():
                    loss = model(**batch).loss
                loss_sum += loss.item()
                scaler.scale(loss / group_size).backward()
                if (step + 1) % args.gradient_accumulation == 0 or step + 1 == len(loader):
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    old_scale = scaler.get_scale()
                    scaler.step(optimizer)
                    scaler.update()
                    if scaler.get_scale() >= old_scale:
                        scheduler.step()
                    optimizer.zero_grad(set_to_none=True)
                if (step + 1) % 100 == 0 or step + 1 == len(loader):
                    print(f"{args.language} epoch={epoch+1} step={step+1}/{len(loader)} loss={loss_sum/(step+1):.4f}", flush=True)
            training_seconds += time.perf_counter() - started
            validation_path = run / f"validation_epoch_{epoch+1}.csv"
            seconds, val_truncation = infer(validation, validation_path)
            metrics, _, _, _ = evaluator.evaluate(validation, read_csv(validation_path))
            history.append({"epoch": epoch + 1, "train_loss": loss_sum / len(loader),
                            "validation_macro_f1": metrics["macro_f1"], "validation_accuracy": metrics["accuracy"],
                            "validation_seconds": seconds})
            if metrics["macro_f1"] > best:
                best = metrics["macro_f1"]
                model.save_pretrained(run / "best", safe_serialization=True)
                tokenizer.save_pretrained(run / "best")
                write_json(run / "selection.json", {"epoch": epoch + 1, "validation_macro_f1": best})
            write_json(run / "history.json", history)
            state = {"model": model.state_dict(), "optimizer": optimizer.state_dict(),
                     "scheduler": scheduler.state_dict(), "scaler": scaler.state_dict(),
                     "epoch": epoch + 1, "best": best, "history": history,
                     "training_seconds": training_seconds, "random": random.getstate(),
                     "numpy": np.random.get_state(), "torch_rng": torch.get_rng_state(),
                     "loader_rng": loader.generator.get_state(),
                     "cuda_rng": torch.cuda.get_rng_state_all() if device == "cuda" else []}
            temporary = run / "resume.tmp.pt"
            torch.save(state, temporary)
            temporary.replace(run / "resume.pt")
            print(json.dumps(history[-1]), flush=True)
        write_json(run / ("smoke_complete.json" if args.smoke else "training_complete.json"),
                   {"completed_at_utc": utc_now(), "training_seconds": training_seconds,
                    "train_truncation": train_truncation, "validation_truncation": val_truncation if history else None,
                    "peak_gpu_memory_bytes": torch.cuda.max_memory_allocated() if device == "cuda" else None})
        if args.smoke:
            print("SMOKE ONLY; no test predictions or project scores generated.")
            return
        del optimizer, scheduler, scaler, state, model
        if device == "cuda":
            torch.cuda.empty_cache()
    output = run / "test_predictions.csv"
    if output.exists():
        p.error("Test predictions already exist; preserving them")
    model = AutoModelForSequenceClassification.from_pretrained(run / "best", local_files_only=True).to(device)
    # Test is first read after validation-only checkpoint selection is complete.
    test = model_inputs(read_csv(data / "test.csv"))
    seconds, test_truncation = infer(test, output)
    metadata = {"method": "BERT_finetuned", "language": args.language, "config": config,
                "total_run_seconds": time.perf_counter() - run_started,
                "selection": json.loads((run / "selection.json").read_text()),
                "inference_seconds": seconds, "training": json.loads((run / "training_complete.json").read_text()),
                "test_truncation": test_truncation, "input_sha256": sha256(data / "test.csv"),
                "created_at_utc": utc_now(), "environment": environment()}
    write_json(output.with_suffix(".metadata.json"), metadata)
    summary = evaluate_to_directory(data / "test.csv", output, run / "evaluation", "BERT_finetuned", args.language, metadata)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
