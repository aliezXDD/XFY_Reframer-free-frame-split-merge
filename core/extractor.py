import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from extract.extract import extract_keyframes


class ExtractTask(QObject):
    progress = Signal(int, int)
    finished = Signal(dict)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, video_path: Path, frames_dir: Path, timestamps_dir: Path, threshold: int) -> None:
        super().__init__()
        self.video_path = Path(video_path)
        self.frames_dir = Path(frames_dir)
        self.timestamps_dir = Path(timestamps_dir)
        self.threshold = int(threshold)

    @Slot()
    def run(self) -> None:
        try:
            self.frames_dir.mkdir(parents=True, exist_ok=True)
            self.timestamps_dir.mkdir(parents=True, exist_ok=True)
            self._clear_existing_frames()

            timing_name = f"{self.video_path.stem}.json"
            timing_path = self.timestamps_dir / timing_name

            self.log.emit("开始拆帧任务...")
            start_time = time.time()
            result = extract_keyframes(
                video_path=str(self.video_path),
                output_folder=str(self.frames_dir),
                timing_json_path=str(timing_path),
                threshold=self.threshold,
                progress_callback=self._on_progress,
            )
            result["timing_json"] = str(timing_path)
            result["elapsed_seconds"] = time.time() - start_time
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.emit(int(current), int(total))

    def _clear_existing_frames(self) -> None:
        for path in self.frames_dir.iterdir():
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                path.unlink()
