"""Entrant abstraction.

An entrant is the race-level unit used throughout simulation and reporting.
It bundles a `Driver` and `RaceCar` so downstream code can treat each
competitor as a single object.
"""

from dataclasses import dataclass

from src.car import RaceCar
from src.driver import Driver


@dataclass
class Entrant:
    """Pairs a driver with a car for a race entry."""
    driver: Driver
    car: RaceCar

    @property
    def name(self) -> str:
        return f"{self.driver.name} ({self.car.name})"
