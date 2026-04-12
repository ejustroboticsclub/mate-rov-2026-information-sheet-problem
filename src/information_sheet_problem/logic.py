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

def _format_deg_min(value: float, is_lat: bool) -> str:
    """
    Format a decimal degree value as degrees+minutes, with N/S/E/W.
    Example: -48.5 -> 48°30'W
    """
    hemi = "N" if is_lat else "E"
    if value < 0:
        hemi = "S" if is_lat else "W"

    abs_val = abs(value)
    deg = int(abs_val)
    minutes = int(round((abs_val - deg) * 60))

    # handle rounding to 60'
    if minutes == 60:
        deg += 1
        minutes = 0

    return f"{deg}°{minutes:02d}'{hemi}"

def render_map(overlay: MapOverlay) -> RenderedMap:
    """
    Converts overlay into an image (PNG bytes) with:
    - grid (lat/lon)
    - labels in degrees+minutes
    - platform points + labels
    - long track line (mimics infinite line)
    """
    import cv2
    import numpy as np

    # --- configuration ---
    width, height = 1200, 900
    padding_px = 80
    grid_step_deg = 0.5  # 30 minutes grid
    track_length_nm = 80.0
    bg_color_bgr = (210, 120, 0)  # deep blue-ish
    grid_color = (120, 80, 0)
    grid_thickness = 1

    # --- extract data ---
    platforms = overlay.platform_points
    track_start, track_end = overlay.iceberg_track

    # approximate heading from track points
    def _heading_deg(a: GeoPoint, b: GeoPoint) -> float:
        dx = math.sin(math.radians(b.longitude - a.longitude))
        dy = math.cos(math.radians(b.latitude - a.latitude))
        return math.degrees(math.atan2(dx, dy)) % 360

    heading = _heading_deg(track_start, track_end)
    dx, dy = heading_to_unit_vector(heading)

    # --- determine bounds ---
    lats = [p.location.latitude for p in platforms] + [track_start.latitude, track_end.latitude]
    lons = [p.location.longitude for p in platforms] + [track_start.longitude, track_end.longitude]

    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    # expand bounds a bit
    lat_min -= 0.3
    lat_max += 0.3
    lon_min -= 0.3
    lon_max += 0.3

    # --- coordinate transform ---
    def to_px(lat: float, lon: float) -> tuple[int, int]:
        x = padding_px + (lon - lon_min) / (lon_max - lon_min) * (width - 2 * padding_px)
        y = padding_px + (lat_max - lat) / (lat_max - lat_min) * (height - 2 * padding_px)
        return int(round(x)), int(round(y))

    img = np.full((height, width, 3), bg_color_bgr, dtype=np.uint8)

    # --- draw grid (lat lines) ---
    lat_start = math.floor(lat_min / grid_step_deg) * grid_step_deg
    lat = lat_start
    while lat <= lat_max + 1e-9:
        x0, y0 = to_px(lat, lon_min)
        x1, y1 = to_px(lat, lon_max)
        cv2.line(img, (x0, y0), (x1, y1), grid_color, grid_thickness)

        label = _format_deg_min(lat, is_lat=True)
        cv2.putText(img, label, (x1 + 6, y1 + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (240, 240, 240), 1, cv2.LINE_AA)
        lat += grid_step_deg

    # --- draw grid (lon lines) ---
    lon_start = math.floor(lon_min / grid_step_deg) * grid_step_deg
    lon = lon_start
    while lon <= lon_max + 1e-9:
        x0, y0 = to_px(lat_min, lon)
        x1, y1 = to_px(lat_max, lon)
        cv2.line(img, (x0, y0), (x1, y1), grid_color, grid_thickness)

        label = _format_deg_min(lon, is_lat=False)
        cv2.putText(img, label, (x0 - 20, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (240, 240, 240), 1, cv2.LINE_AA)
        lon += grid_step_deg

    # --- draw long track line ---
    nm_per_deg = 60.0
    half = track_length_nm / 2.0
    start_lat = track_start.latitude - (dy * half) / nm_per_deg
    start_lon = track_start.longitude - (dx * half) / (nm_per_deg * math.cos(math.radians(track_start.latitude)))
    end_lat = track_start.latitude + (dy * half) / nm_per_deg
    end_lon = track_start.longitude + (dx * half) / (nm_per_deg * math.cos(math.radians(track_start.latitude)))

    p0 = to_px(start_lat, start_lon)
    p1 = to_px(end_lat, end_lon)
    cv2.line(img, p0, p1, (0, 255, 255), 2)

    # --- draw platforms ---
    for p in platforms:
        px, py = to_px(p.location.latitude, p.location.longitude)
        cv2.circle(img, (px, py), 5, (0, 255, 255), -1)
        cv2.putText(img, p.name, (px + 6, py - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    
    # OPTION A (recommended): save the OpenCV image directly
    cv2.imwrite("rendered_map.png", img)
    
    # return PNG bytes
    ok, png = cv2.imencode(".png", img)
    return RenderedMap(png.tobytes())