"""Driver behavior model used to inject stochastic race variability."""

from dataclasses import dataclass


@dataclass
class Driver:
    name: str
    experience: float  # suggested range: 1.0 to 10.0
    aggressiveness: float  # suggested range: 0.0 to 1.0
    sigma_base: float = 1.5
    sigma_k: float = 0.2

    def sigma(self) -> float:
        """
        Lower sigma means more consistent lap times.
        sigma = sigma_base / (1 + k * experience)
        """
        # Higher experience lowers sigma, tightening lap-time spread.
        return self.sigma_base / (1.0 + self.sigma_k * self.experience)

    def skill_factor(self) -> float:
        """
        Multiplicative factor on lap time representing overall driver ability.
        Elite driver (exp=10, agg=1.0) -> ~0.972  (2.8% faster)
        Novice driver (exp=1, agg=0.0) -> ~0.9975 (0.25% faster)
        Spread is ~2.5% of lap time, which at 25s/lap is ~0.6s -- enough
        to let a skilled driver in a weaker car remain competitive.
        """
        # Keep effect bounded so driver skill influences outcomes
        # without overwhelming car/tire/environment contributions.
        base = 1.0 - 0.0025 * self.experience
        aggression_bonus = -0.003 * self.aggressiveness
        return max(0.96, min(1.04, base + aggression_bonus))
