---
title: movie2manual 機能設計書
version: 1.0.0
date: 2025-09-13
owner: movie2manual maintainers
---

## 1. システム構成
- CLI 実行（`main.py`）と MCP サーバー（`server/main.py`）。
- LLM クライアント: Gemini SDK または OpenAI 互換 API クライアント。
- 画像抽出: `extract_screenshot.py`（ffmpeg 呼び出し）。

## 2. 主要コンポーネント
- `extract_screenshot.py`
  - 型 `ScreenshotSpec`（`time`, `filename`, `caption?`）
  - 関数 `extract_screenshots(video_path, output_dir, screenshot_specs)`
- `server/main.py`
  - MCP サーバー起動エントリ `main()`（`FastMCP.run()`）
  - ツール: `build_manual_from_video`, `health_check`
  - LLM 設定取得 `get_provider_config()`、Gemini/OpenAI 互換クライアント生成
  - 応答解析 `_extract_json_from_text()`、Markdown/画像出力 `handle_response_and_extract()`

## 3. データモデル
### 3.1 生成 Spec（JSON）
```json
{
  "video": "<string>",
  "output_dir": "./manual_assets",
  "markdown_output": "manual.md",
  "title": "操作マニュアル",
  "author": "",
  "body_markdown": "# ...",
  "screenshots": [
    { "time": "HH:MM:SS.mmm", "filename": "step01_*.png", "caption": "..." }
  ]
}
```

### 3.2 Manifest
`output_dir/manifest.json` に以下を保存:
```json
{
  "spec": { /* 上記と同様 */ }
}
```

## 4. フロー設計
### 4.1 `build_manual_from_video`
1. 入力取得: `video_path` or `video_url` を受理、URL は一時保存。
2. LLM 設定: `LLM_PROVIDER`（必要なら一時上書き）、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY`。
3. プロンプト生成: `build_prompt(video_path)`。
4. 推論呼び出し:
   - Gemini: 動画バイナリ + プロンプトを `models.generate_content` へ。
   - OpenAI 互換/Ollama: `chat.completions.create` で JSON のみを期待。
5. 応答解析: `_extract_json_from_text` で JSON を抽出→`Spec` へマッピング。
6. 出力: `manifest.json` 保存、`handle_response_and_extract` で Markdown 書出しと画像抽出。
7. 応答返却: `manifest_path`, `markdown_path`, `image_paths[]`, `spec`, `warnings[]`。

### 4.2 例外・片付け
- ダウンロードした一時ファイルは最後に削除試行。
- 解析失敗時はエラーを返し、クライアント側で対処。

## 5. I/F 仕様
### 5.1 MCP ツール: build_manual_from_video
- 入力: `video_path?`, `video_url?`, `output_dir?`, `title_hint?`, `author?`, `model_provider?`, `screenshot_policy_json?`, `safe_write?`。
- 出力: `conversational_summary`, `spec`, `manifest_path`, `markdown_path`, `image_paths[]`, `warnings[]`。

### 5.2 MCP ツール: health_check
- 入力: なし
- 出力: "ok"

## 6. 設定値
- `.env`: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`（or `GOOGLE_API_KEY`）。
- 既定 `DEFAULT_MODEL_NAME = models/gemini-2.5-flash`。

## 7. セキュリティ・ロギング
- API キーはマスクして標準エラーに記録。
- 追加の個人情報は保存しない前提。

## 8. テスト観点
- 正常系: サンプル動画→`manual_assets` が生成され、画像枚数とパスが返る。
- 異常系: JSON 抽出失敗、動画未検出、ffmpeg 未導入、API キー未設定。

## 9. 運用手順（要約）
- CLI: `python main.py --video /path/to/video.mp4`
- MCP STDIO: `fastmcp run server/main.py --transport stdio`
- MCP SSE: `fastmcp run server/main.py --transport sse --port 9001 --host 0.0.0.0`


