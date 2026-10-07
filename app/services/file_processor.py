# app/services/file_processor.py

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import geopandas as gpd

from app.services.crs import transform_to_projected_crs
from app.services.measurement import calculate_measurement


SUPPORTED_EXTENSIONS = {".kml", ".zip"}


def _validate_file(file_path: Path) -> None:
    """Validate that the uploaded file has a supported extension."""
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Only .kml and .zip files are supported."
        )


def _read_kml(file_path: Path) -> gpd.GeoDataFrame:
    """Read a KML file into a GeoDataFrame."""
    try:
        return gpd.read_file(file_path, driver="KML")
    except Exception as exc:
        raise ValueError(f"Failed to read KML file: {exc}") from exc


def _read_shapefile_zip(file_path: Path) -> gpd.GeoDataFrame:
    """Extract and read a Shapefile from a ZIP archive."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            with ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(temp_path)
        except Exception as exc:
            raise ValueError(f"Failed to extract ZIP file: {exc}") from exc

        shapefiles = list(temp_path.rglob("*.shp"))

        if not shapefiles:
            raise ValueError("ZIP archive does not contain a Shapefile.")

        if len(shapefiles) > 1:
            raise ValueError(
                "ZIP archive contains multiple Shapefiles. "
                "Please provide a ZIP containing one Shapefile."
            )

        try:
            return gpd.read_file(shapefiles[0])
        except Exception as exc:
            raise ValueError(
                f"Failed to read Shapefile: {exc}"
            ) from exc


def _read_geospatial_file(file_path: Path) -> gpd.GeoDataFrame:
    """Read a supported geospatial file."""
    extension = file_path.suffix.lower()

    if extension == ".kml":
        return _read_kml(file_path)

    if extension == ".zip":
        return _read_shapefile_zip(file_path)

    raise ValueError(
        "Unsupported file type. Only .kml and .zip files are supported."
    )


def _extract_features(
    original_gdf: gpd.GeoDataFrame,
    projected_gdf: gpd.GeoDataFrame,
) -> list[dict]:
    """Extract feature information and measurements."""
    features = []

    for index, (original_row, projected_row) in enumerate(
        zip(
            original_gdf.itertuples(index=False),
            projected_gdf.itertuples(index=False),
        )
    ):
        original_geometry = original_row.geometry
        projected_geometry = projected_row.geometry

        properties = {
            column: getattr(original_row, column)
            for column in original_gdf.columns
            if column != "geometry"
        }

        measurement = calculate_measurement(projected_geometry)

        features.append(
            {
                "feature_id": index,
                "geometry_type": (
                    original_geometry.geom_type
                    if original_geometry is not None
                    else None
                ),
                "geometry": (
                    original_geometry.__geo_interface__
                    if original_geometry is not None
                    else None
                ),
                "properties": properties,
                "measurement": measurement,
            }
        )

    return features


def process_file(file_path: str | Path) -> dict:
    """
    Process a KML or Shapefile ZIP and return extracted features
    with measurements.
    """
    file_path = Path(file_path)

    _validate_file(file_path)

    original_gdf = _read_geospatial_file(file_path)

    if original_gdf.empty:
        raise ValueError("The uploaded file contains no features.")

    input_crs = original_gdf.crs

    if input_crs is None:
        raise ValueError("Input file does not contain CRS information.")

    projected_gdf, measurement_crs = transform_to_projected_crs(
        original_gdf
    )

    features = _extract_features(
        original_gdf,
        projected_gdf,
    )

    return {
        "filename": file_path.name,
        "feature_count": len(features),
        "crs": input_crs.to_string(),
        "measurement_crs": measurement_crs.to_string(),
        "features": features,
    }