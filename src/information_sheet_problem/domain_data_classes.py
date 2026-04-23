from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True)
class GeoPoint:
    latitude: float  # decimal degrees
    longitude: float  # decimal degrees


@dataclass(frozen=True)
class Platform:
    name: str
    location: GeoPoint
    water_depth: float  # meters


@dataclass(frozen=True)
class Iceberg:
    location: GeoPoint
    heading_degrees: float
    keel_depth: float  # meters


@dataclass(frozen=True)
class Track:
    origin: GeoPoint
    heading_degrees: float


@dataclass(frozen=True)
class PlatformThreatResult:
    platform: Platform
    surface_threat: ThreatLevel
    subsea_threat: ThreatLevel


@dataclass(frozen=True)
class MapOverlay:
    iceberg_track: tuple[GeoPoint, GeoPoint]  # start + projected point
    platform_points: list[Platform]


@dataclass(frozen=True)
class RenderedMap:
    """A map rendered as PNG bytes"""

    png_bytes: bytes | None = None


@dataclass(frozen=True)
class AnalysisResult:
    results: list[PlatformThreatResult]
    overlay: MapOverlay
    rendered_map: RenderedMap
