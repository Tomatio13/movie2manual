#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静止画抽出スクリプト

機能概要:
- 指定された動画とスクリーンショット仕様に基づき、ffmpegで静止画を抽出

前提:
- ffmpeg がインストールされていること

使い方:
  python extract_screenshot.py --spec prompt.json

prompt.json の例:
{
  "video": "./input.mp4",
  "output_dir": "./manual_assets",
  "screenshots": [
    {"time": "00:00:03.500", "filename": "step1.png", "caption": "アプリ起動"},
    {"time": 10.0, "filename": "menu.png", "caption": "メニューから設定を開く"}
  ]
}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def run(cmd: List[str], cwd: Optional[Union[str, Path]] = None) -> int:
    print("$", " ".join(shlex.quote(c) for c in cmd))
    try:
        completed = subprocess.run(cmd, cwd=cwd, check=False)
        return completed.returncode
    except FileNotFoundError:
        return 127


def ensure_dir(p: Union[str, Path]) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)


def format_timecode(value: Union[str, float, int]) -> str:
    """value が秒(float/int)または "HH:MM:SS.mmm" で与えられても ffmpeg 互換文字列へ整形。"""
    if isinstance(value, (float, int)):
        total_ms = int(round(float(value) * 1000))
        ms = total_ms % 1000
        total_s = total_ms // 1000
        s = total_s % 60
        total_m = total_s // 60
        m = total_m % 60
        h = total_m // 60
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    if isinstance(value, str):
        return value
    raise ValueError("Unsupported time format")


@dataclass
class ScreenshotSpec:
    time: Union[str, float, int]
    filename: str
    caption: Optional[str] = None


def extract_screenshots(video: str, output_dir: str, screenshots: List[ScreenshotSpec]) -> List[Path]:
    if which("ffmpeg") is None:
        raise RuntimeError("ffmpeg が見つかりません。インストールしてください。")

    ensure_dir(output_dir)
    out_paths: List[Path] = []
    for i, s in enumerate(screenshots or []):
        t = format_timecode(s.time)
        out_path = Path(output_dir) / s.filename
        # 高速かつ近似シーク: -ss を -i より前に置く
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", t, "-i", video,
            "-frames:v", "1", "-q:v", "2",
            str(out_path),
        ]
        code = run(cmd)
        if code != 0:
            raise RuntimeError(f"ffmpeg 抽出に失敗しました: time={t}, filename={out_path}")
        out_paths.append(out_path)
    return out_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="動画から静止画抽出")
    parser.add_argument("--spec", required=True, help="JSONのパス")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"spec ファイルが見つかりません: {spec_path}", file=sys.stderr)
        return 2

    try:
        spec_dict = json.loads(spec_path.read_text(encoding="utf-8"), strict=False)
    except json.JSONDecodeError as e:
        print(f"JSON の読み込みに失敗しました: {e}", file=sys.stderr)
        return 2

    # 必須キーの検証
    if "video" not in spec_dict:
        print("spec に 'video' がありません", file=sys.stderr)
        return 2
    video = spec_dict["video"]
    output_dir = spec_dict.get("output_dir", "./manual_assets")
    try:
        shots = [ScreenshotSpec(**s) for s in spec_dict.get("screenshots", [])]
    except Exception as e:
        print(f"screenshots の構文が不正です: {e}", file=sys.stderr)
        return 2

    if not Path(video).exists():
        print(f"動画ファイルが見つかりません: {video}", file=sys.stderr)
        return 2

    try:
        images = extract_screenshots(video, output_dir, shots)
    except Exception as e:
        print(f"静止画抽出でエラー: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
