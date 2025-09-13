from __future__ import annotations

from typing import Any, Dict, Optional, List
from pathlib import Path
from contextlib import contextmanager
import json
import os
import tempfile
import urllib.request

from fastmcp import FastMCP, Context


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


def register(mcp: FastMCP) -> None:
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

        # 遅延 import（名前衝突回避のため）
        import importlib
        main = importlib.import_module("main")

        # 2) Provider 設定の取得（必要なら一時的に LLM_PROVIDER を上書き）
        with _override_env("LLM_PROVIDER", (model_provider or os.environ.get("LLM_PROVIDER"))):
            cfg = main.get_provider_config()

        # 3) プロンプト生成
        prompt = main.build_prompt(local_video)

        # 4) LLM 呼び出し
        if cfg.provider == "gemini":
            if not cfg.api_key:
                raise RuntimeError("Gemini 用 API キーがありません")
            if ctx is not None:
                await ctx.info(f"calling Gemini model: {cfg.model_name}")
            client = main.create_gemini_client(cfg.api_key)
            resp_text = main.generate_response_text_gemini(client, local_video, prompt, cfg.model_name)
        else:
            if ctx is not None:
                await ctx.info(f"calling OpenAI-compatible model: {cfg.model_name}")
            client = main.create_openai_compatible_client(cfg.api_key or "", cfg.base_url)
            resp_text = main.generate_response_text_openai(client, prompt, cfg.model_name)

        if ctx is not None:
            await ctx.info("LLM response received. Parsing spec...")

        # 5) Spec 抽出・正規化
        spec_dict = main._extract_json_from_text(resp_text)
        if spec_dict is None:
            raise ValueError("モデル応答から有効なJSONを抽出できませんでした。")

        spec = main.Spec.from_dict(spec_dict)
        if not spec.video:
            spec.video = local_video

        # screenshot_policy（任意）を JSON 文字列で受け取り、必要であれば spec に反映
        try:
            if screenshot_policy_json:
                policy_obj = json.loads(screenshot_policy_json)
                if isinstance(policy_obj, dict):
                    # 現状は未使用。将来的に spec へ反映する際に利用
                    pass
        except Exception:
            # 解析失敗は無視（エラーではない）
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
        main.handle_response_and_extract(resp_text, local_video)

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


