from dataclasses import dataclass


@dataclass
class Tire:
    compound: str  # "DRY" or "WET"
    mu_dry: float
    mu_wet: float

    def mu_effective(self, wetness: float, suspension_factor: float = 0.0) -> float:
        """
        Effective friction based on wetness and a small suspension multiplier.
        wetness in [0, 1]
        suspension_factor is a small tuning value, e.g. -0.05 to +0.05
        """
        wetness = max(0.0, min(1.0, wetness))
        base_mu = (1.0 - wetness) * self.mu_dry + wetness * self.mu_wet
        return max(0.1, base_mu * (1.0 + suspension_factor))

        