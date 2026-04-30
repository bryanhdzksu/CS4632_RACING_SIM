"""Configuration and CLI orchestration layer.

This module converts JSON/CLI inputs into validated `SimConfig` objects, then
builds concrete simulation entities (track, environment, entrants).
"""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.car import RaceCar
from src.driver import Driver
from src.entrant import Entrant
from src.environment import Environment
from src.tire import Tire
from src.track import Track


@dataclass
class SimConfig:
    run_id: str = "001"
    description: str = "Default simulation run"
    random_seed: int | None = None
    num_laps: int = 5
    num_trials: int = 200
    collect_detail: bool = True

    track_name: str = "Generated Track"
    track_num_pairs: int = 6
    track_straight_range: tuple[float, float] = (100.0, 250.0)
    track_corner_radius_range: tuple[float, float] = (25.0, 90.0)
    track_corner_arc_range_deg: tuple[float, float] = (45.0, 135.0)

    env_weather: str | None = None
    env_wetness: float | None = None
    env_visibility: float | None = None

    entrants_config: list[dict[str, Any]] = field(default_factory=list)

    def build_track(self) -> Track:
        """Instantiate a randomized track using configured parameter ranges."""
        return Track.random_track(
            name=self.track_name,
            num_pairs=self.track_num_pairs,
            straight_range=self.track_straight_range,
            corner_radius_range=self.track_corner_radius_range,
            corner_arc_range_deg=self.track_corner_arc_range_deg,
        )

    def build_environment(self) -> Environment:
        """Use fixed env settings when provided; otherwise sample randomly."""
        if (
            self.env_weather is not None
            and self.env_wetness is not None
            and self.env_visibility is not None
        ):
            return Environment(
                weather=self.env_weather,
                wetness=self.env_wetness,
                visibility=self.env_visibility,
            )
        return Environment.random_environment()

    def build_entrants(self) -> list[Entrant]:
        """Build entrant objects from config; fall back to calibrated defaults."""
        if not self.entrants_config:
            return _default_entrants()

        entrants = []
        for ec in self.entrants_config:
            tire_cfg = ec.get("tire", {})
            tire = Tire(
                compound=tire_cfg.get("compound", "DRY"),
                mu_dry=tire_cfg.get("mu_dry", 1.05),
                mu_wet=tire_cfg.get("mu_wet", 0.80),
            )

            car_cfg = ec.get("car", {})
            car = RaceCar(
                name=car_cfg.get("name", "Car"),
                mass=car_cfg.get("mass", 800.0),
                cd=car_cfg.get("cd", 0.90),
                cl=car_cfg.get("cl", 1.50),
                frontal_area=car_cfg.get("frontal_area", 1.5),
                max_accel=car_cfg.get("max_accel", 5.8),
                max_brake=car_cfg.get("max_brake", 8.0),
                top_speed=car_cfg.get("top_speed", 88.0),
                brake_efficiency=car_cfg.get("brake_efficiency", 1.0),
                suspension_factor=car_cfg.get("suspension_factor", 0.0),
                tire=tire,
            )

            driver_cfg = ec.get("driver", {})
            driver = Driver(
                name=driver_cfg.get("name", "Driver"),
                experience=driver_cfg.get("experience", 5.0),
                aggressiveness=driver_cfg.get("aggressiveness", 0.5),
            )

            entrants.append(Entrant(driver=driver, car=car))

        return entrants


def _default_entrants() -> list[Entrant]:
    """
    Three-entrant default field with tight car tradeoffs:
      Mercedes = balanced aero, best brakes, DRY tires
      Red Bull = slight downforce edge but more drag, INTERMEDIATE tires
      McLaren  = lowest drag / highest top speed but less downforce, WET tires
    Tire mu values are calibrated so the per-lap gap between compounds
    is within 1-2 standard deviations of stochastic driver noise, ensuring
    probabilistic rather than deterministic outcomes.
    """
    return [
        Entrant(
            driver=Driver(name="Hamilton", experience=9.0, aggressiveness=0.7),
            car=RaceCar(
                name="Mercedes", mass=798.0, cd=0.90, cl=1.55, frontal_area=1.5,
                max_accel=5.9, max_brake=8.3, top_speed=89.0,
                brake_efficiency=1.0, suspension_factor=0.02,
                tire=Tire(compound="DRY", mu_dry=1.04, mu_wet=0.88),
            ),
        ),
        Entrant(
            driver=Driver(name="Verstappen", experience=8.5, aggressiveness=0.85),
            car=RaceCar(
                name="Red Bull", mass=798.0, cd=0.92, cl=1.58, frontal_area=1.5,
                max_accel=5.9, max_brake=8.2, top_speed=88.5,
                brake_efficiency=0.98, suspension_factor=0.01,
                tire=Tire(compound="INTERMEDIATE", mu_dry=1.02, mu_wet=0.93),
            ),
        ),
        Entrant(
            driver=Driver(name="Norris", experience=6.0, aggressiveness=0.75),
            car=RaceCar(
                name="McLaren", mass=798.0, cd=0.88, cl=1.52, frontal_area=1.5,
                max_accel=5.9, max_brake=8.1, top_speed=89.5,
                brake_efficiency=0.99, suspension_factor=0.0,
                tire=Tire(compound="WET", mu_dry=1.00, mu_wet=0.97),
            ),
        ),
    ]


def validate_config(config: SimConfig) -> list[str]:
    """Returns a list of validation error messages (empty if valid)."""
    errors = []
    if config.num_laps < 1:
        errors.append("num_laps must be >= 1")
    if config.num_trials < 1:
        errors.append("num_trials must be >= 1")
    if config.track_num_pairs < 1:
        errors.append("track_num_pairs must be >= 1")
    if config.env_wetness is not None and not (0.0 <= config.env_wetness <= 1.0):
        errors.append("env_wetness must be in [0, 1]")
    if config.env_visibility is not None and not (0.0 <= config.env_visibility <= 1.0):
        errors.append("env_visibility must be in [0, 1]")

    for i, ec in enumerate(config.entrants_config):
        driver_cfg = ec.get("driver", {})
        exp = driver_cfg.get("experience", 5.0)
        if not (0.0 <= exp <= 10.0):
            errors.append(f"Entrant {i}: experience must be in [0, 10]")
        agg = driver_cfg.get("aggressiveness", 0.5)
        if not (0.0 <= agg <= 1.0):
            errors.append(f"Entrant {i}: aggressiveness must be in [0, 1]")
        car_cfg = ec.get("car", {})
        mass = car_cfg.get("mass", 800.0)
        if mass <= 0:
            errors.append(f"Entrant {i}: mass must be > 0")
        tire_cfg = ec.get("tire", {})
        mu_dry = tire_cfg.get("mu_dry", 1.05)
        mu_wet = tire_cfg.get("mu_wet", 0.80)
        if mu_dry <= 0 or mu_wet <= 0:
            errors.append(f"Entrant {i}: mu values must be > 0")

    return errors


def load_config_from_json(path: str | Path) -> SimConfig:
    """Parse a JSON config file into a typed `SimConfig` instance."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    track_cfg = data.get("track", {})
    env_cfg = data.get("environment", {})

    config = SimConfig(
        run_id=data.get("run_id", "001"),
        description=data.get("description", ""),
        random_seed=data.get("random_seed"),
        num_laps=data.get("num_laps", 5),
        num_trials=data.get("num_trials", 200),
        collect_detail=data.get("collect_detail", True),
        track_name=track_cfg.get("name", "Generated Track"),
        track_num_pairs=track_cfg.get("num_pairs", 6),
        track_straight_range=tuple(track_cfg.get("straight_range", [100.0, 250.0])),
        track_corner_radius_range=tuple(track_cfg.get("corner_radius_range", [25.0, 90.0])),
        track_corner_arc_range_deg=tuple(track_cfg.get("corner_arc_range_deg", [45.0, 135.0])),
        env_weather=env_cfg.get("weather"),
        env_wetness=env_cfg.get("wetness"),
        env_visibility=env_cfg.get("visibility"),
        entrants_config=data.get("entrants", []),
    )

    return config


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line flags used by `main.py`."""
    parser = argparse.ArgumentParser(
        description="Stochastic Motorsport Performance Simulator"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to a single JSON configuration file",
    )
    parser.add_argument(
        "--run-all", action="store_true",
        help="Run every .json config in the configs/ directory sequentially",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed override")
    parser.add_argument("--num-laps", type=int, default=None)
    parser.add_argument("--num-trials", type=int, default=None)
    parser.add_argument("--run-id", type=str, default=None)
    return parser.parse_args()


def build_configs_from_cli(args: argparse.Namespace) -> list[SimConfig]:
    """Return one or more SimConfig objects based on CLI arguments."""
    if args.run_all:
        configs_dir = Path("configs")
        if not configs_dir.exists():
            raise FileNotFoundError("configs/ directory not found")
        config_files = sorted(configs_dir.glob("*.json"))
        if not config_files:
            raise FileNotFoundError("No .json files found in configs/")
        configs = []
        for cf in config_files:
            config = load_config_from_json(cf)
            _apply_cli_overrides(config, args)
            configs.append(config)
        return configs

    if args.config:
        config = load_config_from_json(args.config)
    else:
        config = SimConfig()

    _apply_cli_overrides(config, args)
    return [config]


def _apply_cli_overrides(config: SimConfig, args: argparse.Namespace) -> None:
    """Apply optional CLI overrides after loading defaults/JSON."""
    if args.seed is not None:
        config.random_seed = args.seed
    if args.num_laps is not None:
        config.num_laps = args.num_laps
    if args.num_trials is not None:
        config.num_trials = args.num_trials
    if args.run_id is not None:
        config.run_id = args.run_id
