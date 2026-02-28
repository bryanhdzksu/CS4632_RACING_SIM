from dataclasses import dataclass


@dataclass
class RaceMetrics:
    avg_time_a: float
    avg_time_b: float
    std_time_a: float
    std_time_b: float
    win_prob_a: float
    win_prob_b: float
    wins_a: int
    wins_b: int


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    m = mean(values)
    var = sum((x - m) ** 2 for x in values) / len(values)
    return var ** 0.5