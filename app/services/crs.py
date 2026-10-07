# app/services/crs.py

import geopandas as gpd
from pyproj import CRS


def get_input_crs(gdf: gpd.GeoDataFrame) -> CRS:
    """
    Return the CRS of the input GeoDataFrame.

    Raises:
        ValueError: If the input file does not contain CRS information.
    """
    if gdf.crs is None:
        raise ValueError("Input file does not contain CRS information.")

    return CRS.from_user_input(gdf.crs)


def get_projected_crs(gdf: gpd.GeoDataFrame) -> CRS:
    """
    Determine an appropriate projected CRS for measurements.

    For geographic coordinates, GeoPandas estimates a suitable UTM CRS
    based on the geometries in the GeoDataFrame.

    Raises:
        ValueError: If the GeoDataFrame does not have a CRS.
    """
    input_crs = get_input_crs(gdf)

    if input_crs.is_projected:
        return input_crs

    projected_crs = gdf.estimate_utm_crs()

    if projected_crs is None:
        raise ValueError(
            "Could not determine a suitable projected CRS for measurement."
        )

    return CRS.from_user_input(projected_crs)


def transform_to_projected_crs(
    gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, CRS]:
    """
    Transform the GeoDataFrame to an appropriate projected CRS.

    Returns:
        A tuple containing:
        - transformed GeoDataFrame
        - projected CRS
    """
    projected_crs = get_projected_crs(gdf)

    if gdf.crs == projected_crs:
        return gdf, projected_crs

    transformed_gdf = gdf.to_crs(projected_crs)

    return transformed_gdf, projected_crs