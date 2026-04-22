import pytest

from information_sheet_problem import (
    GeoPoint,
    Iceberg,
    Platform,
    analyze_platforms,
    analyze_platforms_from_runtime_data,
)


def test_analyze_platforms_from_runtime_data_matches_regular_api() -> None:
    iceberg_data = {
        "location": {"latitude": 47.65, "longitude": -48.62},
        "heading_degrees": 158.0,
        "keel_depth": 99.0,
    }

    runtime_result = analyze_platforms_from_runtime_data(iceberg_data)
    direct_result = analyze_platforms(
        Iceberg(
            location=GeoPoint(47.65, -48.62),
            heading_degrees=158.0,
            keel_depth=99.0,
        )
    )

    assert runtime_result.results == direct_result.results


def test_analyze_platforms_from_runtime_data_accepts_runtime_platforms() -> None:
    iceberg_data = {
        "latitude": 47.65,
        "longitude": -48.62,
        "heading_degrees": 158.0,
        "keel_depth": 99.0,
    }
    platforms_data = [
        {
            "name": "Custom",
            "location": {"latitude": 46.75, "longitude": -48.78},
            "water_depth": 78,
        }
    ]

    result = analyze_platforms_from_runtime_data(iceberg_data, platforms_data)
    expected = analyze_platforms(
        Iceberg(GeoPoint(47.65, -48.62), 158.0, 99.0),
        [Platform("Custom", GeoPoint(46.75, -48.78), 78.0)],
    )

    assert result.results == expected.results


def test_analyze_platforms_from_runtime_data_validates_required_fields() -> None:
    with pytest.raises(ValueError, match="missing required field 'keel_depth'"):
        analyze_platforms_from_runtime_data(
            {
                "latitude": 47.65,
                "longitude": -48.62,
                "heading_degrees": 158.0,
            }
        )
