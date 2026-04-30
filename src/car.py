"""Vehicle parameter container used by the simulation engine.

The simulator is intentionally lightweight: instead of a full drivetrain or
suspension model, this dataclass stores calibrated aggregate parameters that
control acceleration, braking, aero behavior, and tire grip interaction.
"""

from dataclasses import dataclass
from src.tire import Tire


@dataclass
class RaceCar:
    name: str
    mass: float  # kg
    cd: float
    cl: float  # positive here means downforce coefficient
    frontal_area: float  # m^2
    max_accel: float  # m/s^2
    max_brake: float  # m/s^2
    top_speed: float  # m/s
    brake_efficiency: float  # multiplier, around 0.9 to 1.1
    suspension_factor: float  # small multiplier, e.g. -0.05 to +0.05
    tire: Tire