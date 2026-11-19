"""
Route Resilience Trial Application - Web Server.
Built with FastAPI. Provides:
- Interactive photograph upload and analysis endpoint
- One-click presets for Indian junctions (Silk Board, ITO, Chandani Chowk, Kathipara)
- Real-time engineering report generation with 3D bypass and zero-demolition verification
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pipeline.image_report_generator import analyze_photograph_and_generate_report

app = FastAPI(
    title="Route Resilience - Aerial Photograph Report Generator",
    description="Interactive trial platform for occlusion-robust road extraction & zero-demolition 3D pathway synthesis.",
    version="3.0.0"
)

# Ensure directories exist
Path("static").mkdir(exist_ok=True)
Path("data/sample_images").mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = Path("static/index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Route Resilience App Initializing...</h1>")


@app.post("/api/analyze-upload")
async def analyze_upload(file: UploadFile = File(...), junction_name: str = Form("Custom Aerial Junction")):
    """Analyzes an uploaded photograph and returns visual & numerical report."""
    contents = await file.read()
    report = analyze_photograph_and_generate_report(contents, junction_name=junction_name)
    return JSONResponse(content=report)


class PresetRequest(BaseModel):
    preset_key: str


@app.post("/api/analyze-preset")
async def analyze_preset(req: PresetRequest):
    """Analyzes a preloaded Indian junction sample image."""
    preset_map = {
        "silk_board": ("data/sample_images/silk_board.jpg", "Central Silk Board Junction (Bengaluru)"),
        "ito_delhi": ("data/sample_images/ito_delhi.jpg", "ITO Junction (New Delhi)"),
        "chandani_chowk": ("data/sample_images/chandani_chowk.jpg", "Chandani Chowk (Pune)"),
        "kathipara_chennai": ("data/sample_images/kathipara_chennai.jpg", "Kathipara Junction (Chennai)"),
        "corridor_multi_junction": ("data/sample_images/corridor_multi_junction.jpg", "Multi-Junction Corridor (3 Consecutive Intersections)")
    }

    if req.preset_key not in preset_map:
        return JSONResponse(status_code=400, content={"error": f"Unknown preset '{req.preset_key}'"})

    img_path, junc_name = preset_map[req.preset_key]
    if not os.path.exists(img_path):
        from scripts.generate_sample_satellite_tiles import generate_samples
        generate_samples()

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    report = analyze_photograph_and_generate_report(img_bytes, junction_name=junc_name)
    return JSONResponse(content=report)


if __name__ == "__main__":
    import uvicorn
    print("\nStarting Route Resilience Interactive Trial Server...")
    print("Open your browser at: http://localhost:8000\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
