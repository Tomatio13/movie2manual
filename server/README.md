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
python -m server.main
```

### SSE サーバー
HTTP(S) 経由で接続可能な SSE サーバーとして起動:
```bash
source .venv/bin/activate
fastmcp run server/main.py --transport sse --port 9001 --host 0.0.0.0
```
- エンドポイント: `http://<host>:9001/sse`
- n8n の MCP Client Tool では上記 URL を設定

### fastmcp CLI（module:var 参照）
`server/main.py` は `mcp` 変数をエクスポートしています:
```bash
source .venv/bin/activate
python -m fastmcp server.main:mcp --transport stdio
```

## 提供ツール
`server/tools` から以下が読み込まれます。
- build_manual: 映像からステップ抽出・初稿マニュアル作成
- refine_manual: マニュアルのリライト/整形
- export_bundle: マニュアルの書き出し（Zip など）

（各ツールの詳細はソースの docstring を参照）

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

## ライセンス
ルートの `LICENSE` を参照してください。
