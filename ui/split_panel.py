import os
from pathlib import Path
from typing import List, Optional

import cv2
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class VideoDropArea(QFrame):
    video_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropArea")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        self.label = QLabel("拖拽视频到这里，或点击上方按钮选择")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setMinimumHeight(88)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            if local_path:
                self.video_dropped.emit(local_path)


class SplitPanel(QWidget):
    video_chosen = Signal(str)
    start_requested = Signal(int)
    open_frames_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.video_path: Optional[Path] = None
        self.frames_dir: Optional[Path] = None
        self._progress_anim: Optional[QPropertyAnimation] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        root = QFrame()
        root.setObjectName("splitControl")
        root.setProperty("class", "panel")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.pick_video_btn = QPushButton("选择视频")
        self.pick_video_btn.clicked.connect(self._choose_video)
        self.start_btn = QPushButton("开始拆帧")
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.open_folder_btn = QPushButton("打开帧目录")
        self.open_folder_btn.setProperty("class", "secondary")
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(lambda: self.open_frames_requested.emit())
        actions.addWidget(self.pick_video_btn)
        actions.addWidget(self.start_btn)
        actions.addWidget(self.open_folder_btn)
        actions.addStretch(1)
        root_layout.addLayout(actions)

        self.drop_area = VideoDropArea()
        self.drop_area.video_dropped.connect(self.video_chosen.emit)
        root_layout.addWidget(self.drop_area)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        self.thumbnail_label = QLabel("暂无预览")
        self.thumbnail_label.setObjectName("thumbPreview")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(360, 202)

        info_card = QFrame()
        info_card.setProperty("class", "subpanel")
        info_layout = QFormLayout(info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setHorizontalSpacing(14)
        info_layout.setVerticalSpacing(8)

        self.file_name_label = QLabel("-")
        self.file_size_label = QLabel("-")
        self.resolution_label = QLabel("-")
        self.duration_label = QLabel("-")
        self.fps_label = QLabel("-")
        self.file_size_label.setProperty("role", "metric")
        self.resolution_label.setProperty("role", "metric")
        self.duration_label.setProperty("role", "metric")
        self.fps_label.setProperty("role", "metric")

        info_layout.addRow("文件名", self.file_name_label)
        info_layout.addRow("分辨率", self.resolution_label)
        info_layout.addRow("时长", self.duration_label)
        info_layout.addRow("帧率", self.fps_label)
        info_layout.addRow("文件大小", self.file_size_label)
        info_row.addWidget(self.thumbnail_label, 0)
        info_row.addWidget(info_card, 1)
        root_layout.addLayout(info_row)

        sensitivity = QFrame()
        sensitivity.setProperty("class", "subpanel")
        sensitivity_layout = QVBoxLayout(sensitivity)
        sensitivity_layout.setContentsMargins(12, 12, 12, 12)
        sensitivity_layout.setSpacing(8)
        sensitivity_layout.addWidget(QLabel("灵敏度（阈值越低，拆帧越多）"))
        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(1, 500)
        self.threshold_slider.setValue(100)
        self.threshold_slider.valueChanged.connect(self._sync_slider_to_spin)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(10_000, 5_000_000)
        self.threshold_spin.setSingleStep(10_000)
        self.threshold_spin.setValue(1_000_000)
        self.threshold_spin.setProperty("role", "metric")
        self.threshold_spin.valueChanged.connect(self._sync_spin_to_slider)
        slider_row.addWidget(self.threshold_slider, 1)
        slider_row.addWidget(self.threshold_spin)
        sensitivity_layout.addLayout(slider_row)
        root_layout.addWidget(sensitivity)

        progress = QFrame()
        progress.setProperty("class", "subpanel")
        progress_layout = QVBoxLayout(progress)
        progress_layout.setContentsMargins(12, 12, 12, 12)
        progress_layout.setSpacing(8)
        bar_row = QHBoxLayout()
        bar_row.setSpacing(10)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setProperty("role", "metric")
        bar_row.addWidget(self.progress_bar, 1)
        bar_row.addWidget(self.progress_percent_label)
        self.progress_details = QLabel("已处理：0 / 0 帧")
        self.progress_details.setProperty("role", "metric")
        self.frames_count_label = QLabel("关键帧：0 张")
        self.frames_count_label.setProperty("role", "metric")
        self.result_label = QLabel("状态：等待开始拆帧。")
        self.result_label.setWordWrap(True)
        self.result_label.setProperty("role", "helper")
        progress_layout.addLayout(bar_row)
        progress_layout.addWidget(self.progress_details)
        progress_layout.addWidget(self.frames_count_label)
        progress_layout.addWidget(self.result_label)
        root_layout.addWidget(progress)

        layout.addWidget(root)

    def _choose_video(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv)",
        )
        if file_path:
            self.video_chosen.emit(file_path)

    def _on_start_clicked(self) -> None:
        self.start_requested.emit(self.threshold_spin.value())

    def _sync_slider_to_spin(self, value: int) -> None:
        mapped = max(10_000, value * 10_000)
        if self.threshold_spin.value() != mapped:
            self.threshold_spin.blockSignals(True)
            self.threshold_spin.setValue(mapped)
            self.threshold_spin.blockSignals(False)

    def _sync_spin_to_slider(self, value: int) -> None:
        mapped = max(1, min(500, int(value / 10_000)))
        if self.threshold_slider.value() != mapped:
            self.threshold_slider.blockSignals(True)
            self.threshold_slider.setValue(mapped)
            self.threshold_slider.blockSignals(False)

    def set_video(self, video_path: Path) -> None:
        self.video_path = Path(video_path)
        self.file_name_label.setText(self.video_path.name)
        self.file_size_label.setText(self._format_size(self.video_path.stat().st_size))

        capture = cv2.VideoCapture(str(self.video_path))
        if not capture.isOpened():
            self.duration_label.setText("无法读取")
            self.resolution_label.setText("无法读取")
            self.fps_label.setText("无法读取")
            return

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 24.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = frame_count / fps if fps else 0.0

        self.duration_label.setText(f"{duration:.2f} 秒")
        self.fps_label.setText(f"{fps:.2f} fps")
        self.resolution_label.setText(f"{width} × {height}")

        ret, frame = capture.read()
        capture.release()
        if ret and frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image).scaled(
                self.thumbnail_label.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setPixmap(QPixmap())
            self.thumbnail_label.setText("暂无预览")

    def set_frames_dir(self, frames_dir: Path) -> None:
        self.frames_dir = Path(frames_dir)
        self.open_folder_btn.setEnabled(True)

    def set_split_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.pick_video_btn.setEnabled(not running)
        self.start_btn.setText("拆帧中..." if running else "开始拆帧")
        self.start_btn.setProperty("state", "loading" if running else "")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def update_progress(self, current: int, total: int) -> None:
        percent = int((current / total) * 100) if total else 0
        self._animate_progress(percent)
        self.progress_percent_label.setText(f"{percent}%")
        self.progress_details.setText(f"已处理：{current} / {total} 帧")

    def show_result(self, result: dict) -> None:
        self.start_btn.setText("✓ 拆帧完成")
        self.start_btn.setProperty("state", "done")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.result_label.setText(
            "状态：已完成。"
            f"关键帧 {result.get('saved_frames', 0)} 张，耗时 {result.get('elapsed_seconds', 0.0):.2f} 秒，"
            f"时间文件 {os.path.basename(result.get('timing_json', ''))}"
        )

    def reset_progress(self) -> None:
        if self._progress_anim:
            self._progress_anim.stop()
            self._progress_anim = None
        self.start_btn.setText("开始拆帧")
        self.start_btn.setProperty("state", "")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")
        self.progress_details.setText("已处理：0 / 0 帧")
        self.result_label.setText("状态：等待开始拆帧。")

    def set_frame_previews(self, image_paths: List[Path]) -> None:
        self.frames_count_label.setText(f"关键帧：{len(image_paths)} 张")

    def clear_project_state(self) -> None:
        self.video_path = None
        self.frames_dir = None
        self.open_folder_btn.setEnabled(False)
        self.file_name_label.setText("-")
        self.file_size_label.setText("-")
        self.resolution_label.setText("-")
        self.duration_label.setText("-")
        self.fps_label.setText("-")
        self.thumbnail_label.setPixmap(QPixmap())
        self.thumbnail_label.setText("暂无预览")
        self.set_frame_previews([])
        self.reset_progress()

    def _animate_progress(self, target_value: int) -> None:
        start_value = self.progress_bar.value()
        if start_value == target_value:
            return
        if self._progress_anim:
            self._progress_anim.stop()
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value", self)
        self._progress_anim.setDuration(180)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._progress_anim.setStartValue(start_value)
        self._progress_anim.setEndValue(target_value)
        self._progress_anim.start()

    def _format_size(self, num_bytes: int) -> str:
        size = float(num_bytes)
        units = ["B", "KB", "MB", "GB"]
        for unit in units:
            if size < 1024.0 or unit == units[-1]:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{num_bytes} B"
