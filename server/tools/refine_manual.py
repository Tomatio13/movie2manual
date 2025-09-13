from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path
import json
import importlib

from fastmcp import FastMCP, Context


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def refine_manual(manifest_path: str, edit_instructions: str, ctx: Context = None) -> Dict[str, Any]:
        if ctx is not None:
            await ctx.info("refine_manual: start")

        p = Path(manifest_path)
        if not p.exists():
            raise FileNotFoundError(f"manifest not found: {manifest_path}")

        manifest = json.loads(p.read_text(encoding="utf-8"))
        spec = manifest.get("spec") or {}

        # 1) LLM による編集（クライアント LLM を活用）
        updated_spec = spec
        changes: List[str] = []
        if ctx is not None:
            await ctx.info("refining spec via client LLM...")
            prompt = (
                "You will receive a manual spec JSON and edit instructions. "
                "Return a JSON with the same schema, applying the edits. "
                "Keep all unspecified fields unchanged. Ensure times are HH:MM:SS.mmm. "
                "Output only JSON.\n\n"
                f"Spec:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
                f"Instructions:\n{edit_instructions}\n"
            )
            try:
                completion = await ctx.sample(prompt)
                text = completion.text
                main = importlib.import_module("main")
                parsed = main._extract_json_from_text(text)
                if isinstance(parsed, dict):
                    updated_spec = parsed
                    changes.append("spec updated by LLM")
                else:
                    changes.append("LLM returned unparsable content; spec unchanged")
            except Exception as e:
                if ctx is not None:
                    await ctx.error(f"LLM refine failed: {e}")
                changes.append("LLM refine failed; spec unchanged")

        # 2) 保存（manifest と markdown）
        manifest["spec"] = updated_spec
        out_dir = Path(updated_spec.get("output_dir") or "./manual_assets")
        out_dir.mkdir(parents=True, exist_ok=True)

        md_name = updated_spec.get("markdown_output") or "manual.md"
        md_path = out_dir / md_name
        try:
            md_path.write_text(updated_spec.get("body_markdown") or "", encoding="utf-8")
        except Exception as e:
            if ctx is not None:
                await ctx.error(f"markdown write error: {e}")

        # 3) スクリーンショット再抽出（仕様が変わった場合を考慮して全再出力）
        try:
            import extract_screenshot as es
            shots = [es.ScreenshotSpec(**s) for s in (updated_spec.get("screenshots") or [])]
            if updated_spec.get("video"):
                if ctx is not None:
                    await ctx.info("re-extracting screenshots...")
                es.extract_screenshots(updated_spec["video"], str(out_dir), shots)
        except Exception as e:
            if ctx is not None:
                await ctx.error(f"screenshot extraction error: {e}")

        # 4) manifest 保存
        try:
            p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            if ctx is not None:
                await ctx.error(f"manifest write error: {e}")

        if ctx is not None:
            await ctx.info("refine_manual: done")

        image_paths: List[str] = [str((out_dir / s["filename"]).resolve()) for s in (updated_spec.get("screenshots") or [])]
        return {
            "conversational_summary": "手順書を更新しました。",
            "manifest_path": str(p.resolve()),
            "markdown_path": str(md_path.resolve()),
            "image_paths": image_paths,
            "spec": updated_spec,
            "changes": changes,
        }


