import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import SimConfig
from src.entrant import Entrant
from src.environment import Environment
from src.simulation import TrialResult
from src.track import Track
from src.utils import RaceMetrics


class DataCollector:
    """Writes per-run CSV/JSON output files and maintains a master index."""

    def __init__(self, base_dir: str | Path = "output"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_run(
        self,
        config: SimConfig,
        track: Track,
        env: Environment,
        entrants: list[Entrant],
        metrics: RaceMetrics,
        trial_results: list[TrialResult],
        execution_time: float,
    ) -> Path:
        run_dir = self.base_dir / f"run_{config.run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        self._save_config_json(run_dir, config, track, env, entrants)
        self._save_summary_json(run_dir, config, metrics, execution_time, track, env)
        self._save_timeseries_csv(run_dir, config, trial_results, env)
        if config.collect_detail:
            self._save_events_csv(run_dir, config, trial_results, env)

        self._update_master_index(config, metrics, execution_time, track, env)

        return run_dir

    # ------------------------------------------------------------------
    # Config JSON
    # ------------------------------------------------------------------
    def _save_config_json(
        self,
        run_dir: Path,
        config: SimConfig,
        track: Track,
        env: Environment,
        entrants: list[Entrant],
    ) -> None:
        data = {
            "run_id": config.run_id,
            "description": config.description,
            "random_seed": config.random_seed,
            "num_laps": config.num_laps,
            "num_trials": config.num_trials,
            "track": {
                "name": track.name,
                "total_length_m": round(track.total_length(), 2),
                "num_segments": len(track.segments),
                "segments": [
                    {
                        "type": seg.segment_type.value,
                        "length_m": round(seg.length, 2),
                        "radius_m": round(seg.radius, 2) if seg.radius else None,
                    }
                    for seg in track.segments
                ],
            },
            "environment": {
                "weather": env.weather,
                "wetness": round(env.wetness, 4),
                "visibility": round(env.visibility, 4),
            },
            "entrants": [
                {
                    "name": e.name,
                    "driver": {
                        "name": e.driver.name,
                        "experience": e.driver.experience,
                        "aggressiveness": e.driver.aggressiveness,
                    },
                    "car": {
                        "name": e.car.name,
                        "mass": e.car.mass,
                        "cd": e.car.cd,
                        "cl": e.car.cl,
                        "top_speed": e.car.top_speed,
                    },
                    "tire": {
                        "compound": e.car.tire.compound,
                        "mu_dry": e.car.tire.mu_dry,
                        "mu_wet": e.car.tire.mu_wet,
                    },
                }
                for e in entrants
            ],
        }
        path = run_dir / f"run_{config.run_id}_config.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Summary JSON
    # ------------------------------------------------------------------
    def _save_summary_json(
        self,
        run_dir: Path,
        config: SimConfig,
        metrics: RaceMetrics,
        execution_time: float,
        track: Track,
        env: Environment,
    ) -> None:
        entrant_summaries = {}
        for em in metrics.entrant_metrics:
            entrant_summaries[em.name] = {
                "avg_time": round(em.avg_time, 4),
                "std_time": round(em.std_time, 4),
                "min_time": round(em.min_time, 4),
                "max_time": round(em.max_time, 4),
                "wins": em.wins,
                "win_pct": round(em.win_prob * 100, 2),
            }

        data = {
            "run_id": config.run_id,
            "description": config.description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_time_seconds": round(execution_time, 3),
            "num_trials": config.num_trials,
            "num_laps": config.num_laps,
            "track_name": track.name,
            "track_length_m": round(track.total_length(), 2),
            "weather": env.weather,
            "wetness": round(env.wetness, 4),
            "visibility": round(env.visibility, 4),
            "entrants": entrant_summaries,
        }
        path = run_dir / f"run_{config.run_id}_summary.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Time-series CSV  (one row per trial × lap × entrant)
    # ------------------------------------------------------------------
    def _save_timeseries_csv(
        self,
        run_dir: Path,
        config: SimConfig,
        trial_results: list[TrialResult],
        env: Environment,
    ) -> None:
        path = run_dir / f"run_{config.run_id}_timeseries.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "trial", "lap", "entrant", "lap_time", "cumulative_time",
                "weather", "wetness",
            ])
            for trial in trial_results:
                for entrant_result in trial.results:
                    cumulative = 0.0
                    for lap in entrant_result.laps:
                        cumulative += lap.lap_time
                        writer.writerow([
                            trial.trial_number,
                            lap.lap_number,
                            entrant_result.entrant_name,
                            round(lap.lap_time, 5),
                            round(cumulative, 5),
                            env.weather,
                            round(env.wetness, 4),
                        ])

    # ------------------------------------------------------------------
    # Events CSV  (one row per trial × lap × entrant × segment)
    # ------------------------------------------------------------------
    def _save_events_csv(
        self,
        run_dir: Path,
        config: SimConfig,
        trial_results: list[TrialResult],
        env: Environment,
    ) -> None:
        path = run_dir / f"run_{config.run_id}_events.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "trial", "lap", "entrant", "segment_idx", "segment_type",
                "length_m", "entry_speed", "exit_speed", "segment_time",
                "mu_effective",
            ])
            for trial in trial_results:
                for entrant_result in trial.results:
                    for lap in entrant_result.laps:
                        for seg in lap.segments:
                            writer.writerow([
                                trial.trial_number,
                                lap.lap_number,
                                entrant_result.entrant_name,
                                seg.segment_idx,
                                seg.segment_type,
                                seg.length,
                                seg.entry_speed,
                                seg.exit_speed,
                                seg.time,
                                seg.mu_effective if seg.mu_effective is not None else "",
                            ])

    # ------------------------------------------------------------------
    # Master index (append-style)
    # ------------------------------------------------------------------
    def _update_master_index(
        self,
        config: SimConfig,
        metrics: RaceMetrics,
        execution_time: float,
        track: Track,
        env: Environment,
    ) -> None:
        index_path = self.base_dir / "run_index.json"

        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = []

        best = min(metrics.entrant_metrics, key=lambda m: m.avg_time)

        index.append({
            "run_id": config.run_id,
            "description": config.description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_time_seconds": round(execution_time, 3),
            "num_entrants": len(metrics.entrant_metrics),
            "num_laps": config.num_laps,
            "num_trials": config.num_trials,
            "track": track.name,
            "weather": env.weather,
            "wetness": round(env.wetness, 4),
            "best_performer": best.name,
            "best_avg_time": round(best.avg_time, 4),
            "data_dir": f"run_{config.run_id}",
        })

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
