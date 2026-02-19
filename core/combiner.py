import os
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from combine.combine import combine_frames


class CombineTask(QObject):
    progress = Signal(int, int)
    finished = Signal(dict)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, timing_json: Path, modified_dir: Path, output_dir: Path, project_name: str) -> None:
        super().__init__()
        self.timing_json = Path(timing_json)
        self.modified_dir = Path(modified_dir)
        self.output_dir = Path(output_dir)
        self.project_name = project_name

    @Slot()
    def run(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_name = f"{self.project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_video = self.output_dir / output_name

            self.log.emit("开始合成视频任务...")
            start_time = time.time()
            result = combine_frames(
                json_path=str(self.timing_json),
                processed_folder=str(self.modified_dir),
                output_video=str(output_video),
                progress_callback=self._on_progress,
            )
            result["elapsed_seconds"] = time.time() - start_time
            if output_video.exists():
                result["output_size"] = os.path.getsize(output_video)
            else:
                result["output_size"] = 0
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.emit(int(current), int(total))
