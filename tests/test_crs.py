# tests/test_crs.py

import geopandas as gpd
import pytest
from shapely.geometry import Point, Polygon

from app.services.crs import (
    get_input_crs,
    get_projected_crs,
    transform_to_projected_crs,
)


def create_wgs84_geodataframe():
    return gpd.GeoDataFrame(
        {
            "name": ["Test"],
            "geometry": [Point(77.5946, 12.9716)],
        },
        crs="EPSG:4326",
    )


def test_crs_detection():
    gdf = create_wgs84_geodataframe()

    crs = get_input_crs(gdf)

    assert crs.to_epsg() == 4326


def test_missing_crs_raises_error():
    gdf = gpd.GeoDataFrame(
        {
            "geometry": [Point(77.5946, 12.9716)],
        }
    )

    with pytest.raises(ValueError, match="does not contain CRS"):
        get_input_crs(gdf)


def test_4326_to_projected_crs():
    gdf = create_wgs84_geodataframe()

    projected_crs = get_projected_crs(gdf)

    assert projected_crs.is_projected
    assert projected_crs.to_epsg() != 4326


def test_geometry_transformation():
    gdf = create_wgs84_geodataframe()

    transformed_gdf, projected_crs = transform_to_projected_crs(gdf)

    assert transformed_gdf.crs == projected_crs
    assert transformed_gdf.crs.is_projected

    original_point = gdf.geometry.iloc[0]
    transformed_point = transformed_gdf.geometry.iloc[0]

    assert original_point.x != transformed_point.x
    assert original_point.y != transformed_point.y


def test_projected_crs_is_preserved():
    gdf = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon(
                    [
                        (500000, 0),
                        (501000, 0),
                        (501000, 1000),
                        (500000, 1000),
                    ]
                )
            ]
        },
        crs="EPSG:32643",
    )

    transformed_gdf, projected_crs = transform_to_projected_crs(gdf)

    assert projected_crs.to_epsg() == 32643
    assert transformed_gdf.crs.to_epsg() == 32643