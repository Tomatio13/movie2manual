from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import os
import shutil
import zipfile

from fastmcp import FastMCP, Context


def _zip_dir(src_dir: Path, out_zip: Path) -> str:
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for f in files:
                full = Path(root) / f
                arc = full.relative_to(src_dir)
                zf.write(full, arcname=str(arc))
    return str(out_zip.resolve())


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def export_manual_bundle(
        manifest_path: str,
        targets_csv: str = "",
        ctx: Context = None,
    ) -> Dict[str, Any]:
        if ctx is not None:
            await ctx.info("export_manual_bundle: start")

        p = Path(manifest_path)
        if not p.exists():
            raise FileNotFoundError(f"manifest not found: {manifest_path}")

        manifest = json.loads(p.read_text(encoding='utf-8'))
        spec = manifest.get("spec") or {}
        out_dir = Path(spec.get("output_dir") or p.parent)
        out_dir.mkdir(parents=True, exist_ok=True)

        # ZIP バンドル
        bundle_path = Path(str(p.with_suffix(".zip")))
        zipped = _zip_dir(out_dir, bundle_path)

        # 他ターゲットは将来実装（s3/gdrive/slack）
        delivered: List[str] = ["zip"]
        if targets_csv:
            # ユーザー入力はコンマ区切り文字列で受け取り、将来拡張に備える
            extras = [t.strip() for t in targets_csv.split(",") if t.strip()]
            delivered.extend(extras)

        if ctx is not None:
            await ctx.info("export_manual_bundle: done")
        return {
            "conversational_summary": "成果物を ZIP にバンドルしました。",
            "manifest_path": str(p.resolve()),
            "bundle_path": zipped,
            "delivered": delivered,
        }


