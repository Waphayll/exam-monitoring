# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uvicorn

from app.cv_processor import detector
from app.db import db

app = FastAPI(title="Exam Proctoring API")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================
# Pydantic Models
# ============================================

class ProcessFrameRequest(BaseModel):
    camera_id: int
    frame: str  # base64 encoded image
    recording_id: Optional[int] = None

class BehaviorEventRequest(BaseModel):
    camera_id: int
    behavior_label: str
    confidence: float
    severity: str = "medium"
    frame_timestamp: str
    bbox: Optional[Dict] = None
    recording_id: Optional[int] = None
    frame_index: Optional[int] = None
    extra_data: Optional[Dict] = None

# ============================================
# Routes
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/process-frame")
async def process_frame(request: ProcessFrameRequest):
    """
    Process a single frame and detect behaviors
    """
    try:
        # Process frame with CV algorithm
        result = detector.process_frame(request.frame, request.camera_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))
        
        # Save each detected behavior to database
        saved_behaviors = []
        for behavior in result.get("behaviors", []):
            try:
                behavior_id = db.insert_behavior_event(
                    camera_id=request.camera_id,
                    behavior_label=behavior["behavior_label"],
                    confidence=behavior["confidence"],
                    severity=behavior["severity"],
                    frame_timestamp=result["timestamp"],
                    bbox=behavior.get("bbox"),
                    recording_id=request.recording_id,
                    extra_data=behavior.get("extra_data")
                )
                saved_behaviors.append({
                    "id": behavior_id,
                    **behavior
                })
            except Exception as e:
                print(f"Failed to save behavior: {e}")
                # Continue processing other behaviors
        
        return {
            "success": True,
            "camera_id": request.camera_id,
            "timestamp": result["timestamp"],
            "behaviors": saved_behaviors,
            "behavior_count": len(saved_behaviors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/behavior-event")
async def create_behavior_event(event: BehaviorEventRequest):
    """
    Manually create a behavior event (for external PT systems)
    """
    try:
        behavior_id = db.insert_behavior_event(
            camera_id=event.camera_id,
            behavior_label=event.behavior_label,
            confidence=event.confidence,
            severity=event.severity,
            frame_timestamp=event.frame_timestamp,
            bbox=event.bbox,
            recording_id=event.recording_id,
            frame_index=event.frame_index,
            extra_data=event.extra_data
        )
        
        return {
            "success": True,
            "behavior_event_id": behavior_id,
            "message": "Behavior event created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/behavior-events")
async def get_behavior_events(camera_id: int, limit: int = 50):
    """
    Get recent behavior events for a camera
    """
    try:
        events = db.get_recent_behaviors(camera_id, limit)
        return {
            "success": True,
            "camera_id": camera_id,
            "events": events,
            "count": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cameras")
async def get_cameras():
    """
    Get all cameras
    """
    try:
        cameras = db.get_cameras()
        return {
            "success": True,
            "cameras": cameras,
            "count": len(cameras)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    """
    Get system statistics
    """
    try:
        # Add your statistics queries here
        return {
            "success": True,
            "statistics": {
                "total_cameras": 4,
                "active_sessions": 1,
                "total_behaviors_detected": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "Not found"}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )

# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
