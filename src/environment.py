from dataclasses import dataclass
import random


WEATHER_TYPES = ["Sunny", "Cloudy", "Rainy", "Foggy"]


@dataclass
class Environment:
    weather: str
    wetness: float  # in [0, 1]
    visibility: float  # in [0, 1]

    @staticmethod
    def random_environment() -> "Environment":
        """
        For M2: sample wetness once per race and keep it constant for the whole race.
        """
        weather = random.choice(WEATHER_TYPES)

        if weather == "Sunny":
            wetness = random.uniform(0.0, 0.15)
            visibility = random.uniform(0.9, 1.0)
        elif weather == "Cloudy":
            wetness = random.uniform(0.1, 0.35)
            visibility = random.uniform(0.8, 0.95)
        elif weather == "Rainy":
            wetness = random.uniform(0.5, 1.0)
            visibility = random.uniform(0.5, 0.8)
        else:  # Foggy
            wetness = random.uniform(0.2, 0.5)
            visibility = random.uniform(0.3, 0.7)

        return Environment(weather=weather, wetness=wetness, visibility=visibility)