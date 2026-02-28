from pathlib import Path
import random

from src.car import RaceCar
from src.driver import Driver
from src.environment import Environment
from src.simulation import SimulationEngine
from src.tire import Tire
from src.track import Track


def build_sample_cars() -> tuple[RaceCar, RaceCar]:
    dry_tire = Tire(compound="DRY", mu_dry=1.15, mu_wet=0.65)
    wet_tire = Tire(compound="WET", mu_dry=0.95, mu_wet=0.90)

    car_a = RaceCar(
        name="Car A",
        mass=820.0,
        cd=0.95,
        cl=1.60,
        frontal_area=1.5,
        max_accel=6.0,
        max_brake=8.0,
        top_speed=88.0,  # ~317 km/h
        brake_efficiency=1.00,
        suspension_factor=0.02,
        tire=dry_tire,
    )

    car_b = RaceCar(
        name="Car B",
        mass=835.0,
        cd=0.90,
        cl=1.45,
        frontal_area=1.5,
        max_accel=5.8,
        max_brake=7.8,
        top_speed=90.0,  # ~324 km/h
        brake_efficiency=0.98,
        suspension_factor=0.00,
        tire=wet_tire,
    )

    return car_a, car_b


def build_sample_drivers() -> tuple[Driver, Driver]:
    driver_a = Driver(name="Driver A", experience=8.0, aggressiveness=0.7)
    driver_b = Driver(name="Driver B", experience=5.0, aggressiveness=0.8)
    return driver_a, driver_b


def format_results(
    track: Track,
    env: Environment,
    metrics,
    num_laps: int,
    num_trials: int,
) -> str:
    lines = []
    lines.append("=== Stochastic Motorsport Performance Simulator ===")
    lines.append("")
    lines.append(f"Track: {track.name}")
    lines.append(f"Total Track Length: {track.total_length():.2f} m")
    lines.append(f"Segments: {len(track.segments)}")
    lines.append(f"Weather: {env.weather}")
    lines.append(f"Wetness: {env.wetness:.3f}")
    lines.append(f"Laps per Race: {num_laps}")
    lines.append(f"Monte Carlo Trials: {num_trials}")
    lines.append("")
    lines.append("--- Results ---")
    lines.append(f"Driver A Avg Race Time: {metrics.avg_time_a:.3f} s")
    lines.append(f"Driver B Avg Race Time: {metrics.avg_time_b:.3f} s")
    lines.append(f"Driver A Std Dev: {metrics.std_time_a:.3f} s")
    lines.append(f"Driver B Std Dev: {metrics.std_time_b:.3f} s")
    lines.append(f"Driver A Wins: {metrics.wins_a} ({metrics.win_prob_a:.1%})")
    lines.append(f"Driver B Wins: {metrics.wins_b} ({metrics.win_prob_b:.1%})")
    lines.append("")
    winner = "Driver A" if metrics.avg_time_a < metrics.avg_time_b else "Driver B"
    lines.append(f"Best Expected Performance: {winner}")
    return "\n".join(lines)


def save_output(text: str) -> None:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "sample_results.txt"
    output_file.write_text(text, encoding="utf-8")


def main() -> None:
    random.seed(42)  # reproducible screenshots for M2 comment out for random results or try another seed

    num_laps = 3
    num_trials = 100

    track = Track.random_track(name="M2 Test Track", num_pairs=4)
    env = Environment.random_environment()

    car_a, car_b = build_sample_cars()
    driver_a, driver_b = build_sample_drivers()

    engine = SimulationEngine()
    metrics = engine.run_trials(
        track=track,
        env=env,
        car_a=car_a,
        driver_a=driver_a,
        car_b=car_b,
        driver_b=driver_b,
        num_laps=num_laps,
        num_trials=num_trials,
    )

    output = format_results(track, env, metrics, num_laps, num_trials)
    print(output)
    save_output(output)


if __name__ == "__main__":
    main()