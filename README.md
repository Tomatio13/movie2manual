<h1 align="center">movie2manual</h1>

<p align="center">
  <a href="README.md">🇯🇵 日本語</a> · 
  <a href="README_EN.md">🇺🇸 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" />
  <img src="https://img.shields.io/badge/ffmpeg-required-orange" />
  <img src="https://img.shields.io/badge/LLM-Gemini%20%7C%20OpenAI%20API%20Compatible%20%7C%20Ollama-green" />
</p>

動画を解析し、操作マニュアル（Markdown と静止画）を自動生成するツールです。

## 機能概要
- LLM（Gemini / OpenAI互換 / Ollama）でマニュアル素案(JSON)を生成
- 指定されたタイムスタンプで ffmpeg により静止画を抽出
- 生成された本文を Markdown として保存（PDF 出力に対応：python-markdown + WeasyPrint）

## 必要要件
- Python 3.9+
- 外部コマンド: ffmpeg（静止画抽出に必須）
- LLM プロバイダ設定（`.env` で指定）
  - Gemini: API キー必須
  - OpenAI 互換: 通常 API キー必須（`LLM_BASE_URL` が必要な場合あり）
  - Ollama: API キー不要（ローカル推論。`LLM_BASE_URL` が必要）

## セットアップ
```bash
git clone https://github.com/Tomatio13/movie2manual.git
cd movie2manual
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env を編集して LLM_PROVIDER/LLM_MODEL/LLM_API_KEY などを設定
```
## 環境変数（.env）
- LLM_PROVIDER: gemini | openai | ollama
- LLM_BASE_URL: OpenAI互換/ollama のときに指定（例: https://api.openai.com/v1, http://localhost:11434/v1）
- LLM_MODEL: 使用モデル（例: models/gemini-2.5-flash, gpt-4o-mini, llama3.1）
- LLM_API_KEY: APIキー（ollamaは不要。Geminiは必須。OpenAI互換は通常必須）

### 設定例
```env
LLM_PROVIDER=gemini
LLM_MODEL=models/gemini-2.5-flash
LLM_API_KEY=AIza...
```
```env
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
```
```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1
# LLM_API_KEY は不要
```

## 使い方
1. 動画ファイルパスを `main.py` の `--video` に設定します。
2. 実行:
```bash
 python main.py --video /path/to/video.mp4
```
- モデル応答の本文が標準出力に出ます。
- `.env` の API キーは読み込み時にマスクされ、標準エラーに記録されます。
- 応答から抽出した JSON に従い、`output_dir` 配下に静止画と Markdown が生成されます。

### PDF 出力（オプション）
- このリポジトリは、記事の基本どおり `markdown.markdown()` で HTML を生成し、WeasyPrint で PDF へ変換します。
- 依存パッケージ: `markdown`, `weasyprint`（`requirements.txt` に含まれています）
- システム依存（Ubuntu 例）: `libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev`

実行例（Markdown 生成後に PDF も生成）:
```bash
python main.py --video /path/to/video.mp4 --export-pdf
# 出力先を明示する場合
python main.py --video /path/to/video.mp4 --export-pdf --pdf-output ./manual_assets/manual.pdf
```

レイアウト仕様（WeasyPrint）
- ページヘッダ: 左=mdファイル名、右=変換日（YYYY-MM-DD）
- ページフッタ: `current/total` 形式のページ番号
- 見出し: `h1/h2` は非ボールド、`h1` のみ下線

### クイックスタート（各プロバイダ）
```bash
# Gemini
echo -e "LLM_PROVIDER=gemini\nLLM_MODEL=models/gemini-2.5-flash\nLLM_API_KEY=AIza..." > .env
python main.py --video /path/to/video.mp4

# OpenAI 互換
echo -e "LLM_PROVIDER=openai\nLLM_BASE_URL=https://api.openai.com/v1\nLLM_MODEL=gpt-4o-mini\nLLM_API_KEY=sk-..." > .env
python main.py --video /path/to/video.mp4

# Ollama
echo -e "LLM_PROVIDER=ollama\nLLM_BASE_URL=http://localhost:11434/v1\nLLM_MODEL=llama3.1" > .env
python main.py --video /path/to/video.mp4
```

### サンプル出力
出力先 `output_dir` に以下が生成されます（例）。
- `manual_assets/manual.md`
- `manual_assets/step01_start.png` ほか

> 例: `manual.md` の抜粋
```markdown
# はじめに
このマニュアルは n8n の基本操作を説明します。
```

## 補足
- ffmpeg が未インストールの場合はエラーになります。
 - サブドキュメント: [`n8n_workflow_chat_with_mcp_manual/n8n_workflow_chat_with_mcp_manual.md`](n8n_workflow_chat_with_mcp_manual/n8n_workflow_chat_with_mcp_manual.md)

## ffmpeg のインストール例
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`
- macOS (Homebrew): `brew install ffmpeg`
- Windows (Chocolatey): `choco install ffmpeg`

## トラブルシューティング
- JSON 抽出に失敗する: モデル応答がJSONでない場合があります。プロバイダやプロンプトを見直してください。
- ffmpeg が見つからない: 上記のインストール手順で導入後、再実行してください。
- 環境変数未設定: `.env` に `LLM_PROVIDER` と必要に応じて `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` を設定してください。
- `--video` のパスが不正: 実在する動画ファイルを指定してください。
- PDF 変換に失敗する（WeasyPrint）: Python パッケージ `markdown`, `weasyprint` を導入
- PDF 変換に失敗する（pandoc）: システム依存ライブラリ `libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev` を導入
- n8nのMCP Clinetのデフォルトタイムアウトは60秒です。動画が長い場合、タイムアウトするので、600秒などに変更してください。
  変更方法は、MCP Clinetのオプションのtimeout時間を変更してください。

## ライセンス
MIT


