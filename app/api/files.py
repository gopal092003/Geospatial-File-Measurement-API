# app/api/files.py

from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.file_processor import process_file


router = APIRouter(prefix="/api/files", tags=["Files"])

# In-memory storage for processed files.
files_store: dict[str, dict] = {}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a KML or Shapefile ZIP.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only .kml and .zip files are supported.",
        )

    file_id = str(uuid4())

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

            while chunk := await file.read(1024 * 1024):
                temp_file.write(chunk)

        result = process_file(temp_path)

        result["id"] = file_id
        result["filename"] = file.filename
        result["status"] = "COMPLETED"

        files_store[file_id] = result

        return {
            "id": file_id,
            "filename": file.filename,
            "feature_count": result["feature_count"],
            "crs": result["crs"],
            "status": result["status"],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded file.",
        ) from exc

    finally:
        if "temp_path" in locals():
            temp_path.unlink(missing_ok=True)


@router.get("/{file_id}/")
async def get_file(file_id: str):
    """
    Return information about an uploaded file.
    """
    result = files_store.get(file_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    return {
        "id": result["id"],
        "filename": result["filename"],
        "feature_count": result["feature_count"],
        "crs": result["crs"],
        "status": result["status"],
    }


@router.get("/{file_id}/measurements/")
async def get_measurements(file_id: str):
    """
    Return measurements for all features in an uploaded file.
    """
    result = files_store.get(file_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    return {
        "file_id": result["id"],
        "crs": result["crs"],
        "measurement_crs": result["measurement_crs"],
        "features": [
            {
                "feature_id": feature["feature_id"],
                "geometry_type": feature["geometry_type"],
                "measurement": feature["measurement"],
            }
            for feature in result["features"]
        ],
    }