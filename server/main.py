from __future__ import annotations

import os
import sys

# スクリプト直実行でもパッケージインポートできるように PYTHONPATH を補正
if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastmcp import FastMCP, Context

# ツール登録関数（絶対インポート）
from server.tools.build_manual import register as register_build_manual
from server.tools.refine_manual import register as register_refine_manual
from server.tools.export_bundle import register as register_export_bundle


def create_server() -> FastMCP:
    mcp = FastMCP("movie2manual")

    # ツール登録（意図ベース、fastmcp デコレータ）
    register_build_manual(mcp)
    register_refine_manual(mcp)
    register_export_bundle(mcp)

    @mcp.tool
    def health_check() -> str:
        return "ok"

    return mcp


def main() -> None:
    # STDIO（デフォルト）で起動。n8n MCP Client から `python -m server.main` で接続
    mcp = create_server()
    mcp.run()  # transport="stdio" が既定

# fastmcp CLI から `python -m fastmcp server.main:mcp` で参照できるよう公開
mcp: FastMCP = create_server()


if __name__ == "__main__":
    main()


