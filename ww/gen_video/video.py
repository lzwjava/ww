#!/usr/bin/env python3
"""ww gen-video — Generate a vertical short-form video (9:16) from a markdown note.

Reads a markdown file, uses an LLM to create a narration script and image prompts,
generates images via black-forest-labs/flux.2-pro on OpenRouter, creates TTS audio
via macOS `say`, and assembles the final video with FFmpeg.

Optimized for Douyin / WeChat Video Account (1080×1920, vertical).
"""

import json
import os
import re
import sys
import tempfile
import subprocess
from pathlib import Path

import requests


# ── helpers ────────────────────────────────────────────────────────────────


def _check_proxy():
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        val = os.environ.get(var, "")
        if val:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(val)
                host = parsed.hostname
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                import socket

                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
                return f"{var}={val} (port {port} reachable)"
            except Exception as e:
                return f"{var}={val} (UNREACHABLE: {e})"
    return "No proxy configured"


def _openrouter_chat(messages, model=None, max_tokens=4096):
    """Call OpenRouter chat completions and return the response text."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set.")
        sys.exit(1)

    if model is None:
        model = os.getenv("MODEL")
    if not model:
        print("Error: MODEL not set and no model specified.")
        sys.exit(1)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {"model": model, "messages": messages, "max_tokens": max_tokens}

    resp = requests.post(url, headers=headers, json=data, timeout=(10, 120))
    if not resp.ok:
        raise Exception(
            f"OpenRouter API error: HTTP {resp.status_code}\n{resp.text[:1000]}"
        )

    body = resp.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise Exception(f"Empty response from model {model}")
    return content


def _openrouter_image(prompt, image_model="black-forest-labs/flux.2-pro"):
    """Generate an image via OpenRouter Flux model. Returns list of image URLs."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set.")
        sys.exit(1)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]
    data = {"model": image_model, "messages": messages, "max_tokens": 1024}

    print(f"  Generating image via {image_model}...")
    resp = requests.post(url, headers=headers, json=data, timeout=(10, 120))
    if not resp.ok:
        print(f"  Warning: Image generation failed: HTTP {resp.status_code}")
        detail = resp.text[:500]
        # If moderation blocked, retry with a sanitized prompt
        if "Request Moderated" in detail or "Protected Content" in detail:
            sanitized = _sanitize_prompt(prompt)
            print("  Moderation blocked — retrying with sanitized prompt...")
            return _openrouter_image(sanitized, image_model=image_model)
        print(f"  {detail}")
        return []

    body = resp.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content")

    if content is None:
        # Try alternative response format (image generation API)
        # Flux models on OpenRouter return images in message.images array
        for choice in body.get("choices", []):
            msg = choice.get("message", {})
            images = msg.get("images", [])
            if images:
                urls = []
                for img in images:
                    if isinstance(img, dict):
                        img_url = img.get("image_url", {}).get("url", "") or img.get(
                            "url", ""
                        )
                        if img_url:
                            urls.append(img_url)
                if urls:
                    print(f"  Found {len(urls)} image(s) via message.images")
                    return urls
            # Check for image_url in content parts
            c = msg.get("content")
            if isinstance(c, list):
                for part in c:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        img_url = part.get("image_url", {}).get("url", "")
                        if img_url:
                            print("  Found image URL in content parts")
                            return [img_url]
            # Check for url field
            if msg.get("url"):
                print("  Found image URL in message.url")
                return [msg["url"]]

        # Try the images endpoint format
        images = body.get("data", [])
        if images:
            urls = []
            for img in images:
                if isinstance(img, dict) and img.get("url"):
                    urls.append(img["url"])
            if urls:
                print(f"  Found {len(urls)} image(s) via data array")
                return urls

        # Try raw response fields
        if body.get("url"):
            print("  Found image URL in response.url")
            return [body["url"]]

        print(f"  Warning: Unexpected response format. Keys: {list(body.keys())}")
        print(f"  Response preview: {str(body)[:500]}")
        return []

    # Extract image URLs from markdown image syntax
    urls = re.findall(r"!\[.*?\]\((https?://[^\s)]+)\)", content)
    if not urls:
        # Try direct URL in content
        urls = re.findall(
            r"https?://[^\s)]+\.(?:png|jpg|jpeg|webp)(?:\?[^\s)]*)?",
            content,
            re.IGNORECASE,
        )
    if not urls:
        print(
            f"  Warning: No image URLs found in response. Content preview: {content[:200]}"
        )
        return []

    print(f"  Got {len(urls)} image(s): {urls[0][:80]}")
    return urls


def _sanitize_prompt(prompt):
    """Remove trademarked brand names that might trigger moderation."""
    replacements = {
        r"\bNVIDIA\b": "GPU chip",
        r"\bTesla\b": "Data Center GPU",
        r"\bRTX\b": "GPU",
        r"\bGeForce\b": "Graphics Card",
        r"\bIntel\b": "Processor",
        r"\bAMD\b": "Chip maker",
    }
    result = prompt
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _download_image(url_or_data, output_path):
    """Download an image from URL or decode a base64 data URL to a local file."""
    # Handle data URLs (base64)
    if url_or_data.startswith("data:"):
        try:
            import base64

            match = re.match(
                r"data:image/(?:png|jpeg|jpg|webp);base64,(.+)", url_or_data
            )
            if match:
                image_data = base64.b64decode(match.group(1))
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"  Decoded base64 image: {output_path}")
                return True
            else:
                print("  Warning: Unknown data URL format")
                return False
        except Exception as e:
            print(f"  Warning: Failed to decode base64 image: {e}")
            return False

    # Regular HTTP URL
    try:
        resp = requests.get(url_or_data, timeout=30)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)
        print(f"  Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"  Warning: Failed to download image: {e}")
        return False


def _strip_frontmatter(text):
    """Remove YAML frontmatter (--- ... ---) from markdown."""
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)


def _generate_script_and_prompts(markdown_text, model=None):
    """Use LLM to generate a narration script and image prompts from the markdown."""
    sys_prompt = """You are a video script writer for short-form tech videos (Douyin/WeChat Video Account style).

Given a markdown article, produce:
1. A **narration script** — spoken in ~60-90 seconds, concise, conversational, in English.
2. **4-6 image prompts** — each prompt describes a visual scene to generate with an AI image model (black-forest-labs/flux.2-pro). These should illustrate key concepts from the article.

Rules:
- Narration should be natural and engaging, like a tech explainer video.
- Each image prompt should be detailed, descriptive, suitable for text-to-image generation. Include style hints like "clean tech illustration", "3D render style", "infographic style", "dark background with neon accents".
- Each image prompt should pair with a segment of the narration.
- The video is 1080×1920 vertical (9:16) — so designs should be vertical-friendly.
- IMPORTANT: Image prompts MUST NOT contain trademarked brand names (NVIDIA, Intel, AMD, Tesla, etc.) — use descriptive alternatives like "GPU chip", "processor company", "graphics card".

Output format — return ONLY valid JSON, no markdown fences:

{
  "script": "Full narration text here...",
  "scenes": [
    {
      "narration": "Segment of narration for this scene.",
      "image_prompt": "Detailed image prompt for generation."
    }
  ]
}

The narration segmentation should feel natural when spoken. Each scene's narration should be roughly equal length (~15-20 seconds of spoken text each)."""

    messages = [
        {"role": "system", "content": sys_prompt},
        {
            "role": "user",
            "content": f"Create a video script from this article:\n\n{markdown_text[:6000]}",
        },
    ]

    print("  Generating script and image prompts...")
    raw = _openrouter_chat(messages, model=model, max_tokens=4096)

    # Strip any markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                print("Error: Could not parse LLM response as JSON.")
                print(f"Raw response:\n{raw[:500]}")
                sys.exit(1)
        else:
            print("Error: No JSON found in LLM response.")
            print(f"Raw response:\n{raw[:500]}")
            sys.exit(1)

    script = data.get("script", "")
    scenes = data.get("scenes", [])
    if not script or not scenes:
        print("Error: LLM response missing script or scenes.")
        print(f"Parsed JSON: {json.dumps(data, indent=2)[:500]}")
        sys.exit(1)

    print(f"  Script length: {len(script)} chars, {len(scenes)} scenes")
    return script, scenes


def _generate_tts(text, output_path, voice="Tingting"):
    """Generate TTS audio using macOS `say` command, convert to AAC.

    Voice options: Tingting (Chinese), Samantha (US English), etc.
    """
    temp_aiff = output_path + ".aiff"
    try:
        subprocess.run(
            ["say", "-v", voice, "-o", temp_aiff, text],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        print(f"  Warning: macOS say failed: {e.stderr}")
        # Try with a different voice
        try:
            subprocess.run(
                ["say", "-v", "Samantha", "-o", temp_aiff, text],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            print("  TTS fallback: used Samantha voice")
        except subprocess.CalledProcessError as e2:
            print(f"  Error: TTS generation failed: {e2.stderr}")
            return None

    # Convert AIFF to AAC
    subprocess.run(
        ["ffmpeg", "-y", "-i", temp_aiff, "-c:a", "aac", "-b:a", "128k", output_path],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    os.unlink(temp_aiff)

    # Get duration
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                output_path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        dur = float(json.loads(result.stdout)["format"]["duration"])
        print(f"  TTS duration: {dur:.1f}s")
        return dur
    except Exception as e:
        print(f"  Warning: Could not get TTS duration: {e}")
        return None


def _create_text_overlay_image(
    text, output_path, width=1080, height=1920, font_size=48
):
    """Create a text overlay image using Pillow for the video."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to load a nice font
    font = None
    for fp in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    # Word-wrap text
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > width - 100:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    # Calculate total height
    line_height = font_size + 12
    total_height = len(lines) * line_height
    start_y = (height - total_height) // 2

    # Draw semi-transparent background
    bg_height = total_height + 40
    bg_y = start_y - 20
    draw.rectangle([0, bg_y, width, bg_y + bg_height], fill=(0, 0, 0, 160))

    # Draw each line
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        y = start_y + i * line_height
        draw.text((x, y), line, fill="white", font=font)

    img.save(output_path)
    return output_path


def _create_video_with_ffmpeg(
    scenes, image_paths, audio_path, output_path, scene_audio_paths=None
):
    """Assemble the final vertical video using FFmpeg.

    Uses concat filter with crossfade transitions between image scenes,
    synchronized with the narration audio.
    """
    width, height = 1080, 1920
    return _create_simple_slideshow(image_paths, audio_path, output_path, width, height)


def _create_simple_slideshow(
    image_paths, audio_path, output_path, width=1080, height=1920
):
    """Create a simple slideshow video with all images and a single audio track."""
    if not image_paths:
        print("Error: No images to create video.")
        return False

    # Get audio duration
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                audio_path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        audio_duration = float(json.loads(result.stdout)["format"]["duration"])
    except Exception as e:
        print(f"Warning: Could not get audio duration: {e}")
        audio_duration = 60.0

    # Calculate per-image duration (split evenly)
    num_images = len(image_paths)
    per_image_duration = audio_duration / num_images

    # Build a concat filter with transitions
    # Simple approach: use the concat demuxer with individual image+audio segments
    temp_dir = Path(tempfile.mkdtemp(prefix="gen_video_"))

    try:
        # Create a temp video for each image with its own duration
        segment_files = []
        for i, img_path in enumerate(image_paths):
            seg_file = temp_dir / f"seg_{i:03d}.mp4"
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(img_path),
                "-c:v",
                "libx264",
                "-t",
                f"{per_image_duration:.2f}",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                "-r",
                "30",
                str(seg_file),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
            segment_files.append(str(seg_file))

        # Create concat file list
        concat_file = temp_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        # Concatenate video segments
        concat_video = temp_dir / "concat_video.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(concat_video),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Add audio
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(concat_video),
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                output_path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        print(f"Video created: {output_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: FFmpeg failed: {e.stderr[:500] if e.stderr else e}")
        return False
    finally:
        # Cleanup temp files
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    try:
        from ww.env import load_env as _le

        _le()
    except ImportError:
        pass

    # Parse args
    args = list(sys.argv[1:])

    if not args or "--help" in args or "-h" in args:
        print("Usage: ww gen-video <file_path> [options]")
        print()
        print("Generate a vertical short-form video (9:16) from a markdown note.")
        print("Optimized for Douyin / WeChat Video Account.")
        print()
        print("Options:")
        print(
            "  --output PATH       Output video path (default: <input_name>_video.mp4)"
        )
        print("  --model MODEL       LLM model for script generation (default: $MODEL)")
        print(
            "  --image-model MODEL Image generation model (default: black-forest-labs/flux.2-pro)"
        )
        print("  --voice VOICE       TTS voice (default: Tingting)")
        print("  --no-tts            Skip TTS generation (use existing audio file)")
        print("  --audio PATH        Use existing audio file instead of generating TTS")
        print()
        print("Examples:")
        print("  ww gen-video notes/2026-07-20-tesla-p100-vs-m60-for-ai-en.md")
        print(
            "  ww gen-video notes/my-article.md --output my_video.mp4 --voice Samantha"
        )
        return

    file_path = args[0]

    # Parse options
    output_path = None
    model = None
    image_model = "black-forest-labs/flux.2-pro"
    voice = "Tingting"
    no_tts = False
    audio_path = None

    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == "--image-model" and i + 1 < len(args):
            image_model = args[i + 1]
            i += 2
        elif args[i] == "--voice" and i + 1 < len(args):
            voice = args[i + 1]
            i += 2
        elif args[i] == "--no-tts":
            no_tts = True
            i += 1
        elif args[i] == "--audio" and i + 1 < len(args):
            audio_path = args[i + 1]
            no_tts = True
            i += 2
        else:
            print(f"Unknown option: {args[i]}")
            sys.exit(1)

    # Resolve input file
    file_path = os.path.expanduser(file_path)
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    if output_path is None:
        base = os.path.splitext(os.path.basename(file_path))[0]
        output_path = f"{base}_video.mp4"

    # ── Step 1: Read markdown ──────────────────────────────────────────────
    print(f"Reading: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        raw_md = f.read()

    md_content = _strip_frontmatter(raw_md)
    print(f"Content length: {len(md_content)} chars")

    # ── Step 2: Generate script and image prompts ──────────────────────────
    print("Step 1/4: Generating script and image prompts...")
    script, scenes = _generate_script_and_prompts(md_content, model=model)

    print(f"\nScript preview: {script[:150]}...")
    print(f"Scenes: {len(scenes)}")

    # ── Step 3: Generate images ────────────────────────────────────────────
    print("\nStep 2/4: Generating images via Flux...")
    temp_dir = Path(tempfile.mkdtemp(prefix="gen_video_"))
    image_paths = []

    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        if not prompt:
            continue

        print(f"\n  Scene {i + 1}/{len(scenes)}: {prompt[:80]}...")
        img_urls = _openrouter_image(prompt, image_model=image_model)

        if img_urls:
            img_path = temp_dir / f"scene_{i:03d}.png"
            success = _download_image(img_urls[0], str(img_path))
            if success:
                image_paths.append(str(img_path))
                # Resize/crop to vertical — use a temp file to avoid overwrite issues
                resized = temp_dir / f"scene_{i:03d}_resized.png"
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(img_path),
                        "-vf",
                        f"scale={1080}:{1920}:force_original_aspect_ratio=decrease,pad={1080}:{1920}:(ow-iw)/2:(oh-ih)/2:black",
                        "-frames:v",
                        "1",
                        str(resized),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    os.replace(str(resized), str(img_path))
                else:
                    print(f"  Warning: FFmpeg resize failed: {result.stderr[:200]}")
            else:
                print("  Warning: Image download failed, will use a fallback frame")
        else:
            # Create a fallback text overlay image
            print("  Creating fallback text overlay...")
            fallback_path = temp_dir / f"scene_{i:03d}.png"
            _create_text_overlay_image(
                scene.get("narration", prompt)[:100],
                str(fallback_path),
            )
            image_paths.append(str(fallback_path))

    # Ensure we have at least 1 image
    if not image_paths:
        print("Warning: No images generated. Creating a fallback frame.")
        fallback = temp_dir / "fallback.png"
        _create_text_overlay_image("AI Video", str(fallback))
        image_paths.append(str(fallback))

    # ── Step 4: Generate TTS audio ─────────────────────────────────────────
    print("\nStep 3/4: Generating narration audio...")
    if no_tts and audio_path:
        # Use provided audio
        audio_path = os.path.expanduser(audio_path)
        if not os.path.isfile(audio_path):
            print(f"Error: Audio file not found: {audio_path}")
            sys.exit(1)
        print(f"  Using existing audio: {audio_path}")
    elif no_tts:
        print("  Skipping TTS (--no-tts)")
        audio_path = None
    else:
        audio_path = str(temp_dir / "narration.aac")
        # Generate TTS for the full script
        dur = _generate_tts(script, audio_path, voice=voice)
        if dur is None:
            print("Warning: TTS generation failed. Video will be silent.")
            audio_path = None

    # ── Step 5: Assemble video ─────────────────────────────────────────────
    print("\nStep 4/4: Assembling video...")
    if audio_path and os.path.isfile(audio_path):
        success = _create_simple_slideshow(
            image_paths,
            audio_path,
            output_path,
        )
    else:
        # No audio — create a video with a fixed duration per image
        print("  No audio track — creating silent video with 5s per image")
        try:
            per_img = 5.0
            seg_files = []
            for i, img_path in enumerate(image_paths):
                seg_file = temp_dir / f"seg_{i:03d}.mp4"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-loop",
                        "1",
                        "-i",
                        str(img_path),
                        "-c:v",
                        "libx264",
                        "-t",
                        str(per_img),
                        "-pix_fmt",
                        "yuv420p",
                        "-vf",
                        "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
                        "-r",
                        "30",
                        str(seg_file),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                seg_files.append(str(seg_file))

            concat_file = temp_dir / "concat.txt"
            with open(concat_file, "w") as f:
                for s in seg_files:
                    f.write(f"file '{s}'\n")

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    output_path,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            success = True
        except subprocess.CalledProcessError as e:
            print(f"Error: FFmpeg failed: {e.stderr[:500] if e.stderr else e}")
            success = False

    # Cleanup temp dir
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)

    if success:
        print(f"\n✓ Video created: {output_path}")
        # Get file size
        try:
            size = os.path.getsize(output_path)
            print(f"  Size: {size / 1024 / 1024:.1f} MB")
        except Exception:
            pass
    else:
        print("\n✗ Video creation failed.")
        sys.exit(1)
