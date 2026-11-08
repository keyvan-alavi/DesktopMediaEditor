"""Background workers for video and image processing."""
from __future__ import annotations

import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image

from app.core.image_ops import apply_filter
from app.core.ffmpeg_utils import find_ffmpeg


class ProgressThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, task: str, *args):
        super().__init__()
        self.task = task
        self.args = args

    def run(self):
        try:
            if self.task == "trim":
                ok = self._trim(*self.args)
                self.finished_signal.emit(self.args[3] if ok else None)
            elif self.task == "mp3":
                ok = self._mp3(*self.args)
                self.finished_signal.emit(self.args[1] if ok else None)
            elif self.task == "filter":
                img, code = self.args
                result = apply_filter(img, code)
                self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(None)

    def _trim(self, input_path, start_secs, end_secs, output_path) -> bool:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            self.error_signal.emit("FFmpeg پیدا نشد.")
            return False
        try:
            duration = end_secs - start_secs
            cmd = [
                ffmpeg, "-i", input_path,
                "-ss", str(start_secs), "-t", str(duration),
                "-c:v", "copy", "-c:a", "copy", "-y", output_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.progress_signal.emit(100)
            return Path(output_path).exists()
        except Exception as e:
            self.error_signal.emit(str(e))
            return False

    def _mp3(self, input_path, output_path) -> bool:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            self.error_signal.emit("FFmpeg پیدا نشد.")
            return False
        try:
            cmd = [
                ffmpeg, "-i", input_path,
                "-vn", "-acodec", "libmp3lame", "-q:a", "2", "-y", output_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.progress_signal.emit(100)
            return True
        except Exception as e:
            self.error_signal.emit(str(e))
            return False
