# tests/test_measurements.py

from shapely.geometry import GeometryCollection, LineString, Point, Polygon

from app.services.measurement import calculate_measurement


def test_polygon_area():
    polygon = Polygon(
        [
            (0, 0),
            (10, 0),
            (10, 10),
            (0, 10),
        ]
    )

    result = calculate_measurement(polygon)

    assert result["measurement_type"] == "area"
    assert result["value"] == 100
    assert result["unit"] == "m²"


def test_linestring_length():
    line = LineString(
        [
            (0, 0),
            (3, 4),
        ]
    )

    result = calculate_measurement(line)

    assert result["measurement_type"] == "length"
    assert result["value"] == 5
    assert result["unit"] == "m"


def test_point_has_no_measurement():
    point = Point(10, 20)

    result = calculate_measurement(point)

    assert result["measurement_type"] is None
    assert result["value"] is None
    assert result["unit"] is None


def test_unsupported_geometry_is_handled_gracefully():
    geometry = GeometryCollection()

    result = calculate_measurement(geometry)

    assert result["measurement_type"] is None
    assert result["value"] is None
    assert result["unit"] is None