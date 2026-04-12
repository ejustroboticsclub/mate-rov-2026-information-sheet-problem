# logic.py — Iceberg Threat Analysis Logic

This module contains the core domain logic used to analyze iceberg threats to offshore platforms. It computes distances and threat levels for surface and subsea assets, builds a map overlay for visualization, and produces a structured analysis result.

---

## Overview

`logic.py` provides:

- Geographic utility functions (distance, heading vector)
- Threat evaluation rules for surface and subsea assets
- An orchestration function to analyze all platforms
- Map overlay building and rendering stubs

It depends on domain data classes defined in:
`information_sheet_problem.domain_data_classes`

---

## Key Concepts

### Platforms
Platforms are offshore structures with known geographic locations and water depths.

### Iceberg
An iceberg has a location, heading, and keel depth (submerged depth).

### Track
A track is an iceberg path defined by its origin and heading.

---

## Constants

### `DEFAULT_PLATFORMS`
```python
DEFAULT_PLATFORMS: list[Platform]
```
A default list of platform definitions:

- Hibernia
- Sea Rose
- Terra Nova
- Hebron

Each platform includes:
- Name
- `GeoPoint` (latitude, longitude)
- Water depth (meters)

---

## Functions

### `heading_to_unit_vector(heading_degrees: float) -> tuple[float, float]`
Converts a compass heading (in degrees) into a 2D unit vector.

**Details**
- Uses standard trigonometric conversion
- Heading in degrees is converted to radians
- Returns `(dx, dy)` where:
  - `dx = sin(heading)`
  - `dy = cos(heading)`

---

### `distance_nm(a: GeoPoint, b: GeoPoint) -> float`
Approximates distance between two geographic points in **nautical miles**.

**Method**
- Assumes 1 minute of latitude = 1 NM
- Scales longitude by cos(mean latitude)
- Uses Pythagorean distance on a local tangent plane

---

### `distance_point_to_track_nm(point: GeoPoint, track: Track) -> float`
Computes the **minimum perpendicular distance** from a point to an iceberg track.

**Steps**
1. Convert point to local NM coordinate system relative to track origin
2. Project point onto track direction
3. Compute perpendicular offset

---

### `intersects_within_radius_nm(point: GeoPoint, track: Track, radius_nm: float) -> bool`
Checks whether a track passes within a given radius of a point.

**Logic**
- Computes perpendicular distance to track
- Returns `True` if distance ≤ radius

---

### `evaluate_surface_threat(distance_nm: float, keel_depth: float, water_depth: float) -> ThreatLevel`
Evaluates surface threat level based on distance and grounding.

**Rules**
1. **Grounding rule**  
   If `keel_depth >= 1.1 * water_depth` → **GREEN**
2. **Distance thresholds**
   - `< 5 NM` → **RED**
   - `<= 10 NM` → **YELLOW**
   - otherwise → **GREEN**

---

### `evaluate_subsea_threat(intersects: bool, keel_depth: float, water_depth: float) -> ThreatLevel`
Evaluates subsea threat level based on intersection and depth ratio.

**Rules**
- If no intersection → **GREEN**
- Otherwise, compute ratio = `(keel_depth / water_depth) * 100`
  - `>= 110%` → **GREEN**
  - `90–110%` → **RED**
  - `70–90%` → **YELLOW**
  - `< 70%` → **GREEN**

---

## Main Workflow

### `analyze_platforms(iceberg: Iceberg, platforms: list[Platform] = DEFAULT_PLATFORMS) -> AnalysisResult`

Central orchestration function that:

1. Builds a `Track` from iceberg location and heading
2. For each platform:
   - Computes distance to track
   - Evaluates surface threat
   - Checks intersection within 25 NM
   - Evaluates subsea threat
3. Builds a `MapOverlay`
4. Renders a `RenderedMap`
5. Returns a full `AnalysisResult`

---

## Map Utilities

### `build_map_overlay(iceberg: Iceberg, platforms: list[Platform]) -> MapOverlay`
Constructs geometric overlay data for visualization.

**Process**
- Converts iceberg heading into a unit vector
- Projects the iceberg track forward 20 NM
- Returns:
  - `iceberg_track` as `(start, projected)`
  - `platform_points` list

---

### `render_map(overlay: MapOverlay) -> RenderedMap`
Stub for rendering a map image.

**Notes**
- Returns an empty `RenderedMap`
- Does not display or save yet
> still working on this update

---

## Data Classes Used

From `information_sheet_problem.domain_data_classes`:

- `AnalysisResult`
- `GeoPoint`
- `Iceberg`
- `MapOverlay`
- `Platform`
- `PlatformThreatResult`
- `RenderedMap`
- `ThreatLevel`
- `Track`

---

## Usage Example (Conceptual)

```python
result = analyze_platforms(iceberg)
for r in result.results:
    print(r.platform.name, r.surface_threat, r.subsea_threat)
```

---

## Notes & Assumptions

- Distance calculations are approximate (local tangent plane)
- Subsea threat is only checked within 25 NM
- `RenderedMap` is a placeholder for GUI rendering layers
