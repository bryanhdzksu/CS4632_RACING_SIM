import math
import random
from dataclasses import dataclass

from src.car import RaceCar
from src.driver import Driver
from src.environment import Environment
from src.track import SegmentType, Track, TrackSegment
from src.utils import RaceMetrics, mean, stddev


@dataclass
class TrialResult:
    total_time_a: float
    total_time_b: float
    winner: str


class SimulationEngine:
    def __init__(self, air_density: float = 1.225, g: float = 9.81):
        self.air_density = air_density
        self.g = g

    def compute_aero(self, velocity: float, car: RaceCar) -> tuple[float, float]:
        """
        Returns (drag_force, downforce)
        """
        drag_force = 0.5 * self.air_density * velocity**2 * car.cd * car.frontal_area
        downforce = 0.5 * self.air_density * velocity**2 * car.cl * car.frontal_area
        return drag_force, downforce

    def compute_corner_vmax(
        self, segment: TrackSegment, car: RaceCar, env: Environment
    ) -> float:
        if segment.segment_type != SegmentType.CORNER or segment.radius is None:
            raise ValueError("compute_corner_vmax called on a non-corner segment")

        # First pass estimate with no-speed guess yet; use a small iteration
        velocity_guess = min(car.top_speed, 25.0)

        for _ in range(4):
            _, downforce = self.compute_aero(velocity_guess, car)
            mu = car.tire.mu_effective(env.wetness, car.suspension_factor)
            mu *= 1.0  # explicit placeholder for future tuning
            vmax = math.sqrt(
                max(
                    0.1,
                    mu
                    * segment.radius
                    * (self.g + (downforce / max(car.mass, 1.0))),
                )
            )
            velocity_guess = min(vmax, car.top_speed)

        return min(velocity_guess, car.top_speed)

    def simulate_straight(
        self,
        segment: TrackSegment,
        entry_speed: float,
        next_corner_speed: float | None,
        car: RaceCar,
    ) -> tuple[float, float]:
        """
        Simulate a straight with:
        - acceleration limited by drag + max accel
        - optional braking if a corner follows
        Returns (segment_time, exit_speed)
        """
        distance = segment.length
        v = min(entry_speed, car.top_speed)

        drag_force, _ = self.compute_aero(v, car)
        a_eff = max(0.0, car.max_accel - drag_force / car.mass)

        # Accelerate over the straight
        v_no_brake_sq = v**2 + 2.0 * a_eff * distance
        v_no_brake = min(math.sqrt(max(0.0, v_no_brake_sq)), car.top_speed)

        if next_corner_speed is None or v_no_brake <= next_corner_speed:
            avg_v = max(1.0, 0.5 * (v + v_no_brake))
            time = distance / avg_v
            return time, v_no_brake

        # Braking model for transition into corner
        decel = max(0.1, car.max_brake * car.brake_efficiency)
        brake_distance = max(
            0.0,
            (v_no_brake**2 - next_corner_speed**2) / (2.0 * decel),
        )

        # If braking distance exceeds straight length, cap exit speed harder
        if brake_distance >= distance:
            # Conservative cap
            constrained_exit = next_corner_speed
            avg_v = max(1.0, 0.5 * (v + constrained_exit))
            time = distance / avg_v
            return time, constrained_exit

        # Otherwise accelerate then brake
        accel_distance = max(0.0, distance - brake_distance)

        v_peak_sq = v**2 + 2.0 * a_eff * accel_distance
        v_peak = min(math.sqrt(max(0.0, v_peak_sq)), car.top_speed)

        # Time on acceleration phase
        if a_eff > 1e-6:
            t_accel = max(0.0, (v_peak - v) / a_eff)
        else:
            t_accel = accel_distance / max(v, 1.0)

        # Time on braking phase
        t_brake = max(0.0, (v_peak - next_corner_speed) / decel)

        return t_accel + t_brake, next_corner_speed

    def simulate_corner(
        self,
        segment: TrackSegment,
        entry_speed: float,
        car: RaceCar,
        env: Environment,
    ) -> tuple[float, float]:
        vmax = self.compute_corner_vmax(segment, car, env)
        corner_speed = min(entry_speed, vmax)

        # If somehow entry > vmax, force it down at entry
        corner_speed = min(corner_speed, vmax)

        time = segment.length / max(corner_speed, 1.0)
        return time, corner_speed

    def simulate_lap(
        self,
        track: Track,
        env: Environment,
        car: RaceCar,
        driver: Driver,
    ) -> float:
        total_time = 0.0
        current_speed = 0.0

        for i, seg in enumerate(track.segments):
            next_corner_speed = None

            if seg.segment_type == SegmentType.STRAIGHT:
                # Look ahead to the immediate next segment; if it's a corner, estimate target speed
                if i + 1 < len(track.segments):
                    next_seg = track.segments[i + 1]
                    if next_seg.segment_type == SegmentType.CORNER:
                        next_corner_speed = self.compute_corner_vmax(next_seg, car, env)

                seg_time, current_speed = self.simulate_straight(
                    seg, current_speed, next_corner_speed, car
                )

            else:
                seg_time, current_speed = self.simulate_corner(
                    seg, current_speed, car, env
                )

            total_time += seg_time

        # Stochastic lap time term based on driver experience
        epsilon = random.gauss(0.0, driver.sigma())
        total_time += epsilon

        return max(1.0, total_time)

    def simulate_race(
        self,
        track: Track,
        env: Environment,
        car_a: RaceCar,
        driver_a: Driver,
        car_b: RaceCar,
        driver_b: Driver,
        num_laps: int,
    ) -> TrialResult:
        total_a = 0.0
        total_b = 0.0

        for _ in range(num_laps):
            total_a += self.simulate_lap(track, env, car_a, driver_a)
            total_b += self.simulate_lap(track, env, car_b, driver_b)

        winner = "A" if total_a < total_b else "B"
        return TrialResult(total_time_a=total_a, total_time_b=total_b, winner=winner)

    def run_trials(
        self,
        track: Track,
        env: Environment,
        car_a: RaceCar,
        driver_a: Driver,
        car_b: RaceCar,
        driver_b: Driver,
        num_laps: int,
        num_trials: int,
    ) -> RaceMetrics:
        times_a: list[float] = []
        times_b: list[float] = []
        wins_a = 0
        wins_b = 0

        for _ in range(num_trials):
            result = self.simulate_race(
                track, env, car_a, driver_a, car_b, driver_b, num_laps
            )
            times_a.append(result.total_time_a)
            times_b.append(result.total_time_b)

            if result.winner == "A":
                wins_a += 1
            else:
                wins_b += 1

        return RaceMetrics(
            avg_time_a=mean(times_a),
            avg_time_b=mean(times_b),
            std_time_a=stddev(times_a),
            std_time_b=stddev(times_b),
            win_prob_a=wins_a / num_trials if num_trials else 0.0,
            win_prob_b=wins_b / num_trials if num_trials else 0.0,
            wins_a=wins_a,
            wins_b=wins_b,
        )