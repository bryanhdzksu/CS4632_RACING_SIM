import random
import time

from src.config import SimConfig, build_configs_from_cli, parse_cli_args, validate_config
from src.data_collector import DataCollector
from src.simulation import SimulationEngine


def run_simulation(config: SimConfig) -> None:
    """Execute a single simulation run from the given configuration."""
    if config.random_seed is not None:
        random.seed(config.random_seed)

    errors = validate_config(config)
    if errors:
        print(f"Configuration errors for run {config.run_id}:")
        for e in errors:
            print(f"  - {e}")
        return

    track = config.build_track()
    env = config.build_environment()
    entrants = config.build_entrants()

    print(f"\n{'=' * 60}")
    print(f"Run {config.run_id}: {config.description}")
    print(f"{'=' * 60}")
    print(f"Track: {track.name} ({track.total_length():.1f} m, {len(track.segments)} segments)")
    print(f"Weather: {env.weather} | Wetness: {env.wetness:.3f} | Visibility: {env.visibility:.3f}")
    print(f"Entrants: {len(entrants)} | Laps: {config.num_laps} | Trials: {config.num_trials}")
    print("Lineup:")
    for e in entrants:
        print(f"  {e.name} | Tire: {e.car.tire.compound} | Exp: {e.driver.experience}")
    print()

    engine = SimulationEngine()
    start_time = time.time()
    metrics, trial_results = engine.run_trials(
        track=track,
        env=env,
        entrants=entrants,
        num_laps=config.num_laps,
        num_trials=config.num_trials,
        collect_detail=config.collect_detail,
    )
    execution_time = time.time() - start_time

    print("--- Results ---")
    for em in metrics.entrant_metrics:
        print(
            f"  {em.name}: avg={em.avg_time:.3f}s  std={em.std_time:.3f}s  "
            f"min={em.min_time:.3f}s  max={em.max_time:.3f}s  "
            f"wins={em.wins} ({em.win_prob:.1%})"
        )

    best = min(metrics.entrant_metrics, key=lambda m: m.avg_time)
    print(f"\nBest Expected Performance: {best.name}")
    print(f"Execution Time: {execution_time:.2f}s")

    collector = DataCollector()
    run_dir = collector.save_run(
        config=config,
        track=track,
        env=env,
        entrants=entrants,
        metrics=metrics,
        trial_results=trial_results,
        execution_time=execution_time,
    )
    print(f"Data saved to: {run_dir}/")


def main() -> None:
    args = parse_cli_args()
    configs = build_configs_from_cli(args)
    for config in configs:
        run_simulation(config)


if __name__ == "__main__":
    main()
