"""Exploratory paired tests on preserved predictions; never trains or infers.

H1 EN BERT minus VADER accuracy; H2 TR BERT minus Qwen accuracy;
H3 EN Qwen minus BERT Macro-F1; H4 TR BERT minus Qwen neutral recall.
All tests are two-sided. The four p values form one Holm-corrected family.
"""
import json
import math
from pathlib import Path

import numpy as np

from common import LABELS, read_csv, write_csv
from experiment_utils import ROOT, load_script, sha256, utc_now

PERMUTATIONS = 19999
SEED = 42
ALPHA = 0.05


def exact_mcnemar(a_only, b_only):
    n = int(a_only + b_only)
    k = int(min(a_only, b_only))
    if n == 0:
        return 1.0
    logs = [math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)-n*math.log(2) for i in range(k+1)]
    highest = max(logs)
    tail = math.exp(highest) * math.fsum(math.exp(x-highest) for x in logs)
    return min(1.0, 2 * tail)


def holm(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [0.0] * len(values)
    cumulative = 0.0
    for rank, index in enumerate(order):
        cumulative = max(cumulative, (len(values)-rank)*values[index])
        adjusted[index] = min(1.0, cumulative)
    return adjusted


def macro_f1(gold, prediction):
    m = np.bincount(3*gold + prediction, minlength=9).reshape(3, 3)
    support = m.sum(axis=0) + m.sum(axis=1)
    return float(np.divide(2*np.diag(m), support, out=np.zeros(3), where=support != 0).mean())


def paired_randomization(gold, a, b, permutations=PERMUTATIONS, seed=SEED):
    observed = macro_f1(gold, a) - macro_f1(gold, b)
    rng = np.random.Generator(np.random.PCG64(seed))
    extreme = 0
    for _ in range(permutations):
        swap = rng.integers(0, 2, len(gold), dtype=np.int8).astype(bool)
        delta = macro_f1(gold, np.where(swap, b, a)) - macro_f1(gold, np.where(swap, a, b))
        extreme += abs(delta) >= abs(observed) - 1e-12
    return (extreme+1)/(permutations+1), int(extreme), observed


def main():
    # Closed-form checks are independent of any research observations.
    assert exact_mcnemar(0, 0) == 1
    assert math.isclose(exact_mcnemar(10, 0), 2/2**10, abs_tol=1e-14)
    assert math.isclose(exact_mcnemar(5, 2), exact_mcnemar(2, 5))
    assert np.allclose(holm([.01, .04, .03]), [.03, .06, .06])
    runs, unavailable = load_script("07_build_results.py").collect()
    assert not unavailable and len(runs) == 6
    index = {(r["language"], r["method"]): r for r in runs}
    arrays = {}
    label_index = {label: i for i, label in enumerate(LABELS)}
    for language in ["en", "tr"]:
        gold_rows = read_csv(ROOT / "data" / language / "test.csv")
        gold = np.array([label_index[r["label"]] for r in gold_rows], dtype=np.int64)
        arrays[(language, "gold")] = gold
        for method in ["bert", "llm", "vader" if language == "en" else "vader_diagnostic"]:
            run = index[(language, method)]
            rows = {r["id"]: r for r in read_csv(ROOT / run["predictions_path"])}
            assert set(rows) == {r["id"] for r in gold_rows}
            predictions = np.array([label_index[rows[r["id"]]["prediction"]] for r in gold_rows], dtype=np.int64)
            assert math.isclose(macro_f1(gold, predictions), run["metrics"]["macro_f1"], abs_tol=1e-12)
            arrays[(language, method)] = predictions
    specs = [
        ("H1", "en", "bert", "vader", "accuracy", None),
        ("H2", "tr", "bert", "llm", "accuracy", None),
        ("H3", "en", "llm", "bert", "macro_f1", None),
        ("H4", "tr", "bert", "llm", "neutral_recall", label_index["neutral"]),
    ]
    results = []
    for name, lang, a_name, b_name, metric, subset in specs:
        gold = arrays[(lang, "gold")]
        a, b = arrays[(lang, a_name)], arrays[(lang, b_name)]
        if subset is not None:
            mask = gold == subset
            gold, a, b = gold[mask], a[mask], b[mask]
        ca, cb = a == gold, b == gold
        a_only, b_only = int(np.sum(ca & ~cb)), int(np.sum(~ca & cb))
        if metric == "macro_f1":
            p, extreme, delta = paired_randomization(gold, a, b)
            test = "paired_approximate_randomization"
        else:
            p = exact_mcnemar(a_only, b_only)
            delta = float(ca.mean()-cb.mean())
            test, extreme = "exact_two_sided_mcnemar", None
        results.append({"hypothesis": name, "language": lang, "first": a_name, "second": b_name,
                        "metric": metric, "n": len(gold), "effect_first_minus_second": delta,
                        "test": test, "p_raw": p, "first_only_correct": a_only,
                        "second_only_correct": b_only, "permutations": PERMUTATIONS if extreme is not None else None,
                        "permutation_extreme_count": extreme})
    for row, adjusted in zip(results, holm([r["p_raw"] for r in results])):
        row["p_holm"] = adjusted
        row["reject_null_at_0_05"] = adjusted < ALPHA
    # Independent library cross-check of the exact paired binary p values.
    cross_check = "not_available"
    try:
        from scipy.stats import binomtest
        for row in results:
            if row["test"] == "exact_two_sided_mcnemar":
                a, b = row["first_only_correct"], row["second_only_correct"]
                expected = binomtest(a, a+b, .5).pvalue if a+b else 1.0
                assert math.isclose(row["p_raw"], expected, rel_tol=1e-10, abs_tol=1e-100)
        cross_check = "all_exact_p_values_match_scipy_binomtest"
    except ImportError:
        pass
    output = {"analyzed_at_utc": utc_now(), "analysis_type": "post_hoc_exploratory",
              "preregistered": False, "two_sided": True, "multiple_testing": "Holm, one family of four tests",
              "alpha": ALPHA, "permutation_seed": SEED, "permutation_bit_generator": "PCG64",
              "numpy_version": np.__version__, "confidence_intervals_computed": False,
              "training_seed_variation_measured": False, "new_model_runs": 0,
              "independent_numeric_check": cross_check,
              "source_prediction_sha256": {r["predictions_path"]: sha256(ROOT/r["predictions_path"]) for r in runs},
              "limitations": ["Hypotheses formulated after inspecting original results",
                              "Holm correction covers four specified tests, not all possible researcher choices",
                              "Inference conditions on frozen models, test sampling and source labels; no training-seed replication",
                              "Review-level exchangeability assumes no unmeasured author/product clusters"],
              "results": results}
    path = ROOT / "deliverables/hypothesis_tests.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(ROOT / "deliverables/hypothesis_tests.csv", results, list(results[0]))
    print(json.dumps({"independent_numeric_check": cross_check, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
