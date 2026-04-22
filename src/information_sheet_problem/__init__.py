import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

EARTH_RADIUS_M = 6_371_000.0
M_PER_NM = 1852.0

class ThreatLevel(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

@dataclass(frozen=True)
class GeoPoint:
    latitude: float   # decimal degrees
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
    keel_depth: float

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
    png_bytes: bytes
    """TODO: should probably be a numpy image with fixed shape"""

@dataclass(frozen=True)
class AnalysisResult:
    results: list[PlatformThreatResult]
    overlay: MapOverlay
    rendered_map: RenderedMap


def _require_float(
    data: Mapping[str, object],
    key: str,
    *,
    context: str,
) -> float:
    value = data.get(key)
    if value is None:
        raise ValueError(f"missing required field '{key}' in {context}")
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"field '{key}' in {context} must be numeric")
    return float(value)


def _parse_geo_point_from_mapping(
    data: Mapping[str, object],
    *,
    context: str,
) -> GeoPoint:
    if "location" in data:
        location = data.get("location")
        if not isinstance(location, Mapping):
            raise ValueError(f"field 'location' in {context} must be an object")
        return _parse_geo_point_from_mapping(location, context=f"{context}.location")

    latitude = _require_float(data, "latitude", context=context)
    longitude = _require_float(data, "longitude", context=context)
    return GeoPoint(latitude=latitude, longitude=longitude)


def _parse_iceberg_from_mapping(data: Mapping[str, object]) -> Iceberg:
    location = _parse_geo_point_from_mapping(data, context="iceberg")
    heading_degrees = _require_float(data, "heading_degrees", context="iceberg")
    keel_depth = _require_float(data, "keel_depth", context="iceberg")
    return Iceberg(
        location=location,
        heading_degrees=heading_degrees,
        keel_depth=keel_depth,
    )


def _parse_platform_from_mapping(
    data: Mapping[str, object],
    *,
    index: int,
) -> Platform:
    context = f"platforms[{index}]"
    name = data.get("name")
    if name is None:
        raise ValueError(f"missing required field 'name' in {context}")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"field 'name' in {context} must be a non-empty string")

    location = _parse_geo_point_from_mapping(data, context=context)
    water_depth = _require_float(data, "water_depth", context=context)
    return Platform(name=name, location=location, water_depth=water_depth)


def analyze_platforms_from_runtime_data(
    iceberg_data: Mapping[str, object],
    platforms_data: Sequence[Mapping[str, object]] | None = None,
) -> AnalysisResult:
    """
    Analyze threat levels using plain runtime data structures.

    Expected iceberg shape:
      {"latitude": float, "longitude": float, "heading_degrees": float, "keel_depth": float}
    or:
      {"location": {"latitude": float, "longitude": float}, "heading_degrees": float, "keel_depth": float}

    Expected platform shape:
      {"name": str, "latitude": float, "longitude": float, "water_depth": float}
    or:
      {"name": str, "location": {"latitude": float, "longitude": float}, "water_depth": float}
    """
    iceberg = _parse_iceberg_from_mapping(iceberg_data)
    if platforms_data is None:
        platforms = DEFAULT_PLATFORMS
    else:
        platforms = [
            _parse_platform_from_mapping(platform_data, index=i)
            for i, platform_data in enumerate(platforms_data)
        ]
    return analyze_platforms(iceberg=iceberg, platforms=platforms)


def heading_to_unit_vector(heading_degrees: float) -> tuple[float, float]:
    """Convert heading (degrees) to a 2D unit vector."""
    heading_radians = math.radians(heading_degrees)
    dx = math.sin(heading_radians)
    dy = math.cos(heading_radians)
    return (dx, dy)
    raise NotImplementedError("TODO")

def distance_nm(a: GeoPoint, b: GeoPoint) -> float:
    """Approximate distance in nautical miles."""
    mean_lat_rad = math.radians((a.latitude + b.latitude) / 2.0)

    delta_lat_nm = (b.latitude - a.latitude) * 60.0
    delta_lon_nm = (b.longitude - a.longitude) * 60.0 * math.cos(mean_lat_rad)

    return math.hypot(delta_lon_nm, delta_lat_nm)

    raise NotImplementedError("TODO")

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

    raise NotImplementedError("TODO")

def intersects_within_radius_nm(
    point: GeoPoint,
    track: Track,
    radius_nm: float,
) -> bool:
    """Whether iceberg track passes within radius of point."""
    distance = distance_point_to_track_nm(point, track)
    return distance <= radius_nm

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
    if keel_depth >= 1.1 * water_depth:
        return ThreatLevel.GREEN

    if distance_nm < 5.0:
        return ThreatLevel.RED
    if distance_nm <= 10.0:
        return ThreatLevel.YELLOW
    return ThreatLevel.GREEN

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
    raise NotImplementedError("TODO")

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
    """Format decimal degrees as degrees+minutes with hemisphere (e.g., 48°37'W)."""
    hemi = "N" if is_lat else "E"
    if value < 0:
        hemi = "S" if is_lat else "W"

    a = abs(value)
    deg = int(a)
    minutes = int(round((a - deg) * 60.0))
    if minutes == 60:
        deg += 1
        minutes = 0
    return f"{deg}°{minutes:02d}'{hemi}"


def _clip_infinite_line_to_rect(
    p0: tuple[float, float],
    v: tuple[float, float],
    rect: tuple[float, float, float, float],
    eps: float = 1e-12,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """
    Clip infinite line p(t)=p0+t*v to axis-aligned rectangle (xmin, ymin, xmax, ymax).
    Returns two boundary points (entry/exit) or None if no intersection.
    """
    x0, y0 = p0
    vx, vy = v
    xmin, ymin, xmax, ymax = rect

    pts: list[tuple[float, float]] = []

    if abs(vx) > eps:
        for x in (xmin, xmax):
            t = (x - x0) / vx
            y = y0 + t * vy
            if ymin - eps <= y <= ymax + eps:
                pts.append((x, y))

    if abs(vy) > eps:
        for y in (ymin, ymax):
            t = (y - y0) / vy
            x = x0 + t * vx
            if xmin - eps <= x <= xmax + eps:
                pts.append((x, y))

    uniq: list[tuple[float, float]] = []
    for p in pts:
        if not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 for q in uniq):
            uniq.append(p)

    if len(uniq) < 2:
        return None

    # choose farthest pair (ensures full-span segment)
    best = (uniq[0], uniq[1])
    bestd = -1.0
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            dx = uniq[i][0] - uniq[j][0]
            dy = uniq[i][1] - uniq[j][1]
            d = dx * dx + dy * dy
            if d > bestd:
                bestd = d
                best = (uniq[i], uniq[j])
    return best


def _put_rotated_text_right(
    img,
    text: str,
    anchor_xy: tuple[int, int],
    *,
    font,
    font_scale: float = 0.45,
    thickness: int = 1,
    color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Draw 90°-rotated text (OpenCV workaround)."""
    import cv2
    import numpy as np

    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    pad = 4
    canvas = np.full((th + baseline + pad * 2, tw + pad * 2, 3), 255, dtype=np.uint8)
    cv2.putText(canvas, text, (pad, th + pad), font, font_scale, color, thickness, cv2.LINE_AA)
    rotated = cv2.rotate(canvas, cv2.ROTATE_90_COUNTERCLOCKWISE)

    x, y = anchor_xy
    h, w = rotated.shape[:2]
    x2 = min(img.shape[1], x + w)
    y2 = min(img.shape[0], y + h)
    if x >= img.shape[1] or y >= img.shape[0] or x2 <= 0 or y2 <= 0:
        return
    img[y:y2, x:x2] = rotated[0 : (y2 - y), 0 : (x2 - x)]

def render_map(
    overlay: MapOverlay,
    *,
    # PDF-style view window
    lat_min: float = 46.0,
    lat_max: float = 48.0,
    lon_min: float = -49.5,
    lon_max: float = -47.5,
    grid_step_minutes: int = 30,
    image_size: tuple[int, int] = (900, 1200),  # (width, height)
    padding_px: int = 70,
    subtle_nw_gradient: bool = True,
    # If provided, will save PNG to disk (avoid during tests unless you want it)
    save_path: str | None = None,
) -> RenderedMap:
    """
    High-precision renderer using pyproj:

    - Uses WGS84 (EPSG:4326) and projects into UTM 22N (EPSG:32622) which is accurate for Newfoundland.
    - Draws grid lines defined in lat/lon (degrees+minutes) but rendered by projecting endpoints into meters.
    - Draws an infinite track line clipped to the view rectangle in projected meters.

    Dependencies:
      pip install pyproj opencv-python numpy

    Return type note:
      Your current RenderedMap dataclass has no fields; so we return RenderedMap().
      If you want the PNG bytes returned, update RenderedMap to:
          @dataclass(frozen=True)
          class RenderedMap:
              png_bytes: bytes
      then return RenderedMap(png.tobytes()) below.
    """
    import cv2
    import numpy as np
    from pyproj import CRS, Transformer

    width, height = image_size
    grid_step_deg = grid_step_minutes / 60.0
    font = cv2.FONT_HERSHEY_SIMPLEX

    # --- Background (white with subtle NW gradient) ---
    img = np.full((height, width, 3), 255, dtype=np.uint8)
    if subtle_nw_gradient:
        yy = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
        xx = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
        w = ((1.0 - yy) + (1.0 - xx)) / 2.0
        shade = (255 - (w * 10)).clip(245, 255).astype(np.uint8)
        img[:, :, 0] = shade
        img[:, :, 1] = shade
        img[:, :, 2] = shade

    # --- Projection setup (WGS84 -> UTM 22N) ---
    crs_geo = CRS.from_epsg(4326)    # lon/lat WGS84
    crs_utm = CRS.from_epsg(32622)  # UTM zone 22N
    to_m = Transformer.from_crs(crs_geo, crs_utm, always_xy=True)  # (lon,lat)->(E,N)

    # --- Project view bounds into meters (use corners) ---
    corners = [
        (lon_min, lat_min),
        (lon_min, lat_max),
        (lon_max, lat_min),
        (lon_max, lat_max),
    ]
    EN = [to_m.transform(lon, lat) for lon, lat in corners]
    xs = [e for e, _ in EN]
    ys = [n for _, n in EN]
    xmin_m, xmax_m = min(xs), max(xs)
    ymin_m, ymax_m = min(ys), max(ys)

    def to_px_from_m(E: float, N: float) -> tuple[int, int]:
        x = padding_px + (E - xmin_m) / (xmax_m - xmin_m) * (width - 2 * padding_px)
        y = padding_px + (ymax_m - N) / (ymax_m - ymin_m) * (height - 2 * padding_px)
        return int(round(x)), int(round(y))

    # Inner plot rectangle
    left = padding_px
    right = width - padding_px
    top = padding_px
    bottom = height - padding_px
    cv2.rectangle(img, (left, top), (right, bottom), (0, 0, 0), 1)

    def floor_to_step(v: float, step: float) -> float:
        return math.floor(v / step) * step

    # --- Grid: lon lines + top labels ---
    grid_color = (120, 120, 120)
    lon = floor_to_step(lon_min, grid_step_deg)
    while lon <= lon_max + 1e-12:
        E1, N1 = to_m.transform(lon, lat_min)
        E2, N2 = to_m.transform(lon, lat_max)
        p1 = to_px_from_m(E1, N1)
        p2 = to_px_from_m(E2, N2)
        cv2.line(img, p1, p2, grid_color, 1)

        label = _format_deg_min(lon, is_lat=False)
        (tw, _), _ = cv2.getTextSize(label, font, 0.45, 1)
        cv2.putText(img, label, (p2[0] - tw // 2, top - 12), font, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        lon += grid_step_deg

    # --- Grid: lat lines + right rotated labels ---
    lat = floor_to_step(lat_min, grid_step_deg)
    while lat <= lat_max + 1e-12:
        E1, N1 = to_m.transform(lon_min, lat)
        E2, N2 = to_m.transform(lon_max, lat)
        p1 = to_px_from_m(E1, N1)
        p2 = to_px_from_m(E2, N2)
        cv2.line(img, p1, p2, grid_color, 1)

        label = _format_deg_min(lat, is_lat=True)
        _put_rotated_text_right(img, label, (right + 8, p2[1] - 20), font=font, font_scale=0.45, thickness=1)

        lat += grid_step_deg

    # --- Track line: build from overlay's start->end (in projected meters) ---
    track_start, track_end = overlay.iceberg_track
    E0, N0 = to_m.transform(track_start.longitude, track_start.latitude)
    E1, N1 = to_m.transform(track_end.longitude, track_end.latitude)

    vx = E1 - E0
    vy = N1 - N0
    norm = math.hypot(vx, vy)
    if norm > 0:
        vx /= norm
        vy /= norm

        clipped = _clip_infinite_line_to_rect(
            (E0, N0),
            (vx, vy),
            (xmin_m, ymin_m, xmax_m, ymax_m),
        )
        if clipped:
            (Ea, Na), (Eb, Nb) = clipped
            p0 = to_px_from_m(Ea, Na)
            p1 = to_px_from_m(Eb, Nb)
            cv2.line(img, p0, p1, (0, 0, 0), 2)

    # --- Origin marker + label A ---
    ox, oy = to_px_from_m(E0, N0)
    cv2.circle(img, (ox, oy), 6, (0, 0, 0), -1)
    cv2.putText(img, "A", (ox - 14, oy - 12), font, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

    # --- Platforms ---
    for plat in overlay.platform_points:
        E, N = to_m.transform(plat.location.longitude, plat.location.latitude)
        px, py = to_px_from_m(E, N)
        cv2.circle(img, (px, py), 6, (0, 0, 0), 2)
        cv2.putText(img, plat.name, (px + 10, py + 5), font, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

    # Encode PNG (and optionally save)
    ok, png = cv2.imencode(".png", img)
    if ok and save_path is not None:
        with open(save_path, "wb") as f:
            f.write(png.tobytes())

    # Keep compatibility with your current RenderedMap (no fields)
    return RenderedMap(png_bytes=png.tobytes())
