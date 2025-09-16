import io
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import streamlit as st

from extract_screenshot import extract_screenshots
from main import (
    Spec,
    _extract_json_from_text,
    build_prompt,
    create_gemini_client,
    create_openai_compatible_client,
    generate_response_text_gemini,
    generate_response_text_openai,
    get_provider_config,
)
from pdf_export import convert_markdown_to_pdf


def _sanitize_dir_name(raw: Optional[str]) -> Path:
    candidate = Path(raw or "manual_assets")
    if candidate.is_absolute():
        candidate = Path(candidate.name)
    safe_parts = [part for part in candidate.parts if part not in ("..", ".", "")]
    return Path(*safe_parts) if safe_parts else Path("manual_assets")


def _sanitize_filename(raw: Optional[str], default: str) -> str:
    name = Path(raw or default).name
    return name or default


def _run_generation(video_path: Path, work_dir: Path, export_pdf: bool) -> dict:
    cfg = get_provider_config()
    prompt = build_prompt(str(video_path))
    if cfg.provider == "gemini":
        if not cfg.api_key:
            raise RuntimeError("Gemini 用 API キーが設定されていません")
        client = create_gemini_client(cfg.api_key)
        response_text = generate_response_text_gemini(client, str(video_path), prompt, cfg.model_name)
    else:
        client = create_openai_compatible_client(cfg.api_key or "", cfg.base_url)
        response_text = generate_response_text_openai(client, prompt, cfg.model_name)

    spec_dict = _extract_json_from_text(response_text)
    if spec_dict is None:
        raise ValueError("LLM の応答からマニュアル仕様(JSON)を抽出できませんでした。")

    spec = Spec.from_dict(spec_dict)
    spec.video = str(video_path)

    rel_dir = _sanitize_dir_name(spec.output_dir)
    output_dir = work_dir / rel_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_name = _sanitize_filename(spec.markdown_output, "manual.md")
    markdown_path = output_dir / markdown_name
    markdown_path.write_text(spec.body_markdown or "", encoding="utf-8")

    spec.output_dir = str(output_dir)
    spec.markdown_output = markdown_name

    screenshots = extract_screenshots(spec.video, str(output_dir), spec.screenshots or [])

    pdf_path = None
    if export_pdf:
        pdf_path = markdown_path.with_suffix(".pdf")
        convert_markdown_to_pdf(str(markdown_path), str(pdf_path))
        spec_dict["pdf_output"] = str(pdf_path)

    return {
        "spec": spec,
        "output_dir": output_dir,
        "markdown_path": markdown_path,
        "pdf_path": pdf_path,
        "response_text": response_text,
        "screenshots": screenshots,
    }


def _make_zip_buffer(root: Path) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(root)))
    buffer.seek(0)
    return buffer


def main() -> None:
    st.set_page_config(page_title="movie2manual", page_icon="🎬", layout="centered")
    st.title("movie2manual console")
    st.markdown("動画をアップロードして下さい。 LLM ベースのマニュアルを生成します。")
    
    uploaded = st.file_uploader("動画ファイルを選択", type=["mp4"])
    export_pdf = st.checkbox("PDF も生成する", value=False)

    if st.button("マニュアルを生成", type="primary"):
        if not uploaded:
            st.warning("先に動画ファイルをアップロードしてください。")
            return

        with st.spinner("マニュアルを生成しています…"):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                video_path = tmpdir_path / uploaded.name
                video_path.write_bytes(uploaded.getvalue())

                try:
                    result = _run_generation(video_path, tmpdir_path, export_pdf)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"生成に失敗しました: {exc}")
                    return

                output_dir = result["output_dir"]
                markdown_path = result["markdown_path"]
                pdf_path = result["pdf_path"]
                spec = result["spec"]

                st.success("マニュアル生成が完了しました。")
                st.write("### 生成サマリ")
                st.write(f"- タイトル: {spec.title}")
                if spec.author:
                    st.write(f"- 作者: {spec.author}")
                st.write(f"- Markdown: `{markdown_path.name}`")
                st.write(f"- スクリーンショット枚数: {len(result['screenshots'])}")
                if pdf_path:
                    st.write(f"- PDF: `{pdf_path.name}`")

                with st.expander("生成された JSON 応答"):
                    st.code(json.dumps(result["spec"].__dict__, default=str, ensure_ascii=False, indent=2), language="json")

                zip_buffer = _make_zip_buffer(output_dir)
                st.download_button(
                    label="生成結果をZIPでダウンロード",
                    data=zip_buffer,
                    file_name=f"{output_dir.name}.zip",
                    mime="application/zip",
                )

                if pdf_path and pdf_path.exists():
                    with pdf_path.open("rb") as f:
                        st.download_button(
                            label="PDFをダウンロード",
                            data=f.read(),
                            file_name=pdf_path.name,
                            mime="application/pdf",
                        )


if __name__ == "__main__":
    main()
