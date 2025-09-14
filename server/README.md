## movie2manual MCP サーバー (server)

FastMCP を用いた MCP サーバー実装です。`n8n` や Claude Desktop 等の MCP クライアントから接続し、動画から手順書を生成・整形・エクスポートするツール群を提供します。

## 前提条件
- Python 3.10+
- 仮想環境 `.venv` を使用
- 依存関係はリポジトリルートの `requirements.txt` で管理

## セットアップ
```bash
git clone https://github.com/Tomatio13/movie2manual.git
cd movie2manual
python -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## 起動方法

### STDIO（デフォルト）
MCP クライアントが STDIO で接続する場合:
```bash
source .venv/bin/activate
cd server
fastmcp run main.py --transport stdio  
```

### SSE サーバー
HTTP(S) 経由で接続可能な SSE サーバーとして起動:
```bash
source .venv/bin/activate
cd server
fastmcp run main.py --transport sse --port 9001 --host 0.0.0.0
```
- エンドポイント: `http://<host>:9001/sse`
- n8n の MCP Client Tool では上記 URL を設定
- 備考: `fastmcp run server/main.py` のようなファイルパス実行は、
  インポート解決の都合で失敗する場合があります（推奨しません）。

## 提供ツール
本サーバーが提供する MCP ツールは次のとおりです。

- build_manual_from_video: 映像からステップ抽出・初稿マニュアル作成（Markdown + 画像 + manifest）
- health_check: 疎通確認（"ok"）

### ツール詳細

#### build_manual_from_video
- 概要: 動画を解析し、手順書ドラフト（Markdown）とスクリーンショットを出力し、`manifest.json` を保存
- 引数:
  - `video_path: string`（推奨）: ローカル動画パス。空文字の場合は `video_url` を使用
  - `video_url: string`: ダウンロードして一時保存して処理
  - `output_dir: string`: 出力先ディレクトリ。空文字は自動決定（spec/既定）
  - `title_hint: string` / `author: string`: タイトル・作者ヒント
  - `model_provider: string`: `gemini` / `openai` / `ollama`（空は環境変数に従う）
  - `screenshot_policy_json: string`: 追加ポリシーを JSON 文字列で（任意）
  - `safe_write: boolean`: 将来拡張用（既定: false）
  - `export_pdf: boolean`（任意）: Markdown 完成後に PDF を生成（WeasyPrint）
  - `pdf_output: string`（任意）: 出力先パス。未指定時は `markdown.md` と同ディレクトリに同名 `.pdf`
- 返り値（抜粋）:
  - `manifest_path`, `markdown_path`, `image_paths[]`, `spec`, `warnings[]`, `conversational_summary`
- 注意:
  - `video_path` または `video_url` のどちらかは必須
  - LLM は `.env` の `LLM_PROVIDER`, `LLM_API_KEY` 等を参照（Gemini は `GOOGLE_API_KEY` 可）

使用例（n8n MCP Client）
```json
{
  "tool": "build_manual_from_video",
  "args": {
    "video_path": "/path/to/movie.mp4",
    "output_dir": "./manual_assets",
    "title_hint": "App setup",
    "author": "Team",
    "model_provider": "gemini",
    "screenshot_policy_json": "{}",
    "safe_write": false,
    "export_pdf": true,
    "pdf_output": "./manual_assets/manual.pdf"
  }
}
```

#### refine_manual
- 概要: 既存 `manifest.json` の spec を、与えた編集方針でリライトし再出力
- 引数: `manifest_path: string`（必須）, `edit_instructions: string`（必須）
- 返り値: `manifest_path`, `markdown_path`, `image_paths[]`, `spec`, `changes[]`

使用例
```json
{
  "tool": "refine_manual",
  "args": {
    "manifest_path": "./manual_assets/manifest.json",
    "edit_instructions": "各ステップに説明文を追加し、見出しを英語へ"
  }
}
```

#### health_check
- 概要: 簡易疎通（常に "ok" を返す）
- 引数: なし
- 返り値: "ok"

## ヘルスチェック
簡易ツール `health_check` を提供:
```json
{
  "tool": "health_check",
  "args": {}
}
```
応答: "ok"

## トラブルシューティング
- ImportError: "attempted relative import with no known parent package"
  - ルートで `python -m server.main` を実行、または `PYTHONPATH` 調整
- ModuleNotFoundError: No module named 'fastmcp'
  - `.venv` を有効化し、`pip install -r requirements.txt`
- SSE に接続できない
  - ポート/バインド先（`--host`）を確認。`ss -ltnp '( sport = :9001 )'` で待受確認
 - PDF 変換に失敗する（WeasyPrint）
   - Python パッケージ `markdown`, `weasyprint` を導入
   - 追加のシステム依存（Ubuntu 例）: `libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev`

## ライセンス
ルートの `LICENSE` を参照してください。
