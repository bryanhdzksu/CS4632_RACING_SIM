"""
Milestone 4: sensitivity sweeps, aggregated CSVs, statistics, and figures.

Usage (from project root):
    python m4_analysis.py              # run sweeps + aggregate + figures
    python m4_analysis.py --figures-only

Outputs under output/m4_analysis/ (does not modify output/run_index.json for M3 runs).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from main import run_simulation_core
from src.config import SimConfig, load_config_from_json
from src.data_collector import DataCollector
from src.utils import mean, stddev

BASELINE_JSON = Path("configs/run_001_baseline_dry.json")
OUT_DIR = Path("output/m4_analysis")
FIG_DIR = OUT_DIR / "figures"

# Reference entrant for sensitivity metrics (matches M3 focus)
REF_ENTRANT = "Verstappen (Red Bull)"


def _baseline() -> SimConfig:
    return load_config_from_json(BASELINE_JSON)


def _ci95_mean(values: list[float]) -> tuple[float, float, float]:
    """Returns (mean, lower, upper) for 95% CI of the mean, n = len(values)."""
    n = len(values)
    xbar = mean(values)
    if n < 2:
        return xbar, xbar, xbar
    s = stddev(values)
    half = 1.96 * s / math.sqrt(n)
    return xbar, xbar - half, xbar + half


def _run_and_save(config: SimConfig):
    """Run once, save under output/m4_analysis/, return metrics."""
    metrics, trial_results, execution_time, track, env, entrants = run_simulation_core(
        config
    )
    collector = DataCollector(base_dir=OUT_DIR)
    collector.save_run(
        config=config,
        track=track,
        env=env,
        entrants=entrants,
        metrics=metrics,
        trial_results=trial_results,
        execution_time=execution_time,
    )
    return metrics


def _metric_for_entrant(metrics, name: str):
    for em in metrics.entrant_metrics:
        if em.name == name:
            return em
    return metrics.entrant_metrics[0]


def sweep_wetness() -> list[dict]:
    """Vary wetness only; Sunny; visibility 0.95; seed 100; 200 trials; 5 laps."""
    rows = []
    for w in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        c = _baseline()
        c.run_id = f"m4_sw_{int(w * 100):03d}"
        c.description = f"M4 sensitivity: wetness={w:.2f} (other params match baseline)"
        c.env_weather = "Sunny"
        c.env_wetness = w
        c.env_visibility = 0.95
        c.random_seed = 100
        c.num_laps = 5
        c.num_trials = 200
        c.collect_detail = False
        metrics = _run_and_save(c)
        em = _metric_for_entrant(metrics, REF_ENTRANT)
        _, ci_lo, ci_hi = _ci95_mean(em.all_times)
        rows.append({
            "parameter": "wetness",
            "wetness": w,
            "visibility": 0.95,
            "num_laps": 5,
            "num_trials": 200,
            "track_num_pairs": c.track_num_pairs,
            f"{REF_ENTRANT} avg_race_time_s": round(em.avg_time, 4),
            f"{REF_ENTRANT} std_s": round(em.std_time, 4),
            f"{REF_ENTRANT} win_pct": round(em.win_prob * 100, 2),
            "ci95_mean_low": round(ci_lo, 4),
            "ci95_mean_high": round(ci_hi, 4),
        })
    return rows


def sweep_visibility() -> list[dict]:
    """Vary visibility only; Cloudy; wetness 0.30."""
    rows = []
    for vis in [0.25, 0.45, 0.65, 0.85, 0.95]:
        c = _baseline()
        c.run_id = f"m4_sv_{int(vis * 100):03d}"
        c.description = f"M4 sensitivity: visibility={vis:.2f}"
        c.env_weather = "Cloudy"
        c.env_wetness = 0.30
        c.env_visibility = vis
        c.random_seed = 100
        c.num_laps = 5
        c.num_trials = 200
        c.collect_detail = False
        metrics = _run_and_save(c)
        em = _metric_for_entrant(metrics, REF_ENTRANT)
        _, ci_lo, ci_hi = _ci95_mean(em.all_times)
        rows.append({
            "parameter": "visibility",
            "wetness": 0.30,
            "visibility": vis,
            "num_laps": 5,
            "num_trials": 200,
            "track_num_pairs": c.track_num_pairs,
            f"{REF_ENTRANT} avg_race_time_s": round(em.avg_time, 4),
            f"{REF_ENTRANT} std_s": round(em.std_time, 4),
            f"{REF_ENTRANT} win_pct": round(em.win_prob * 100, 2),
            "ci95_mean_low": round(ci_lo, 4),
            "ci95_mean_high": round(ci_hi, 4),
        })
    return rows


def sweep_num_laps() -> list[dict]:
    """Vary num_laps only."""
    rows = []
    for laps in [1, 3, 5, 10]:
        c = _baseline()
        c.run_id = f"m4_lp_{laps:02d}"
        c.description = f"M4 sensitivity: num_laps={laps}"
        c.env_weather = "Sunny"
        c.env_wetness = 0.05
        c.env_visibility = 0.95
        c.random_seed = 100
        c.num_laps = laps
        c.num_trials = 200
        c.collect_detail = False
        metrics = _run_and_save(c)
        em = _metric_for_entrant(metrics, REF_ENTRANT)
        _, ci_lo, ci_hi = _ci95_mean(em.all_times)
        rows.append({
            "parameter": "num_laps",
            "wetness": 0.05,
            "visibility": 0.95,
            "num_laps": laps,
            "num_trials": 200,
            "track_num_pairs": c.track_num_pairs,
            f"{REF_ENTRANT} avg_race_time_s": round(em.avg_time, 4),
            f"{REF_ENTRANT} std_s": round(em.std_time, 4),
            f"{REF_ENTRANT} win_pct": round(em.win_prob * 100, 2),
            "ci95_mean_low": round(ci_lo, 4),
            "ci95_mean_high": round(ci_hi, 4),
        })
    return rows


def sweep_num_trials() -> list[dict]:
    """Vary Monte Carlo trial count (same seed, wetness 0.05)."""
    rows = []
    for nt in [50, 100, 200, 500]:
        c = _baseline()
        c.run_id = f"m4_nt_{nt}"
        c.description = f"M4 sensitivity: num_trials={nt}"
        c.env_weather = "Sunny"
        c.env_wetness = 0.05
        c.env_visibility = 0.95
        c.random_seed = 100
        c.num_laps = 5
        c.num_trials = nt
        c.collect_detail = False
        metrics = _run_and_save(c)
        em = _metric_for_entrant(metrics, REF_ENTRANT)
        _, ci_lo, ci_hi = _ci95_mean(em.all_times)
        rows.append({
            "parameter": "num_trials",
            "wetness": 0.05,
            "visibility": 0.95,
            "num_laps": 5,
            "num_trials": nt,
            "track_num_pairs": c.track_num_pairs,
            f"{REF_ENTRANT} avg_race_time_s": round(em.avg_time, 4),
            f"{REF_ENTRANT} std_s": round(em.std_time, 4),
            f"{REF_ENTRANT} win_pct": round(em.win_prob * 100, 2),
            "ci95_mean_low": round(ci_lo, 4),
            "ci95_mean_high": round(ci_hi, 4),
        })
    return rows


def sweep_track_pairs() -> list[dict]:
    """Vary track complexity (segment pairs) only."""
    rows = []
    for pairs in [2, 4, 6, 8]:
        c = _baseline()
        c.run_id = f"m4_tp_{pairs}"
        c.description = f"M4 sensitivity: track_num_pairs={pairs}"
        c.track_num_pairs = pairs
        c.env_weather = "Sunny"
        c.env_wetness = 0.05
        c.env_visibility = 0.95
        c.random_seed = 100
        c.num_laps = 5
        c.num_trials = 200
        c.collect_detail = False
        metrics = _run_and_save(c)
        em = _metric_for_entrant(metrics, REF_ENTRANT)
        _, ci_lo, ci_hi = _ci95_mean(em.all_times)
        rows.append({
            "parameter": "track_num_pairs",
            "wetness": 0.05,
            "visibility": 0.95,
            "num_laps": 5,
            "num_trials": 200,
            "track_num_pairs": pairs,
            f"{REF_ENTRANT} avg_race_time_s": round(em.avg_time, 4),
            f"{REF_ENTRANT} std_s": round(em.std_time, 4),
            f"{REF_ENTRANT} win_pct": round(em.win_prob * 100, 2),
            "ci95_mean_low": round(ci_lo, 4),
            "ci95_mean_high": round(ci_hi, 4),
        })
    return rows


def _write_csv(name: str, rows: list[dict]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    if not rows:
        return path
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return path


def sensitivity_ratio(
    x1: float, x2: float, y1: float, y2: float
) -> float | None:
    """Appendix A.2: (%Δy) / (%Δx). Returns None if denominator is zero."""
    if x1 == 0 or x2 == 0:
        return None
    px = (x2 - x1) / x1 * 100.0 if x1 != 0 else 0.0
    py = (y2 - y1) / y1 * 100.0 if y1 != 0 else 0.0
    if abs(px) < 1e-9:
        return None
    return py / px


def run_all_sweeps() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("M4: wetness sweep...")
    w_rows = sweep_wetness()
    _write_csv("sensitivity_wetness.csv", w_rows)

    print("M4: visibility sweep...")
    v_rows = sweep_visibility()
    _write_csv("sensitivity_visibility.csv", v_rows)

    print("M4: num_laps sweep...")
    l_rows = sweep_num_laps()
    _write_csv("sensitivity_num_laps.csv", l_rows)

    print("M4: num_trials sweep...")
    t_rows = sweep_num_trials()
    _write_csv("sensitivity_num_trials.csv", t_rows)

    print("M4: track_num_pairs sweep...")
    p_rows = sweep_track_pairs()
    _write_csv("sensitivity_track_pairs.csv", p_rows)

    # Example sensitivity (wetness 0.2 -> 0.8 on avg race time)
    ykey = f"{REF_ENTRANT} avg_race_time_s"
    w02 = next(r for r in w_rows if r["wetness"] == 0.2)[ykey]
    w08 = next(r for r in w_rows if r["wetness"] == 0.8)[ykey]
    sr_wet = sensitivity_ratio(0.2, 0.8, w02, w08)

    meta = {
        "reference_entrant": REF_ENTRANT,
        "sensitivity_wetness_02_to_08": {
            "delta_wetness_fraction": 0.6,
            "pct_delta_output": (w08 - w02) / w02 * 100.0 if w02 else None,
            "sensitivity_ratio_py_over_px": sr_wet,
        },
        "scenario_rows_source": "output/test_results.csv (M3 runs 001,002,007,012)",
    }
    with open(OUT_DIR / "m4_analysis_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    _write_scenario_subset_csv()

    # Statistical summary table (baseline M3 run 001 from test_results if present)
    stats = build_statistical_summary()
    with open(OUT_DIR / "m4_statistical_summary.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return meta


def _write_scenario_subset_csv() -> None:
    """Copy selected M3 runs from test_results.csv for scenario section."""
    src = Path("output/test_results.csv")
    if not src.exists():
        return
    want = {"001", "002", "007", "012"}
    rows_out = []
    with open(src, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row.get("run_id", "").strip() in want:
                rows_out.append(row)
    if not rows_out:
        return
    path = OUT_DIR / "scenario_m3_runs_subset.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)


def build_statistical_summary() -> list[dict]:
    """Key metrics for 3 entrants from M3 run 001 summary file."""
    import json as _json

    p = Path("output/run_001/run_001_summary.json")
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = _json.load(f)
    out = []
    for name, e in data.get("entrants", {}).items():
        out.append({
            "metric": f"Total race time (5 laps) — {name}",
            "mean_s": e["avg_time"],
            "std_s": e["std_time"],
            "min_s": e["min_time"],
            "max_s": e["max_time"],
            "n_trials": data.get("num_trials", 200),
        })
    return out


def generate_figures() -> None:
    """Requires matplotlib."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skip figures. pip install matplotlib")
        return

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ykey = f"{REF_ENTRANT} avg_race_time_s"
    wkey = f"{REF_ENTRANT} win_pct"

    def load_csv(name: str) -> list[dict]:
        path = OUT_DIR / name
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    # Wetness
    rows = load_csv("sensitivity_wetness.csv")
    if rows:
        xs = [float(r["wetness"]) for r in rows]
        ys = [float(r[ykey]) for r in rows]
        plt.figure(figsize=(7, 4))
        plt.plot(xs, ys, "o-", color="#0f3460")
        plt.xlabel("Wetness (0 = dry, 1 = fully wet)")
        plt.ylabel("Mean total race time (s)")
        plt.title(f"Sensitivity: wetness vs {REF_ENTRANT} mean race time")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG_DIR / "fig_wetness_vs_time.png", dpi=150)
        plt.close()

    # Visibility
    rows = load_csv("sensitivity_visibility.csv")
    if rows:
        xs = [float(r["visibility"]) for r in rows]
        ys = [float(r[ykey]) for r in rows]
        plt.figure(figsize=(7, 4))
        plt.plot(xs, ys, "s-", color="#16213e")
        plt.xlabel("Visibility (0–1)")
        plt.ylabel("Mean total race time (s)")
        plt.title(f"Sensitivity: visibility vs {REF_ENTRANT} mean race time")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG_DIR / "fig_visibility_vs_time.png", dpi=150)
        plt.close()

    # Laps
    rows = load_csv("sensitivity_num_laps.csv")
    if rows:
        xs = [int(r["num_laps"]) for r in rows]
        ys = [float(r[wkey]) for r in rows]
        plt.figure(figsize=(7, 4))
        plt.plot(xs, ys, "o-", color="#533483")
        plt.xlabel("Number of laps")
        plt.ylabel("Win rate (%)")
        plt.title(f"{REF_ENTRANT} win % vs race length (trials=200)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG_DIR / "fig_laps_vs_winpct.png", dpi=150)
        plt.close()

    # Trials (CI width proxy)
    rows = load_csv("sensitivity_num_trials.csv")
    if rows:
        xs = [int(r["num_trials"]) for r in rows]
        lo = [float(r["ci95_mean_low"]) for r in rows]
        hi = [float(r["ci95_mean_high"]) for r in rows]
        mid = [float(r[ykey]) for r in rows]
        plt.figure(figsize=(7, 4))
        plt.fill_between(xs, lo, hi, alpha=0.25, color="#0f3460")
        plt.plot(xs, mid, "o-", color="#0f3460")
        plt.xlabel("Number of Monte Carlo trials")
        plt.ylabel("Mean race time (s) with 95% CI band")
        plt.title(f"{REF_ENTRANT}: mean total time vs trial count")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG_DIR / "fig_trials_vs_ci.png", dpi=150)
        plt.close()

    # Track pairs
    rows = load_csv("sensitivity_track_pairs.csv")
    if rows:
        xs = [int(r["track_num_pairs"]) for r in rows]
        ys = [float(r[ykey]) for r in rows]
        plt.figure(figsize=(7, 4))
        plt.bar([str(x) for x in xs], ys, color="#1a508b")
        plt.xlabel("Track segment pairs (complexity)")
        plt.ylabel("Mean total race time (s)")
        plt.title(f"{REF_ENTRANT} mean race time vs track complexity")
        plt.tight_layout()
        plt.savefig(FIG_DIR / "fig_track_pairs_vs_time.png", dpi=150)
        plt.close()

    print(f"Figures written to {FIG_DIR}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Milestone 4 analysis pipeline")
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Only regenerate figures from existing CSVs",
    )
    args = parser.parse_args()
    if args.figures_only:
        generate_figures()
        return
    run_all_sweeps()
    generate_figures()
    print("\nDone. See output/m4_analysis/ and figures/ for CSVs and PNGs.")


if __name__ == "__main__":
    main()
