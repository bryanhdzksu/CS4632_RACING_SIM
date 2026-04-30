"""Shared metrics dataclasses and simple statistics helpers."""

from dataclasses import dataclass, field


@dataclass
class EntrantMetrics:
    name: str
    avg_time: float = 0.0
    std_time: float = 0.0
    min_time: float = 0.0
    max_time: float = 0.0
    wins: int = 0
    win_prob: float = 0.0
    all_times: list[float] = field(default_factory=list)


@dataclass
class RaceMetrics:
    entrant_metrics: list[EntrantMetrics] = field(default_factory=list)
    num_trials: int = 0


def mean(values: list[float]) -> float:
    """Population mean helper used throughout simulation summaries."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def stddev(values: list[float]) -> float:
    """Population standard deviation (not sample-corrected)."""
    if not values:
        return 0.0
    m = mean(values)
    var = sum((x - m) ** 2 for x in values) / len(values)
    return var ** 0.5
