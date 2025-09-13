from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.request
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP, Context
from google import genai
from google.genai import types
from openai import OpenAI

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore

# extract_screenshot はリポジトリ直下にあるため、ルートを import 解決に追加
PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_str = str(PROJECT_ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
from extract_screenshot import ScreenshotSpec, extract_screenshots  # type: ignore


# チュートリアル準拠の最小構成: グローバル mcp に直接ツールを登録
# 参考: https://github.com/jlowin/fastmcp/blob/main/docs/tutorials/create-mcp-server.mdx
mcp = FastMCP("movie2manual")


@contextmanager
def _override_env(var: str, value: Optional[str]):
    prev = os.environ.get(var)
    try:
        if value is None:
            if var in os.environ:
                del os.environ[var]
        else:
            os.environ[var] = value
        yield
    finally:
        if prev is None:
            if var in os.environ:
                del os.environ[var]
        else:
            os.environ[var] = prev


def _download_to_tmp(url: str) -> str:
    suffix = os.path.splitext(url.split("?")[0].split("#")[0])[1] or ".mp4"
    fd, tmp_path = tempfile.mkstemp(prefix="movie2manual_", suffix=suffix)
    os.close(fd)
    urllib.request.urlretrieve(url, tmp_path)
    return tmp_path

# ===== ルート main.py 相当の最低限の実装を内包（依存削減のため） =====
DEFAULT_MODEL_NAME = "models/gemini-2.5-flash"


@dataclass
class ProviderConfig:
    provider: str  # "gemini" | "openai" | "ollama"
    base_url: Optional[str]
    model_name: str
    api_key: Optional[str]


def _load_env_file() -> None:
    if load_dotenv is not None:
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def _mask_api_key(key: str) -> str:
    if isinstance(key, str) and len(key) >= 8:
        return f"{key[:4]}...{key[-4:]}"
    return "***"


def get_provider_config() -> ProviderConfig:
    _load_env_file()
    provider = (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()
    base_url = os.getenv("LLM_BASE_URL")
    model_name = os.getenv("LLM_MODEL") or DEFAULT_MODEL_NAME

    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GENAI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    if provider == "gemini":
        if not api_key:
            raise RuntimeError("Gemini 用 API キーが必要です")
        if not model_name:
            model_name = DEFAULT_MODEL_NAME
    elif provider in ("openai", "ollama"):
        if provider == "openai" and not base_url:
            base_url = "https://api.openai.com/v1"
        if provider == "ollama" and not base_url:
            base_url = "http://localhost:11434/v1"
        if provider == "openai" and not api_key:
            raise RuntimeError("OpenAI 用 API キーが必要です")
        if provider == "ollama" and not api_key:
            api_key = "ollama"
        if not model_name or model_name == DEFAULT_MODEL_NAME:
            model_name = os.getenv("LLM_MODEL") or ("gpt-4o-mini" if provider == "openai" else "llama3.1")
    else:
        raise RuntimeError(f"未対応の LLM_PROVIDER: {provider}")

    if api_key:
        print(f"API キーを .env から読み込みました: {_mask_api_key(api_key)}", file=sys.stderr)
    else:
        print("API キーなしで動作します（ollama想定）", file=sys.stderr)

    return ProviderConfig(provider=provider, base_url=base_url, model_name=model_name, api_key=api_key)


def create_gemini_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def create_openai_compatible_client(api_key: str, base_url: Optional[str]) -> OpenAI:
    if base_url:
        return OpenAI(api_key=api_key or "", base_url=base_url)
    return OpenAI(api_key=api_key or "")


PROMPT_TEMPLATE = """
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


def build_prompt(video_file_name: str) -> str:
    return PROMPT_TEMPLATE.replace("{video_file_name}", video_file_name)


def read_video_bytes(video_file_name: str) -> bytes:
    with open(video_file_name, "rb") as f:
        return f.read()


def generate_response_text_gemini(client: genai.Client, video_file_name: str, prompt: str, model_name: str) -> str:
    video_bytes = read_video_bytes(video_file_name)
    response = client.models.generate_content(
        model=model_name,
        contents=types.Content(
            parts=[
                types.Part(
                    inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
                ),
                types.Part(text=prompt),
            ]
        ),
    )
    return response.text


def generate_response_text_openai(client: OpenAI, prompt: str, model_name: str) -> str:
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful AI that outputs valid JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content or ""


def _extract_json_from_text(text: str):
    def escape_newlines_in_json_strings(s: str) -> str:
        result_chars = []
        in_string = False
        escape = False
        for ch in s:
            if in_string:
                if escape:
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
        try:
            return json.loads(candidate)
        except Exception:
            pass
        try:
            return json.loads(escape_newlines_in_json_strings(candidate))
        except Exception:
            return None

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


@dataclass
class Spec:
    video: str
    output_dir: str = "./manual_assets"
    markdown_output: str = "./manual.md"
    title: str = "操作マニュアル"
    author: str = ""
    body_markdown: str = ""
    screenshots: Optional[List[ScreenshotSpec]] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Spec":
        shots = [ScreenshotSpec(**s) for s in d.get("screenshots", [])]
        return Spec(
            video=d.get("video", ""),
            output_dir=d.get("output_dir", "./manual_assets"),
            markdown_output=d.get("markdown_output", "./manual.md"),
            title=d.get("title", "操作マニュアル"),
            author=d.get("author", ""),
            body_markdown=d.get("body_markdown", ""),
            screenshots=shots,
        )


def handle_response_and_extract(resp_text: str, default_video_file: str) -> None:
    spec_dict = _extract_json_from_text(resp_text)
    if spec_dict is None:
        raise ValueError("モデル応答から有効なJSONを抽出できませんでした。")
    spec = Spec.from_dict(spec_dict)
    if not spec.video:
        spec.video = default_video_file
    try:
        out_dir = Path(spec.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / spec.markdown_output
        md_path.write_text(spec.body_markdown or "", encoding="utf-8")
    except Exception as e:
        print(f"Markdown 保存でエラー: {e}", file=sys.stderr)
    if not Path(spec.video).exists():
        print(f"動画ファイルが見つかりません: {spec.video}", file=sys.stderr)
        return
    with redirect_stdout(sys.stderr):
        extract_screenshots(spec.video, spec.output_dir, spec.screenshots or [])


@mcp.tool
async def build_manual_from_video(
    video_path: str = "",
    video_url: str = "",
    output_dir: str = "",
    title_hint: str = "",
    author: str = "",
    model_provider: str = "",
    screenshot_policy_json: str = "",
    safe_write: bool = False,
    ctx: Context = None,
) -> Dict[str, Any]:
    if ctx is not None:
        await ctx.info("build_manual_from_video: start")

    # 1) 入力動画の取得
    local_video: Optional[str] = video_path or None
    downloaded_tmp: Optional[str] = None
    if not local_video and video_url:
        if ctx is not None:
            await ctx.info("downloading video from URL...")
        local_video = _download_to_tmp(video_url)
        downloaded_tmp = local_video

    if not local_video or not Path(local_video).exists():
        raise ValueError("video_path か video_url のいずれかを指定してください（存在すること）")

    # 2) Provider 設定の取得（必要なら一時的に LLM_PROVIDER を上書き）
    with _override_env("LLM_PROVIDER", (model_provider or os.environ.get("LLM_PROVIDER"))):
        cfg = get_provider_config()

    # 3) プロンプト生成
    prompt = build_prompt(local_video)

    # 4) LLM 呼び出し
    if cfg.provider == "gemini":
        if not cfg.api_key:
            raise RuntimeError("Gemini 用 API キーがありません")
        if ctx is not None:
            await ctx.info(f"calling Gemini model: {cfg.model_name}")
        client = create_gemini_client(cfg.api_key)
        resp_text = generate_response_text_gemini(client, local_video, prompt, cfg.model_name)
    else:
        if ctx is not None:
            await ctx.info(f"calling OpenAI-compatible model: {cfg.model_name}")
        client = create_openai_compatible_client(cfg.api_key or "", cfg.base_url)
        resp_text = generate_response_text_openai(client, prompt, cfg.model_name)

    if ctx is not None:
        await ctx.info("LLM response received. Parsing spec...")

    # 5) Spec 抽出・正規化
    spec_dict = _extract_json_from_text(resp_text)
    if spec_dict is None:
        raise ValueError("モデル応答から有効なJSONを抽出できませんでした。")

    spec = Spec.from_dict(spec_dict)
    if not spec.video:
        spec.video = local_video

    # screenshot_policy（任意）を JSON 文字列で受け取り、必要であれば spec に反映（現状未使用）
    try:
        if screenshot_policy_json:
            policy_obj = json.loads(screenshot_policy_json)
            if isinstance(policy_obj, dict):
                pass
    except Exception:
        pass

    # 出力ディレクトリ
    out_dir = Path((output_dir or spec.output_dir or "./manual_assets"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # 6) Manifest を保存
    manifest_path = out_dir / "manifest.json"
    try:
        manifest_obj = {
            "spec": {
                "video": spec.video,
                "output_dir": str(out_dir),
                "markdown_output": spec.markdown_output,
                "title": spec.title,
                "author": spec.author,
                "body_markdown": spec.body_markdown,
                "screenshots": [
                    {"time": s.time, "filename": s.filename, "caption": getattr(s, "caption", None)}
                    for s in (spec.screenshots or [])
                ],
            }
        }
        manifest_path.write_text(json.dumps(manifest_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        if ctx is not None:
            await ctx.error(f"manifest write error: {e}")

    # 7) Markdown 保存 + 画像抽出（既存関数で実行）
    if ctx is not None:
        await ctx.info("writing markdown and extracting screenshots...")
    handle_response_and_extract(resp_text, local_video)

    # 8) 結果整形
    markdown_path = str((out_dir / spec.markdown_output).resolve())
    image_paths: List[str] = [str((out_dir / s.filename).resolve()) for s in (spec.screenshots or [])]
    warnings: List[str] = []

    if downloaded_tmp and Path(downloaded_tmp).exists():
        try:
            os.remove(downloaded_tmp)
        except Exception:
            pass

    if ctx is not None:
        await ctx.info("build_manual_from_video: done")

    return {
        "conversational_summary": f"手順書を生成し、{len(image_paths)} 枚のスクリーンショットを抽出しました。",
        "spec": manifest_obj["spec"],
        "manifest_path": str(manifest_path.resolve()),
        "markdown_path": markdown_path,
        "image_paths": image_paths,
        "warnings": warnings,
    }


@mcp.tool
def health_check() -> str:
    return "ok"


def main() -> None:
    # STDIO（デフォルト）で起動
    mcp.run()


if __name__ == "__main__":
    main()


