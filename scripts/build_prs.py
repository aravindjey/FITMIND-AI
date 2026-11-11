#!/usr/bin/env python3
"""Build the refined FITMIND AI PRS report as PDF, HTML, and DOCX with automatically computed page numbers.

Pipeline:
  1. Parse docs/prs/report.md into the 10 prescribed college chapters.
  2. Embed diagrams as high-resolution PNGs (base64 in HTML, media in DOCX).
  3. Render each chapter with headless Chrome to count pages.
  4. Inject exact page numbers into the Table of Contents (S.No | Title of the Exercise | Page No.).
  5. Compile final PDF with verified pagination:
       - FITMIND_AI_PRS_FINAL.pdf (Primary final submission deliverable)
       - FITMIND_AI_PRS_Report.pdf (Preserved original deliverable)
  6. Generate standalone HTML for docs/prs/FITMIND_AI_PRS_Report.html and docs/FITMIND_AI_SRS_DOCUMENT.html
     with distinct page sheets and visible page breaks for web browsers.
  7. Generate Microsoft Word DOCX files (FITMIND_AI_PRS_FINAL.docx, FITMIND_AI_PRS_Report.docx, and docs copies)
     with native Word page breaks (<w:br w:type="page"/>) and embedded PNG diagrams for Google Docs.
"""
import base64
import html
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "prs", "report.md")
FIG_DIR = os.path.join(ROOT, "docs", "prs")

OUT_PDF_FINAL = os.path.join(ROOT, "FITMIND_AI_PRS_FINAL.pdf")
OUT_PDF_REPORT = os.path.join(ROOT, "FITMIND_AI_PRS_Report.pdf")
OUT_HTML_PRS = os.path.join(ROOT, "docs", "prs", "FITMIND_AI_PRS_Report.html")
OUT_HTML_SRS = os.path.join(ROOT, "docs", "FITMIND_AI_SRS_DOCUMENT.html")
OUT_DOCX_FINAL = os.path.join(ROOT, "FITMIND_AI_PRS_FINAL.docx")
OUT_DOCX_REPORT = os.path.join(ROOT, "FITMIND_AI_PRS_Report.docx")
OUT_DOCX_DOCS_FINAL = os.path.join(ROOT, "docs", "FITMIND_AI_PRS_FINAL.docx")
OUT_DOCX_DOCS_REPORT = os.path.join(ROOT, "docs", "FITMIND_AI_PRS_REPORT.docx")
OUT_MD_SRS = os.path.join(ROOT, "docs", "FITMIND_AI_SRS_DOCUMENT.md")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PRESCRIBED = [
    "Introduction",
    "Problem Definition, Scope and Objectives",
    "Literature Survey",
    "Requirement Analysis",
    "Proposed Methodology and System Design",
    "Implementation",
    "Results and Discussion",
    "Conclusion",
    "References",
    "Annexure - I: Outcome-Specific Supporting Evidence",
]

# Load base64 PNGs for self-contained, Google-Docs-friendly HTML embedding
ARCH_PNG_PATH = os.path.join(FIG_DIR, "fig_architecture.png")
PIPE_PNG_PATH = os.path.join(FIG_DIR, "fig_pipeline.png")

if not os.path.exists(ARCH_PNG_PATH) or not os.path.exists(PIPE_PNG_PATH):
    for svg_file, png_file in [("fig_architecture.svg", "fig_architecture.png"), ("fig_pipeline.svg", "fig_pipeline.png")]:
        s_p = os.path.join(FIG_DIR, svg_file)
        p_p = os.path.join(FIG_DIR, png_file)
        if os.path.exists(s_p) and not os.path.exists(p_p):
            subprocess.run(["/opt/homebrew/bin/rsvg-convert", "-z", "2", s_p, "-o", p_p], check=True)

ARCH_B64 = base64.b64encode(open(ARCH_PNG_PATH, "rb").read()).decode("ascii") if os.path.exists(ARCH_PNG_PATH) else ""
PIPE_B64 = base64.b64encode(open(PIPE_PNG_PATH, "rb").read()).decode("ascii") if os.path.exists(PIPE_PNG_PATH) else ""

CSS = """
@page {
  size: A4;
  margin: 22mm 20mm 24mm 20mm;
  @bottom-left   { content: "FITMIND AI \\2014  Project Requirements Specification"; font: 8.5pt Helvetica, Arial, sans-serif; color: #64748b; }
  @bottom-right  { content: "Page " counter(page); font: 8.5pt Helvetica, Arial, sans-serif; color: #64748b; }
}

* { box-sizing: border-box; }

body {
  font-family: "Times New Roman", Times, serif;
  font-size: 11pt;
  line-height: 1.5;
  color: #111827;
  margin: 0;
}

/* Print / PDF Mode */
@media print {
  body {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  .screen-page-divider {
    display: none !important;
  }
  .report-page {
    background: transparent !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    border: none !important;
  }
  .toc-page {
    page-break-after: always !important;
    break-after: page !important;
  }
  .chapter-section {
    page-break-before: always !important;
    break-before: page !important;
  }
  h1.chapter {
    page-break-before: always !important;
    break-before: page !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
  }
  h1.chapter.first {
    page-break-before: auto !important;
    break-before: auto !important;
  }
  h3, h4 {
    page-break-after: avoid !important;
    break-after: avoid !important;
  }
  table, pre, figure {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
}

/* Screen / Web Browser Mode (Safari, Chrome) */
@media screen {
  body {
    background-color: #f1f5f9;
    padding: 30px 15px;
    margin: 0;
  }
  .report-page {
    background: #ffffff;
    max-width: 840px;
    margin: 0 auto 30px auto;
    padding: 45px 55px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(15, 23, 42, 0.05);
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    box-sizing: border-box;
  }
  .toc-page {
    min-height: 520px;
  }
  .screen-page-divider {
    max-width: 840px;
    margin: 45px auto 25px auto;
    text-align: center;
    position: relative;
  }
  .screen-page-divider::before {
    content: "";
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 2px;
    background: #cbd5e1;
    z-index: 1;
  }
  .screen-page-divider span {
    position: relative;
    z-index: 2;
    background: #f8fafc;
    padding: 6px 18px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
    border: 1px solid #94a3b8;
    border-radius: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
}

h1.chapter {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 19pt;
  color: #0f172a;
  border-bottom: 2px solid #0f172a;
  padding-bottom: 6px;
  margin: 0 0 16px 0;
}
h1.toc {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 20pt;
  text-align: center;
  margin: 15px 0 25px 0;
  color: #0f172a;
  letter-spacing: 0.04em;
}
h3 {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12.5pt;
  color: #1e293b;
  margin: 18px 0 6px;
}
h4 {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 11pt;
  color: #334155;
  margin: 14px 0 4px;
}
p {
  margin: 6px 0;
  text-align: justify;
}
ul, ol {
  margin: 6px 0 6px 0;
  padding-left: 24px;
}
li {
  margin: 3px 0;
}
code {
  font-family: Menlo, Consolas, monospace;
  font-size: 9pt;
  background: #f1f5f9;
  padding: 1px 4px;
  border-radius: 3px;
}
pre {
  font-family: Menlo, Consolas, monospace;
  font-size: 8.2pt;
  line-height: 1.4;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 8px 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
pre code {
  background: none;
  padding: 0;
  font-size: inherit;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  line-height: 1.35;
}
th, td {
  border: 1px solid #94a3b8;
  padding: 5px 8px;
  vertical-align: top;
  text-align: left;
}
th {
  background: #e2e8f0;
  font-weight: 700;
  color: #0f172a;
}
tr:nth-child(even) td {
  background: #f8fafc;
}
figure {
  margin: 14px 0;
  text-align: center;
}
figure img {
  max-width: 100%;
  height: auto;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
figcaption {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  font-weight: 600;
  color: #334155;
  margin-top: 6px;
}
table.toc {
  font-size: 11pt;
  margin: 10px auto;
  width: 100%;
}
table.toc th, table.toc td {
  padding: 10px 14px;
  border: 1px solid #475569;
}
table.toc td.sno {
  text-align: center;
  width: 80px;
  font-weight: bold;
}
table.toc td.pg {
  text-align: center;
  width: 90px;
  font-weight: bold;
}
table.toc th {
  text-align: center;
  background: #e2e8f0;
  white-space: nowrap;
}
"""


# ----------------------------------------------------------------- markdown
def inline(text):
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: "<code>%s</code>" % html.escape(codes[int(m.group(1))], quote=False), text)


def render_table(rows):
    header = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    out = ["<table><thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in header) + "</tr></thead><tbody>"]
    for r in rows[2:]:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in cells) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def md_to_html(md):
    lines = md.split("\n")
    out, i, para = [], 0, []

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            flush()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf), quote=False))
            i += 1
            continue
        m = re.match(r"\{\{svg:([^|}]+)\|([^}]+)\}\}", s)
        if m:
            flush()
            svg_file = m.group(1)
            caption = m.group(2)
            if "architecture" in svg_file and ARCH_B64:
                img_tag = f'<img src="data:image/png;base64,{ARCH_B64}" alt="{html.escape(caption)}" />'
            elif "pipeline" in svg_file and PIPE_B64:
                img_tag = f'<img src="data:image/png;base64,{PIPE_B64}" alt="{html.escape(caption)}" />'
            else:
                svg_content = open(os.path.join(FIG_DIR, svg_file), encoding="utf-8").read()
                img_tag = svg_content
            out.append(f"<figure>{img_tag}<figcaption>{html.escape(caption)}</figcaption></figure>")
            i += 1
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(render_table(rows))
            continue
        if s.startswith("#### "):
            flush()
            out.append("<h4>%s</h4>" % inline(s[5:]))
            i += 1
            continue
        if s.startswith("### "):
            flush()
            out.append("<h3>%s</h3>" % inline(s[4:]))
            i += 1
            continue
        if re.match(r"^(\d+)\. ", s) or s.startswith("- "):
            flush()
            ordered = bool(re.match(r"^\d+\. ", s))
            tag = "ol" if ordered else "ul"
            pat = r"^\d+\. " if ordered else r"^- "
            items = []
            while i < len(lines) and re.match(pat, lines[i].strip()):
                items.append(re.sub(pat, "", lines[i].strip()))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(t) for t in items), tag))
            continue
        if not s:
            flush()
            i += 1
            continue
        para.append(s)
        i += 1
    flush()
    return "\n".join(out)


def split_chapters(md):
    # Only match '# N. Title' outside code blocks
    lines = md.split("\n")
    in_code = False
    cleaned_lines = []
    for l in lines:
        if l.strip().startswith("```"):
            in_code = not in_code
        if in_code and re.match(r"^# \d+\. ", l):
            cleaned_lines.append(l.replace("# ", "// "))
        else:
            cleaned_lines.append(l)
    clean_md = "\n".join(cleaned_lines)
    parts = re.split(r"(?m)^# (\d+)\. (.+)$", clean_md)
    chapters = []
    for k in range(1, len(parts), 3):
        chapters.append((int(parts[k]), parts[k + 1].strip(), parts[k + 2]))
    return chapters


def check_structure(chapters):
    titles = [t for _, t, _ in chapters]
    nums = [n for n, _, _ in chapters]
    if titles != PRESCRIBED or nums != list(range(1, 11)):
        sys.exit("STRUCTURE ERROR: report.md must contain exactly the 10 prescribed chapters in order.\n"
                 "found: %r" % list(zip(nums, titles)))


# ------------------------------------------------------------------- HTML Renderers
def chapter_html(n, title, body, first, start_page=None):
    cls = "chapter first" if first else "chapter"
    divider = ""
    if not first and start_page is not None:
        divider = f'<div class="screen-page-divider"><span>PAGE BREAK &bull; CHAPTER {n} BEGINS ON NEW PAGE (PAGE {start_page})</span></div>\n'
    return f'{divider}<section class="report-page chapter-section" id="chapter-{n}">\n<h1 class="{cls}">{n}. {html.escape(title)}</h1>\n{md_to_html(body)}\n</section>'


def toc_html(pages):
    rows = "".join(
        f'<tr><td class="sno">{i + 1}.</td><td>{html.escape(t)}</td><td class="pg">{pages[i]}</td></tr>'
        for i, t in enumerate(PRESCRIBED)
    )
    return (
        '<section class="report-page toc-page">'
        '<h1 class="toc">TABLE OF CONTENTS</h1>'
        '<table class="toc">'
        '<thead><tr><th>S.No</th><th>Title of the Exercise</th><th>Page No.</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
        '</section>'
    )


def document(inner):
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>FITMIND AI - Project Requirements Specification Report</title>'
        f'<style>{CSS}</style></head><body>{inner}</body></html>'
    )


# ------------------------------------------------------------------- Headless Chrome PDF
def chrome_pdf(html_text, pdf_path):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_text)
        tmp = f.name
    profile = tempfile.mkdtemp(prefix="prs-chrome-")
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--user-data-dir=" + profile, "--no-first-run", "--no-sandbox",
             "--virtual-time-budget=3000", "--print-to-pdf=" + pdf_path, "file://" + tmp],
            capture_output=True, text=True, timeout=180)
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            sys.exit("Chrome failed to create PDF:\n" + r.stderr[-1500:])
    finally:
        os.unlink(tmp)
        shutil.rmtree(profile, ignore_errors=True)


def count_pages(pdf_path):
    data = open(pdf_path, "rb").read()
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


# ------------------------------------------------------------------- Pure Python DOCX Generator
def generate_docx(chapters, start_pages, out_path):
    CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rIdArch" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/fig_arch.png"/>
  <Relationship Id="rIdPipe" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/fig_pipe.png"/>
</Relationships>"""

    STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="23"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>"""

    def esc(txt):
        return html.escape(txt, quote=False)

    def p_xml(text, bold=False, italic=False, size=23, font="Times New Roman", align="both", space_after=120):
        b_tag = "<w:b/>" if bold else ""
        i_tag = "<w:i/>" if italic else ""
        return f'<w:p><w:pPr><w:jc w:val="{align}"/><w:spacing w:after="{space_after}"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>{b_tag}{i_tag}<w:sz w:val="{size}"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'

    def page_break_xml():
        return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

    def table_xml(rows):
        tbl = ['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/><w:left w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/><w:right w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/></w:tblBorders></w:tblPr>']
        for r_idx, r in enumerate(rows):
            tbl.append('<w:tr>')
            is_hdr = (r_idx == 0)
            for c in r:
                shd = '<w:shd w:val="clear" w:color="auto" w:fill="E2E8F0"/>' if is_hdr else ''
                bld = '<w:b/>' if is_hdr else ''
                font = '<w:rFonts w:ascii="Helvetica" w:hAnsi="Helvetica"/>'
                sz = '<w:sz w:val="19"/>'
                tbl.append(f'<w:tc><w:tcPr>{shd}<w:tcMar><w:top w:w="80"/><w:left w:w="120"/><w:bottom w:w="80"/><w:right w:w="120"/></w:tcMar></w:tcPr><w:p><w:spacing w:after="0"/><w:r><w:rPr>{font}{bld}{sz}</w:rPr><w:t xml:space="preserve">{esc(c)}</w:t></w:r></w:p></w:tc>')
            tbl.append('</w:tr>')
        tbl.append('</w:tbl>')
        return "".join(tbl)

    def drawing_xml(rel_id, title, cx=5486400, cy=3200400):
        return f"""<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="60"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="{esc(title)}"/><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="1" name="image.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rel_id}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p><w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Helvetica" w:hAnsi="Helvetica"/><w:i/><w:b/><w:sz w:val="18"/><w:color w:val="334155"/></w:rPr><w:t>{esc(title)}</w:t></w:r></w:p>"""

    body_parts = []

    # Table of Contents
    body_parts.append(p_xml("TABLE OF CONTENTS", bold=True, size=38, font="Helvetica", align="center", space_after=300))
    toc_rows = [["S.No", "Title of the Exercise", "Page No."]]
    for idx, t in enumerate(PRESCRIBED):
        toc_rows.append([f"{idx + 1}.", t, str(start_pages[idx])])
    body_parts.append(table_xml(toc_rows))
    body_parts.append(page_break_xml())

    # Chapters 1 to 10
    for idx, (n, title, body) in enumerate(chapters):
        body_parts.append(p_xml(f"{n}. {title}", bold=True, size=34, font="Helvetica", align="left", space_after=220))
        lines = body.split("\n")
        l_idx = 0
        while l_idx < len(lines):
            l = lines[l_idx].strip()
            if not l:
                l_idx += 1
                continue
            if l.startswith("### "):
                body_parts.append(p_xml(l[4:], bold=True, size=26, font="Helvetica", align="left", space_after=100))
                l_idx += 1
                continue
            if l.startswith("#### "):
                body_parts.append(p_xml(l[5:], bold=True, size=22, font="Helvetica", align="left", space_after=80))
                l_idx += 1
                continue
            if l.startswith("{{svg:fig_architecture"):
                m = re.match(r"\{\{svg:[^|]+\|([^}]+)\}\}", l)
                cap = m.group(1) if m else "Figure 5.1: Layered modular monolith architecture of FITMIND AI"
                body_parts.append(drawing_xml("rIdArch", cap, cx=5486400, cy=3200400))
                l_idx += 1
                continue
            if l.startswith("{{svg:fig_pipeline"):
                m = re.match(r"\{\{svg:[^|]+\|([^}]+)\}\}", l)
                cap = m.group(1) if m else "Figure 5.2: Five-stage unidirectional pipeline for AI-assisted requests"
                body_parts.append(drawing_xml("rIdPipe", cap, cx=5486400, cy=1800000))
                l_idx += 1
                continue
            if l.startswith("```"):
                l_idx += 1
                code_buf = []
                while l_idx < len(lines) and not lines[l_idx].strip().startswith("```"):
                    code_buf.append(lines[l_idx])
                    l_idx += 1
                l_idx += 1
                body_parts.append(p_xml("\n".join(code_buf), font="Consolas", size=17, align="left", space_after=140))
                continue
            if l.startswith("|"):
                tbl_rows = []
                while l_idx < len(lines) and lines[l_idx].strip().startswith("|"):
                    raw = lines[l_idx].strip()
                    if not re.match(r"^\|?\s*:?-+:?\s*\|", raw):
                        cells = [c.strip() for c in raw.strip("|").split("|")]
                        tbl_rows.append(cells)
                    l_idx += 1
                body_parts.append(table_xml(tbl_rows))
                continue
            if l.startswith("- ") or re.match(r"^\d+\. ", l):
                clean_item = re.sub(r"^(- |\d+\. )", "", l)
                clean_item = clean_item.replace("**", "").replace("`", "")
                bullet_char = "• " if l.startswith("- ") else ""
                body_parts.append(p_xml(bullet_char + clean_item, size=22, align="both", space_after=80))
                l_idx += 1
                continue
            
            clean_p = l.replace("**", "").replace("`", "")
            body_parts.append(p_xml(clean_p, size=23, align="both", space_after=140))
            l_idx += 1

        if idx < len(chapters) - 1:
            body_parts.append(page_break_xml())

    DOC_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {"".join(body_parts)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    arch_bytes = open(ARCH_PNG_PATH, "rb").read() if os.path.exists(ARCH_PNG_PATH) else b""
    pipe_bytes = open(PIPE_PNG_PATH, "rb").read() if os.path.exists(PIPE_PNG_PATH) else b""

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", DOC_XML)
        if arch_bytes:
            z.writestr("word/media/fig_arch.png", arch_bytes)
        if pipe_bytes:
            z.writestr("word/media/fig_pipe.png", pipe_bytes)


# ------------------------------------------------------------------- Main
def main():
    md = open(SRC, encoding="utf-8").read()
    chapters = split_chapters(md)
    check_structure(chapters)

    # Pass 1: measure pages per chapter (each chapter rendered in isolation)
    counts = []
    with tempfile.TemporaryDirectory() as td:
        for n, title, body in chapters:
            p = os.path.join(td, "c%d.pdf" % n)
            chrome_pdf(document(chapter_html(n, title, body, True)), p)
            counts.append(count_pages(p))

    start, cur = [], 2  # Page 1 is the Table of Contents
    for c in counts:
        start.append(cur)
        cur += c
    expected_total = cur - 1

    # Pass 2: final document with computed TOC and screen page dividers
    inner = toc_html(start) + "\n".join(chapter_html(n, t, b, False, start[idx]) for idx, (n, t, b) in enumerate(chapters))
    final_html = document(inner)

    # Write HTML outputs to both PRS and legacy SRS path for instant browser viewing
    os.makedirs(os.path.dirname(OUT_HTML_PRS), exist_ok=True)
    with open(OUT_HTML_PRS, "w", encoding="utf-8") as f:
        f.write(final_html)
    with open(OUT_HTML_SRS, "w", encoding="utf-8") as f:
        f.write(final_html)

    # Synchronize markdown files
    with open(OUT_MD_SRS, "w", encoding="utf-8") as f:
        f.write(md)

    # Compile Final PDF (Both Final deliverable and preserved report deliverable)
    chrome_pdf(final_html, OUT_PDF_FINAL)
    shutil.copy(OUT_PDF_FINAL, OUT_PDF_REPORT)
    actual_total = count_pages(OUT_PDF_FINAL)

    # Generate Word DOCX files (Both Final deliverable and preserved report deliverable)
    generate_docx(chapters, start, OUT_DOCX_FINAL)
    generate_docx(chapters, start, OUT_DOCX_REPORT)
    generate_docx(chapters, start, OUT_DOCX_DOCS_FINAL)
    generate_docx(chapters, start, OUT_DOCX_DOCS_REPORT)

    print("Pages per chapter :", counts)
    print("Chapter start page:", start)
    print("Expected total    :", expected_total, "| Actual total:", actual_total)
    if actual_total != expected_total:
        sys.exit(f"PAGE MISMATCH: expected {expected_total}, got {actual_total}")
    print("OK -> FINAL PDF   :", OUT_PDF_FINAL)
    print("OK -> REPORT PDF  :", OUT_PDF_REPORT)
    print("OK -> HTML PRS    :", OUT_HTML_PRS)
    print("OK -> HTML SRS    :", OUT_HTML_SRS)
    print("OK -> DOCX FINAL  :", OUT_DOCX_FINAL)
    print("OK -> DOCX REPORT :", OUT_DOCX_REPORT)


if __name__ == "__main__":
    main()
