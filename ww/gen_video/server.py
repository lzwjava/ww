#!/usr/bin/env python3
"""ww gen-video server — Start a FastAPI server that generates videos from markdown content.

Usage:
    ww gen-video server [--port PORT] [--host HOST]

API:
    POST   /api/generate-video     Submit a video generation job (returns job_id immediately)
    GET    /api/jobs/{job_id}       Query job status
    GET    /api/jobs/{job_id}/download  Download the completed video
    GET    /api/jobs                List all jobs
    GET    /health                  Health check
"""

import argparse
import os
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ww.gen_video.video import generate_video_from_content

app = FastAPI(
    title="Gen Video API",
    description="Generate 15s vertical short-form videos (9:16) from markdown content.",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    content: str
    model: str | None = None
    image_model: str = "black-forest-labs/flux.2-pro"


OUTPUT_DIR = Path("/tmp/gen_video_server_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store: {job_id: {status, progress, output_path, error, created_at, completed_at}}
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _run_generation(
    job_id: str, content: str, output_path: str, model: str | None, image_model: str
):
    """Run the video generation pipeline in a background thread."""
    with _jobs_lock:
        _jobs[job_id]["status"] = "processing"

    try:
        success, out_path, error_msg = generate_video_from_content(
            content,
            output_path,
            model=model,
            image_model=image_model,
            verbose=True,
        )
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["error"] = str(e)
            _jobs[job_id]["completed_at"] = time.time()
        return

    with _jobs_lock:
        if success and out_path and os.path.isfile(out_path):
            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["output_path"] = out_path
        else:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["error"] = error_msg or "Unknown error"
        _jobs[job_id]["completed_at"] = time.time()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "jobs": len(_jobs)}


@app.post("/api/generate-video")
async def submit_job(req: GenerateRequest):
    """Submit a video generation job.

    Returns immediately with a job_id. Poll GET /api/jobs/{job_id} for status,
    then download from GET /api/jobs/{job_id}/download when completed.
    """
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="content cannot be empty")

    job_id = str(uuid.uuid4())[:8]
    output_path = str(OUTPUT_DIR / f"gen_video_{job_id}.mp4")

    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "output_path": None,
            "error": None,
            "created_at": time.time(),
            "completed_at": None,
        }

    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, req.content, output_path, req.model, req.image_model),
        daemon=True,
    )
    thread.start()

    return {
        "job_id": job_id,
        "status": "pending",
        "status_url": f"/api/jobs/{job_id}",
        "download_url": f"/api/jobs/{job_id}/download",
    }


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs with their current status."""
    with _jobs_lock:
        jobs = []
        for jid, job in _jobs.items():
            entry = {
                "job_id": jid,
                "status": job["status"],
                "created_at": job["created_at"],
                "completed_at": job["completed_at"],
                "error": job["error"],
            }
            jobs.append(entry)
        jobs.sort(key=lambda j: j["created_at"], reverse=True)
    return {"jobs": jobs}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the current status of a video generation job."""
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "error": job["error"],
        "created_at": job["created_at"],
        "completed_at": job["completed_at"],
        "download_url": f"/api/jobs/{job_id}/download"
        if job["status"] == "completed"
        else None,
    }


@app.get("/api/jobs/{job_id}/download")
async def download_video(job_id: str):
    """Download the completed video for a job."""
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is '{job['status']}', not yet completed",
        )

    out_path = job["output_path"]
    if not out_path or not os.path.isfile(out_path):
        raise HTTPException(status_code=500, detail="Output file not found on disk")

    return FileResponse(
        out_path,
        media_type="video/mp4",
        filename=f"gen_video_{job_id}.mp4",
    )


def main():
    """CLI entry point: parse args and start the uvicorn server."""
    try:
        from ww.env import load_env as _le

        _le()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Start the gen-video API server.")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development)",
    )

    args = parser.parse_args()

    print("Gen Video API server starting...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Submit:  POST http://{args.host}:{args.port}/api/generate-video")
    print(f"  Status:  GET  http://{args.host}:{args.port}/api/jobs/{{job_id}}")
    print(
        f"  Download: GET  http://{args.host}:{args.port}/api/jobs/{{job_id}}/download"
    )
    print(f"  Health:   GET  http://{args.host}:{args.port}/health")
    print()
    print("Example (curl):")
    print("  # Submit job")
    print("  curl -s -X POST http://localhost:8000/api/generate-video \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"content": "# Hello\\n\\nThis is a test video."}\'')
    print()
    print("  # Poll until completed (replace JOB_ID)")
    print("  curl -s http://localhost:8000/api/jobs/JOB_ID")
    print()
    print("  # Download video")
    print("  curl -s -o video.mp4 http://localhost:8000/api/jobs/JOB_ID/download")
    print()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
