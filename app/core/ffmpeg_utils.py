"""Locate ffmpeg / ffprobe binaries."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # app/core/ -> project root
    return Path(__file__).resolve().parent.parent.parent


def find_ffmpeg() -> str | None:
    base = _base_dir()
    for p in (
        base / "ffmpeg" / "ffmpeg.exe",
        base / "ffmpeg" / "ffmpeg",
        base / "ffmpeg.exe",
        base / "ffmpeg",
    ):
        if p.exists():
            return str(p)
    return shutil.which("ffmpeg")


def find_ffprobe() -> str | None:
    base = _base_dir()
    for p in (
        base / "ffmpeg" / "ffprobe.exe",
        base / "ffmpeg" / "ffprobe",
        base / "ffprobe.exe",
        base / "ffprobe",
    ):
        if p.exists():
            return str(p)
    return shutil.which("ffprobe")


def setup_moviepy_env() -> tuple[str | None, str | None]:
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    if ffmpeg:
        os.environ["FFMPEG_BINARY"] = ffmpeg
    if ffprobe:
        os.environ["FFPROBE_BINARY"] = ffprobe
    return ffmpeg, ffprobe
