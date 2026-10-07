# app/main.py

from fastapi import FastAPI

from app.api.files import router as files_router


app = FastAPI(
    title="Geospatial File Measurement API",
    description=(
        "Backend API for processing KML and Shapefile files "
        "and calculating geospatial measurements."
    ),
    version="1.0.0",
)

app.include_router(files_router)