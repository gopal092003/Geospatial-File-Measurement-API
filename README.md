# Geospatial File Measurement API

A modular FastAPI backend service that accepts geospatial files, extracts their features and attributes, handles coordinate reference systems (CRS), and calculates measurements for supported geometries.

The API supports KML files and ZIP archives containing a Shapefile.

## Features

* Upload `.kml` files.
* Upload `.zip` files containing a Shapefile.
* Extract feature information:

  * Feature ID/index
  * Geometry type
  * Geometry
  * CRS
  * Properties/attributes
* Calculate measurements:

  * Polygon → Area
  * MultiPolygon → Area
  * LineString → Length
  * MultiLineString → Length
  * Point → No measurement
* Automatically transform geographic coordinates to an appropriate projected CRS before calculating measurements.
* Gracefully handle unsupported geometry types.
* Temporarily process uploaded files without permanently storing the original files.
* Store processed results in memory using a generated file ID.
* Provide interactive API documentation through FastAPI Swagger UI.
* Include automated unit and API tests.

## Tech Stack

* Python
* FastAPI
* GeoPandas
* Shapely
* PyProj
* Pyogrio
* Pytest
* HTTPX

## Project Structure

```text
geospatial-measurement-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── files.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── file_processor.py
│       ├── measurement.py
│       └── crs.py
│
├── tests/
│   ├── test_files.py
│   ├── test_measurements.py
│   └── test_crs.py
│
├── sample_data/
│   ├── sample.kml
│   └── sample_shapefile.zip
│
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd geospatial-measurement-api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it.

**Windows Command Prompt:**

```cmd
.venv\Scripts\activate
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

The Swagger UI can be used to upload files and test all API endpoints without requiring a separate frontend.

## API

### 1. Upload File

```http
POST /api/files/
```

Accepts:

* `.kml`
* `.zip` containing a Shapefile

Example using cURL:

```bash
curl -X POST \
  -F "file=@sample_data/sample.kml" \
  http://127.0.0.1:8000/api/files/
```

Example response:

```json
{
  "id": "abc123",
  "filename": "sample.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

The returned `id` is used to retrieve information and measurements for the processed file.

### 2. Get File Information

```http
GET /api/files/{id}/
```

Example:

```bash
curl http://127.0.0.1:8000/api/files/abc123/
```

Example response:

```json
{
  "id": "abc123",
  "filename": "sample.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

### 3. Get Measurements

```http
GET /api/files/{id}/measurements/
```

Example:

```bash
curl http://127.0.0.1:8000/api/files/abc123/measurements/
```

Example response:

```json
{
  "file_id": "abc123",
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "features": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "measurement": {
        "measurement_type": "area",
        "value": 15432.52,
        "unit": "m²"
      }
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "measurement": {
        "measurement_type": "length",
        "value": 382.41,
        "unit": "m"
      }
    },
    {
      "feature_id": 2,
      "geometry_type": "Point",
      "measurement": {
        "measurement_type": null,
        "value": null,
        "unit": null
      }
    }
  ]
}
```

## Supported Geometries

| Geometry        | Measurement                            |
| --------------- | -------------------------------------- |
| Polygon         | Area in m²                             |
| MultiPolygon    | Area in m²                             |
| LineString      | Length in m                            |
| MultiLineString | Length in m                            |
| Point           | No measurement                         |
| Other           | Gracefully handled with no measurement |

## Architecture

The application separates HTTP/API handling from geospatial file processing, CRS handling, and measurement logic.

```text
Client
  ↓
FastAPI
  ↓
api/files.py
  ↓
file_processor.py
  ├── crs.py
  └── measurement.py
```

### Responsibilities

**`app/main.py`**

Creates the FastAPI application and registers the API router.

**`app/api/files.py`**

Handles:

* File uploads
* Input validation
* HTTP responses
* File IDs
* In-memory storage
* File information endpoint
* Measurement endpoint

**`app/services/file_processor.py`**

Handles:

* File validation
* KML reading
* Shapefile ZIP extraction
* GeoDataFrame creation
* Feature extraction
* CRS coordination
* Measurement orchestration

**`app/services/crs.py`**

Handles:

* Input CRS detection
* Projected CRS selection
* Geographic-to-projected CRS transformation

**`app/services/measurement.py`**

Contains geometry-specific measurement logic.

## File Processing Flow

```text
Upload file
    ↓
Validate extension
    ↓
Read KML / extract Shapefile ZIP
    ↓
Load GeoDataFrame
    ↓
Validate CRS and features
    ↓
Determine projected CRS
    ↓
Transform geometries
    ↓
Calculate measurements
    ↓
Extract original feature information
    ↓
Store processed result in memory
    ↓
Return API response
```

## Measurement Flow

Measurements are calculated only after geometries have been transformed into a suitable projected CRS.

```text
Input geometry
      ↓
Check input CRS
      ↓
Transform to projected CRS
      ↓
┌──────────────┬──────────────┬──────────────┐
│   Polygon    │ LineString   │    Point     │
│      ↓       │      ↓       │      ↓       │
│     Area     │    Length    │ No measure-  │
│              │              │    ment      │
└──────────────┴──────────────┴──────────────┘

Unsupported geometry
      ↓
No measurement
```

## CRS Handling

Geographic coordinate systems such as `EPSG:4326` represent coordinates using latitude and longitude in angular degrees.

Area and length should not be calculated directly from these degree-based coordinates because the resulting values would not represent meaningful metric measurements.

The application therefore:

1. Detects the input CRS.
2. Validates that CRS information is available.
3. Checks whether the input CRS is already projected.
4. If the CRS is geographic, determines an appropriate projected UTM CRS using GeoPandas.
5. Transforms the geometries into the projected CRS.
6. Calculates measurements using the projected geometries.

The original geometry and original CRS are retained for the API response, while the transformed geometry is used internally for measurement calculations.

For example:

```text
Input CRS
EPSG:4326
   ↓
Estimate suitable UTM CRS
   ↓
Projected CRS
EPSG:32643
   ↓
Calculate area/length in meters
```

This ensures that:

* Lengths are returned in meters.
* Areas are returned in square meters.

## Design Decisions

### FastAPI

FastAPI was selected because it provides a lightweight backend framework, automatic OpenAPI documentation, and straightforward file-upload handling.

### GeoPandas

GeoPandas provides the high-level interface for reading and processing geospatial datasets and managing GeoDataFrames and CRS information.

### Shapely

Shapely provides geometry objects and geometric operations such as polygon area and line length calculations.

### PyProj

PyProj is used for CRS representation and coordinate-system transformations.

### Pyogrio

Pyogrio provides the underlying geospatial file I/O functionality used by the GeoPandas environment for reading and writing supported vector formats.

### In-Memory Storage

A database was intentionally not introduced because persistence is not required by the assignment.

Processed results are stored in an in-memory Python dictionary using a generated UUID as the file ID.

This keeps the implementation small and focused on the required functionality.

Because the storage is in memory, processed files and their results are lost when the application process restarts.

### Temporary File Processing

Uploaded files are written to temporary files for processing rather than being permanently stored on disk.

For Shapefile ZIP uploads, the archive is extracted into a temporary directory and removed after processing.

### Projected CRS for Measurements

Measurements are performed using a projected CRS rather than geographic latitude/longitude coordinates.

This avoids calculating distances and areas directly in angular degrees and allows measurements to be returned in metric units.

## Error Handling

The API handles several invalid-input scenarios, including:

* Unsupported file extensions
* Missing filenames
* Empty geospatial files
* Files without CRS information
* ZIP archives without a Shapefile
* ZIP archives containing multiple Shapefiles
* Invalid or unreadable KML files
* Invalid or unreadable Shapefiles
* Requests for non-existent file IDs
* Unsupported geometry types

Invalid input is returned as an appropriate HTTP `400` response, while requests for unknown file IDs return `404`.

## Testing

Run the test suite with:

```bash
python -m pytest
```

The project currently has **16 passing tests** covering:

* CRS detection
* Missing CRS handling
* Geographic-to-projected CRS transformation
* Preservation of already-projected CRS
* Polygon area calculation
* LineString length calculation
* Point handling
* Unsupported geometry handling
* KML upload
* Shapefile ZIP upload
* Invalid file type handling
* File information endpoint
* Measurement endpoint
* Non-existent file handling

Latest local test result:

```text
16 passed
```

### End-to-End File Testing

In addition to automated tests, the API was manually tested through the FastAPI Swagger UI using real files.

#### KML

A real KML file was uploaded through:

```text
POST /api/files/
```

The returned file ID was then used successfully with:

```text
GET /api/files/{id}/
```

and:

```text
GET /api/files/{id}/measurements/
```

#### Shapefile ZIP

A real ZIP archive containing a Shapefile was also uploaded successfully through:

```text
POST /api/files/
```

The resulting file ID was successfully used with:

```text
GET /api/files/{id}/
```

and:

```text
GET /api/files/{id}/measurements/
```

Both file formats therefore work successfully through the complete API flow.

## Learning

This project provided practical experience with:

* Building a modular FastAPI backend.
* Designing API endpoints for file processing.
* Processing geospatial file formats with GeoPandas.
* Working with Shapely geometries.
* Handling coordinate reference systems.
* Transforming geographic coordinates into projected coordinate systems.
* Performing measurements using projected coordinates.
* Designing separation between HTTP/API handling and business logic.
* Writing automated tests for geospatial processing.
* Testing real KML and Shapefile ZIP files through an API.

## Future Scope

Potential improvements include:

* Persistent database storage.
* Asynchronous/background processing for large files.
* File-size and resource limits.
* Authentication and authorization.
* Persistent object storage for uploaded files.
* More advanced CRS selection for specialized geographic regions.
* Additional geospatial measurements and geometry types.
* Improved validation and secure extraction of Shapefile ZIP contents.
* Support for additional geospatial formats.
* More detailed API response schemas using Pydantic models.
* Production deployment configuration.
* Structured logging and monitoring.

## API Summary

| Method | Endpoint                        | Purpose                                   |
| ------ | ------------------------------- | ----------------------------------------- |
| `POST` | `/api/files/`                   | Upload and process a KML or Shapefile ZIP |
| `GET`  | `/api/files/{id}/`              | Retrieve processed file information       |
| `GET`  | `/api/files/{id}/measurements/` | Retrieve feature measurements             |
| `GET`  | `/docs`                         | Open interactive Swa                      |
