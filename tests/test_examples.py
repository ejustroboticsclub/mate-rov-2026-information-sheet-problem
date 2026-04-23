import pytest

from information_sheet_problem import ThreatLevel, analyze_iceberg


@pytest.mark.parametrize(
    ("example_name", "iceberg_args", "expected_surface", "expected_subsea"),
    [
        (
            "A",
            (47, 39, 0, "N", 48, 37, 0, "W", 158, 99),
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
            (47, 58, 0, "N", 48, 50, 0, "W", 180, 78),
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
            (47, 53, 0, "N", 47, 51, 0, "W", 188, 112),
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
            (47, 40, 0, "N", 49, 25, 0, "W", 152, 60),
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
            (47, 45, 0, "N", 48, 29, 0, "W", 198, 84),
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
            (47, 56, 0, "N", 47, 45, 0, "W", 181, 126),
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
    iceberg_args: tuple,
    expected_surface: dict[str, ThreatLevel],
    expected_subsea: dict[str, ThreatLevel],
) -> None:
    """Official examples taken from
    `https://20693798.fs1.hubspotusercontent-na1.net/hubfs/20693798/2026/Supporting%20Documents/Iceberg%20Information%20Examples%20EX%20PN%20RN%20Updated%202_16.pdf`"""

    result = analyze_iceberg(*iceberg_args)

    got_surface = {item.platform.name: item.surface_threat for item in result.results}
    got_subsea = {item.platform.name: item.subsea_threat for item in result.results}

    assert got_surface == expected_surface, (
        f"surface mismatch for example {example_name}"
    )
    assert got_subsea == expected_subsea, f"subsea mismatch for example {example_name}"
