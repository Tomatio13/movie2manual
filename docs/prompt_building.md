---
title: movie2manual 開発・運用プロンプト集（MCP 含む）
version: 1.0.0
date: 2025-09-13
owner: movie2manual maintainers
---

## 1. 目的
本ドキュメントは、movie2manual の開発・運用で使用するプロンプトの雛形を提供します。MCP ツール呼び出し、モデル切替、品質向上のための指示テンプレートを含みます。

## 2. LLM への基本指示（共通）
```text
あなたは優秀な日本人の動画分析エンジニアです。動画から操作手順書を作成するため、以下の JSON スキーマに厳密に従って出力してください。

- JSON 以外の出力は一切含めないこと
- `screenshots[].time` は `HH:MM:SS.mmm` 形式で秒数指定
- `body_markdown` は Markdown として成立する文章にすること
- `video` は入力動画パスをそのまま記載
- `output_dir` と `markdown_output` は英数字・記号で安全な名前

出力フォーマット:
{
  "video": "<string>",
  "output_dir": "./manual_assets",
  "markdown_output": "manual.md",
  "title": "<string>",
  "author": "<string>",
  "body_markdown": "# ...",
  "screenshots": [
    { "time": "HH:MM:SS.mmm", "filename": "step01_*.png", "caption": "..." }
  ]
}
```

## 3. Gemini 用（動画同梱）
```text
以下の動画バイナリとプロンプトに基づいて JSON を返してください。JSON 以外は返さないでください。
```

## 4. OpenAI 互換 / Ollama 用（Chat Completions）
```text
あなたは有能なテクニカルライターです。上記「基本指示」に従い、有効な JSON のみを返してください。コードフェンスや説明文は不要です。
```

## 5. MCP クライアント呼び出しテンプレート
### 5.1 build_manual_from_video（n8n 例）
```json
{
  "tool": "build_manual_from_video",
  "args": {
    "video_path": "/absolute/path/to/video.mp4",
    "output_dir": "./manual_assets",
    "title_hint": "<optional>",
    "author": "<optional>",
    "model_provider": "gemini",
    "screenshot_policy_json": "{}",
    "safe_write": false
  }
}
```

### 5.2 health_check
```json
{ "tool": "health_check", "args": {} }
```

## 6. 品質改善プロンプト例
- **簡潔性強化**: 「各ステップの説明は 2〜3 文で簡潔に。冗長な前置きは禁止。」
- **粒度調整**: 「スクリーンショットは 5〜8 枚に抑え、要点となる画面のみ選定。」
- **用語統一**: 「UI のラベルは動画中の表記を正とし、訳語は使わない。」
- **再現性**: 「前提条件セクションに必要なバージョンや設定を明記。」

## 7. 開発者向け運用メモ
- `.env` で `LLM_PROVIDER` を切替（gemini/openai/ollama）。
- OpenAI 互換 / Ollama の `LLM_BASE_URL` を忘れず設定。
- 動画は `mp4` を推奨。長尺は処理時間増に注意。

## 8. PDF 出力の体裁に寄せるための指示（任意）
- 見出しは `#`/`##` を使用し、太字を避ける（出力 CSS と整合）。
- `# タイトル` の直後に短い概要文を置く（レイアウトの見栄え改善）。
- 画像の直後にキャプションを 1 文で添える。
- 箇条書きは `-` 記法を使用し、1 項目は 1 行に収める。


