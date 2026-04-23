import math

from information_sheet_problem.domain_data_classes import (
    AnalysisResult,
    GeoPoint,
    Iceberg,
    MapOverlay,
    Platform,
    PlatformThreatResult,
    RenderedMap,
    ThreatLevel,
    Track,
)

DEFAULT_PLATFORMS: list[Platform] = [
    Platform("Hibernia", GeoPoint(46.7504, -48.7819), 78),
    Platform("Sea Rose", GeoPoint(46.7895, -48.1417), 107),
    Platform("Terra Nova", GeoPoint(46.4, -48.4), 91),
    Platform("Hebron", GeoPoint(46.544, -48.498), 93),
]


def heading_to_unit_vector(heading_degrees: float) -> tuple[float, float]:
    """Convert heading (degrees) to a 2D unit vector."""
    heading_radians = math.radians(heading_degrees)
    dx = math.sin(heading_radians)
    dy = math.cos(heading_radians)
    return (dx, dy)


def distance_nm(a: GeoPoint, b: GeoPoint) -> float:
    """Approximate distance in nautical miles (1 minute latitude = 1 NM)."""
    mean_lat_rad = math.radians((a.latitude + b.latitude) / 2.0)

    delta_lat_nm = (b.latitude - a.latitude) * 60.0
    delta_lon_nm = (b.longitude - a.longitude) * 60.0 * math.cos(mean_lat_rad)

    return math.hypot(delta_lon_nm, delta_lat_nm)


def distance_point_to_track_nm(
    point: GeoPoint,
    track: Track,
) -> float:
    """
    Minimum distance (nautical miles) from a platform to iceberg path.
    """
    mean_lat_rad = math.radians((track.origin.latitude + point.latitude) / 2.0)

    x = (point.longitude - track.origin.longitude) * 60.0 * math.cos(mean_lat_rad)
    y = (point.latitude - track.origin.latitude) * 60.0

    dx, dy = heading_to_unit_vector(track.heading_degrees)

    proj = x * dx + y * dy
    perp_x = x - proj * dx
    perp_y = y - proj * dy

    return math.hypot(perp_x, perp_y)


def intersects_within_radius_nm(
    point: GeoPoint,
    track: Track,
    radius_nm: float,
) -> bool:
    """Whether iceberg track passes within radius of point."""
    distance = distance_point_to_track_nm(point, track)
    return distance <= radius_nm


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
    if keel_depth >= 1.1 * water_depth:
        return ThreatLevel.GREEN

    if distance_nm < 5.0:
        return ThreatLevel.RED
    if distance_nm <= 10.0:
        return ThreatLevel.YELLOW
    return ThreatLevel.GREEN


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
    if not intersects:
        return ThreatLevel.GREEN

    ratio_percent = (keel_depth / water_depth) * 100.0

    if ratio_percent >= 110.0:
        return ThreatLevel.GREEN
    if ratio_percent >= 90.0:
        return ThreatLevel.RED
    if ratio_percent >= 70.0:
        return ThreatLevel.YELLOW
    return ThreatLevel.GREEN


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
    track = Track(origin=iceberg.location, heading_degrees=iceberg.heading_degrees)

    results: list[PlatformThreatResult] = []
    for platform in platforms:
        distance = distance_point_to_track_nm(platform.location, track)
        surface = evaluate_surface_threat(
            distance, iceberg.keel_depth, platform.water_depth
        )

        # Subsea assets: only consider threats within 25 NM
        intersects = intersects_within_radius_nm(
            platform.location, track, radius_nm=25.0
        )
        subsea = evaluate_subsea_threat(
            intersects, iceberg.keel_depth, platform.water_depth
        )

        results.append(
            PlatformThreatResult(
                platform=platform,
                surface_threat=surface,
                subsea_threat=subsea,
            )
        )

    overlay = build_map_overlay(iceberg, platforms)
    rendered = render_map(overlay)

    return AnalysisResult(results=results, overlay=overlay, rendered_map=rendered)


def build_map_overlay(
    iceberg: Iceberg,
    platforms: list[Platform],
) -> MapOverlay:
    """
    Returns drawable data (NOT an image).
    GUI layer decides how to render.
    """
    dx, dy = heading_to_unit_vector(iceberg.heading_degrees)

    projection_nm = 20.0
    nm_per_degree = 60.0

    delta_lat_deg = (dy * projection_nm) / nm_per_degree
    mean_lat = math.radians(iceberg.location.latitude)
    delta_lon_deg = (dx * projection_nm) / (nm_per_degree * math.cos(mean_lat))

    start = iceberg.location
    projected = GeoPoint(
        latitude=start.latitude + delta_lat_deg,
        longitude=start.longitude + delta_lon_deg,
    )

    return MapOverlay(
        iceberg_track=(start, projected),
        platform_points=platforms,
    )


def render_map(overlay: MapOverlay) -> RenderedMap:
    """
    Converts overlay into an image (PNG bytes).

    No displaying, no saving to disk.
    """
    return RenderedMap()


def analyze_iceberg(
    lat_degrees: int,
    lat_minutes: int,
    lat_seconds: int,
    lat_hemisphere: str,
    lon_degrees: int,
    lon_minutes: int,
    lon_seconds: int,
    lon_hemisphere: str,
    heading_degrees: float,
    keel_depth: float,
    platforms: list[Platform] = DEFAULT_PLATFORMS,
) -> AnalysisResult:
    """
    Exported main analysis function using DMS coordinates.
    """
    def _dms_to_decimal(deg: int, mins: int, secs: int, hem: str) -> float:
        val = deg + mins / 60.0 + secs / 3600.0
        if hem.upper() in {"S", "W"}:
            return -val
        return val

    lat = _dms_to_decimal(lat_degrees, lat_minutes, lat_seconds, lat_hemisphere)
    lon = _dms_to_decimal(lon_degrees, lon_minutes, lon_seconds, lon_hemisphere)

    iceberg = Iceberg(
        location=GeoPoint(latitude=lat, longitude=lon),
        heading_degrees=heading_degrees,
        keel_depth=keel_depth,
    )

    return analyze_platforms(iceberg, platforms=platforms)
