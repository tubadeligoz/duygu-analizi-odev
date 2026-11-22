"""Derive thesis figures/tables from frozen predictions; no inference or training."""
import argparse
import json
from pathlib import Path

from common import LABELS, write_csv
from experiment_utils import ROOT, load_script, sha256, utc_now


def main(article=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    runs, unavailable = load_script("07_build_results.py").collect()
    if unavailable or len(runs) != 6:
        raise ValueError("Thesis requires six verified completed runs")
    out = ROOT / ("deliverables/article_figures" if article else "deliverables/tez_figures")
    tables = ROOT / "deliverables/tez_tables"
    out.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5 if article else 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.dpi": 220})
    colors = ["#52728A", "#276F60", "#BA743C"]
    names = ["Negatif", "Nötr", "Pozitif"]
    labels = [r["language"].upper() + "  " + r["display_name"] for r in runs]

    fig, axes = plt.subplots(2, 1, figsize=(3.4, 5.6) if article else (7.4, 6.7), layout="constrained")
    for ax, field, title in zip(axes, ["accuracy", "macro_f1"], ["Doğruluk", "Macro F1"]):
        vals = [r["metrics"][field] for r in runs]
        ax.barh(labels[::-1], vals[::-1], color=(colors * 2)[::-1], height=.65)
        ax.set_xlim(0, 1)
        ax.set_xlabel(title)
        ax.grid(axis="x", alpha=.16)
        ax.set_axisbelow(True)
        for i, value in enumerate(vals[::-1]):
            ax.text(value + .012, i, f"{value:.3f}" if article else f"{value:.4f}", va="center", fontsize=8 if article else 10)
    fig.savefig(out / "genel_basarim.png", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(3.4, 4.9) if article else (7.4, 6.2), layout="constrained")
    for ax, lang in zip(axes, ["en", "tr"]):
        subset = [r for r in runs if r["language"] == lang]
        x = np.arange(3)
        for j, r in enumerate(subset):
            vals = [c["incorrect"] for c in r["classes"]]
            bars = ax.bar(x + (j - 1) * .25, vals, width=.23, color=colors[j], label=r["display_name"])
            ax.bar_label(bars, fontsize=8 if article else 10, padding=3)
        ax.set_xticks(x, names)
        ax.set_ylim(0, 1120)
        ax.set_ylabel("Hatalı tahmin sayısı")
        ax.set_title("İngilizce" if lang == "en" else ("Türkçe  VADER tanısal" if article else "Türkçe"), loc="left", fontweight="bold")
        if article:
            ax.legend(["VADER", "BERT", "Qwen"], loc="upper right", frameon=False, fontsize=8, ncol=3,
                      handlelength=1, columnspacing=.7)
        else:
            ax.legend(loc="upper right", frameon=False, fontsize=9, ncol=3)
        ax.grid(axis="y", alpha=.16)
        ax.set_axisbelow(True)
    fig.savefig(out / "sinif_hatalari.png", bbox_inches="tight")
    plt.close(fig)

    for lang in ["en", "tr"]:
        subset = [r for r in runs if r["language"] == lang]
        fig, axes = plt.subplots(3, 1, figsize=(3.4, 6.6) if article else (6.3, 9.5), layout="constrained")
        for ax, r in zip(axes, subset):
            m = np.array([[r["matrix"][c][p] for p in LABELS] for c in LABELS])
            ax.imshow(m, cmap="Blues", vmin=0, vmax=1000, aspect="auto")
            ax.set_xticks(range(3), names)
            ax.set_yticks(range(3), names)
            ax.set_xlabel("Tahmin edilen sınıf", fontsize=8 if article else 10)
            ax.set_ylabel("Gerçek sınıf", fontsize=8 if article else 10)
            ax.set_title(r["display_name"], loc="left", fontweight="bold", fontsize=9 if article else 12)
            for i in range(3):
                for j in range(3):
                    ax.text(j, i, str(m[i, j]), ha="center", va="center", fontsize=10 if article else 13,
                            color="white" if m[i, j] > 570 else "black")
        fig.savefig(out / f"karisiklik_{lang}.png", bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(3.4, 4.7) if article else (7.4, 5.7), layout="constrained")
    histories = {}
    history_rows = []
    for j, lang in enumerate(["en", "tr"]):
        h = json.loads((ROOT / f"runs/{lang}_bert_seed42/history.json").read_text(encoding="utf-8"))
        histories[lang] = h
        for row in h:
            history_rows.append({"language": lang, **row})
        for ax, field in zip(axes, ["train_loss", "validation_macro_f1"]):
            ax.plot([x["epoch"] for x in h], [x[field] for x in h], "o-", color=colors[j+1], label=lang.upper(), linewidth=2)
            ax.set_xticks([1, 2, 3])
            ax.set_xlabel("Epoch")
            ax.grid(alpha=.18)
            ax.legend(frameon=False)
    axes[0].set_ylabel("Çapraz entropi kaybı" if article else "Eğitim çapraz entropi kaybı")
    axes[1].set_ylabel("Doğrulama Macro F1")
    fig.savefig(out / "ogrenme_egrileri.png", bbox_inches="tight")
    plt.close(fig)
    write_csv(tables / "epoch_metrics.csv", history_rows, list(history_rows[0]))

    distribution = []
    fig, ax = plt.subplots(figsize=(3.4, 3.3) if article else (7.6, 4.5), layout="constrained")
    left = np.zeros(6)
    for j, c in enumerate(LABELS):
        counts = [sum(r["matrix"][gold][c] for gold in LABELS) for r in runs]
        ax.barh(labels, np.array(counts) / 30, left=left, color=colors[j], label=names[j])
        for i, n in enumerate(counts):
            distribution.append({"language": runs[i]["language"], "method": runs[i]["display_name"],
                                 "predicted_class": c, "count": n, "proportion": n/3000})
            if n >= (350 if article else 180):
                ax.text(left[i] + n/60, i, str(n), ha="center", va="center", color="white", fontsize=8 if article else 10)
        left += np.array(counts) / 30
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Tahmin edilen sınıfların oranı  %")
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=3, frameon=False)
    fig.savefig(out / "tahmin_dagilimi.png", bbox_inches="tight")
    plt.close(fig)
    write_csv(tables / "prediction_distribution.csv", distribution, list(distribution[0]))

    fig, ax = plt.subplots(figsize=(3.4, 3.3) if article else (6.8, 4.8), layout="constrained")
    m = np.array([[r["classes"][j]["f1"] for j in range(3)] for r in runs])
    ax.imshow(m, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(3), names)
    ax.set_yticks(range(6), labels)
    for i in range(6):
        for j in range(3):
            ax.text(j, i, f"{m[i,j]:.4f}", ha="center", va="center", fontsize=9 if article else 12,
                    color="white" if m[i,j] > .6 else "black")
    fig.savefig(out / "sinif_f1.png", bbox_inches="tight")
    plt.close(fig)

    # All original prediction bytes and source figures remain untouched.
    source = {r["predictions_path"]: sha256(ROOT / r["predictions_path"]) for r in runs}
    evidence = {"built_at_utc": utc_now(), "experiments_added": 0, "runs": 6,
                "reference_predictions": source, "figure_count": len(list(out.glob("*.png"))),
                "derivation": "Recomputed class counts and metrics from frozen, ID-matched predictions"}
    evidence["layout"] = "article_single_column_figures" if article else "thesis"
    (ROOT / ("audit/article_assets.json" if article else "audit/thesis_assets.json")).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"figures": evidence["figure_count"], "tables": 2, "verified_runs": 6}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", action="store_true", help="Create readable figures for an 8.1 cm article column")
    main(parser.parse_args().article)
