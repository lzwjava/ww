"""
ww card — Generate a professional business card from a resume Markdown + a photo.

Workflow:
  1. Extract a square head-and-shoulders avatar from the photo
     (macOS Vision face detection, falls back to a center square crop).
  2. Render a 2100x1200 business-card PNG with the avatar, name, role,
     short self-intro and contact links parsed from the resume.

Usage:
  ww card [--photo FILE] [--resume FILE] [-o DIR] [--intro TEXT] [--llm]
  ww card avatar [--photo FILE] [-o DIR]
"""

import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# defaults
# ---------------------------------------------------------------------------
DEFAULT_PHOTO = "/Users/lzwjava/Downloads/bb2297343d0f044bf94fcbca468986c5.jpg"
DEFAULT_RESUME = os.path.expanduser(
    "~/projects/jekyll-ai-blog/original/2025-01-11-resume-en.md"
)

DEFAULT_INTRO = (
    "Full-stack & AI engineer with 12 years of experience (9 corporate + 3 "
    "freelance) — banking platforms at HSBC and DBS, two startups, and 10 "
    "open-source projects with 500+ commits each. Hands-on LLM practice: trained "
    "GPT-2 up to 1.5B parameters on H200 and MI300X GPUs, ~5B tokens consumed "
    "in the past year. Blogger with 400+ posts and ~75K monthly page views. "
    "Open to AI / full-stack roles — Guangzhou, Shenzhen, Hong Kong, Singapore, "
    "or remote."
)

# Card canvas (3.5" x 2" scaled up)
CARD_W, CARD_H = 2100, 1200

# Palette
BG = (13, 27, 44)  # deep navy
PANEL = (21, 45, 72)  # left panel navy
ACCENT = (78, 190, 255)  # light blue accent
TEXT = (236, 241, 248)
MUTED = (148, 166, 188)

FONT_BOLD_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_REG_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


# ---------------------------------------------------------------------------
# fonts
# ---------------------------------------------------------------------------
def _load_font(size, bold=False):
    for path in FONT_BOLD_PATHS if bold else FONT_REG_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# resume parsing
# ---------------------------------------------------------------------------
def parse_resume(md_path):
    """Extract name, role, location and contact links from the resume Markdown."""
    data = {
        "name": "Zhiwei Li",
        "role": "AI Full Stack Engineer",
        "location": "Guangzhou, China",
        "links": {},
    }
    if not md_path or not os.path.exists(md_path):
        print(f"[card] resume not found: {md_path or '(none)'} — using defaults")
        return data

    with open(md_path, encoding="utf-8") as f:
        text = f.read()

    # Expected positions -> role
    m = re.search(r"Expected Positions:\s*([^\n]+)", text)
    if m:
        roles = [r.strip() for r in m.group(1).split("/")]
        if roles:
            data["role"] = roles[0]

    # Links section -> contact map (lowercased labels)
    m = re.search(r"##\s*Links(.*?)(?=\n##\s|\Z)", text, re.S)
    if m:
        for label, url in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", m.group(1)):
            data["links"][label.lower().strip()] = url

    return data


def _curated_intro():
    return DEFAULT_INTRO


def _llm_intro(resume_text):
    """Generate a short first-person intro with OpenRouter; fallback on failure."""
    try:
        from ww.llm.openrouter_client import call_openrouter_api_with_messages

        prompt = (
            "Write a concise 3-4 sentence professional 'About me' intro for a "
            "business card, in first person, based on this resume. Keep it under "
            "430 characters total. Plain text only, no markdown, no heading.\n\n"
            + (resume_text[:6000] if resume_text else "")
        )
        out = call_openrouter_api_with_messages(
            [{"role": "user", "content": prompt}], max_tokens=300
        )
        text = out.strip().strip('"').strip()
        if text:
            return text[:460]
    except Exception as e:  # noqa: BLE001 — network/API issues, fall back
        print(f"[card] LLM intro failed ({e}); using curated intro")
    return _curated_intro()


# ---------------------------------------------------------------------------
# avatar extraction
# ---------------------------------------------------------------------------
def _center_square_box(sw, sh):
    side = min(sw, sh)
    left = (sw - side) // 2
    top = (sh - side) // 2
    return (left, top, left + side, top + side)


def extract_avatar(photo, out_dir, size=1024):
    """Crop a square head-and-shoulders avatar. macOS Vision first, center fallback."""
    if not os.path.exists(photo):
        print(f"[card] photo not found: {photo}")
        sys.exit(1)

    img = Image.open(photo)
    sw, sh = img.size

    box = None
    try:
        # macOS Vision face detection (same detector as `ww image face`)
        from ww.image.face import detect_face

        _, _, cx, cy, fw, fh = detect_face(photo)
        print(
            f"[card] face detected: center=({cx:.0f},{cy:.0f}) face={fw:.0f}x{fh:.0f}"
        )
        side = fh * 2.3
        left = cx - side / 2
        top = cy - side * 0.42  # face center 42% down from top
        if left < 0:
            left = 0
        if left + side > sw:
            left = sw - side
        if top < 0:
            top = 0
        if top + side > sh:
            top = sh - side
        box = (int(left), int(top), int(left + side), int(top + side))
    except Exception as e:  # noqa: BLE001
        print(f"[card] face detection unavailable ({e}); using center crop")
        box = _center_square_box(sw, sh)

    avatar = img.crop(box).convert("RGB").resize((size, size), Image.LANCZOS)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "avatar.jpg")
    avatar.save(out, "JPEG", quality=92)
    print(f"[card] avatar saved: {out} ({size}x{size})")
    return avatar, out


# ---------------------------------------------------------------------------
# business card rendering
# ---------------------------------------------------------------------------
def _circle_mask(size):
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    return mask


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_card(avatar, data, intro, out_path):
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    d = ImageDraw.Draw(img)

    # --- left panel ---------------------------------------------------------
    d.rectangle((0, 0, 760, CARD_H), fill=PANEL)
    d.rectangle((756, 0, 760, CARD_H), fill=ACCENT)  # accent divider

    # avatar (circular)
    av_size = 400
    av = avatar.resize((av_size, av_size), Image.LANCZOS)
    av_center = (380, 300)
    img.paste(
        av,
        (av_center[0] - av_size // 2, av_center[1] - av_size // 2),
        _circle_mask(av_size),
    )
    d.ellipse(
        (
            av_center[0] - av_size // 2 - 6,
            av_center[1] - av_size // 2 - 6,
            av_center[0] + av_size // 2 + 6,
            av_center[1] + av_size // 2 + 6,
        ),
        outline=ACCENT,
        width=6,
    )

    # name
    name_f = _load_font(72, bold=True)
    name = data["name"]
    nw = d.textlength(name, font=name_f)
    d.text((380 - nw / 2, 580), name, font=name_f, fill=TEXT)

    # role
    role_f = _load_font(36, bold=True)
    role = data["role"]
    rw = d.textlength(role, font=role_f)
    d.text((380 - rw / 2, 690), role, font=role_f, fill=ACCENT)

    # location
    loc_f = _load_font(30)
    loc = data["location"]
    lw_ = d.textlength(loc, font=loc_f)
    d.text((380 - lw_ / 2, 770), loc, font=loc_f, fill=MUTED)

    # --- right content ------------------------------------------------------
    x0, y0 = 900, 150
    max_w = CARD_W - x0 - 160  # right margin 160

    # "ABOUT" label
    label_f = _load_font(34, bold=True)
    d.text((x0, y0), "ABOUT ME", font=label_f, fill=ACCENT)
    d.rectangle((x0, y0 + 52, x0 + 320, y0 + 56), fill=ACCENT)

    # intro body
    body_f = _load_font(38)
    lines = _wrap(d, intro, body_f, max_w)
    y = y0 + 96
    line_h = 56
    for ln in lines:
        d.text((x0, y), ln, font=body_f, fill=TEXT)
        y += line_h

    # "FIND ME" label — prioritize GitHub / Blog / LinkedIn
    priority = ["github", "blog", "linkedin", "ai portfolio", "software portfolio"]
    contacts = []
    for key in priority:
        if key in data["links"]:
            contacts.append((key, data["links"][key]))
        if len(contacts) == 5:
            break
    if not contacts:
        contacts = list(data["links"].items())[:5]
    find_y = y + 40
    d.text((x0, find_y), "FIND ME", font=label_f, fill=ACCENT)
    d.rectangle((x0, find_y + 52, x0 + 260, find_y + 56), fill=ACCENT)

    contact_f = _load_font(32)
    cy_ = find_y + 96
    contact_h = 54
    if contacts:
        for label, url in contacts[:5]:
            short = url.replace("https://", "").replace("http://", "")
            d.text((x0, cy_), f"{label.title()}: {short}", font=contact_f, fill=TEXT)
            cy_ += contact_h
    else:
        d.text((x0, cy_), "github.com/lzwjava · lzwjava.com", font=contact_f, fill=TEXT)

    # watermark
    wm_f = _load_font(26)
    wm = f"lzwjava.com  ·  github.com/lzwjava  ·  {data['role']}"
    ww_ = CARD_W - d.textlength(wm, font=wm_f) - 80
    d.text((ww_, CARD_H - 70), wm, font=wm_f, fill=MUTED)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    print(f"[card] business card saved: {out_path} ({CARD_W}x{CARD_H})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _usage():
    print(__doc__)
    print("Options:")
    print("  --photo, -p FILE   Source photo (default: ~/Downloads photo)")
    print("  --resume, -r FILE  Resume Markdown (default: jekyll-ai-blog resume)")
    print("  --out, -o DIR      Output directory (default: ./card_output)")
    print("  --intro TEXT       Custom 'About me' intro text")
    print("  --llm              Generate the intro with OpenRouter from the resume")
    print("  -h, --help         Show this help")


def main():
    args = sys.argv[1:]

    # mode token injected by ww/main.py ("make" or "avatar")
    mode = "make"
    if args and args[0] in ("make", "avatar"):
        mode = args.pop(0)

    photo = None
    resume = None
    out_dir = "card_output"
    intro = None
    use_llm = False

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-p", "--photo"):
            photo = args[i + 1]
            i += 2
        elif a in ("-r", "--resume"):
            resume = args[i + 1]
            i += 2
        elif a in ("-o", "--out"):
            out_dir = args[i + 1]
            i += 2
        elif a == "--intro":
            intro = args[i + 1]
            i += 2
        elif a == "--llm":
            use_llm = True
            i += 1
        elif a in ("-h", "--help"):
            _usage()
            sys.exit(0)
        elif not a.startswith("-") and photo is None:
            photo = a
            i += 1
        else:
            print(f"Unknown or unexpected argument: {a}")
            _usage()
            sys.exit(1)

    if photo is None:
        photo = DEFAULT_PHOTO if os.path.exists(DEFAULT_PHOTO) else None
    if resume is None:
        resume = DEFAULT_RESUME if os.path.exists(DEFAULT_RESUME) else None

    if photo is None or not os.path.exists(photo):
        print("[card] no photo found — pass one with --photo FILE")
        sys.exit(1)

    # ---- step 1: avatar ----------------------------------------------------
    avatar_img, avatar_path = extract_avatar(photo, out_dir)

    if mode == "avatar":
        print(f"[card] avatar only — done: {avatar_path}")
        return

    # ---- step 2: intro + resume data ---------------------------------------
    resume_text = None
    if resume and os.path.exists(resume):
        with open(resume, encoding="utf-8") as f:
            resume_text = f.read()
    data = parse_resume(resume)

    if intro is None:
        intro = _llm_intro(resume_text) if use_llm else _curated_intro()

    # ---- step 3: business card ---------------------------------------------
    out_path = os.path.join(out_dir, "business_card.png")
    render_card(avatar_img, data, intro, out_path)
    print(f"[card] done — card + avatar in: {os.path.abspath(out_dir)}")
