---
title: movie2manual 要件定義書
version: 1.0.0
date: 2025-09-13
owner: movie2manual maintainers
---

## 1. 目的
動画から操作手順書（Markdown と静止画）を自動生成し、社内外のナレッジ共有を効率化する。

## 2. スコープ
- 入力: ローカル動画ファイルまたは URL。
- 出力: Markdown 本文、スクリーンショット画像群、`manifest.json`。
- 実行形態: CLI と MCP サーバー（STDIO / SSE）。

## 3. 利用者／ステークホルダー
- 一般ユーザー: 手順書作成担当、QA、CS。
- 管理者: 環境構築、キー管理、モデル選定。
- 開発者: 機能拡張、保守。

## 4. 前提・制約
- 依存: Python 3.9+（MCP サーバーは 3.10+ 推奨）、ffmpeg、LLM プロバイダ（Gemini / OpenAI 互換 / Ollama）。
- 環境変数: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` 等。
- セキュリティ: API キーは `.env` で管理し出力時にはマスク表示。
- 互換性: Linux / macOS / Windows（ffmpeg 導入前提）。

## 5. 機能要件
### 5.1 マニュアル生成（必須）
- 入力動画を解析し、以下構造の JSON を LLM で生成できること。
  - `video`, `output_dir`, `markdown_output`, `title`, `author`, `body_markdown`, `screenshots[]`。
- `screenshots[].time` は `HH:MM:SS.mmm` 形式の秒数指定とする。
- `extract_screenshots` により静止画を抽出し、`output_dir` に保存すること。
- `body_markdown` を Markdown ファイルへ書き出すこと。

### 5.2 MCP ツール提供
- `build_manual_from_video` を提供し、引数（`video_path`/`video_url`/`output_dir`/他）を受け取れること。
- `health_check` により疎通確認ができること。

### 5.3 マニフェスト出力
- 生成内容を `manifest.json` として `output_dir` に保存すること。

### 5.4 プロバイダ切替
- `LLM_PROVIDER` または引数により `gemini` / `openai` / `ollama` を切替可能。
- Gemini は動画バイナリをインラインで与え、OpenAI 互換は Chat Completions を使用。

## 6. 非機能要件
- パフォーマンス: 10 分以内の動画で 2 分以内に Markdown と 3〜10 枚の静止画を出力する目安。
- 可用性: CLI はローカル完結。MCP サーバーは SSE/STDIO の起動手順を提供。
- 運用: ログは標準エラーへ要点を出力。API キーはマスク。
- 移植性: requirements.txt に依存を明記。

## 7. 入出力仕様
- 入力: `--video`（CLI）、`video_path`/`video_url`（MCP）。
- 出力: `manual_assets/` 配下に `manual.md` と `stepXX_*.png`、`manifest.json`。

## 8. エラーハンドリング
- JSON 抽出失敗時は例外を投げ、ユーザーにプロンプト/モデル見直しを促す。
- 動画未検出・ffmpeg 未導入・API キー未設定時は明示的エラー。

## 9. セキュリティ・プライバシー
- API キーを標準出力へ出さない。ログでは先頭4桁+末尾4桁のみ表示。
- URL 入力時は一時ファイルへダウンロードし、処理後は削除試行。

## 10. 品質保証
- 動作確認: サンプル動画で CLI と MCP の双方を手動テスト。
- Linter: リポジトリ標準に従う。

## 11. 将来拡張（参考）
- PDF/HTML エクスポート、図表生成、字幕解析、OCR 連携、国際化（i18n）。


