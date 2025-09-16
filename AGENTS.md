# Repository Guidelines

## プロジェクト構成とモジュール構成
movie2manual は Python 製の動画マニュアル生成ツールで、ルートの `main.py` が CLI から LLM・ffmpeg・PDF 生成を統括します。`extract_screenshot.py` は JSON のタイムスタンプにしたがって ffmpeg を呼び出し、`pdf_export.py` が Markdown を WeasyPrint で PDF へ変換します。MCP サーバーは `server/main.py` にまとまり、FastMCP から動画解析ツール `build_manual_from_video` などを公開します。設計資料は `docs/`、サンプルの出力例は `sample/`、実行結果は既定で `output_dir/manual_assets/` に保存されます。

## ビルド・テスト・開発コマンド
- `python -m venv .venv && source .venv/bin/activate`: 仮想環境を構築して依存関係を隔離します。
- `python -m pip install -r requirements.txt`: LLM クライアント、FastMCP、WeasyPrint など必須パッケージを導入します。
- `python main.py --video /path/to/video.mp4 --export-pdf --pdf-output ./manual_assets/manual.pdf`: CLI でマニュアルと PDF を出力します。`--dry-run` オプションは存在しないため、検証時は一時ディレクトリを指定してください。
- `cd server && fastmcp run main.py --transport sse --port 9001`: MCP サーバーを起動し、n8n や Claude Desktop から接続できるようにします。

## コーディングスタイルと命名規則
Python 3.9 以降を前提に 4 スペースインデントと型ヒントを維持してください。LLM 設定やスクリーンショット仕様は `ProviderConfig` や `ScreenshotSpec` のように `CamelCase` クラス名＋スネークケース属性で統一されています。新規モジュールも `Path` と `dataclass` を活用し、副作用は `if __name__ == "__main__"` で囲みます。外部コマンド呼び出しは `subprocess` ではなく既存のユーティリティを再利用し、例外メッセージは日本語で明瞭に記述します。

## テスト指針
自動テストは未整備のため、動画長の異なるケースで CLI と MCP の両経路を手動確認してください。`python main.py --video ...` 実行後、`manual_assets/manifest.json` と画像枚数がプロンプトで要求した数に一致するかをレビューします。サーバー経由では `fastmcp` の `health_check` ツールを呼び、HTTP 9001 番の待受を `ss -ltnp` で確認します。再現手順は README_EN.md のクイックスタート節に追記し、差分が出るサンプルを `sample/` 以下へ追加します。

## コミットと Pull Request ガイドライン
履歴では「PDF出力機能を追加し…」のように日本語で機能全体を一文要約するコミットメッセージが使われています。1 コミット 1 トピックを守り、主要ファイルと観測結果をメッセージ末尾に簡潔に添えてください。Pull Request では背景、変更点、検証コマンド、生成された `manual_assets` のスクリーンショット（必要な場合）を説明し、関連 Issue を `refs #123` 形式で紐づけます。公開リソースに API キーや動画データを含めないこと、実行ログにマスク済みキーが出力されているかを確認してから提出します。

## セキュリティと設定
`.env.example` を複製して `LLM_PROVIDER`、`LLM_MODEL`、`LLM_API_KEY` を設定しますが、個人の `.env` ファイルや生成された `output_dir` はコミットに含めないでください。ffmpeg と WeasyPrint のシステム依存パッケージが不足すると失敗するため、CI やサーバー環境では `apt-get install ffmpeg libcairo2 libpango-1.0-0 ...` などを事前に実行します。大容量動画を扱う場合は一時領域が肥大化するため、`output_dir` を SSD 上の十分な空き領域へ変更し、完了後に成果物以外のテンポラリを削除してください。
