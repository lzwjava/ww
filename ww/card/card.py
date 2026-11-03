"""
ww card — Generate a professional business card from a resume Markdown + a photo.

Workflow:
  1. Extract a square head-and-shoulders avatar from the photo
     (macOS Vision face detection, falls back to a center square crop).
  2. Render a 2100x1200 business-card PNG with the avatar, name, role,
     short self-intro and contact links parsed from the resume.

Usage:
  ww card [--photo FILE] [--resume FILE] [-o DIR] [--lang en|zh] [--intro TEXT] [--llm]
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

ZH_INTRO = (
    "拥有 12 年以上经验的全栈与 AI 工程师（9 年企业、3 年自由职业），参与过汇丰（HSBC）"
    "与星展（DBS）银行平台，也是 10 个 500+ 提交开源项目的主要开发者。热衷 LLM：在 H200 "
    "与 MI300X 上训练 GPT-2 至 1.5B 参数，近一年消费约 50 亿 token。博主：400+ 文章，月访问"
    "约 7.5 万。欢迎 AI / 全栈岗位，广州、深圳、香港、新加坡或远程。"
)

ZH_NAME = "李智维"
ZH_ROLE = "AI 工程师"
ZH_LOCATION = "中国广州"
ZH_CONTACT_LABELS = {
    "github": "GitHub",
    "blog": "博客",
    "linkedin": "领英",
    "ai portfolio": "AI 作品集",
    "software portfolio": "软件作品集",
}

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
FONT_CJK_BOLD_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
FONT_CJK_REG_PATHS = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


# ---------------------------------------------------------------------------
# fonts
# ---------------------------------------------------------------------------
def _load_font(size, bold=False, lang="en"):
    if lang == "zh":
        paths = FONT_CJK_BOLD_PATHS if bold else FONT_CJK_REG_PATHS
    else:
        paths = FONT_BOLD_PATHS if bold else FONT_REG_PATHS
    for path in paths:
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


def _curated_intro(lang="en"):
    return ZH_INTRO if lang == "zh" else DEFAULT_INTRO


def _llm_intro(resume_text, lang="en"):
    """Generate a short first-person intro with OpenRouter; fallback on failure."""
    try:
        from ww.llm.openrouter_client import call_openrouter_api_with_messages

        if lang == "zh":
            prompt = (
                "根据这份简历，为名片写一段简洁的中文“关于我”介绍，第一人称，"
                "3-4 句话，总字数控制在 150 字以内。纯文本，不要 markdown，不要标题。\n\n"
                + (resume_text[:6000] if resume_text else "")
            )
            limit = 170
        else:
            prompt = (
                "Write a concise 3-4 sentence professional 'About me' intro for a "
                "business card, in first person, based on this resume. Keep it under "
                "430 characters total. Plain text only, no markdown, no heading.\n\n"
                + (resume_text[:6000] if resume_text else "")
            )
            limit = 460
        out = call_openrouter_api_with_messages(
            [{"role": "user", "content": prompt}], max_tokens=300
        )
        text = out.strip().strip('"').strip()
        if text:
            return text[:limit]
    except Exception as e:  # noqa: BLE001 — network/API issues, fall back
        print(f"[card] LLM intro failed ({e}); using curated intro")
    return _curated_intro(lang)


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


def _wrap(draw, text, font, max_w, cjk=False):
    if cjk:
        return _wrap_cjk(draw, text, font, max_w)
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


def _wrap_cjk(draw, text, font, max_w):
    """CJK-friendly wrap — Chinese can break anywhere (prefer after spaces/punct)."""
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            cur = cur.rstrip()
            if cur:
                lines.append(cur)
            cur = "" if ch == " " else ch
    cur = cur.strip()
    if cur:
        lines.append(cur)
    return lines


def render_card(avatar, data, intro, out_path, lang="en"):
    zh = lang == "zh"
    name = ZH_NAME if zh else data["name"]
    role = ZH_ROLE if zh else data["role"]
    loc = ZH_LOCATION if zh else data["location"]
    about_label = "关于我" if zh else "ABOUT ME"
    find_label = "联系我" if zh else "FIND ME"
    contact_labels = ZH_CONTACT_LABELS if zh else {}

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
    name_f = _load_font(72, bold=True, lang=lang)
    nw = d.textlength(name, font=name_f)
    d.text((380 - nw / 2, 580), name, font=name_f, fill=TEXT)

    # role
    role_f = _load_font(36, bold=True, lang=lang)
    rw = d.textlength(role, font=role_f)
    d.text((380 - rw / 2, 690), role, font=role_f, fill=ACCENT)

    # location
    loc_f = _load_font(30, lang=lang)
    lw_ = d.textlength(loc, font=loc_f)
    d.text((380 - lw_ / 2, 770), loc, font=loc_f, fill=MUTED)

    # --- right content ------------------------------------------------------
    x0, y0 = 900, 150
    max_w = CARD_W - x0 - 160  # right margin 160

    # "ABOUT" label
    label_f = _load_font(34, bold=True, lang=lang)
    d.text((x0, y0), about_label, font=label_f, fill=ACCENT)
    about_w = d.textlength(about_label, font=label_f)
    d.rectangle((x0, y0 + 52, x0 + about_w + 40, y0 + 56), fill=ACCENT)

    # intro body
    body_f = _load_font(38, lang=lang)
    lines = _wrap(d, intro, body_f, max_w, cjk=zh)
    y = y0 + 96
    line_h = 58 if zh else 56
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
    d.text((x0, find_y), find_label, font=label_f, fill=ACCENT)
    find_w = d.textlength(find_label, font=label_f)
    d.rectangle((x0, find_y + 52, x0 + find_w + 40, find_y + 56), fill=ACCENT)

    contact_f = _load_font(32, lang=lang)
    cy_ = find_y + 96
    contact_h = 54
    if contacts:
        for label, url in contacts[:5]:
            short = url.replace("https://", "").replace("http://", "")
            disp = contact_labels.get(label, label.title())
            d.text((x0, cy_), f"{disp}: {short}", font=contact_f, fill=TEXT)
            cy_ += contact_h
    else:
        d.text((x0, cy_), "github.com/lzwjava · lzwjava.com", font=contact_f, fill=TEXT)

    # watermark
    wm_f = _load_font(26, lang=lang)
    wm = f"lzwjava.com  ·  github.com/lzwjava  ·  {role}"
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
    print("  --lang en|zh       Card language (default: en)")
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
    lang = "en"
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
        elif a == "--lang":
            lang = args[i + 1]
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
    if lang not in ("en", "zh"):
        print(f"[card] unknown --lang {lang!r} (expected en or zh)")
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
        intro = _llm_intro(resume_text, lang) if use_llm else _curated_intro(lang)

    # ---- step 3: business card ---------------------------------------------
    out_path = os.path.join(out_dir, f"business_card_{lang}.png")
    render_card(avatar_img, data, intro, out_path, lang)
    print(f"[card] done ({lang}) — card + avatar in: {os.path.abspath(out_dir)}")
