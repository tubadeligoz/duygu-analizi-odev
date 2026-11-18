"""Strict outputs, label-free requests, durable resume and cost estimation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import random
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from common import INVALID, LABELS, unique_index
from experiment_utils import object_hash, utc_now


def model_signature(identity):
    """Runtime patch version is separate from immutable weights and chat template."""
    return {k: v for k, v in identity.items() if k != "ollama_version"}


def compatible_signature(previous, current, allow_runtime_change=False):
    if not allow_runtime_change:
        return previous == current
    a, b = dict(previous), dict(current)
    a["model_identity"] = model_signature(a["model_identity"])
    b["model_identity"] = model_signature(b["model_identity"])
    return a == b


def parse_label(raw):
    return raw.strip() if isinstance(raw, str) and raw.strip() in LABELS else INVALID


def messages_for(text, prompt):
    return [{"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps({"review": text}, ensure_ascii=False)}]


def select_pilot(rows, per_class, seed=42):
    rng = random.Random(seed)
    selected = []
    for label in LABELS:
        candidates = sorted((r for r in rows if r["label"] == label), key=lambda r: r["id"])
        if len(candidates) < per_class:
            raise ValueError("Insufficient validation rows")
        selected.extend(rng.sample(candidates, per_class))
    rng.shuffle(selected)
    return selected


def http_json(url, body=None, timeout=90, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    request = Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with urlopen(request, timeout=timeout) as stream:
        return json.load(stream)


def ollama_identity(config):
    tags = http_json(config["base_url"].rstrip("/") + "/api/tags", timeout=15)["models"]
    matches = [r for r in tags if r["name"] == config["model"] or r.get("model") == config["model"]]
    if len(matches) != 1:
        raise ValueError("Configured model is not installed, or its tag is ambiguous")
    model = matches[0]
    show = http_json(config["base_url"].rstrip("/") + "/api/show", {"model": config["model"]}, timeout=15)
    version = http_json(config["base_url"].rstrip("/") + "/api/version", timeout=15)
    return {"model": model["name"], "digest": model["digest"], "size": model["size"],
            "details": model.get("details"), "ollama_version": version.get("version"),
            "template_sha256": object_hash(show.get("template", "")),
            "parameters": show.get("parameters"), "capabilities": show.get("capabilities")}


def request_once(text, prompt, config):
    messages = messages_for(text, prompt)
    if config["provider"] == "ollama":
        body = {"model": config["model"], "messages": messages, "stream": False,
                "keep_alive": "30m", "options": {"temperature": config["temperature"],
                "seed": config["seed"], "num_ctx": config["num_ctx"],
                "num_predict": config["max_output_tokens"]}}
        result = http_json(config["base_url"].rstrip("/") + "/api/chat", body, config["timeout_seconds"])
        raw = result.get("message", {}).get("content", "")
        usage = {"input_tokens": result.get("prompt_eval_count"), "output_tokens": result.get("eval_count"),
                 "total_duration_ns": result.get("total_duration"), "load_duration_ns": result.get("load_duration"),
                 "done_reason": result.get("done_reason")}
    else:
        key = os.environ.get(config.get("api_key_env", "OPENAI_API_KEY"))
        if not key:
            raise ValueError("Missing API key environment variable")
        body = {"model": config["model"], "messages": messages,
                "temperature": config["temperature"], "max_tokens": config["max_output_tokens"]}
        result = http_json(config["base_url"].rstrip("/") + "/chat/completions", body,
                           config["timeout_seconds"], key)
        raw = result["choices"][0]["message"].get("content", "")
        original = result.get("usage", {})
        usage = {"input_tokens": original.get("prompt_tokens"), "output_tokens": original.get("completion_tokens"),
                 "response_model": result.get("model"), "system_fingerprint": result.get("system_fingerprint")}
    return raw, usage


def classify(row, prompt, config, requester=request_once, sleeper=time.sleep):
    started = time.perf_counter()
    attempts, prediction = [], INVALID
    for attempt in range(config["max_attempts"]):
        attempt_start = time.perf_counter()
        raw, usage, error = "", {}, None
        try:
            raw, usage = requester(row["text"], prompt, config)
            prediction = parse_label(raw)
            if prediction == INVALID:
                error = "invalid_label"
        except Exception as exc:
            # Never record headers, secret values, URL credentials or arbitrary server error bodies.
            error = type(exc).__name__ + (f":HTTP{exc.code}" if isinstance(exc, HTTPError) else "")
        attempts.append({"attempt": attempt + 1, "raw_response": raw, "usage": usage,
                         "seconds": time.perf_counter() - attempt_start, "error": error})
        if prediction != INVALID:
            break
        if attempt + 1 < config["max_attempts"]:
            sleeper(min(2 ** attempt, 8))
    return {"id": row["id"], "prediction": prediction, "raw_response": attempts[-1]["raw_response"],
            "seconds": time.perf_counter() - started, "attempts": attempts, "completed_at_utc": utc_now(),
            "runtime_version": config.get("_runtime_version"),
            "input_tokens": sum(a["usage"].get("input_tokens") or 0 for a in attempts),
            "output_tokens": sum(a["usage"].get("output_tokens") or 0 for a in attempts)}


def load_journal(path, valid_ids, repair_tail=False):
    path = Path(path)
    if not path.exists():
        return {}
    data = path.read_bytes()
    lines = data.splitlines(keepends=True)
    rows, offset = [], 0
    for i, line in enumerate(lines):
        try:
            row = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            if repair_tail and i == len(lines) - 1 and not line.endswith(b"\n"):
                with path.open("r+b") as stream:
                    stream.truncate(offset)
                break
            raise ValueError("Corrupt journal; only a torn final line may be repaired")
        if not line.endswith(b"\n"):
            # A complete JSON object without its commit newline is an uncommitted tail.
            if repair_tail and i == len(lines) - 1:
                with path.open("r+b") as stream:
                    stream.truncate(offset)
                break
            raise ValueError("Uncommitted journal tail; use --resume to repair")
        if row.get("prediction") not in (*LABELS, INVALID):
            raise ValueError("Unknown journal label")
        rows.append(row)
        offset += len(line)
    index = unique_index(rows, "id", "Journal")
    if set(index) - set(valid_ids):
        raise ValueError("Journal contains IDs from a different input")
    return index


def run_pending(rows, prompt, config, journal, workers=1, existing=None):
    done = dict(existing or {})
    pending = [r for r in rows if r["id"] not in done]
    path = Path(journal)
    path.parent.mkdir(parents=True, exist_ok=True)
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            jobs = {pool.submit(classify, row, prompt, config): row["id"] for row in pending}
            for future in as_completed(jobs):
                result = future.result()
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                done[result["id"]] = result
                if len(done) % 100 == 0 or len(done) == len(rows):
                    print(f"LLM completed={len(done)}/{len(rows)} invalid={sum(r['prediction']==INVALID for r in done.values())}", flush=True)
    finally:
        # On interruption, cancel queued work instead of waiting for the entire corpus.
        # In-flight requests remain bounded by their configured network timeout.
        pool.shutdown(wait=False, cancel_futures=True)
    return done


def estimate_cost(rows, prompt, config, input_price, output_price):
    # Transparent character bound, not an exact tokenizer count. Max attempts included.
    chars = sum(len(json.dumps(messages_for(r["text"], prompt), ensure_ascii=False)) for r in rows)
    byte_count = sum(len(json.dumps(messages_for(r["text"], prompt), ensure_ascii=False).encode("utf-8")) for r in rows)
    n = len(rows)
    tries = config["max_attempts"]
    upper_input = (byte_count + 64 * n) * tries
    upper_output = n * config["max_output_tokens"] * tries
    return {"model": config["model"], "requests": n, "max_attempts": tries,
            "input_token_estimate_char_div_3": chars / 3, "conservative_input_token_budget": upper_input,
            "output_token_budget": upper_output, "input_usd_per_million": input_price,
            "output_usd_per_million": output_price,
            "conservative_usd": (upper_input * input_price + upper_output * output_price) / 1e6,
            "assumptions": "One token per UTF-8 byte plus 64 framing tokens/request, max output and all retries; actual billing may vary."}
