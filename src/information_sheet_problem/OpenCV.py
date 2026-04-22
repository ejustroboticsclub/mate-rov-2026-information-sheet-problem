import math
from collections.abc import Iterable
from dataclasses import dataclass

import cv2
import numpy as np
from pyproj import CRS, Transformer


@dataclass(frozen=True)
class GeoPoint:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Platform:
    name: str
    location: GeoPoint


@dataclass(frozen=True)
class Track:
    origin: GeoPoint
    heading_degrees: float  # bearing: 0=N, 90=E clockwise (true bearing)


def dms_to_decimal(deg: int, minutes: int, seconds: float = 0.0, hemi: str = "N") -> float:
    v = abs(deg) + minutes / 60.0 + seconds / 3600.0
    if hemi.upper() in ("S", "W"):
        v = -v
    return v


def format_deg_min(value: float, is_lat: bool) -> str:
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


def heading_to_unit_vector_bearing(bearing_deg: float) -> tuple[float, float]:
    """
    Unit direction in local EN (East, North) coordinates.
    0°=North, 90°=East, clockwise.
    """
    r = math.radians(bearing_deg % 360.0)
    return math.sin(r), math.cos(r)  # (E, N)


def clip_infinite_line_to_rect(
    p0: tuple[float, float],
    v: tuple[float, float],
    rect: tuple[float, float, float, float],
    eps: float = 1e-12,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """
    Clip infinite line p(t)=p0+t*v to rectangle (xmin,ymin,xmax,ymax).
    Returns two points on the rectangle boundary (entry/exit) or None.
    """
    x0, y0 = p0
    vx, vy = v
    xmin, ymin, xmax, ymax = rect
    pts = []

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

    # Dedup
    uniq = []
    for p in pts:
        if not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 for q in uniq):
            uniq.append(p)

    if len(uniq) < 2:
        return None

    # Choose farthest pair
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


def put_rotated_text_right(
    img: np.ndarray,
    text: str,
    anchor_xy: tuple[int, int],
    font=cv2.FONT_HERSHEY_SIMPLEX,
    font_scale: float = 0.45,
    thickness: int = 1,
    color: tuple[int, int, int] = (0, 0, 0),
) -> None:
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


def draw_pdf_style_map_precise(
    track: Track,
    platforms: Iterable[Platform],
    image_size: tuple[int, int] = (900, 1200),  # (width, height)
    padding_px: int = 70,
    grid_step_minutes: int = 30,
    bounds_deg: tuple[float, float, float, float] = (46.0, 48.0, -49.5, -47.5),  # lat_min, lat_max, lon_min, lon_max
    subtle_nw_gradient: bool = True,
    # Use UTM 22N (covers Newfoundland area well)
    crs_projected: CRS = CRS.from_epsg(32622),
) -> np.ndarray:
    """
    High-precision rendering:
      - lat/lon -> UTM meters using pyproj (WGS84 ellipsoid)
      - track direction uses bearing converted to EN vector in meters
      - clip infinite line in meter coordinates
      - map meters -> pixels

    This eliminates the "degrees approximation" used in equirectangular/cos(lat) methods.
    """
    width, height = image_size
    lat_min, lat_max, lon_min, lon_max = bounds_deg
    plats = list(platforms)

    # Background
    img = np.full((height, width, 3), 255, dtype=np.uint8)
    if subtle_nw_gradient:
        yy = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
        xx = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
        w = ((1.0 - yy) + (1.0 - xx)) / 2.0
        shade = (255 - (w * 10)).clip(245, 255).astype(np.uint8)
        img[:, :, 0] = shade
        img[:, :, 1] = shade
        img[:, :, 2] = shade

    # CRS transforms
    crs_geo = CRS.from_epsg(4326)  # lon/lat WGS84
    to_m = Transformer.from_crs(crs_geo, crs_projected, always_xy=True)   # (lon,lat)->(E,N)
    to_geo = Transformer.from_crs(crs_projected, crs_geo, always_xy=True) # (E,N)->(lon,lat) if needed

    # Project the bounds corners to meters
    # We compute xmin/xmax/ymin/ymax in projected space using the 4 corners.
    corners = [
        (lon_min, lat_min),
        (lon_min, lat_max),
        (lon_max, lat_min),
        (lon_max, lat_max),
    ]
    EN = [to_m.transform(lon, lat) for lon, lat in corners]
    xs = [e for e, n in EN]
    ys = [n for e, n in EN]
    xmin_m, xmax_m = min(xs), max(xs)
    ymin_m, ymax_m = min(ys), max(ys)

    # Pixel transform (Easting->x, Northing->y)
    def to_px_from_m(E: float, N: float) -> tuple[int, int]:
        x = padding_px + (E - xmin_m) / (xmax_m - xmin_m) * (width - 2 * padding_px)
        y = padding_px + (ymax_m - N) / (ymax_m - ymin_m) * (height - 2 * padding_px)
        return int(round(x)), int(round(y))

    # Grid lines (still defined in degrees/minutes, but drawn precisely via projection)
    grid_step_deg = grid_step_minutes / 60.0
    grid_color = (120, 120, 120)
    font = cv2.FONT_HERSHEY_SIMPLEX

    left = padding_px
    right = width - padding_px
    top = padding_px
    bottom = height - padding_px
    cv2.rectangle(img, (left, top), (right, bottom), (0, 0, 0), 1)

    def floor_to_step(v: float, step: float) -> float:
        return math.floor(v / step) * step

    # vertical lon lines
    lon = floor_to_step(lon_min, grid_step_deg)
    while lon <= lon_max + 1e-12:
        # draw line by sampling two lat endpoints and projecting
        E1, N1 = to_m.transform(lon, lat_min)
        E2, N2 = to_m.transform(lon, lat_max)
        p1 = to_px_from_m(E1, N1)
        p2 = to_px_from_m(E2, N2)
        cv2.line(img, p1, p2, grid_color, 1)

        label = format_deg_min(lon, is_lat=False)
        (tw, th), _ = cv2.getTextSize(label, font, 0.45, 1)
        # place at top endpoint
        cv2.putText(img, label, (p2[0] - tw // 2, top - 12), font, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        lon += grid_step_deg

    # horizontal lat lines
    lat = floor_to_step(lat_min, grid_step_deg)
    while lat <= lat_max + 1e-12:
        E1, N1 = to_m.transform(lon_min, lat)
        E2, N2 = to_m.transform(lon_max, lat)
        p1 = to_px_from_m(E1, N1)
        p2 = to_px_from_m(E2, N2)
        cv2.line(img, p1, p2, grid_color, 1)

        label = format_deg_min(lat, is_lat=True)
        # right-side rotated label near right boundary at the lat line
        # anchor near the right end point
        put_rotated_text_right(img, label, (right + 8, p2[1] - 20), font_scale=0.45, thickness=1)

        lat += grid_step_deg

    # Track line (precise in meters)
    E0, N0 = to_m.transform(track.origin.longitude, track.origin.latitude)
    dx_e, dy_n = heading_to_unit_vector_bearing(track.heading_degrees)  # unit EN
    # Direction in meters (unit vector is fine; scale cancels in clipping)
    vx, vy = dx_e, dy_n

    clipped = clip_infinite_line_to_rect(
        (E0, N0),
        (vx, vy),
        (xmin_m, ymin_m, xmax_m, ymax_m),
    )
    if clipped:
        (Ea, Na), (Eb, Nb) = clipped
        p0 = to_px_from_m(Ea, Na)
        p1 = to_px_from_m(Eb, Nb)
        cv2.line(img, p0, p1, (0, 0, 0), 2)

    # Origin marker A
    ox, oy = to_px_from_m(E0, N0)
    cv2.circle(img, (ox, oy), 6, (0, 0, 0), -1)
    cv2.putText(img, "A", (ox - 14, oy - 12), font, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

    # Platforms
    for p in plats:
        E, N = to_m.transform(p.location.longitude, p.location.latitude)
        px, py = to_px_from_m(E, N)
        cv2.circle(img, (px, py), 6, (0, 0, 0), 2)
        cv2.putText(img, p.name, (px + 10, py + 5), font, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

    return img


if __name__ == "__main__":
    origin = GeoPoint(
        dms_to_decimal(47, 53, 0, "N"),
        dms_to_decimal(47, 51, 0, "W"),
    )

    platforms = [
        Platform("Hibernia", GeoPoint(46.7504, -48.7819)),
        Platform("Sea Rose", GeoPoint(46.7895, -48.1417)),
        Platform("Terra Nova", GeoPoint(46.4, -48.4)),
        Platform("Hebron", GeoPoint(46.544, -48.498)),
    ]

    track = Track(origin=origin, heading_degrees=188.0)

    img = draw_pdf_style_map_precise(track, platforms)
    cv2.imwrite("map.png", img)