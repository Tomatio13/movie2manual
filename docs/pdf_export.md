---
title: movie2manual PDF 出力ガイド（WeasyPrint）
version: 1.0.0
date: 2025-09-14
owner: movie2manual maintainers
---

## 概要
movie2manual は Markdown から PDF への変換を、Python-Markdown + WeasyPrint で実装しています。記事の基本どおり `markdown.markdown()` で HTML を生成し、WeasyPrint で PDF にレンダリングします。

## 依存
- Python パッケージ（`requirements.txt`）
  - markdown
  - weasyprint
- システムライブラリ（Ubuntu/Debian 例）
  - `libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev`

## レイアウト仕様
- ページヘッダ: 左=mdファイル名、右=変換日（YYYY-MM-DD）
- ページフッタ: `counter(page)/counter(pages)`
- 見出し: `h1/h2` は非ボールド、`h1` のみ下線

## CLI からの利用
```bash
python main.py --video /path/to/video.mp4 --export-pdf
# 出力先を指定する場合
python main.py --video /path/to/video.mp4 --export-pdf --pdf-output ./manual_assets/manual.pdf
```

## MCP からの利用
`build_manual_from_video` 引数:
- `export_pdf: boolean`
- `pdf_output: string`（任意）

## 既知事項 / トラブルシュート
- 画像パスは Markdown と同ディレクトリを基準に解決されます。
- 生成に失敗する場合、WeasyPrint の依存パッケージが不足していないか確認してください。
