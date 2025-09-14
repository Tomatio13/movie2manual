from __future__ import annotations

from pathlib import Path
from datetime import date


def convert_markdown_to_pdf_with_weasyprint(markdown_path: str, pdf_path: str) -> None:
    """
    Python-Markdown で Markdown を HTML に変換し、WeasyPrint で PDF 化する。

    参考: Python-Markdown を使った HTML 変換の基本（記事の趣旨 `markdown.markdown()`）
    必要な Python パッケージ:
      - markdown
      - weasyprint

    WeasyPrint はシステム依存ライブラリ（cairo/pango 等）に依存します。
    Ubuntu/Debian の例:
      sudo apt-get update && sudo apt-get install -y \
        libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev
    """

    try:
        import markdown  # type: ignore
    except Exception:
        raise RuntimeError("python-markdown が見つかりません。'pip install markdown' を実行してください。")

    try:
        from weasyprint import HTML  # type: ignore
    except Exception:
        raise RuntimeError(
            "WeasyPrint が見つかりません。'pip install weasyprint' を実行し、必要なシステムライブラリも導入してください。"
        )

    md = Path(markdown_path)
    pdf = Path(pdf_path)
    pdf.parent.mkdir(parents=True, exist_ok=True)

    if not md.exists():
        raise FileNotFoundError(f"Markdown ファイルが見つかりません: {md}")

    md_text = md.read_text(encoding="utf-8")

    # よく使う拡張を有効化
    html_body = markdown.markdown(
        md_text,
        extensions=[
            "extra",
            "toc",
            "sane_lists",
            "tables",
            "fenced_code",
        ],
        output_format="html5",
    )

    # 簡易テンプレート + 日本語フォント指定
    # base_url に md.parent を渡すことで、相対パス画像を解決
    today_str = date.today().strftime("%Y-%m-%d")
    html_template = f"""
<!DOCTYPE html>
<html lang=\"ja\">
<head>
  <meta charset=\"UTF-8\" />
  <title>{md.stem}</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm;
      @top-left {{ content: "{md.name}"; font-size: 10pt; color: #333; }}
      @top-right {{ content: "{today_str}"; font-size: 10pt; color: #333; }}
      @bottom-center {{ content: counter(page) "/" counter(pages); font-size: 10pt; color: #333; }}
    }}
    body {{
      font-family: 'Noto Sans CJK JP', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
      line-height: 1.7;
      font-size: 12pt;
      color: #222;
    }}

    h1, h2, h3, h4, h5, h6 {{ page-break-after: avoid; }}
    h1 {{ font-weight: 400; border-bottom: 1px solid #222; padding-bottom: 6px; margin-bottom: 12px; }}
    h2 {{ font-weight: 400; }}

    pre {{ background: #f5f7fa; padding: 10px; border-radius: 6px; overflow: auto; }}
    code {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}
    img {{ max-width: 100%; height: auto; page-break-inside: avoid; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; }}
  </style>
  <meta name=\"generator\" content=\"movie2manual weasyprint\" />
  <meta http-equiv=\"Content-Language\" content=\"ja\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\" />
  <meta charset=\"utf-8\" />
  <meta name=\"referrer\" content=\"no-referrer\" />
  <meta name=\"robots\" content=\"noindex, nofollow\" />
  <meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self' data: 'unsafe-inline'\" />
  <meta name=\"pdf-engine\" content=\"weasyprint\" />
  <meta name=\"base-dir\" content=\"{md.parent}\" />
  <meta name=\"source\" content=\"{md.name}\" />
  <meta name=\"lang\" content=\"ja\" />
  <meta name=\"charset\" content=\"utf-8\" />
  <meta name=\"format-detection\" content=\"telephone=no\" />
  <meta name=\"format-detection\" content=\"address=no\" />
  <meta name=\"format-detection\" content=\"email=no\" />
  <meta name=\"format-detection\" content=\"date=no\" />
</head>
<body>
{html_body}
</body>
</html>
"""

    HTML(string=html_template, base_url=str(md.parent.resolve())).write_pdf(str(pdf))


def convert_markdown_to_pdf(markdown_path: str, pdf_path: str) -> None:
    """Markdown を HTML に変換して WeasyPrint で PDF 出力する（一本化）。

    参考: 記事にある `markdown.markdown()` の基本的な使い方を採用。
    See: https://chocottopro.com/?p=512
    """
    return convert_markdown_to_pdf_with_weasyprint(markdown_path, pdf_path)


