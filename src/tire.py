from dataclasses import dataclass


@dataclass
class Tire:
    compound: str  # "DRY", "WET", or "INTERMEDIATE"
    mu_dry: float
    mu_wet: float

    def mu_effective(self, wetness: float, suspension_factor: float = 0.0) -> float:
        """
        Effective friction using smoothstep blending for a more gradual
        grip transition across the wetness range.  The S-curve widens the
        crossover zone so that tire compound choice is competitive across
        a broader band of conditions rather than producing binary outcomes.
        """
        wetness = max(0.0, min(1.0, wetness))
        t = wetness * wetness * (3.0 - 2.0 * wetness)
        base_mu = (1.0 - t) * self.mu_dry + t * self.mu_wet
        return max(0.1, base_mu * (1.0 + suspension_factor))
