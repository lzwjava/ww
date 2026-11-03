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
    "Founder of TruthSoft, a Guangzhou-based AI-native studio. Previously at "
    "LeanCloud and TEKsystems, founder of Fun Live and Square Root Technology — "
    "delivered 50+ projects as a PM / software engineer for Yuanfudao, Fenbi, "
    "Jiangsu TV, DBS, HSBC.\n\n"
    "Full-stack engineer & mobile dev: Android, iOS, Vue, React, Angular, "
    "Java/Spring, Python; small-model training & inference with PyTorch/CUDA; "
    "cloud: Alibaba Cloud, AWS, Azure.\n\n"
    "Male, born 1995, Guangzhou · NOIP top 300 · IELTS 6.5. One year at Beijing "
    "Forestry University, then self-taught along the way; now an associate degree "
    "at GDUFS (13 exams) & an MSc at CSTU. 16,000+ engineers across platforms; "
    "blog ~100K monthly views."
)

ZH_INTRO = (
    "求真软件创始人、广州 AI 原生软件公司。曾就职 LeanCloud、TEKsystems，"
    "创办趣直播与平方根科技，以项目经理/软件工程师身份交付 50+ 项目，服务过"
    "猿辅导、粉笔、江苏卫视、星展银行 DBS、汇丰银行 HSBC 等。\n\n"
    "技术方面，熟悉移动端 Android/iOS、前端 Vue/React/Angular、"
    "后端 Java/Spring/Python、小模型训练与推理 PyTorch/CUDA，以及"
    "阿里云、AWS、Azure 上的日志、数据库与微服务架构。\n\n"
    "男，1995 年生，广州。广东 NOIP 2011 前 300，雅思 6.5。曾就读北京林业大学一年"
    "后退学工作创业；现读广东外语外贸大学专科（已过 13 科）、美国加州科学技术大学 "
    "CSTU 硕士在读。各平台连接 16000+ 工程师，博客月访问约 10 万。"
)

ZH_NAME = "李智维"
ZH_ROLE = "创始人 · AI 全栈工程师"
EN_ROLE = "Founder & AI Full Stack Engineer"
ZH_LOCATION = "中国广州"
TRUTHSOFT_URL = "truthsoft.dev"
WECHAT_QR = "/Users/lzwjava/Downloads/qrcode.jpg"  # WeChat QR code image
PHONE = "+86 132-6163-0925"
EMAIL = "lzwjava@gmail.com"
ZH_CONTACT_LABELS = {
    "truthsoft": "求真软件",
    "email": "邮箱",
    "wechat": "微信",
    "whatsapp": "WhatsApp",
    "github": "GitHub",
    "blog": "博客",
    "linkedin": "领英",
    "ai portfolio": "AI 作品集",
    "software portfolio": "软件作品集",
}
EN_CONTACT_LABELS = {
    "truthsoft": "TruthSoft",
    "email": "Email",
    "wechat": "WeChat",
    "whatsapp": "WhatsApp",
    "github": "GitHub",
    "blog": "Blog",
    "linkedin": "LinkedIn",
    "ai portfolio": "AI Portfolio",
    "software portfolio": "Software Portfolio",
}

# Card canvas (3.5" x 2" scaled up)
CARD_W, CARD_H = 2100, 1200

# Palettes — both matched to the avatar photo tones (warm beige/brown/caramel)
THEMES = {
    "dark": {
        "bg": (43, 32, 24),  # warm dark espresso
        "panel": (74, 53, 39),  # warm umber
        "accent": (226, 173, 106),  # caramel gold
        "text": (245, 237, 227),  # cream
        "muted": (178, 158, 136),  # warm taupe
        "divider": (96, 70, 50),
    },
    "light": {
        "bg": (247, 240, 230),  # cream
        "panel": (219, 200, 175),  # warm beige
        "accent": (180, 116, 52),  # dark caramel
        "text": (62, 45, 32),  # dark espresso
        "muted": (133, 110, 92),  # warm gray-brown
        "divider": (196, 172, 142),
    },
}

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


def _has_cjk(s):
    """True if the string contains CJK ideographs (needs a CJK font)."""
    return any("\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f" for c in s)


def _mixed_width(text, latin_f, cjk_f):
    """Advance width of text drawing Latin with latin_f and CJK with cjk_f."""
    return sum(
        cjk_f.getlength(c) if _has_cjk(c) else latin_f.getlength(c) for c in text
    )


def _draw_mixed(d, xy, text, latin_f, cjk_f, fill):
    """Draw text, using latin_f for Latin chars and cjk_f for CJK chars."""
    x, y = xy
    for ch in text:
        f = cjk_f if _has_cjk(ch) else latin_f
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch)


def _word_wrap(text, max_w, width_fn):
    lines, cur = [], ""
    for w in text.split():
        trial = f"{cur} {w}".strip()
        if width_fn(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_card(avatar, data, intro, out_path, lang="en", scale=2, theme="dark", qr_path=None):
    zh = lang == "zh"
    s = float(scale)
    pal = THEMES.get(theme, THEMES["dark"])
    (BG, PANEL, ACCENT, TEXT, MUTED, DIVIDER) = (
        pal["bg"], pal["panel"], pal["accent"], pal["text"], pal["muted"], pal["divider"],
    )
    name = ZH_NAME if zh else data["name"]
    role = ZH_ROLE if zh else EN_ROLE
    loc = ZH_LOCATION if zh else data["location"]
    about_label = "关于我" if zh else "ABOUT ME"
    contact_label = "联系" if zh else "CONTACT"
    contact_labels = ZH_CONTACT_LABELS if zh else EN_CONTACT_LABELS

    img = Image.new("RGB", (int(CARD_W * s), int(CARD_H * s)), BG)
    d = ImageDraw.Draw(img)

    # --- left panel ---------------------------------------------------------
    d.rectangle((0, 0, 760 * s, CARD_H * s), fill=PANEL)
    d.rectangle((756 * s, 0, 760 * s, CARD_H * s), fill=ACCENT)  # accent divider

    # avatar (circular)
    av_size = int(400 * s)
    av = avatar.resize((av_size, av_size), Image.LANCZOS)
    av_center = (int(380 * s), int(292 * s))
    img.paste(
        av,
        (av_center[0] - av_size // 2, av_center[1] - av_size // 2),
        _circle_mask(av_size),
    )
    ring = max(4, int(6 * s))
    d.ellipse(
        (
            av_center[0] - av_size // 2 - ring,
            av_center[1] - av_size // 2 - ring,
            av_center[0] + av_size // 2 + ring,
            av_center[1] + av_size // 2 + ring,
        ),
        outline=ACCENT,
        width=ring,
    )

    # name
    name_f = _load_font(int(80 * s), bold=True, lang=lang)
    nw = d.textlength(name, font=name_f)
    d.text((380 * s - nw / 2, 560 * s), name, font=name_f, fill=TEXT)

    # role
    role_f = _load_font(int(40 * s), bold=True, lang=lang)
    rw = d.textlength(role, font=role_f)
    d.text((380 * s - rw / 2, 668 * s), role, font=role_f, fill=ACCENT)

    # location
    loc_f = _load_font(int(32 * s), lang=lang)
    lw_ = d.textlength(loc, font=loc_f)
    d.text((380 * s - lw_ / 2, 742 * s), loc, font=loc_f, fill=MUTED)

    # --- WeChat QR code (centered under the location line) ------------------
    qr_ready = False
    if qr_path and os.path.exists(qr_path):
        qr_target = int(82 * s)
        pad = int(6 * s)
        try:
            qr = Image.open(qr_path).convert("RGB")
            side = min(qr.size)
            qr = qr.crop(
                (
                    (qr.size[0] - side) // 2,
                    (qr.size[1] - side) // 2,
                    (qr.size[0] + side) // 2,
                    (qr.size[1] + side) // 2,
                )
            ).resize((qr_target, qr_target), Image.LANCZOS)
            chip = Image.new("RGB", (qr_target + 2 * pad, qr_target + 2 * pad), (255, 255, 255))
            chip.paste(qr, (pad, pad))
            chip_left = int(380 * s - (qr_target + 2 * pad) / 2)
            chip_top = int(806 * s)  # just below the location text
            img.paste(chip, (chip_left, chip_top))
            qr_ready = True
        except Exception as e:  # noqa: BLE001
            print(f"[card] could not draw QR code: {e}")

    # --- left panel: contacts ----------------------------------------------
    priority = ["truthsoft", "email", "wechat", "whatsapp", "github"]
    contact_map = dict(data["links"])
    contact_map.setdefault("truthsoft", "https://" + TRUTHSOFT_URL)
    contact_map.setdefault("email", EMAIL)
    contact_map.setdefault("wechat", PHONE)
    contact_map.setdefault("whatsapp", PHONE)
    contacts = []
    for key in priority:
        if key in contact_map:
            contacts.append((key, contact_map[key]))
        if len(contacts) == 4:  # keep room for the WeChat QR code below
            break
    if not contacts:
        contacts = list(contact_map.items())[:4]

    d.line((60 * s, 896 * s, 700 * s, 896 * s), fill=DIVIDER, width=max(2, int(3 * s)))  # divider
    cap_f = _load_font(int(28 * s), bold=True, lang=lang)
    d.text((60 * s, 922 * s), contact_label, font=cap_f, fill=ACCENT)

    contact_f = _load_font(int(30 * s), lang=lang)
    cy_ = 968 * s
    contact_h = 42 * s
    for label, val in contacts:
        short = val.replace("https://", "").replace("http://", "")
        disp = contact_labels.get(label, label.title())
        d.text((60 * s, cy_), f"{disp}: {short}", font=contact_f, fill=TEXT)
        cy_ += contact_h

    # --- right: about me ----------------------------------------------------
    x0, y0 = 900 * s, 150 * s
    max_w = CARD_W * s - x0 - 160 * s  # right margin 160

    label_f = _load_font(int(38 * s), bold=True, lang=lang)
    d.text((x0, y0), about_label, font=label_f, fill=ACCENT)
    about_w = d.textlength(about_label, font=label_f)
    d.rectangle((x0, y0 + 52 * s, x0 + about_w + 40 * s, y0 + 56 * s), fill=ACCENT)

    # Arial has no CJK glyphs — for mixed EN text draw Latin with Arial and
    # CJK chars with a CJK font (per-run, keeps Arial wrapping metrics).
    # Bold weights for a bit more presence on the About Me body.
    latin_body_f = _load_font(int(38 * s), bold=True, lang="en")
    cjk_body_f = _load_font(int(40 * s), bold=True, lang="zh")
    line_h = (60 if zh else 58) * s
    para_gap = 22 * s
    y = y0 + 96 * s
    for para in intro.split("\n\n"):
        if not para.strip():
            continue
        para = para.strip()
        if zh:
            lines = _wrap_cjk(d, para, cjk_body_f, max_w)
        elif _has_cjk(para):
            lines = _word_wrap(para, max_w, lambda t: _mixed_width(t, latin_body_f, cjk_body_f))
        else:
            lines = _word_wrap(para, max_w, lambda t: latin_body_f.getlength(t))
        for ln in lines:
            if zh or not _has_cjk(ln):
                d.text((x0, y), ln, font=zh and cjk_body_f or latin_body_f, fill=TEXT)
            else:
                _draw_mixed(d, (x0, y), ln, latin_body_f, cjk_body_f, TEXT)
            y += line_h
        y += para_gap

    # watermark
    wm_f = _load_font(int(30 * s), lang=lang)
    wm = f"{TRUTHSOFT_URL}  ·  lzwjava.com  ·  github.com/lzwjava"
    ww_ = CARD_W * s - d.textlength(wm, font=wm_f) - 80 * s
    d.text((ww_, CARD_H * s - 70 * s), wm, font=wm_f, fill=MUTED)

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
    print(f"  --theme dark|light Color theme (default: dark; options: {', '.join(THEMES)})")
    print("  --scale N          Pixel density multiplier 1-8 (default: 2, i.e. 4200x2400)")
    print("  --qr FILE          WeChat QR code image (default: ~/Downloads/qrcode.jpg)")
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
    scale = 2.0
    theme = "dark"
    qr_path = WECHAT_QR if os.path.exists(WECHAT_QR) else None
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
        elif a == "--scale":
            scale = args[i + 1]
            i += 2
        elif a == "--theme":
            theme = args[i + 1]
            i += 2
        elif a == "--qr":
            qr_path = args[i + 1]
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
    try:
        scale = float(scale)
        if scale < 1 or scale > 8:
            raise ValueError
    except ValueError:
        print(f"[card] --scale must be a number between 1 and 8 (got {scale!r})")
        sys.exit(1)
    if theme not in THEMES:
        print(f"[card] unknown --theme {theme!r} (available: {', '.join(THEMES)})")
        sys.exit(1)
    if qr_path and not os.path.exists(qr_path):
        print(f"[card] QR image not found: {qr_path}")
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
    render_card(avatar_img, data, intro, out_path, lang, scale, theme, qr_path)
    print(f"[card] rendered {theme} theme at {scale:.1f}x ({int(CARD_W*scale)}x{int(CARD_H*scale)} px)")
    print(f"[card] done ({lang}) — card + avatar in: {os.path.abspath(out_dir)}")
