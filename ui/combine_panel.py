import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class ImageDropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropArea")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        self.label = QLabel("拖拽图片或文件夹到这里，或点击上方按钮选择")
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
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
        if paths:
            self.files_dropped.emit(paths)


class CombinePanel(QWidget):
    images_selected = Signal(list)
    timing_changed = Signal(str)
    combine_requested = Signal(str)
    open_output_requested = Signal()
    play_output_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.current_dir = ""
        self._progress_anim: Optional[QPropertyAnimation] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        root = QFrame()
        root.setProperty("class", "panel")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.pick_images_btn = QPushButton("选择图片")
        self.pick_images_btn.clicked.connect(self._choose_images)
        self.pick_folder_btn = QPushButton("选择文件夹")
        self.pick_folder_btn.setProperty("class", "secondary")
        self.pick_folder_btn.clicked.connect(self._choose_folder)
        self.start_btn = QPushButton("开始合成")
        self.start_btn.clicked.connect(self._request_combine)
        actions.addWidget(self.pick_images_btn)
        actions.addWidget(self.pick_folder_btn)
        actions.addWidget(self.start_btn)
        actions.addStretch(1)
        root_layout.addLayout(actions)

        self.drop_area = ImageDropArea()
        self.drop_area.files_dropped.connect(self.images_selected.emit)
        root_layout.addWidget(self.drop_area)

        preview = QFrame()
        preview.setProperty("class", "subpanel")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(8)
        self.modified_count_label = QLabel("已上传：0 张")
        self.modified_count_label.setProperty("role", "metric")
        self.preview_list = QListWidget()
        self.preview_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.preview_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.preview_list.setMovement(QListWidget.Movement.Static)
        self.preview_list.setIconSize(QPixmap(96, 96).size())
        self.preview_list.setSpacing(8)
        self.preview_list.setMinimumHeight(170)
        preview_layout.addWidget(self.modified_count_label)
        preview_layout.addWidget(self.preview_list)
        root_layout.addWidget(preview)

        timing = QFrame()
        timing.setProperty("class", "subpanel")
        timing_layout = QHBoxLayout(timing)
        timing_layout.setContentsMargins(12, 12, 12, 12)
        timing_layout.setSpacing(8)
        timing_layout.addWidget(QLabel("时间文件"))
        self.timing_combo = QComboBox()
        self.timing_combo.currentIndexChanged.connect(self._emit_timing_changed)
        self.browse_timing_btn = QPushButton("浏览")
        self.browse_timing_btn.setProperty("class", "secondary")
        self.browse_timing_btn.clicked.connect(self._browse_timing)
        timing_layout.addWidget(self.timing_combo, 1)
        timing_layout.addWidget(self.browse_timing_btn)
        root_layout.addWidget(timing)

        self.timing_info_label = QLabel("未选择时间文件。")
        self.timing_info_label.setProperty("role", "helper")
        root_layout.addWidget(self.timing_info_label)

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
        self.progress_details = QLabel("已处理：0 / 0 场景")
        self.progress_details.setProperty("role", "metric")
        self.result_label = QLabel("状态：等待开始合成。")
        self.result_label.setProperty("role", "helper")
        self.result_label.setWordWrap(True)
        action_bottom_row = QHBoxLayout()
        action_bottom_row.setSpacing(8)
        self.open_output_btn = QPushButton("打开输出目录")
        self.open_output_btn.setProperty("class", "secondary")
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(lambda: self.open_output_requested.emit())
        self.play_output_btn = QPushButton("播放视频")
        self.play_output_btn.setEnabled(False)
        self.play_output_btn.clicked.connect(lambda: self.play_output_requested.emit())
        action_bottom_row.addWidget(self.open_output_btn)
        action_bottom_row.addWidget(self.play_output_btn)
        action_bottom_row.addStretch(1)
        progress_layout.addLayout(bar_row)
        progress_layout.addWidget(self.progress_details)
        progress_layout.addWidget(self.result_label)
        progress_layout.addLayout(action_bottom_row)
        root_layout.addWidget(progress)

        layout.addWidget(root)

    def set_current_dir(self, directory: Optional[Path]) -> None:
        self.current_dir = str(directory) if directory else ""

    def set_modified_images(self, image_paths: List[Path]) -> None:
        self.preview_list.clear()
        self.modified_count_label.setText(f"已上传：{len(image_paths)} 张")
        for image_path in image_paths[:220]:
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                continue
            icon = QIcon(
                pixmap.scaled(
                    96,
                    96,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.preview_list.addItem(QListWidgetItem(icon, image_path.name))

    def set_timing_files(self, timing_paths: List[Path], selected: Optional[Path] = None) -> None:
        self.timing_combo.blockSignals(True)
        self.timing_combo.clear()
        selected_index = 0
        for idx, path in enumerate(timing_paths):
            self.timing_combo.addItem(path.name, str(path))
            if selected and str(path) == str(selected):
                selected_index = idx
        self.timing_combo.setCurrentIndex(selected_index if timing_paths else -1)
        self.timing_combo.blockSignals(False)
        if timing_paths:
            self._emit_timing_changed()
        else:
            self.timing_info_label.setText("未选择时间文件。")

    def set_timing_info(self, info: dict) -> None:
        if not info:
            self.timing_info_label.setText("未选择时间文件。")
            return
        self.timing_info_label.setText(
            f"FPS：{info.get('fps', 0):.2f}  场景数：{info.get('scene_count', 0)}  总帧数：{info.get('duration_frames', 0)}"
        )

    def selected_timing_path(self) -> str:
        return str(self.timing_combo.currentData() or "")

    def set_combine_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.pick_images_btn.setEnabled(not running)
        self.pick_folder_btn.setEnabled(not running)
        self.browse_timing_btn.setEnabled(not running)
        self.start_btn.setText("合成中..." if running else "开始合成")
        self.start_btn.setProperty("state", "loading" if running else "")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def update_progress(self, current: int, total: int) -> None:
        percent = int((current / total) * 100) if total else 0
        self._animate_progress(percent)
        self.progress_percent_label.setText(f"{percent}%")
        self.progress_details.setText(f"已处理：{current} / {total} 场景")

    def show_result(self, result: dict) -> None:
        output_path = str(result.get("output_video", ""))
        size_text = self._format_size(int(result.get("output_size", 0)))
        self.start_btn.setText("✓ 合成完成")
        self.start_btn.setProperty("state", "done")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.result_label.setText(
            f"状态：已完成。输出 {os.path.basename(output_path)}，大小 {size_text}，耗时 {result.get('elapsed_seconds', 0.0):.2f} 秒"
        )
        self.open_output_btn.setEnabled(True)
        self.play_output_btn.setEnabled(True)

    def reset_progress(self) -> None:
        if self._progress_anim:
            self._progress_anim.stop()
            self._progress_anim = None
        self.start_btn.setText("开始合成")
        self.start_btn.setProperty("state", "")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")
        self.progress_details.setText("已处理：0 / 0 场景")
        self.result_label.setText("状态：等待开始合成。")

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

    def _choose_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择修改后的图片",
            self.current_dir,
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if files:
            self.images_selected.emit(files)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹", self.current_dir)
        if folder:
            self.images_selected.emit([folder])

    def _browse_timing(self) -> None:
        timing_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择时间文件",
            self.current_dir,
            "JSON 文件 (*.json)",
        )
        if timing_path:
            self.timing_combo.addItem(Path(timing_path).name, timing_path)
            self.timing_combo.setCurrentIndex(self.timing_combo.count() - 1)
            self._emit_timing_changed()

    def _emit_timing_changed(self) -> None:
        self.timing_changed.emit(self.selected_timing_path())

    def _request_combine(self) -> None:
        self.combine_requested.emit(self.selected_timing_path())

    def clear_project_state(self) -> None:
        self.current_dir = ""
        self.set_modified_images([])
        self.set_timing_files([])
        self.set_timing_info({})
        self.open_output_btn.setEnabled(False)
        self.play_output_btn.setEnabled(False)
        self.reset_progress()

    def _format_size(self, num_bytes: int) -> str:
        size = float(num_bytes)
        units = ["B", "KB", "MB", "GB"]
        for unit in units:
            if size < 1024.0 or unit == units[-1]:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{num_bytes} B"
