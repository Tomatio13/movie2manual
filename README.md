# movie2manual

動画を解析し、操作マニュアル（Markdown と静止画）を自動生成するツールです。

## 機能概要
- Google Generative AI (Gemini) で動画内容を解析し、マニュアル素案(JSON)を生成
- 指定されたタイムスタンプで ffmpeg により静止画を抽出
- 生成された本文を Markdown として保存（必要に応じて PDF 化の拡張も可能）

## 必要要件
- Python 3.9+
- 外部コマンド: ffmpeg（静止画抽出に必須）
- Google Generative AI の API キー（`.env` に設定）

## セットアップ
```bash
git clone https://github.com/your_name/movie2manual.git
cd movie2manual
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env を編集して GOOGLE_API_KEY=... を設定
```

## 使い方
1. 動画ファイルパスを `main.py` の `video_file_name` に設定します（またはコードを環境変数化してください）。
2. 実行:
```bash
python main.py 2> run.log
```
- モデル応答の本文が標準出力に出ます。
- `.env` の API キーは読み込み時にマスクされ、標準エラーに記録されます。
- 応答から抽出した JSON に従い、`output_dir` 配下に静止画と Markdown が生成されます。

## 環境変数
`.env` に以下のいずれかを設定してください（上ほど優先）。
```
GOOGLE_API_KEY=xxx
# GEMINI_API_KEY=xxx
# GENAI_API_KEY=xxx
```

## 補足
- ffmpeg が未インストールの場合はエラーになります。

## ライセンス
MIT (予定)
