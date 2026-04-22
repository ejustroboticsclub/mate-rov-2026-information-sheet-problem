from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

try:
    from .domain_data_classes import GeoPoint, Iceberg, ThreatLevel
    from .logic import analyze_platforms
except ImportError:  # running as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from information_sheet_problem.domain_data_classes import GeoPoint, Iceberg, ThreatLevel
    from information_sheet_problem.logic import analyze_platforms

__all__ = (
    "Iceberg",
    "GeoPoint",
    "ThreatLevel",
    "analyze_platforms",
    "save_generated_image",
)

_DEFAULT_PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000000020001e221bc330000000049454e44ae426082"
)


def _extract_png_bytes(rendered_map: object) -> bytes:
    for attr in ("png_bytes", "image_bytes", "bytes", "data"):
        value = getattr(rendered_map, attr, None)
        if isinstance(value, bytes) and value:
            return value
    return _DEFAULT_PNG_BYTES


def save_generated_image(image_bytes: bytes, output_dir: Path | None = None) -> Path:
    directory = output_dir or (Path.cwd() / "generated")
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    image_path = directory / f"{timestamp}.png"
    image_path.write_bytes(image_bytes)
    return image_path


def _demo_save_image() -> Path:
    example_iceberg = Iceberg(location=GeoPoint(47.65, -48.62), heading_degrees=158, keel_depth=99)
    result = analyze_platforms(example_iceberg)
    image_bytes = _extract_png_bytes(result.rendered_map)
    return save_generated_image(image_bytes)


if __name__ == "__main__":
    path = _demo_save_image()
    print(f"Image saved to: {path}")
