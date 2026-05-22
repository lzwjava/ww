"""Scan images in a directory for EXIF GPS location data, and optionally strip it.

Usage:
    ww image exif <input_dir> [--all] [-r] [--clean]
"""

import os
import argparse

from PIL import Image
from PIL.ExifTags import GPSTAGS


def _parse_gps_coords(value, ref):
    """Convert EXIF GPS rational tuple to decimal degrees."""
    d, m, s = (float(x) for x in value)
    decimal = d + m / 60.0 + s / 3600.0
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def _extract_gps(img):
    """Extract GPS coordinates from an image, or None if unavailable."""
    exif = img.getexif()
    if not exif:
        return None

    gps_info = exif.get_ifd(0x8825)
    if not gps_info:
        return None

    required = {"GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef"}
    tag_map = {GPSTAGS.get(k, k): k for k in gps_info}
    if not required.issubset(tag_map):
        return None

    lat = _parse_gps_coords(
        gps_info[tag_map["GPSLatitude"]], gps_info[tag_map["GPSLatitudeRef"]]
    )
    lon = _parse_gps_coords(
        gps_info[tag_map["GPSLongitude"]], gps_info[tag_map["GPSLongitudeRef"]]
    )
    return (lat, lon)


def _clean_gps_jpeg(path):
    """Remove GPS EXIF from a JPEG file in-place (no pixel re-encoding)."""
    import piexif

    data = piexif.load(path)
    if "GPS" not in data:
        return False
    del data["GPS"]
    piexif.insert(piexif.dump(data), path)
    return True


def _clean_gps_pillow(path):
    """Remove GPS EXIF using Pillow re-save (fallback for non-JPEG)."""
    img = Image.open(path)
    exif = img.getexif()
    if 34853 not in exif:
        img.close()
        return False
    del exif[34853]
    exif_bytes = exif.tobytes()
    # Save with original format and keep quality
    fmt = img.format or "JPEG"
    save_kwargs = {}
    if fmt == "JPEG":
        save_kwargs["quality"] = "keep"
    img.save(path, format=fmt, exif=exif_bytes, **save_kwargs)
    img.close()
    return True


def _is_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tiff", ".tif"}


def _is_jpeg(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in {".jpg", ".jpeg"}


def _collect_images(root_dir, recursive):
    """Yield (relpath, abspath) for every image under root_dir."""
    if recursive:
        for dirpath, _dirnames, filenames in os.walk(root_dir):
            for f in sorted(filenames):
                if _is_image(f):
                    abspath = os.path.join(dirpath, f)
                    relpath = os.path.relpath(abspath, root_dir)
                    yield relpath, abspath
    else:
        for f in sorted(os.listdir(root_dir)):
            abspath = os.path.join(root_dir, f)
            if os.path.isfile(abspath) and _is_image(f):
                yield f, abspath


def main():
    parser = argparse.ArgumentParser(
        description="Scan images for EXIF GPS data, optionally strip it."
    )
    parser.add_argument("input_dir", help="Directory containing images to scan")
    parser.add_argument(
        "--all",
        action="store_true",
        help="List all images, marking those with/without GPS data",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove GPS EXIF data from images that have it (in-place)",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.rstrip(os.sep)
    if not os.path.isdir(input_dir):
        print(f"Error: '{input_dir}' is not a directory")
        return

    found = 0
    cleaned = 0
    scanned = 0

    for relpath, abspath in _collect_images(input_dir, args.recursive):
        try:
            img = Image.open(abspath)
            coords = _extract_gps(img)
            img.close()
            scanned += 1
        except Exception as e:
            if args.all:
                print(f"  {relpath}  [error: {e}]")
            continue

        if coords:
            lat, lon = coords
            found += 1

            if args.clean:
                try:
                    if _is_jpeg(relpath):
                        ok = _clean_gps_jpeg(abspath)
                    else:
                        ok = _clean_gps_pillow(abspath)
                    if ok:
                        cleaned += 1
                        print(f"  {relpath}  GPS removed  ({lat:.6f}, {lon:.6f})")
                    else:
                        print(f"  {relpath}  GPS: {lat:.6f}, {lon:.6f}  [clean failed]")
                except Exception as e:
                    print(f"  {relpath}  GPS: {lat:.6f}, {lon:.6f}  [clean error: {e}]")
            else:
                maps_url = f"https://maps.google.com/?q={lat},{lon}"
                print(f"  {relpath}  GPS: {lat:.6f}, {lon:.6f}  {maps_url}")
        else:
            if args.all:
                print(f"  {relpath}  (no GPS)")

    print()
    parts = [f"Scanned: {scanned}", f"GPS found: {found}"]
    if args.clean:
        parts.append(f"Cleaned: {cleaned}")
    parts.append(f"Directory: {input_dir}")
    print("  ".join(parts))
