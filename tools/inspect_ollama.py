import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm_support import ollama_identity
from experiment_utils import ROOT

config = json.loads((ROOT / "configs/llm_local.json").read_text())
previous = json.loads((ROOT / "runs/tr_llm_test/run_config.json").read_text())["signature"]["model_identity"]
current = ollama_identity(config)
print(json.dumps({"previous": previous, "current": current,
                  "different_keys": [k for k in previous if previous[k] != current.get(k)]}, indent=2))
