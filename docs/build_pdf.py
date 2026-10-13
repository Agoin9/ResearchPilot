# -*- coding: utf-8 -*-
"""ResearchPilot 文档导出：Markdown → HTML → PDF（Edge 无头打印）。

用法：
    python build_pdf.py            # 默认导出 ResearchPilot-项目文档.md → .pdf
    python build_pdf.py 输入.md 输出.pdf

依赖：markdown（pip install markdown）；PDF 由本机 Edge 无头模式打印（需 Windows 自带 Edge）。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 16mm 14mm 17mm 14mm; }
body { font-family: "Microsoft YaHei", "PingFang SC", "SimHei", sans-serif;
       font-size: 10pt; line-height: 1.62; color: #1f2937; }
h1 { font-size: 15.5pt; color: #0e7490; page-break-before: always;
     border-bottom: 2.5px solid #0e7490; padding-bottom: 5px;
     margin: 2px 0 10px; line-height: 1.35; }
body > h1:first-of-type { page-break-before: avoid; font-size: 21pt;
     text-align: center; border-bottom: none; padding-bottom: 0; }
h2 { font-size: 12.5pt; color: #0e7490; margin: 13px 0 5px; }
h3 { font-size: 11pt; color: #111827; margin: 10px 0 4px; }
p { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 7px 0; }
th, td { border: 1px solid #cbd5e1; padding: 3px 6px; font-size: 8.5pt;
         text-align: left; vertical-align: top; word-break: break-word; }
th { background: #e7f0f4; font-weight: 600; color: #0e7490; }
tr { page-break-inside: avoid; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8pt;
       background: #f3f4f6; padding: 1px 3px; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #e2e8f0; border-left: 3px solid #0e7490;
      padding: 6px 9px; border-radius: 4px; margin: 6px 0; }
pre code { background: none; padding: 0; display: block; white-space: pre-wrap;
           word-break: break-all; line-height: 1.45; }
blockquote { border-left: 3px solid #cbd5e1; margin: 6px 0; padding: 2px 10px;
             color: #4b5563; background: #fafafa; }
ul, ol { margin: 4px 0; padding-left: 20px; }
li { margin: 1.5px 0; }
hr { border: none; border-top: 1px solid #d1d5db; margin: 12px 0; }
strong { color: #111827; }
a { color: #0e7490; text-decoration: none; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_edge() -> str:
    for candidate in EDGE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("未找到 Edge 浏览器，请安装或修改 EDGE_CANDIDATES")


def convert(md_path: Path, pdf_path: Path) -> None:
    html_path = pdf_path.with_suffix(".html")
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    html_path.write_text(
        TEMPLATE.format(title=md_path.stem, css=CSS, body=body), encoding="utf-8"
    )
    print(f"[1/3] HTML 已生成：{html_path}")

    edge = find_edge()
    profile = str(Path(tempfile.gettempdir()) / "rp-edge-pdf-profile")
    cmd = [
        edge,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--user-data-dir={profile}",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=180)
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        raise RuntimeError(
            f"Edge 打印失败：\n{result.stdout.decode(errors='ignore')[-500:]}\n"
            f"{result.stderr.decode(errors='ignore')[-500:]}"
        )
    print(f"[2/3] PDF 已生成：{pdf_path}（{pdf_path.stat().st_size // 1024} KB）")


def verify(pdf_path: Path) -> None:
    import pymupdf  # 仅验证用，需 pip install pymupdf

    doc = pymupdf.open(str(pdf_path))
    first = doc[0].get_text()
    last = doc[-1].get_text()
    assert doc[0].rect.width > 500, "页面尺寸异常"
    assert "ResearchPilot" in first, "封面缺失"
    assert "不足与未来优化方向" in "\n".join(
        doc[i].get_text() for i in range(doc.page_count)
    ), "末章缺失"
    print(f"[3/3] 验证通过：共 {doc.page_count} 页，A4，中文与章节结构完整")


if __name__ == "__main__":
    args = sys.argv[1:]
    md_file = Path(args[0]) if len(args) > 0 else Path(__file__).parent / "ResearchPilot-项目文档.md"
    pdf_file = Path(args[1]) if len(args) > 1 else md_file.with_suffix(".pdf")
    convert(md_file, pdf_file)
    verify(pdf_file)
