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


DEFAULT_PLATFORMS: list[Platform] = [
    Platform("Hibernia", GeoPoint(46.7504, -48.7819), 78),
    Platform("Sea Rose", GeoPoint(46.7895, -48.1417), 107),
    Platform("Terra Nova", GeoPoint(46.4, -48.4), 91),
    Platform("Hebron", GeoPoint(46.544, -48.498), 93),
]


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
    platform_points: list[GeoPoint]


@dataclass(frozen=True)
class RenderedMap:
    """TODO: should probably be a numpy image with fixed shape"""


@dataclass(frozen=True)
class AnalysisResult:
    results: list[PlatformThreatResult]
    overlay: MapOverlay
    rendered_map: RenderedMap


def heading_to_unit_vector(heading_degrees: float) -> tuple[float, float]:
    """Convert heading (degrees) to a 2D unit vector."""
    raise NotImplementedError("TODO")


def distance_nm(a: GeoPoint, b: GeoPoint) -> float:
    """Approximate distance in nautical miles."""
    raise NotImplementedError("TODO")


def distance_point_to_track_nm(
    point: GeoPoint,
    track: Track,
) -> float:
    """
    Minimum distance (nautical miles) from a platform to iceberg path.
    """
    raise NotImplementedError("TODO")


def intersects_within_radius_nm(
    point: GeoPoint,
    track: Track,
    radius_nm: float,
) -> bool:
    """Whether iceberg track passes within radius of point."""
    raise NotImplementedError("TODO")


def evaluate_surface_threat(
    distance_nm: float,
    keel_depth: float,
    water_depth: float,
) -> ThreatLevel:
    """
    Apply rules:
    - grounding rule
    - distance thresholds (5, 10 nm)
    """
    raise NotImplementedError("TODO")


def evaluate_subsea_threat(
    intersects: bool,
    keel_depth: float,
    water_depth: float,
) -> ThreatLevel:
    """
    Apply % thresholds:
    - >=110% → green
    - 90–110 → red
    - 70–90 → yellow
    - <70 → green
    """
    raise NotImplementedError("TODO")


def analyze_platforms(
    iceberg: Iceberg,
    platforms: list[Platform] = DEFAULT_PLATFORMS,
) -> AnalysisResult:
    """
    Main entry point.

    - builds track
    - computes distances
    - evaluates threats
    - returns structured result
    """
    raise NotImplementedError("TODO")


def build_map_overlay(
    iceberg: Iceberg,
    platforms: list[Platform],
) -> MapOverlay:
    """
    Returns drawable data (NOT an image).
    GUI layer decides how to render.
    """
    raise NotImplementedError("TODO")


def render_map(overlay: MapOverlay) -> RenderedMap:
    """
    Converts overlay into an image (PNG bytes).

    No displaying, no saving to disk.
    """
    raise NotImplementedError("TODO")
