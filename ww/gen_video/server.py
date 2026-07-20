#!/usr/bin/env python3
"""ww gen-video server — Start a FastAPI server that generates videos from markdown content.

Usage:
    ww gen-video server [--port PORT] [--host HOST]

API:
    POST /api/generate-video
        Body: {"content": "markdown text", "model": "...", "image_model": "..."}
        Returns: video/mp4 file download

    GET /health
        Returns: {"status": "ok"}
"""

import argparse
import os
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


class GenerateResponse(BaseModel):
    success: bool
    video_path: str | None = None
    error: str | None = None


# Directory to store generated videos while the server is running
OUTPUT_DIR = Path("/tmp/gen_video_server_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/generate-video")
async def generate_video(req: GenerateRequest):
    """Generate a video from markdown content and return it as a file download.

    Accepts markdown text, runs the full pipeline (scenes → images → slides → video),
    and returns the resulting .mp4 file.
    """
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="content cannot be empty")

    # Generate a unique output path
    video_id = str(uuid.uuid4())[:8]
    output_path = str(OUTPUT_DIR / f"gen_video_{video_id}.mp4")

    try:
        success, out_path, error_msg = generate_video_from_content(
            req.content,
            output_path,
            model=req.model,
            image_model=req.image_model,
            verbose=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")

    if not success:
        raise HTTPException(
            status_code=500,
            detail=error_msg or "Video generation failed with unknown error",
        )

    if not out_path or not os.path.isfile(out_path):
        raise HTTPException(
            status_code=500, detail="Output file not found after generation"
        )

    return FileResponse(
        out_path,
        media_type="video/mp4",
        filename=f"gen_video_{video_id}.mp4",
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
    print(f"  Endpoint: POST http://{args.host}:{args.port}/api/generate-video")
    print(f"  Health:   GET  http://{args.host}:{args.port}/health")
    print()
    print("Example (curl):")
    print("  curl -X POST http://localhost:8000/api/generate-video \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"content": "# Hello\\n\\nThis is a test video."}\' \\')
    print("    --output video.mp4")
    print()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
