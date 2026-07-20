#!/usr/bin/env python3
"""ww gen-video upload — Upload a video to YouTube.

Reads YAML frontmatter from the markdown note to extract title/description/tags,
then uploads the MP4 to YouTube via the YouTube Data API v3.

Requires:
  pip install google-api-python-client google-auth-oauthlib

Setup:
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable YouTube Data API v3
  3. Create OAuth 2.0 credentials (Desktop app type)
  4. Save as ~/.google/client_secret.json
"""

import json
import os
import re
import sys
import webbrowser
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _parse_frontmatter(text):
    """Parse YAML frontmatter from markdown text. Returns (frontmatter_dict, body)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text

    yaml_text = match.group(1)
    body = text[match.end() :]

    # Simple key: value parser (no nested structures)
    frontmatter = {}
    for line in yaml_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip("\"'").strip()
            frontmatter[key] = value

    return frontmatter, body


def _clean_description(text):
    """Convert raw markdown body to a clean YouTube-safe description.

    - Removes reference link definitions ([N]: url)
    - Removes horizontal rules (---)
    - Removes table separator rows (|---|---|)
    - Strips markdown formatting symbols (**bold**, `code`, etc.)
    - Collapses excessive blank lines
    - Limits to 4000 bytes to stay well under YT's 5000 limit
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        # Skip reference link definitions: [N]: url "title"
        if re.match(r"^\[.*?\]:\s*https?://", line.strip()):
            continue
        # Skip horizontal rules
        if re.match(r"^-{3,}\s*$", line.strip()):
            continue
        # Skip table separator rows
        if re.match(r"^[\s\|:-]+$", line) and "|" in line and "---" in line:
            continue
        # Strip markdown formatting but keep text
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)  # **bold**
        line = re.sub(r"\*(.+?)\*", r"\1", line)  # *italic*
        line = re.sub(r"`(.+?)`", r"\1", line)  # `code`
        line = re.sub(r"^#+\s*", "", line)  # # headings
        # Replace < with text equivalent — YouTube rejects < as HTML-like
        line = line.replace("<", "less than ")
        cleaned.append(line)

    # Collapse multiple blank lines
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()

    # Truncate to 4000 bytes (UTF-8 aware)
    encoded = result.encode("utf-8")
    if len(encoded) > 4000:
        result = encoded[:4000].decode("utf-8", errors="ignore")
        result = result.rsplit("\n", 1)[0] + "\n\n..."

    return result


def _get_credentials(credential_file=None):
    """Get or refresh YouTube API credentials.

    Default credential path: ~/.google/client_secret.json
    Token cache: ~/.google/youtube_token.json
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    home = Path.home()
    google_dir = home / ".google"
    google_dir.mkdir(parents=True, exist_ok=True)

    if credential_file is None:
        credential_file = str(google_dir / "client_secret.json")

    token_file = google_dir / "youtube_token.json"
    credentials = None

    # Load cached token
    if token_file.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception:
            credentials = None

    # Refresh or get new credentials
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid:
        if not os.path.isfile(credential_file):
            print(f"Error: Google OAuth client secret not found at {credential_file}")
            print()
            print("To set up YouTube upload:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a project -> Enable YouTube Data API v3")
            print("3. Create OAuth 2.0 credentials (Desktop app type)")
            print("4. Download the JSON and save it as:")
            print(f"   {credential_file}")
            print("5. In Google Cloud Console, add this Authorized redirect URI:")
            print("   http://localhost:8080/")
            print()
            sys.exit(1)

        flow = InstalledAppFlow.from_client_secrets_file(credential_file, SCOPES)
        print("Opening browser for Google OAuth...")
        credentials = flow.run_local_server(port=8080)

    # Save token for next run
    with open(token_file, "w") as f:
        f.write(credentials.to_json())

    return credentials


def main():
    try:
        from ww.env import load_env as _le

        _le()
    except ImportError:
        pass

    args = list(sys.argv[1:])

    # ── Help ────────────────────────────────────────────────────────────────
    if not args or "--help" in args or "-h" in args:
        print("Usage: ww gen-video upload <note_path> <mp4_path> [options]")
        print()
        print("Upload a video to YouTube using metadata from a markdown note.")
        print()
        print("Arguments:")
        print("  note_path          Path to a markdown note with YAML frontmatter")
        print("                     (title extracted from frontmatter)")
        print("  mp4_path           Path to the MP4 video file to upload")
        print()
        print("Options:")
        print("  --public           Set video privacy to public (default: private)")
        print("  --unlisted         Set video privacy to unlisted (default: private)")
        print("  --credential PATH  Path to Google OAuth client_secret.json")
        print("  --description TEXT Override video description")
        print("  --tags TAG1,TAG2   Comma-separated tags (overrides frontmatter)")
        print()
        print("Examples:")
        print(
            "  ww gen-video upload notes/2026-07-20-tesla-p100-vs-m60-for-ai.md output.mp4"
        )
        print(
            "  ww gen-video upload notes/2026-07-20-tesla-p100-vs-m60-for-ai.md output.mp4 --public"
        )
        return

    if len(args) < 2:
        print("Error: Both note_path and mp4_path are required.")
        print("Usage: ww gen-video upload <note_path> <mp4_path>")
        sys.exit(1)

    note_path = args[0]
    mp4_path = args[1]

    # ── Parse options ───────────────────────────────────────────────────────
    privacy_status = "private"
    credential_file = None
    description_override = None
    tags_override = None

    i = 2
    while i < len(args):
        if args[i] == "--public":
            privacy_status = "public"
            i += 1
        elif args[i] == "--unlisted":
            privacy_status = "unlisted"
            i += 1
        elif args[i] == "--credential" and i + 1 < len(args):
            credential_file = args[i + 1]
            i += 2
        elif args[i] == "--description" and i + 1 < len(args):
            description_override = args[i + 1]
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags_override = args[i + 1].split(",")
            i += 2
        else:
            print(f"Unknown option: {args[i]}")
            sys.exit(1)

    # Resolve paths
    note_path = os.path.expanduser(note_path)
    mp4_path = os.path.expanduser(mp4_path)

    if not os.path.isfile(note_path):
        print(f"Error: Note file not found: {note_path}")
        sys.exit(1)
    if not os.path.isfile(mp4_path):
        print(f"Error: Video file not found: {mp4_path}")
        sys.exit(1)

    # ── Read note and extract metadata ──────────────────────────────────────
    with open(note_path, "r", encoding="utf-8") as f:
        text = f.read()

    frontmatter, body = _parse_frontmatter(text)

    title = frontmatter.get("title", "")
    if not title:
        title = os.path.splitext(os.path.basename(note_path))[0]

    tags = tags_override
    if tags is None and "tags" in frontmatter:
        tag_str = frontmatter["tags"]
        if isinstance(tag_str, str):
            tags = [t.strip() for t in tag_str.replace(",", " ").split() if t.strip()]

    if tags is None:
        tags = []

    description = description_override
    if description is None:
        description = _clean_description(body)

    # Append source attribution
    description += f"\n\nSource: {note_path}"

    print(f"Title: {title}")
    print(f"Description: {len(description)} chars")
    print(f"Tags: {', '.join(tags) if tags else '(none)'}")
    print(f"Privacy: {privacy_status}")
    print(f"Video: {mp4_path} ({os.path.getsize(mp4_path) / 1024 / 1024:.1f} MB)")
    print()

    # ── Authenticate and upload ─────────────────────────────────────────────
    print("Authenticating with Google...")
    credentials = _get_credentials(credential_file)

    print("Building YouTube API client...")
    youtube = build("youtube", "v3", credentials=credentials)

    print("Uploading video...")
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    media = MediaFileUpload(mp4_path, chunksize=5 * 1024 * 1024, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    try:
        response = request.execute()
    except HttpError as e:
        detail = e.content.decode() if hasattr(e, "content") and e.content else str(e)
        print(f"Error: YouTube API returned HTTP {e.status_code}")
        print(f"Details: {detail}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Upload failed: {e}")
        sys.exit(1)

    video_id = response.get("id")
    if not video_id:
        print("Error: No video ID in response.")
        print(f"Full response: {json.dumps(response, indent=2)}")
        sys.exit(1)

    url = f"https://youtu.be/{video_id}"
    print("\nUploaded successfully!")
    print(f"  Video ID: {video_id}")
    print(f"  URL: {url}")

    webbrowser.open(url)
