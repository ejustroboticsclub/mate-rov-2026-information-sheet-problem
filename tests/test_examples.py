import pytest

from information_sheet_problem import Iceberg
from information_sheet_problem import GeoPoint
from information_sheet_problem import ThreatLevel
from information_sheet_problem import analyze_platforms


# TODO: this is a bit of a hack to convert the DMS coordinates in the PDF examples to decimal degrees. I don't
# think we should be using decimal degrees in the first place but that is the initial design choice that I made so
# we just have to deal with it for now.
def _nmea_like_dms_to_decimal(
    degrees: int, minutes: int, seconds: int, hemisphere: str
) -> float:
    value = degrees + minutes / 60 + seconds / 3600
    if hemisphere in {"S", "W"}:
        return -value
    return value


@pytest.mark.parametrize(
    ("example_name", "iceberg", "expected_surface", "expected_subsea"),
    [
        (
            "A",
            Iceberg(
                location=GeoPoint(
                    _nmea_like_dms_to_decimal(47, 39, 0, "N"),
                    _nmea_like_dms_to_decimal(48, 37, 0, "W"),
                ),
                heading_degrees=158,
                keel_depth=99,
            ),
            {
                "Hibernia": ThreatLevel.GREEN,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.RED,
                "Terra Nova": ThreatLevel.GREEN,
            },
            {
                "Hibernia": ThreatLevel.GREEN,
                "Hebron": ThreatLevel.RED,
                "Sea Rose": ThreatLevel.RED,
                "Terra Nova": ThreatLevel.RED,
            },
        ),
        (
            "B",
            Iceberg(
                location=GeoPoint(
                    _nmea_like_dms_to_decimal(47, 58, 0, "N"),
                    _nmea_like_dms_to_decimal(48, 50, 0, "W"),
                ),
                heading_degrees=180,
                keel_depth=78,
            ),
            {
                "Hibernia": ThreatLevel.RED,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.GREEN,
            },
            {
                "Hibernia": ThreatLevel.RED,
                "Hebron": ThreatLevel.YELLOW,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.YELLOW,
            },
        ),
        (
            "C",
            Iceberg(
                location=GeoPoint(
                    _nmea_like_dms_to_decimal(47, 53, 0, "N"),
                    _nmea_like_dms_to_decimal(47, 51, 0, "W"),
                ),
                heading_degrees=188,
                keel_depth=112,
            ),
            {
                "Hibernia": ThreatLevel.GREEN,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.RED,
                "Terra Nova": ThreatLevel.GREEN,
            },
            {
                "Hibernia": ThreatLevel.GREEN,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.RED,
                "Terra Nova": ThreatLevel.GREEN,
            },
        ),
        (
            "D",
            Iceberg(
                location=GeoPoint(
                    _nmea_like_dms_to_decimal(47, 40, 0, "N"),
                    _nmea_like_dms_to_decimal(49, 25, 0, "W"),
                ),
                heading_degrees=152,
                keel_depth=60,
            ),
            {
                "Hibernia": ThreatLevel.RED,
                "Hebron": ThreatLevel.RED,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.RED,
            },
            {
                "Hibernia": ThreatLevel.YELLOW,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.GREEN,
            },
        ),
        (
            "E",
            Iceberg(
                location=GeoPoint(
                    _nmea_like_dms_to_decimal(47, 45, 0, "N"),
                    _nmea_like_dms_to_decimal(48, 29, 0, "W"),
                ),
                heading_degrees=198,
                keel_depth=84,
            ),
            {
                "Hibernia": ThreatLevel.YELLOW,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.GREEN,
            },
            {
                "Hibernia": ThreatLevel.RED,
                "Hebron": ThreatLevel.RED,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.GREEN,
            },
        ),
        (
            "F",
            Iceberg(
                location=GeoPoint(
                    _nmea_like_dms_to_decimal(47, 56, 0, "N"),
                    _nmea_like_dms_to_decimal(47, 45, 0, "W"),
                ),
                heading_degrees=181,
                keel_depth=126,
            ),
            {
                "Hibernia": ThreatLevel.GREEN,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.GREEN,
            },
            {
                "Hibernia": ThreatLevel.GREEN,
                "Hebron": ThreatLevel.GREEN,
                "Sea Rose": ThreatLevel.GREEN,
                "Terra Nova": ThreatLevel.GREEN,
            },
        ),
    ],
)
def test_analyze_platforms_matches_pdf_examples(
    example_name: str,
    iceberg: Iceberg,
    expected_surface: dict[str, ThreatLevel],
    expected_subsea: dict[str, ThreatLevel],
) -> None:
    """Official examples taken from
    `https://20693798.fs1.hubspotusercontent-na1.net/hubfs/20693798/2026/Supporting%20Documents/Iceberg%20Information%20Examples%20EX%20PN%20RN%20Updated%202_16.pdf`"""

    result = analyze_platforms(iceberg)

    got_surface = {item.platform.name: item.surface_threat for item in result.results}
    got_subsea = {item.platform.name: item.subsea_threat for item in result.results}

    assert got_surface == expected_surface, (
        f"surface mismatch for example {example_name}"
    )
    assert got_subsea == expected_subsea, f"subsea mismatch for example {example_name}"
