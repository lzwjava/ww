#!/usr/bin/env python3
"""ww gen-video — Generate a 15s vertical short-form video (9:16) from a markdown note.

5 slides × 3 seconds each. Each slide: image centered in frame, title text at top,
subtitle text at bottom. No audio. Optimized for Douyin / WeChat Video Account.
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
    """Generate an image via OpenRouter Flux model. Returns list of image URLs/data URLs."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set.")
        sys.exit(1)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = [{"role": "user", "content": prompt}]
    data = {"model": image_model, "messages": messages, "max_tokens": 1024}

    print(f"  Generating image via {image_model}...")
    resp = requests.post(url, headers=headers, json=data, timeout=(10, 120))
    if not resp.ok:
        detail = resp.text[:500]
        if "Request Moderated" in detail or "Protected Content" in detail:
            sanitized = _sanitize_prompt(prompt)
            print("  Moderation blocked — retrying with sanitized prompt...")
            return _openrouter_image(sanitized, image_model=image_model)
        print(f"  Warning: Image generation failed: HTTP {resp.status_code}")
        print(f"  {detail}")
        return []

    body = resp.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content")

    if content is None:
        # Flux models return images in message.images array
        for choice in body.get("choices", []):
            msg = choice.get("message", {})
            images = msg.get("images", [])
            if images:
                urls = []
                for img in images:
                    if isinstance(img, dict):
                        img_url = img.get("image_url", {}).get("url", "") or img.get("url", "")
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

        if body.get("url"):
            print("  Found image URL in response.url")
            return [body["url"]]

        print(f"  Warning: Unexpected response format. Keys: {list(body.keys())}")
        print(f"  Response preview: {str(body)[:500]}")
        return []

    # Extract image URLs from markdown image syntax
    urls = re.findall(r"!\[.*?\]\((https?://[^\s)]+)\)", content)
    if not urls:
        urls = re.findall(
            r"https?://[^\s)]+\.(?:png|jpg|jpeg|webp)(?:\?[^\s)]*)?",
            content,
            re.IGNORECASE,
        )
    if not urls:
        print(f"  Warning: No image URLs found in response. Content preview: {content[:200]}")
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
    if url_or_data.startswith("data:"):
        try:
            import base64

            match = re.match(r"data:image/(?:png|jpeg|jpg|webp);base64,(.+)", url_or_data)
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


def _generate_scenes(markdown_text, model=None):
    """Use LLM to generate 5 scenes with image prompts, titles, and subtitles."""
    sys_prompt = """You are a video script writer for short-form tech videos (Douyin/WeChat Video Account style).

Given a markdown article, produce exactly **5 scenes**. Each scene is a 3-second slide.

Each scene needs:
1. **image_prompt** — a detailed prompt for black-forest-labs/flux.2-pro to generate a vertical image. Style: clean tech illustration, infographic style, dark background with neon accents. MUST NOT contain trademarked brand names (NVIDIA, Intel, AMD, Tesla, etc.) — use descriptive alternatives like "GPU chip", "processor company", "graphics card".
2. **title** — short text (2-6 words) shown at the TOP of the slide. Bold, eye-catching.
3. **subtitle** — short text (5-15 words) shown at the BOTTOM of the slide. Explanatory, informative.

Output format — return ONLY valid JSON, no markdown fences:

{
  "scenes": [
    {
      "title": "Short Title",
      "subtitle": "Short explanatory subtitle for this slide.",
      "image_prompt": "Detailed image prompt for Flux."
    }
  ]
}"""

    messages = [
        {"role": "system", "content": sys_prompt},
        {
            "role": "user",
            "content": f"Create a 5-scene video script from this article:\n\n{markdown_text[:6000]}",
        },
    ]

    print("  Generating scenes (titles, subtitles, image prompts)...")
    raw = _openrouter_chat(messages, model=model, max_tokens=4096)

    # Strip any markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())

    # Find the outermost JSON object by tracking brace depth
    start = raw.find("{")
    if start == -1:
        print("Error: No JSON object found in LLM response.")
        print(f"Raw response:\n{raw[:500]}")
        sys.exit(1)

    depth = 0
    end = start
    in_string = False
    escape = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
    if depth != 0:
        print("Error: Unmatched braces in LLM response.")
        print(f"Raw response:\n{raw[:500]}")
        sys.exit(1)

    json_str = raw[start: end + 1]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse LLM response as JSON: {e}")
        print(f"Raw response:\n{raw[:500]}")
        sys.exit(1)

    scenes = data.get("scenes", [])
    if not scenes:
        print("Error: LLM response missing scenes.")
        print(f"Parsed JSON: {json.dumps(data, indent=2)[:500]}")
        sys.exit(1)

    print(f"  {len(scenes)} scenes generated")
    return scenes


def _create_slide_frame(image_path, title, subtitle, output_path, width=1080, height=1920):
    """Create a full slide frame: image centered + top title + bottom subtitle.

    The image is placed in the middle 60% of the frame. Top and bottom sections
    have semi-transparent black backgrounds with white text.
    """
    from PIL import Image, ImageDraw, ImageFont

    # Create black background
    frame = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # Load the scene image
    if os.path.isfile(image_path):
        try:
            scene_img = Image.open(image_path).convert("RGB")
        except Exception:
            scene_img = None
    else:
        scene_img = None

    if scene_img:
        # Place image centered in the middle 60% of the frame
        img_area_top = int(height * 0.20)
        img_area_bottom = int(height * 0.80)
        img_area_height = img_area_bottom - img_area_top
        img_area_width = width

        # Scale image to fit the area while maintaining aspect ratio
        img_aspect = scene_img.width / scene_img.height
        area_aspect = img_area_width / img_area_height

        if img_aspect > area_aspect:
            # Image is wider — fit to width
            new_w = img_area_width
            new_h = int(new_w / img_aspect)
        else:
            # Image is taller — fit to height
            new_h = img_area_height
            new_w = int(new_h * img_aspect)

        scene_img = scene_img.resize((new_w, new_h), Image.LANCZOS)

        # Center the image in the area
        img_x = (width - new_w) // 2
        img_y = img_area_top + (img_area_height - new_h) // 2
        frame.paste(scene_img, (img_x, img_y))

    # Load fonts
    title_font = None
    subtitle_font = None
    for fp in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]:
        if os.path.exists(fp):
            try:
                title_font = ImageFont.truetype(fp, 72)
                subtitle_font = ImageFont.truetype(fp, 40)
                break
            except Exception:
                continue
    if title_font is None:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # ── Top bar: title ─────────────────────────────────────────────────
    top_bar_height = int(height * 0.15)
    draw.rectangle([0, 0, width, top_bar_height], fill=(0, 0, 0, 200))

    # Center the title text
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (width - title_w) // 2
    title_y = (top_bar_height - title_h) // 2
    draw.text((title_x, title_y), title, fill="white", font=title_font)

    # ── Bottom bar: subtitle ───────────────────────────────────────────
    bottom_bar_height = int(height * 0.15)
    bottom_y = height - bottom_bar_height
    draw.rectangle([0, bottom_y, width, height], fill=(0, 0, 0, 200))

    # Word-wrap subtitle
    words = subtitle.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=subtitle_font)
        if bbox[2] - bbox[0] > width - 120:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    # Center subtitle text vertically in bottom bar
    line_height = 48
    total_text_height = len(lines) * line_height
    text_start_y = bottom_y + (bottom_bar_height - total_text_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=subtitle_font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        y = text_start_y + i * line_height
        draw.text((x, y), line, fill="white", font=subtitle_font)

    # Add a subtle gradient line separator between bars and image area
    for y_offset in range(3):
        draw.rectangle([0, top_bar_height + y_offset, width, top_bar_height + y_offset + 1],
                       fill=(50, 50, 50, 100))
        draw.rectangle([0, bottom_y + y_offset, width, bottom_y + y_offset + 1],
                       fill=(50, 50, 50, 100))

    frame.save(output_path, "PNG")
    return output_path


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
        print("Generate a 15-second vertical short-form video (9:16) from a markdown note.")
        print("5 slides × 3 seconds each. No audio.")
        print("Optimized for Douyin / WeChat Video Account.")
        print()
        print("Options:")
        print("  --output PATH       Output video path (default: <input_name>_video.mp4)")
        print("  --model MODEL       LLM model for script generation (default: $MODEL)")
        print("  --image-model MODEL Image generation model (default: black-forest-labs/flux.2-pro)")
        print()
        print("Examples:")
        print("  ww gen-video notes/2026-07-20-tesla-p100-vs-m60-for-ai-en.md")
        return

    file_path = args[0]

    output_path = None
    model = None
    image_model = "black-forest-labs/flux.2-pro"

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

    # ── Step 2: Generate scenes (titles, subtitles, image prompts) ─────────
    print("Step 1/3: Generating scenes (titles, subtitles, image prompts)...")
    scenes = _generate_scenes(md_content, model=model)
    print(f"Scenes: {len(scenes)}")

    for i, s in enumerate(scenes):
        print(f"  Scene {i+1}: \"{s.get('title', '')}\" — {s.get('subtitle', '')[:60]}...")

    # ── Step 3: Generate images via Flux ──────────────────────────────────
    print("\nStep 2/3: Generating images via Flux...")
    temp_dir = Path(tempfile.mkdtemp(prefix="gen_video_"))
    raw_image_paths = []

    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        if not prompt:
            continue

        print(f"\n  Scene {i+1}/{len(scenes)}: {prompt[:80]}...")
        img_urls = _openrouter_image(prompt, image_model=image_model)

        if img_urls:
            img_path = temp_dir / f"raw_scene_{i:03d}.png"
            success = _download_image(img_urls[0], str(img_path))
            if success:
                raw_image_paths.append(str(img_path))
            else:
                print("  Warning: Image download failed")
                # Create a simple colored placeholder
                placeholder = temp_dir / f"raw_scene_{i:03d}.png"
                from PIL import Image as PILImage
                bg = PILImage.new("RGB", (1080, 1920), (20, 20, 40))
                bg.save(str(placeholder))
                raw_image_paths.append(str(placeholder))
        else:
            print("  Creating placeholder...")
            placeholder = temp_dir / f"raw_scene_{i:03d}.png"
            from PIL import Image as PILImage
            bg = PILImage.new("RGB", (1080, 1920), (20, 20, 40))
            bg.save(str(placeholder))
            raw_image_paths.append(str(placeholder))

    # Ensure exactly 5 images (pad or trim)
    while len(raw_image_paths) < 5:
        placeholder = temp_dir / f"raw_scene_{len(raw_image_paths):03d}.png"
        from PIL import Image as PILImage
        bg = PILImage.new("RGB", (1080, 1920), (20, 20, 40))
        bg.save(str(placeholder))
        raw_image_paths.append(str(placeholder))
    raw_image_paths = raw_image_paths[:5]

    # ── Step 4: Create slide frames with text overlays ────────────────────
    print("\nStep 3/3: Creating slide frames and assembling video...")
    slide_frames = []
    for i, (img_path, scene) in enumerate(zip(raw_image_paths, scenes[:5])):
        title = scene.get("title", "")
        subtitle = scene.get("subtitle", "")
        slide_path = temp_dir / f"slide_{i:03d}.png"
        _create_slide_frame(img_path, title, subtitle, str(slide_path))
        slide_frames.append(str(slide_path))
        print(f"  Slide {i+1}: \"{title}\"")

    # ── Step 5: Assemble video ────────────────────────────────────────────
    print("\nAssembling video (5 slides × 3s = 15s)...")
    try:
        seg_files = []
        for i, slide_path in enumerate(slide_frames):
            seg_file = temp_dir / f"seg_{i:03d}.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", str(slide_path),
                    "-c:v", "libx264",
                    "-t", "3",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    "-vf", "scale=1080:1920",
                    str(seg_file),
                ],
                check=True, capture_output=True, text=True, timeout=60,
            )
            seg_files.append(str(seg_file))

        concat_file = temp_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for s in seg_files:
                f.write(f"file '{s}'\n")

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                output_path,
            ],
            check=True, capture_output=True, text=True, timeout=120,
        )

        success = True
    except subprocess.CalledProcessError as e:
        print(f"Error: FFmpeg failed: {e.stderr[:500] if e.stderr else e}")
        success = False

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    if success:
        print(f"\n✓ Video created: {output_path}")
        try:
            size = os.path.getsize(output_path)
            print(f"  Size: {size / 1024 / 1024:.1f} MB")
            dur = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "json", output_path],
                capture_output=True, text=True, timeout=10,
            )
            d = json.loads(dur.stdout)["format"]["duration"]
            print(f"  Duration: {float(d):.1f}s")
        except Exception:
            pass
    else:
        print("\n✗ Video creation failed.")
        sys.exit(1)