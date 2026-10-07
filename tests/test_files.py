# tests/test_files.py

import io
import zipfile

from fastapi.testclient import TestClient
from shapely.geometry import Point, Polygon

from app.main import app
from app.api.files import files_store


client = TestClient(app)


def create_kml() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <Placemark>
            <name>Test Polygon</name>
            <Polygon>
                <outerBoundaryIs>
                    <LinearRing>
                        <coordinates>
                            77.5940,12.9710,0
                            77.5950,12.9710,0
                            77.5950,12.9720,0
                            77.5940,12.9720,0
                            77.5940,12.9710,0
                        </coordinates>
                    </LinearRing>
                </outerBoundaryIs>
            </Polygon>
        </Placemark>
    </Document>
</kml>
"""


def create_shapefile_zip() -> bytes:
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(
        {
            "name": ["Test Polygon"],
            "geometry": [
                Polygon(
                    [
                        (77.5940, 12.9710),
                        (77.5950, 12.9710),
                        (77.5950, 12.9720),
                        (77.5940, 12.9720),
                    ]
                )
            ],
        },
        crs="EPSG:4326",
    )

    with __import__("tempfile").TemporaryDirectory() as temp_dir:
        import os

        shapefile_path = os.path.join(temp_dir, "test.shp")
        gdf.to_file(shapefile_path)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zip_file:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)

                if os.path.isfile(file_path):
                    zip_file.write(
                        file_path,
                        arcname=filename,
                    )

        return zip_buffer.getvalue()


def setup_function():
    """Clear in-memory storage before every test."""
    files_store.clear()


def test_kml_upload():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.kml",
                create_kml(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "test.kml"
    assert data["feature_count"] == 1
    assert data["crs"] is not None
    assert data["status"] == "COMPLETED"
    assert data["id"]


def test_shapefile_zip_upload():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.zip",
                create_shapefile_zip(),
                "application/zip",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "test.zip"
    assert data["feature_count"] == 1
    assert data["crs"] == "EPSG:4326"
    assert data["status"] == "COMPLETED"


def test_invalid_file_type():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.txt",
                b"not a geospatial file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_get_file_information():
    upload_response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.kml",
                create_kml(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == file_id
    assert data["filename"] == "test.kml"
    assert data["feature_count"] == 1
    assert data["status"] == "COMPLETED"


def test_get_measurements():
    upload_response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.kml",
                create_kml(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    file_id = upload_response.json()["id"]

    response = client.get(
        f"/api/files/{file_id}/measurements/"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["file_id"] == file_id
    assert data["crs"] is not None
    assert data["measurement_crs"] is not None
    assert len(data["features"]) == 1

    feature = data["features"][0]

    assert feature["feature_id"] == 0
    assert feature["geometry_type"] == "Polygon"
    assert feature["measurement"]["measurement_type"] == "area"
    assert feature["measurement"]["value"] > 0
    assert feature["measurement"]["unit"] == "m²"


def test_nonexistent_file():
    response = client.get(
        "/api/files/non-existent-id/"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."


def test_nonexistent_file_measurements():
    response = client.get(
        "/api/files/non-existent-id/measurements/"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."