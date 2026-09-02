"""
Face-aware photo cropper for resume / visa / ID photo sizes.

Detects the largest face with macOS Vision (VNDetectFaceRectanglesRequest),
frames it as a centered head-and-shoulders crop, then resamples to each
target pixel size.

Usage:
    ww image face <src.jpg>                         # all presets
    ww image face <src.jpg> -o ./out                # custom output dir
    ww image face <src.jpg> --size 600x600 --size 413x531  # only these sizes
    ww image face <src.jpg> --scale 2.7 --top 0.40  # tuning framing
    ww image face <src.jpg> --quality 90 --dpi 300

Requires macOS (pyobjc-framework-Vision + pyobjc-framework-Quartz).
"""

import os
import sys

from PIL import Image


# --- presets ----------------------------------------------------------------
# (name, width, height, description)
PRESETS = [
    ("square_600x600", 600, 600, "1:1   resume / profile"),
    ("rectangle_800x1000", 800, 1000, "4:5   resume / LinkedIn"),
    ("qmas_visa_1500x2000", 1500, 2000, "3:4   QMAS / HK visa"),
    ("1inch_id_295x413", 295, 413, "25x35mm  China 1-inch ID"),
    ("2inch_id_413x579", 413, 579, "35x53mm  China 2-inch ID"),
    ("passport_413x531", 413, 531, "33x48mm  passport / visa"),
]

# Framing defaults (in units of detected face height)
DEFAULT_FACE_SCALE = 2.7  # crop height = 2.7 x face height
DEFAULT_FACE_FRAC_FROM_TOP = 0.40  # face center sits 40% down from top


def detect_face(src_path):
    """Return (image_w, image_h, face_cx, face_cy, face_w, face_h) in pixels.

    Picks the largest detected face box (most likely the subject).
    """
    from Foundation import NSURL
    from Quartz import (
        CGImageSourceCreateWithURL,
        CGImageSourceCreateImageAtIndex,
        CGImageGetWidth,
        CGImageGetHeight,
    )
    from Vision import VNDetectFaceRectanglesRequest, VNImageRequestHandler

    url = NSURL.fileURLWithPath_(src_path)
    handler = VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    req = VNDetectFaceRectanglesRequest.alloc().init()
    ok = handler.performRequests_error_([req], None)
    if not ok[0]:
        raise RuntimeError(f"Vision request failed: {ok[1]!r}")
    results = req.results() or []
    if not results:
        raise RuntimeError("No face detected by Vision.")

    src = CGImageSourceCreateWithURL(url, None)
    cg = CGImageSourceCreateImageAtIndex(src, 0, None)
    w, h = CGImageGetWidth(cg), CGImageGetHeight(cg)

    bb = max(
        results,
        key=lambda r: r.boundingBox().size.width * r.boundingBox().size.height,
    ).boundingBox()  # normalized, origin bottom-left

    px = bb.origin.x * w
    py = (1 - bb.origin.y - bb.size.height) * h  # flip to top-left origin
    pw = bb.size.width * w
    ph = bb.size.height * h
    cx, cy = px + pw / 2, py + ph / 2
    print(
        f"  face px: x={px:.0f} y={py:.0f} w={pw:.0f} h={ph:.0f}  "
        f"cx={cx:.0f} cy={cy:.0f}"
    )
    return w, h, cx, cy, pw, ph


def compute_crop(
    sw, sh, cx, cy, fw, fh, target_w, target_h, face_scale, face_frac_from_top
):
    """Compute a clamped crop box (left, top, right, bottom) framed on the face."""
    ar = target_w / target_h
    crop_h = fh * face_scale
    crop_w = crop_h * ar

    # If width would exceed image, shrink by width instead
    if crop_w > sw:
        crop_w = sw
        crop_h = crop_w / ar
    # Never exceed image height either
    if crop_h > sh:
        crop_h = sh
        crop_w = crop_h * ar

    # horizontal: centered on face
    left = cx - crop_w / 2
    # vertical: face center at face_frac_from_top from top
    top = cy - face_frac_from_top * crop_h

    # clamp into bounds, preserving size
    if left < 0:
        left = 0
    if left + crop_w > sw:
        left = sw - crop_w
        if left < 0:
            left = 0
    if top < 0:
        top = 0
    if top + crop_h > sh:
        top = sh - crop_h
        if top < 0:
            top = 0

    return (
        int(round(left)),
        int(round(top)),
        int(round(left + crop_w)),
        int(round(top + crop_h)),
    )


def _parse_size(s):
    """Parse '600x600' or '600x600 = name' style into (name, w, h)."""
    desc = ""
    if "=" in s:
        s, desc = s.split("=", 1)
        desc = desc.strip()
    s = s.strip()
    if "x" not in s.lower():
        raise ValueError(f"bad size {s!r}, expected WxH")
    w_str, h_str = s.lower().split("x", 1)
    name = desc or s.lower().replace("x", "_")
    return (name, int(w_str), int(h_str), desc)


def _usage():
    print(__doc__)
    print("Presets (use --preset, or none for all):")
    for name, w, h, desc in PRESETS:
        print(f"  {name:24s} {w}x{h:<6d} {desc}")


def main():
    args = list(sys.argv[1:])

    if not args or args[0] in ("-h", "--help"):
        _usage()
        sys.exit(0 if args else 1)

    src = args[0]
    rest = args[1:]

    out_dir = None
    sizes = []  # list of (name, w, h, desc)
    only_presets = []  # list of preset names
    face_scale = DEFAULT_FACE_SCALE
    face_frac = DEFAULT_FACE_FRAC_FROM_TOP
    quality = 95
    dpi = 300
    fmt = "JPEG"

    i = 0
    while i < len(rest):
        a = rest[i]
        if a in ("-o", "--out", "--out-dir"):
            out_dir = rest[i + 1]
            i += 2
        elif a == "--size":
            sizes.append(_parse_size(rest[i + 1]))
            i += 2
        elif a == "--preset":
            only_presets.append(rest[i + 1])
            i += 2
        elif a in ("--scale", "--face-scale"):
            face_scale = float(rest[i + 1])
            i += 2
        elif a in ("--top", "--face-top"):
            face_frac = float(rest[i + 1])
            i += 2
        elif a == "--quality":
            quality = int(rest[i + 1])
            i += 2
        elif a == "--dpi":
            dpi = int(rest[i + 1])
            i += 2
        elif a == "--format":
            fmt = rest[i + 1].upper()
            i += 2
        elif a in ("-h", "--help"):
            _usage()
            sys.exit(0)
        else:
            print(f"Unknown option: {a}")
            _usage()
            sys.exit(1)

    if not os.path.exists(src):
        print(f"Input not found: {src}")
        sys.exit(1)

    # Resolve target size list
    if sizes:
        targets = sizes
    elif only_presets:
        name_map = {n: (n, w, h, d) for n, w, h, d in PRESETS}
        missing = [n for n in only_presets if n not in name_map]
        if missing:
            print(f"Unknown preset(s): {', '.join(missing)}")
            _usage()
            sys.exit(1)
        targets = [name_map[n] for n in only_presets]
    else:
        targets = PRESETS

    if out_dir is None:
        out_dir = os.path.join(
            os.path.dirname(os.path.abspath(src)),
            f"{os.path.splitext(os.path.basename(src))[0]}_face",
        )
    os.makedirs(out_dir, exist_ok=True)

    print(f"Source: {src}")
    sw, sh, cx, cy, fw, fh = detect_face(src)
    print(f"  image: {sw}x{sh}")
    print(f"  framing: scale={face_scale} top={face_frac}")

    im = Image.open(src)
    base = os.path.splitext(os.path.basename(src))[0]

    for name, tw, th, desc in targets:
        left, top, right, bottom = compute_crop(
            sw, sh, cx, cy, fw, fh, tw, th, face_scale, face_frac
        )
        cw, chh = right - left, bottom - top
        cropped = im.crop((left, top, right, bottom))
        resized = cropped.resize((tw, th), Image.LANCZOS)
        ext = "jpg" if fmt == "JPEG" else "png"
        out = os.path.join(out_dir, f"{base}_{name}.{ext}")
        save_kwargs = {}
        if fmt == "JPEG":
            save_kwargs = {"quality": quality, "dpi": (dpi, dpi)}
        resized.save(out, fmt, **save_kwargs)
        print(
            f"  {name}: crop=({left},{top})-({right},{bottom}) "
            f"{cw}x{chh} -> {tw}x{th}  {desc}"
        )

    print(f"\nDone. {len(targets)} file(s) in: {out_dir}")
