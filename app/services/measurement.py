# app/services/measurement.py

from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)


def calculate_measurement(geometry) -> dict:
    """
    Calculate the measurement for an already-projected geometry.

    Returns a consistent dictionary containing:
        - measurement_type
        - value
        - unit

    Supported geometries:
        Polygon / MultiPolygon -> area in square meters
        LineString / MultiLineString -> length in meters
        Point -> no measurement

    Unsupported geometries are handled gracefully.
    """

    if isinstance(geometry, (Polygon, MultiPolygon)):
        return {
            "measurement_type": "area",
            "value": geometry.area,
            "unit": "m²",
        }

    if isinstance(geometry, (LineString, MultiLineString)):
        return {
            "measurement_type": "length",
            "value": geometry.length,
            "unit": "m",
        }

    if isinstance(geometry, Point):
        return {
            "measurement_type": None,
            "value": None,
            "unit": None,
        }

    return {
        "measurement_type": None,
        "value": None,
        "unit": None,
    }