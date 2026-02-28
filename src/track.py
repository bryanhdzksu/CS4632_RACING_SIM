from dataclasses import dataclass, field
from enum import Enum
import random


class SegmentType(Enum):
    STRAIGHT = "STRAIGHT"
    CORNER = "CORNER"


@dataclass
class TrackSegment:
    segment_type: SegmentType
    length: float  # meters
    radius: float | None = None  # meters, only for corners


@dataclass
class Track:
    name: str
    segments: list[TrackSegment] = field(default_factory=list)
    surface_grip: float = 1.0

    @staticmethod
    def random_track(
        name: str = "Generated Track",
        num_pairs: int = 4,
        straight_range: tuple[float, float] = (80.0, 200.0),
        corner_radius_range: tuple[float, float] = (20.0, 80.0),
        corner_arc_range_deg: tuple[float, float] = (45.0, 120.0),
    ) -> "Track":
        """
        Generates alternating straight/corner segments.
        num_pairs=4 => 8 total segments.
        Corner length is derived from radius and arc angle.
        """
        segments: list[TrackSegment] = []

        for _ in range(num_pairs):
            straight_length = random.uniform(*straight_range)
            segments.append(
                TrackSegment(segment_type=SegmentType.STRAIGHT, length=straight_length)
            )

            radius = random.uniform(*corner_radius_range)
            arc_deg = random.uniform(*corner_arc_range_deg)
            arc_rad = arc_deg * 3.141592653589793 / 180.0
            corner_length = radius * arc_rad

            segments.append(
                TrackSegment(
                    segment_type=SegmentType.CORNER,
                    length=corner_length,
                    radius=radius,
                )
            )

        return Track(name=name, segments=segments, surface_grip=1.0)

    def total_length(self) -> float:
        return sum(seg.length for seg in self.segments)