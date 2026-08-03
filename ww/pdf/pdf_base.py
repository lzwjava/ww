import os
import subprocess
import platform
import tempfile
import shutil
from typing import Iterable, Optional

try:
    # pypdf is a project dependency (pyproject.toml)
    from pypdf import PdfReader, PdfWriter  # type: ignore
except Exception:  # pragma: no cover - optional import for environments without pypdf
    PdfReader = None  # type: ignore
    PdfWriter = None  # type: ignore


def _find_cjk_font():
    """Locate a system font that supports CJK characters, or None."""
    candidates = []
    if platform.system() == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fonts = os.path.join(windir, "Fonts")
        candidates = [
            os.path.join(fonts, "msyh.ttc"),      # Microsoft YaHei
            os.path.join(fonts, "msyh.ttf"),
            os.path.join(fonts, "simhei.ttf"),    # SimHei
            os.path.join(fonts, "simsun.ttc"),    # SimSun
            os.path.join(fonts, "Deng.ttf"),      # DengXian
        ]
    elif platform.system() == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
        ]
    else:  # Linux / other
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _md_to_pdf_via_fpdf(input_markdown_path, output_pdf_path, *, pt: int = 16):
    """Pure-Python fallback: markdown → HTML → PDF via fpdf2.

    No pandoc/xelatex required. Uses fpdf2's write_html() to render the
    converted HTML. Loads a system CJK font when available so Chinese/
    Japanese/Korean text renders correctly.
    """
    import markdown as md_lib
    from fpdf import FPDF

    with open(input_markdown_path, encoding="utf-8") as f:
        md_text = f.read()

    html = md_lib.markdown(
        md_text,
        extensions=["fenced_code", "tables", "toc", "sane_lists", "nl2br"],
    )

    # fpdf2's write_html can't handle nested tags inside <td>/<th> cells.
    # Strip inner tags from cells (keep text) so tables still render; if a
    # table still fails, it is replaced with a placeholder.
    import re as _re

    def _flatten_cells(m):
        tag, inner = m.group(1), m.group(2)
        inner = _re.sub(r"<[^>]+>", "", inner)
        return f"<{tag}>{inner}</{tag}>"

    html = _re.sub(r"<(td|th)>(.*?)</\1>", _flatten_cells, html, flags=_re.DOTALL)

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Use a CJK-capable font if found; otherwise fall back to the built-in Helvetica.
    cjk_font = _find_cjk_font()
    if cjk_font:
        try:
            pdf.add_font("Main", style="", fname=cjk_font)
            pdf.add_font("Main", style="B", fname=cjk_font)
            pdf.set_font("Main", size=pt)
        except Exception as e:
            print(f"Warning: could not load CJK font {cjk_font}: {e}")
            pdf.set_font("Helvetica", size=pt)
    else:
        pdf.set_font("Helvetica", size=pt)

    # Inline stylesheet so headings scale relative to body size and code is monospaced.
    base_pt = max(int(pt * 0.75), 9)
    h1_sz = int(base_pt * 1.9)
    h2_sz = int(base_pt * 1.5)
    h3_sz = int(base_pt * 1.25)
    from fpdf.fonts import FontFace

    tag_styles = {
        "h1": FontFace(size_pt=h1_sz, emphasis="B"),
        "h2": FontFace(size_pt=h2_sz, emphasis="B"),
        "h3": FontFace(size_pt=h3_sz, emphasis="B"),
        "h4": FontFace(size_pt=base_pt, emphasis="B"),
        "h5": FontFace(size_pt=base_pt, emphasis="B"),
        "h6": FontFace(size_pt=base_pt, emphasis="B"),
        "pre": FontFace(size_pt=base_pt - 2),
        "code": FontFace(size_pt=base_pt - 2),
    }
    try:
        pdf.write_html(html, tag_styles=tag_styles)
    except Exception as e:
        # If the error is table-related, strip tables and retry
        if "table" in str(e).lower():
            print("Warning: table rendering not supported, stripping tables")
            html = _re.sub(r"<table[^>]*>.*?</table>", "", html, flags=_re.DOTALL)
            try:
                pdf = None
                pdf = FPDF(format="A4")
                pdf.set_auto_page_break(auto=True, margin=18)
                pdf.add_page()
                if cjk_font:
                    pdf.add_font("Main", style="", fname=cjk_font)
                    pdf.set_font("Main", size=pt)
                else:
                    pdf.set_font("Helvetica", size=pt)
                pdf.write_html(html, tag_styles=tag_styles)
            except Exception as e2:
                print(f"Warning: write_html still failed after stripping tables ({e2})")
                pdf = None
        else:
            print(f"Warning: write_html failed ({e})")

        if pdf is None:
            # Final fallback: render markdown text with basic formatting
            print("Falling back to plain text rendering")
            pdf = FPDF(format="A4")
            pdf.set_auto_page_break(auto=True, margin=18)
            pdf.add_page()
            if cjk_font:
                try:
                    pdf.add_font("Main", style="", fname=cjk_font)
                except Exception:
                    pass
                try:
                    pdf.set_font("Main", size=pt)
                except Exception:
                    pdf.set_font("Helvetica", size=pt)
            else:
                pdf.set_font("Helvetica", size=pt)
            for line in md_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    level = len(stripped) - len(stripped.lstrip("#"))
                    text = stripped.lstrip("# ").strip()
                    sz = max(pt + 4 - level * 2, pt)
                    pdf.set_font("Main" if cjk_font else "Helvetica", size=sz)
                    pdf.multi_cell(0, sz * 0.5, text, new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Main" if cjk_font else "Helvetica", size=pt)
                    pdf.ln(2)
                elif stripped.startswith(">"):
                    text = stripped.lstrip("> ").strip()
                    pdf.multi_cell(0, pt * 0.45, text, new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(1)
                elif stripped.startswith(("- ", "* ", "+ ")):
                    text = "  • " + stripped[2:]
                    pdf.multi_cell(0, pt * 0.45, text, new_x="LMARGIN", new_y="NEXT")
                elif stripped and stripped[0].isdigit() and ". " in stripped[:5]:
                    text = "  " + stripped
                    pdf.multi_cell(0, pt * 0.45, text, new_x="LMARGIN", new_y="NEXT")
                elif stripped == "---":
                    y = pdf.get_y()
                    pdf.line(10, y, 200, y)
                    pdf.ln(2)
                elif stripped == "":
                    pdf.ln(3)
                else:
                    pdf.multi_cell(0, pt * 0.45, line, new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_pdf_path)
    return True


def text_to_pdf_from_markdown(
    input_markdown_path,
    output_pdf_path,
    dry_run=False,
    extra_pandoc_args=None,
    *,
    pt: int = 16,
    title_page: bool = False,
    toc: bool = False,
    toc_depth: int = 2,
    toc_title: Optional[str] = None,
    toc_own_page: bool = True,
):
    if dry_run:
        print(f"Dry run: Would generate PDF from: {input_markdown_path}")
        return

    print(f"Generating PDF from: {input_markdown_path}")

    GEOMETRY = "left=1.4cm, top=.8cm, right=1.4cm, bottom=1.8cm, footskip=.5cm"

    if not os.path.exists(input_markdown_path):
        raise Exception(f"Input file does not exist: {input_markdown_path}")

    # If pandoc isn't installed (common on Windows), fall back to a pure-Python
    # renderer (markdown + fpdf2) so no system LaTeX toolchain is required.
    if shutil.which("pandoc") is None:
        print(
            "pandoc not found — using built-in renderer (markdown + fpdf2). "
            "Install pandoc + xelatex for advanced typography."
        )
        os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)
        ok = _md_to_pdf_via_fpdf(input_markdown_path, output_pdf_path, pt=pt)
        if ok:
            print(f"PDF content written to {output_pdf_path}")
        return ok

    lang = os.path.basename(input_markdown_path).split("-")[-1].split(".")[0]
    CJK_FONT = _font_for_lang(lang)
    # Body font size via \fontsize since article class only supports 10/11/12pt.
    # Use \AtBeginDocument to ensure our size wins over pandoc/class defaults.
    # Also cap heading sizes via titlesec so they stay proportional.
    baseline = int(pt * 1.25)
    heading_pt = max(int(pt * 1.3), pt + 2)
    subheading_pt = max(int(pt * 1.15), pt + 1)
    header_tex = "\n".join(
        [
            "\\usepackage{setspace}",
            "\\setstretch{1.5}",
            "\\usepackage{titlesec}",
            f"\\renewcommand{{\\normalsize}}{{\\fontsize{{{pt}}}{{{baseline}}}\\selectfont}}",
            "\\AtBeginDocument{\\normalsize}",
            f"\\titleformat{{\\section}}{{\\bfseries\\fontsize{{{heading_pt}}}{{{int(heading_pt * 1.2)}}}\\selectfont}}{{}}{{}}{{}}",
            f"\\titleformat{{\\subsection}}{{\\bfseries\\fontsize{{{subheading_pt}}}{{{int(subheading_pt * 1.2)}}}\\selectfont}}{{}}{{}}{{}}",
            "\\titleformat{\\subsubsection}{\\bfseries\\normalsize}{}{}{}",
            "",
        ]
    )

    # Write header-includes to a temp file so newlines survive pandoc parsing
    header_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".tex", delete=False, encoding="utf-8"
    )
    header_file.write(header_tex)
    header_file.close()

    command = [
        "pandoc",
        input_markdown_path,
        "-o",
        output_pdf_path,
        "-f",
        # Disable YAML metadata block and raw LaTeX to avoid alias/\n issues
        "markdown-yaml_metadata_block-raw_tex",
        "--pdf-engine",
        "xelatex",
        "--include-in-header",
        header_file.name,
        "-V",
        f"romanfont={CJK_FONT}",
        "-V",
        f"mainfont={CJK_FONT}",
        "-V",
        f"CJKmainfont={CJK_FONT}",
        "-V",
        f"CJKsansfont={CJK_FONT}",
        "-V",
        f"CJKmonofont={CJK_FONT}",
        "-V",
        f"geometry:{GEOMETRY}",
        "-V",
        "classoption=12pt",
        "-V",
        "CJKoptions=Scale=1.1",
    ]

    # Book-like toggles
    if toc:
        command.extend(["--toc", "--toc-depth", str(int(toc_depth))])
        if toc_title:
            command.extend(["-V", f"toc-title={toc_title}"])
        if toc_own_page:
            command.extend(["-V", "toc-own-page=true"])
    if title_page:
        # Relying on pandoc's titlepage can be tricky when TOC is also used.
        # Keep this available, but for book builds prefer a separate LaTeX title page.
        command.extend(["-V", "titlepage=true"])

    # Allow callers to override/extend pandoc behavior (e.g., --toc)
    if extra_pandoc_args:
        if not isinstance(extra_pandoc_args, (list, tuple)):
            raise TypeError("extra_pandoc_args must be a list or tuple of strings")
        command.extend([str(x) for x in extra_pandoc_args])

    result = subprocess.run(command, capture_output=True, text=True)
    os.unlink(header_file.name)
    if result.returncode != 0:
        print(f"Pandoc error for {output_pdf_path}: {result.stderr}")
        # raise Exception(f"Pandoc failed for {input_markdown_path}")
        return False

    print(f"PDF content written to {output_pdf_path}")
    return True


def _font_for_lang(lang: str) -> str:
    """Return a good default font for the language and platform, matching pandoc settings."""
    if platform.system() == "Darwin":
        if lang == "hi":
            return "Kohinoor Devanagari"
        if lang == "ar":
            return "Geeza Pro"
        if lang in ["en", "fr", "de", "es"]:
            return "Helvetica"
        if lang == "zh":
            return "PingFang SC"
        if lang == "hant":
            return "PingFang TC"
        if lang == "ja":
            return "Hiragino Sans"
        return "Arial Unicode MS"
    else:
        if lang == "hi":
            return "Noto Sans Devanagari"
        if lang == "ar":
            return "Noto Naskh Arabic"
        if lang in ["en", "fr", "de", "es"]:
            return "DejaVu Sans"
        if lang == "zh":
            return "Noto Sans CJK SC"
        if lang == "hant":
            return "Noto Sans CJK TC"
        if lang == "ja":
            return "Noto Sans CJK JP"
        return "Noto Sans"


def generate_title_page_pdf(
    *,
    title: str,
    output_pdf_path: str,
    subtitle: Optional[str] = None,
    lang: str = "en",
    font_size_pt: int = 48,
    geom: str = "left=1.4cm, top=.8cm, right=1.4cm, bottom=1.8cm, footskip=.5cm",
) -> bool:
    """Render a single-page PDF title page via xelatex.

    # Uses fontspec + setmainfont with a language-appropriate font.
    - Suppresses page numbers and centers the title.
    """
    font_name = _font_for_lang(lang)

    # Minimal LaTeX document for a clean title page
    lines = [
        r"\documentclass[12pt]{article}",
        r"\usepackage{fontspec}",
        r"\usepackage{geometry}",
        rf"\geometry{{{geom}}}",
        rf"\setmainfont{{{font_name}}}",
        r"\pagenumbering{gobble}",
        r"\begin{document}",
        r"\thispagestyle{empty}",
        r"\vspace*{0.25\textheight}",
        r"\begin{center}",
        rf"{{\fontsize{{{font_size_pt}}}{{{int(font_size_pt * 1.15)}}}\selectfont {title}\par}}",
    ]
    if subtitle:
        lines.extend(
            [
                r"\vspace{1.2em}",
                rf"{{\Large {subtitle}\par}}",
            ]
        )
    lines.extend(
        [
            r"\end{center}",
            r"\end{document}",
            "",
        ]
    )

    workdir = tempfile.mkdtemp(prefix="titlepage-")
    tex_path = os.path.join(workdir, "titlepage.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    try:
        cmd = [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory",
            workdir,
            tex_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Failed to compile title page with xelatex:")
            print(result.stderr)
            return False

        pdf_src = os.path.join(workdir, "titlepage.pdf")
        if not os.path.exists(pdf_src):
            print("Title page PDF was not produced by xelatex.")
            return False

        os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)
        shutil.copyfile(pdf_src, output_pdf_path)
        print(f"Title page written to {output_pdf_path}")
        return True
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def merge_pdfs(inputs: Iterable[str], output_pdf_path: str) -> bool:
    """Merge multiple PDFs into one using pypdf. Returns True on success."""
    if PdfWriter is None or PdfReader is None:
        print("pypdf not available; cannot merge PDFs.")
        return False

    writer = PdfWriter()
    added_any = False

    for path in inputs:
        if not path or not os.path.exists(path):
            print(f"Skipping missing PDF: {path}")
            continue
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
            added_any = True
        except Exception as e:
            print(f"Error reading {path}: {e}")

    if not added_any:
        print("No valid PDFs to merge.")
        return False

    os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)
    with open(output_pdf_path, "wb") as f:
        writer.write(f)
    print(f"Merged PDF written to {output_pdf_path}")
    return True
