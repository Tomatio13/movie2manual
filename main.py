from google import genai
from google.genai import types
import json
import re
import sys
import os
from pathlib import Path
from contextlib import redirect_stdout
from extract_screenshot import Spec, extract_screenshots

# .env から環境変数を読み込み
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore

if load_dotenv is not None:
    # プロジェクト直下の .env を優先的に読み込む
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# API キーは複数候補名を許容（互換性のため）
api_key = (
    os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GENAI_API_KEY")
)

if not api_key:
    print(
        "環境変数 GOOGLE_API_KEY (または GEMINI_API_KEY/GENAI_API_KEY) が未設定です。",
        file=sys.stderr,
    )
    sys.exit(1)

# マスクして読み込み結果を出力（stdout 汚染を避け stderr へ）
masked = (
    f"{api_key[:4]}...{api_key[-4:]}" if isinstance(api_key, str) and len(api_key) >= 8 else "***"
)
print(f"API キーを .env から読み込みました: {masked}", file=sys.stderr)

client = genai.Client(api_key=api_key)

video_file_name = "/home/masato/Downloads/test/ワークフロー作成マニュアル.mp4"
video_bytes = open(video_file_name, 'rb').read()

prompt="""
あなたは優秀な日本人の動画分析エンジニアです。
指定された動画を分析して、操作マニュアルを作成するための要素を抽出し、出力します。

以下が出力例です。

- `body_markddown` に操作手順の文章を記述してください。文章には、`screenshots`に記述したファイル名やcaptionを埋め込んでMarkdownで表示できるようにしてださい。
- `screenshots` に操作手順書に必要となる画像のタイムスタンプを記述してください。timeの記述は、必ず秒数(例.00:00:03.500)で記述してください。
- `video` には指定された動画のパス{video_file_name}をそのまま記述してください
- `output_dir` に操作手順書の出力先ディレクトリを記述してください。動画の内容から英文字でディレクトリ名を作成してください。
- `markdown_output` に操作手順書のMarkdownファイル名を記述してください。動画の内容から英文字でファイル名を作成してください。
- `title` に操作手順書のタイトルを記述してください。動画の内容からタイトルを作成してください。
- `author` に操作手順書の作者を記述してください。動画の内容から作者を作成してください。 

# 出力例
  {
  "video": "/home/masato/Downloads/test/n8n認証情報マニュアル化.mp4",
  "output_dir": "./manual_assets",
  "markdown_output": "manual.md",
  "title": "n8n 操作マニュアル",
  "author": "Team",
  "body_markdown": "# はじめに\nこのマニュアルは n8n の基本操作を説明します。\n\n## 前提条件\n- n8n がインストール済みであること\n\n## 手順概要\n1. アプリを起動します。\n2. ワークフローを作成します。\n3. 認証情報を設定します。\n",
  "screenshots": [
        { "time": "00:00:03.500", "filename": "step01_start.png", "caption": "アプリを起動" },
          { "time": "00:00:10.000", "filename": "step02_home.png", "caption": "ホーム画面を確認" },
          { "time": "00:00:22.000", "filename": "step03_new_workflow.png", "caption": "新規ワークフロー作成" },
          { "time": "00:00:40.200", "filename": "step04_credentials.png", "caption": "認証情報の設定画面" },
          { "time": "00:01:05.000", "filename": "step05_execute.png", "caption": "ワークフローを実行" }
        ]
  }

"""

# プレースホルダを実際の動画パスへ埋め込み
prompt = prompt.replace("{video_file_name}", video_file_name)

response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
            ),
            types.Part(text=prompt)
        ]
    )
)

resp_text = response.text
print(resp_text)

# --- 以下: 応答本文からJSONを抽出し、静止画抽出を実行（標準出力は汚さない） ---

def _extract_json_from_text(text: str):
    def escape_newlines_in_json_strings(s: str) -> str:
        result_chars = []
        in_string = False
        escape = False
        for ch in s:
            if in_string:
                if escape:
                    # 次の文字はエスケープとしてそのまま
                    result_chars.append(ch)
                    escape = False
                    continue
                if ch == "\\":
                    result_chars.append(ch)
                    escape = True
                    continue
                if ch == "\n":
                    result_chars.append("\\n")
                    continue
                if ch == "\r":
                    # CRLF の場合は無視（\n 側で処理）
                    continue
                if ch == '"':
                    in_string = False
                    result_chars.append(ch)
                    continue
                result_chars.append(ch)
            else:
                if ch == '"':
                    in_string = True
                    result_chars.append(ch)
                else:
                    result_chars.append(ch)
        return "".join(result_chars)

    def try_load(candidate: str):
        # そのまま
        try:
            return json.loads(candidate)
        except Exception:
            pass
        # 文字列中の生改行を \n に置換
        try:
            return json.loads(escape_newlines_in_json_strings(candidate))
        except Exception:
            return None

    # 候補を列挙: 全文 → フェンスjson → フェンス任意 → 波括弧範囲
    candidates = []
    candidates.append(text)

    fence_json = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
    candidates += fence_json.findall(text)

    fence_any = re.compile(r"```\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
    candidates += fence_any.findall(text)

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidates.append(text[first:last+1])

    for cand in candidates:
        obj = try_load(cand)
        if obj is not None:
            return obj
    return None

try:
    spec_dict = _extract_json_from_text(resp_text)
    if spec_dict is None:
        raise ValueError("モデル応答から有効なJSONを抽出できませんでした。")

    # デフォルト補完
    if "video" not in spec_dict:
        spec_dict["video"] = video_file_name
    if "output_dir" not in spec_dict:
        spec_dict["output_dir"] = "./manual_assets"
    if "markdown_output" not in spec_dict:
        spec_dict["markdown_output"] = "./manual.md"


    # body_markdown を output_dir/markdown_output に保存
    try:
        out_dir = Path(spec_dict.get("output_dir", "./manual_assets"))
        out_dir.mkdir(parents=True, exist_ok=True)
        md_name = spec_dict.get("markdown_output", "manual.md")
        md_path = out_dir / md_name
        body = spec_dict.get("body_markdown", "")
        md_path.write_text(body, encoding="utf-8")
    except Exception as e:
        print(f"Markdown 保存でエラー: {e}", file=sys.stderr)

    # Spec 変換
    spec = Spec.from_dict(spec_dict)
    # 動画存在チェック
    if not Path(spec.video).exists():
        print(f"動画ファイルが見つかりません: {spec.video}", file=sys.stderr)
    else:
        # 実行中の標準出力は標準エラーへ退避して、応答本文のみがstdoutに残るようにする
        with redirect_stdout(sys.stderr):
            extract_screenshots(spec)


except Exception as e:
    print(f"スクリーンショット抽出処理でエラー: {e}", file=sys.stderr)
