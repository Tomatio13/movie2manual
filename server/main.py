from __future__ import annotations

from fastmcp import FastMCP, Context

# ツール登録関数（絶対インポート）
from tools.build_manual import register as register_build_manual
from tools.refine_manual import register as register_refine_manual
from tools.export_bundle import register as register_export_bundle


# チュートリアル準拠の最小構成: グローバル mcp に直接ツールを登録
# 参考: https://github.com/jlowin/fastmcp/blob/main/docs/tutorials/create-mcp-server.mdx
mcp = FastMCP("movie2manual")

# ツール登録
register_build_manual(mcp)
register_refine_manual(mcp)
register_export_bundle(mcp)


@mcp.tool
def health_check() -> str:
    return "ok"


def main() -> None:
    # STDIO（デフォルト）で起動
    mcp.run()


if __name__ == "__main__":
    main()


