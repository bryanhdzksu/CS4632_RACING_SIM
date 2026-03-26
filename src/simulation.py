import math
import random
from dataclasses import dataclass, field

from src.car import RaceCar
from src.driver import Driver
from src.entrant import Entrant
from src.environment import Environment
from src.track import SegmentType, Track, TrackSegment
from src.utils import EntrantMetrics, RaceMetrics, mean, stddev


@dataclass
class SegmentResult:
    segment_idx: int
    segment_type: str
    length: float
    entry_speed: float
    exit_speed: float
    time: float
    mu_effective: float | None = None


@dataclass
class LapResult:
    lap_number: int
    lap_time: float
    segments: list[SegmentResult] = field(default_factory=list)


@dataclass
class EntrantRaceResult:
    entrant_name: str
    total_time: float
    laps: list[LapResult] = field(default_factory=list)


@dataclass
class TrialResult:
    trial_number: int
    results: list[EntrantRaceResult] = field(default_factory=list)

    @property
    def winner(self) -> str:
        if not self.results:
            return ""
        best = min(self.results, key=lambda r: r.total_time)
        return best.entrant_name


class SimulationEngine:
    def __init__(self, air_density: float = 1.225, g: float = 9.81):
        self.air_density = air_density
        self.g = g

    def compute_aero(self, velocity: float, car: RaceCar) -> tuple[float, float]:
        """Returns (drag_force, downforce)."""
        drag_force = 0.5 * self.air_density * velocity**2 * car.cd * car.frontal_area
        downforce = 0.5 * self.air_density * velocity**2 * car.cl * car.frontal_area
        return drag_force, downforce

    def compute_corner_vmax(
        self, segment: TrackSegment, car: RaceCar, env: Environment
    ) -> float:
        if segment.segment_type != SegmentType.CORNER or segment.radius is None:
            raise ValueError("compute_corner_vmax called on a non-corner segment")

        velocity_guess = min(car.top_speed, 25.0)

        for _ in range(4):
            _, downforce = self.compute_aero(velocity_guess, car)
            mu = car.tire.mu_effective(env.wetness, car.suspension_factor)
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

    def _traction_limited_accel(self, car: RaceCar, env: Environment) -> float:
        """
        Straight-line acceleration is limited by whichever is lower:
        the engine's max accel or what the tires can transmit to the road.
        In wet conditions this restricts acceleration meaningfully.
        """
        mu = car.tire.mu_effective(env.wetness, car.suspension_factor)
        traction_accel = mu * self.g
        return min(car.max_accel, traction_accel)

    def _wet_brake_decel(self, car: RaceCar, env: Environment) -> float:
        """
        Braking performance degrades with reduced grip.  At full grip
        (mu >= 1.0) the driver gets full brake efficiency; at mu ~0.5
        braking is roughly 70% effective.
        """
        mu = car.tire.mu_effective(env.wetness, car.suspension_factor)
        grip_factor = min(1.0, 0.4 + 0.6 * mu)
        return max(0.1, car.max_brake * car.brake_efficiency * grip_factor)

    def _visibility_penalty(self, env: Environment) -> float:
        """
        Low visibility adds a small reaction-time overhead per segment,
        simulating reduced driver anticipation in fog or heavy rain.
        """
        return max(0.0, 0.3 * (1.0 - env.visibility))

    def simulate_straight(
        self,
        segment: TrackSegment,
        entry_speed: float,
        next_corner_speed: float | None,
        car: RaceCar,
        env: Environment,
    ) -> tuple[float, float]:
        """
        Simulate a straight with traction-limited acceleration, drag,
        and grip-aware braking if a corner follows.
        Returns (segment_time, exit_speed).
        """
        distance = segment.length
        v = min(entry_speed, car.top_speed)

        drag_force, _ = self.compute_aero(v, car)
        a_eff = max(0.0, self._traction_limited_accel(car, env) - drag_force / car.mass)

        v_no_brake_sq = v**2 + 2.0 * a_eff * distance
        v_no_brake = min(math.sqrt(max(0.0, v_no_brake_sq)), car.top_speed)

        if next_corner_speed is None or v_no_brake <= next_corner_speed:
            avg_v = max(1.0, 0.5 * (v + v_no_brake))
            time = distance / avg_v
            return time, v_no_brake

        decel = self._wet_brake_decel(car, env)
        brake_distance = max(
            0.0,
            (v_no_brake**2 - next_corner_speed**2) / (2.0 * decel),
        )

        if brake_distance >= distance:
            constrained_exit = next_corner_speed
            avg_v = max(1.0, 0.5 * (v + constrained_exit))
            time = distance / avg_v
            return time, constrained_exit

        accel_distance = max(0.0, distance - brake_distance)

        v_peak_sq = v**2 + 2.0 * a_eff * accel_distance
        v_peak = min(math.sqrt(max(0.0, v_peak_sq)), car.top_speed)

        if a_eff > 1e-6:
            t_accel = max(0.0, (v_peak - v) / a_eff)
        else:
            t_accel = accel_distance / max(v, 1.0)

        t_brake = max(0.0, (v_peak - next_corner_speed) / decel)

        return t_accel + t_brake, next_corner_speed

    def simulate_corner(
        self,
        segment: TrackSegment,
        entry_speed: float,
        car: RaceCar,
        env: Environment,
    ) -> tuple[float, float, float]:
        """Returns (segment_time, exit_speed, mu_effective)."""
        vmax = self.compute_corner_vmax(segment, car, env)
        corner_speed = min(entry_speed, vmax)
        mu = car.tire.mu_effective(env.wetness, car.suspension_factor)
        time = segment.length / max(corner_speed, 1.0)
        return time, corner_speed, mu

    def simulate_lap(
        self,
        track: Track,
        env: Environment,
        car: RaceCar,
        driver: Driver,
        lap_number: int = 1,
        collect_detail: bool = False,
    ) -> LapResult:
        total_time = 0.0
        current_speed = 0.0
        segments: list[SegmentResult] = []
        vis_penalty = self._visibility_penalty(env)

        for i, seg in enumerate(track.segments):
            next_corner_speed = None

            if seg.segment_type == SegmentType.STRAIGHT:
                if i + 1 < len(track.segments):
                    next_seg = track.segments[i + 1]
                    if next_seg.segment_type == SegmentType.CORNER:
                        next_corner_speed = self.compute_corner_vmax(
                            next_seg, car, env
                        )

                seg_time, exit_speed = self.simulate_straight(
                    seg, current_speed, next_corner_speed, car, env
                )
                mu_eff = None
            else:
                seg_time, exit_speed, mu_eff = self.simulate_corner(
                    seg, current_speed, car, env
                )

            seg_time += vis_penalty

            if collect_detail:
                segments.append(SegmentResult(
                    segment_idx=i,
                    segment_type=seg.segment_type.value,
                    length=round(seg.length, 3),
                    entry_speed=round(current_speed, 3),
                    exit_speed=round(exit_speed, 3),
                    time=round(seg_time, 5),
                    mu_effective=round(mu_eff, 4) if mu_eff is not None else None,
                ))

            total_time += seg_time
            current_speed = exit_speed

        epsilon = random.gauss(0.0, driver.sigma())
        total_time = total_time * driver.skill_factor() + epsilon
        total_time = max(1.0, total_time)

        return LapResult(
            lap_number=lap_number,
            lap_time=total_time,
            segments=segments,
        )

    def simulate_race(
        self,
        track: Track,
        env: Environment,
        entrants: list[Entrant],
        num_laps: int,
        collect_detail: bool = False,
    ) -> TrialResult:
        race_results: list[EntrantRaceResult] = []

        for entrant in entrants:
            laps: list[LapResult] = []
            total_time = 0.0

            for lap_num in range(1, num_laps + 1):
                lap_result = self.simulate_lap(
                    track, env, entrant.car, entrant.driver,
                    lap_number=lap_num, collect_detail=collect_detail,
                )
                laps.append(lap_result)
                total_time += lap_result.lap_time

            race_results.append(EntrantRaceResult(
                entrant_name=entrant.name,
                total_time=total_time,
                laps=laps,
            ))

        return TrialResult(trial_number=0, results=race_results)

    def run_trials(
        self,
        track: Track,
        env: Environment,
        entrants: list[Entrant],
        num_laps: int,
        num_trials: int,
        collect_detail: bool = False,
    ) -> tuple[RaceMetrics, list[TrialResult]]:
        all_times: dict[str, list[float]] = {e.name: [] for e in entrants}
        win_counts: dict[str, int] = {e.name: 0 for e in entrants}
        all_trial_results: list[TrialResult] = []

        for trial_num in range(1, num_trials + 1):
            trial = self.simulate_race(
                track, env, entrants, num_laps, collect_detail=collect_detail,
            )
            trial.trial_number = trial_num
            all_trial_results.append(trial)

            for result in trial.results:
                all_times[result.entrant_name].append(result.total_time)

            winner = trial.winner
            if winner in win_counts:
                win_counts[winner] += 1

        entrant_metrics = []
        for e in entrants:
            times = all_times[e.name]
            entrant_metrics.append(EntrantMetrics(
                name=e.name,
                avg_time=mean(times),
                std_time=stddev(times),
                min_time=min(times) if times else 0.0,
                max_time=max(times) if times else 0.0,
                wins=win_counts[e.name],
                win_prob=win_counts[e.name] / num_trials if num_trials else 0.0,
                all_times=times,
            ))

        metrics = RaceMetrics(entrant_metrics=entrant_metrics, num_trials=num_trials)
        return metrics, all_trial_results
