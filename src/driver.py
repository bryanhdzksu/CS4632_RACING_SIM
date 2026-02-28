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
        Explicitly addresses M1 feedback:
        sigma = sigma_base / (1 + k * experience)
        """
        return self.sigma_base / (1.0 + self.sigma_k * self.experience)