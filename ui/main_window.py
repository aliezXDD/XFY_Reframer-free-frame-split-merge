from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QThread, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core import CombineTask, ExtractTask, ProjectInfo, ProjectManager
from ui.combine_panel import CombinePanel
from ui.project_panel import ProjectPanel
from ui.split_panel import SplitPanel
from ui.styles import get_stylesheet


class ToastWidget(QFrame):
    def __init__(self, parent: QWidget, message: str, level: str = "info") -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setProperty("level", level)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        self.setMaximumWidth(420)


class WorkflowSteps(QWidget):
    steps = [
        "上传视频",
        "拆分关键帧",
        "外部修改图片",
        "上传修改图",
        "选择时间文件",
        "合成视频",
    ]
    def __init__(self) -> None:
        super().__init__()
        self._current_index = 0
        self._items: List[QFrame] = []
        self._labels: List[QLabel] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for idx, step in enumerate(self.steps):
            frame = QFrame()
            frame.setObjectName("stepItem")
            frame.setProperty("state", "todo")
            label = QLabel(f"{idx + 1}. {step}")
            sub_layout = QVBoxLayout(frame)
            sub_layout.setContentsMargins(12, 10, 12, 10)
            sub_layout.addWidget(label)
            layout.addWidget(frame, 1)
            self._items.append(frame)
            self._labels.append(label)

    def set_state(self, completed: List[bool], current_index: int) -> None:
        self._current_index = max(0, min(current_index, len(self.steps) - 1))
        for idx, frame in enumerate(self._items):
            if completed[idx]:
                state = "done"
                text = f"{idx + 1}. {self.steps[idx]}"
            elif idx == self._current_index:
                state = "current"
                text = f"{idx + 1}. {self.steps[idx]}"
            else:
                state = "todo"
                text = f"{idx + 1}. {self.steps[idx]}"

            frame.setProperty("state", state)
            self._labels[idx].setText(text)
            frame.style().unpolish(frame)
            frame.style().polish(frame)


class MainWindow(QMainWindow):
    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        super().__init__()
        self.workspace_root = Path(workspace_root or Path(__file__).resolve().parent.parent)
        self.project_manager = ProjectManager(self.workspace_root)
        self.current_project: Optional[ProjectInfo] = None
        self.latest_output_path: Optional[Path] = None
        self.current_timing_path: Optional[Path] = None

        self.extract_thread: Optional[QThread] = None
        self.extract_task: Optional[ExtractTask] = None
        self.combine_thread: Optional[QThread] = None
        self.combine_task: Optional[CombineTask] = None
        self._window_fade_anim: Optional[QPropertyAnimation] = None

        self.setWindowTitle("XFY Reframer")
        self.resize(1420, 900)
        self.setStyleSheet(get_stylesheet())
        self._build_ui()
        self.refresh_projects()
        self._update_step_indicator()

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(14)

        header = QFrame()
        header.setProperty("class", "panel")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        self.title_label = QLabel("XFY Reframer")
        self.title_label.setObjectName("titleLabel")
        self.current_project_label = QLabel("当前项目：未选择")
        self.current_project_label.setObjectName("subtitleLabel")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.current_project_label)
        root_layout.addWidget(header)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)
        self.project_panel = ProjectPanel()
        self.project_panel.project_selected.connect(self._on_project_selected)
        self.project_panel.project_delete_requested.connect(self._on_project_delete_requested)
        body_layout.addWidget(self.project_panel, 0)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        self.steps_widget = WorkflowSteps()
        content_layout.addWidget(self.steps_widget)

        self.tabs = QTabWidget()
        self.split_panel = SplitPanel()
        self.combine_panel = CombinePanel()
        self.tabs.addTab(self.split_panel, "拆帧")
        self.tabs.addTab(self.combine_panel, "合成")
        content_layout.addWidget(self.tabs, 1)
        body_layout.addWidget(content_widget, 1)
        root_layout.addLayout(body_layout, 1)

        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("就绪")
        self.log_label = QLabel("暂无日志。")
        status.addWidget(self.status_label, 1)
        status.addPermanentWidget(self.log_label, 1)

        self.split_panel.video_chosen.connect(self._on_video_chosen)
        self.split_panel.start_requested.connect(self._on_start_extract)
        self.split_panel.open_frames_requested.connect(self._open_frames_folder)
        self.combine_panel.images_selected.connect(self._on_images_selected)
        self.combine_panel.timing_changed.connect(self._on_timing_changed)
        self.combine_panel.combine_requested.connect(self._on_start_combine)
        self.combine_panel.open_output_requested.connect(self._open_output_folder)
        self.combine_panel.play_output_requested.connect(self._play_output_video)

    def refresh_projects(self) -> None:
        projects = self.project_manager.list_projects()
        self.project_panel.set_projects(projects)
        if self.current_project is not None:
            self.project_panel.set_current_project(self.current_project.root_dir)

    def _on_project_selected(self, project_path: str) -> None:
        project = self.project_manager.load_project(Path(project_path))
        self._set_current_project(project)
        self._show_toast(f"已切换项目：{project.name}", "info")

    def _on_project_delete_requested(self, project_path: str) -> None:
        target = Path(project_path)
        if not target.exists():
            self.refresh_projects()
            return

        reply = QMessageBox.question(
            self,
            "删除项目",
            f"确定删除项目“{target.name}”吗？\n该操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.project_manager.delete_project(target)
        except Exception as exc:
            self._show_toast(f"删除失败：{exc}", "error")
            return

        if self.current_project and self.current_project.root_dir.resolve() == target.resolve():
            self._clear_current_project()

        self.refresh_projects()
        self._set_status("项目已删除。")
        self._set_log(f"已删除项目：{target.name}")
        self._show_toast(f"已删除项目：{target.name}", "success")

    def _set_current_project(self, project: ProjectInfo) -> None:
        self.current_project = project
        self.current_project_label.setText(f"当前项目：{project.name}")
        self.combine_panel.set_current_dir(project.root_dir)
        if project.original_video and project.original_video.exists():
            self.split_panel.set_video(project.original_video)
        self._refresh_project_views()
        self.project_panel.set_current_project(project.root_dir)
        self._update_step_indicator()

    def _clear_current_project(self) -> None:
        self.current_project = None
        self.current_timing_path = None
        self.latest_output_path = None
        self.current_project_label.setText("当前项目：未选择")
        self.split_panel.clear_project_state()
        self.combine_panel.clear_project_state()
        self._update_step_indicator()

    def _refresh_project_views(self) -> None:
        if not self.current_project:
            return

        state = self.project_manager.get_project_state(self.current_project)
        modified_images = self.project_manager.list_images(self.current_project.modified_dir)
        frame_images = self.project_manager.list_images(self.current_project.frames_dir)
        self.combine_panel.set_modified_images(modified_images)
        self.split_panel.set_frame_previews(frame_images)

        timing_files = state["timing_files"]
        selected = self.current_timing_path if self.current_timing_path in timing_files else state["selected_timing"]
        self.current_timing_path = selected
        self.combine_panel.set_timing_files(timing_files, selected=selected)

        if selected:
            info = self.project_manager.read_timing_info(selected)
            self.combine_panel.set_timing_info(info)
        else:
            self.combine_panel.set_timing_info({})

        latest_output = state.get("latest_output")
        self.latest_output_path = latest_output if isinstance(latest_output, Path) else None
        if self.latest_output_path and self.latest_output_path.exists():
            self.combine_panel.open_output_btn.setEnabled(True)
            self.combine_panel.play_output_btn.setEnabled(True)
        else:
            self.combine_panel.open_output_btn.setEnabled(False)
            self.combine_panel.play_output_btn.setEnabled(False)
        self.split_panel.set_frames_dir(self.current_project.frames_dir)
        self._update_step_indicator()

    def _on_video_chosen(self, video_path: str) -> None:
        try:
            project = self.project_manager.create_project_from_video(video_path)
        except Exception as exc:
            self._show_toast(f"创建项目失败：{exc}", "error")
            return

        self._set_current_project(project)
        self.refresh_projects()
        self._show_toast("视频已导入并创建项目。", "success")
        self._set_status("已选择视频。")

    def _on_start_extract(self, threshold: int) -> None:
        if not self.current_project or not self.current_project.original_video:
            self._show_toast("请先上传视频。", "warning")
            return

        self.project_manager.clear_images(self.current_project.modified_dir)
        self.combine_panel.set_modified_images([])
        self.split_panel.reset_progress()
        self.split_panel.set_split_running(True)

        self.extract_thread = QThread(self)
        self.extract_task = ExtractTask(
            video_path=self.current_project.original_video,
            frames_dir=self.current_project.frames_dir,
            timestamps_dir=self.current_project.timestamps_dir,
            threshold=threshold,
        )
        self.extract_task.moveToThread(self.extract_thread)
        self.extract_thread.started.connect(self.extract_task.run)
        self.extract_task.progress.connect(self._on_extract_progress)
        self.extract_task.finished.connect(self._on_extract_finished)
        self.extract_task.failed.connect(self._on_extract_failed)
        self.extract_task.log.connect(self._set_log)
        self.extract_task.finished.connect(self.extract_thread.quit)
        self.extract_task.failed.connect(self.extract_thread.quit)
        self.extract_thread.finished.connect(self._cleanup_extract_thread)
        self.extract_thread.start()

        self._set_status("正在拆帧...")
        self._set_log("拆帧任务已开始。")

    def _cleanup_extract_thread(self) -> None:
        if self.extract_task:
            self.extract_task.deleteLater()
            self.extract_task = None
        if self.extract_thread:
            self.extract_thread.deleteLater()
            self.extract_thread = None

    def _on_extract_progress(self, current: int, total: int) -> None:
        self.split_panel.update_progress(current, total)
        self._set_status(f"正在拆帧... {current}/{total}")

    def _on_extract_finished(self, result: dict) -> None:
        self.split_panel.set_split_running(False)
        self.split_panel.show_result(result)
        self.current_timing_path = Path(result.get("timing_json", "")) if result.get("timing_json") else None
        self._refresh_project_views()
        self._set_status("拆帧完成。")
        self._set_log(f"已保存 {result.get('saved_frames', 0)} 张关键帧。")
        self._show_toast("拆帧完成。", "success")

    def _on_extract_failed(self, error_message: str) -> None:
        self.split_panel.set_split_running(False)
        self._set_status("拆帧失败。")
        self._set_log(error_message)
        self._show_toast(f"拆帧失败：{error_message}", "error")

    def _on_images_selected(self, paths: List[str]) -> None:
        if not self.current_project:
            self._show_toast("请先选择或创建项目。", "warning")
            return
        try:
            copied = self.project_manager.replace_modified_images(self.current_project, paths)
        except Exception as exc:
            self._show_toast(f"导入图片失败：{exc}", "error")
            return

        modified_images = self.project_manager.list_images(self.current_project.modified_dir)
        self.combine_panel.set_modified_images(modified_images)
        self._set_status(f"已导入 {copied} 张修改图。")
        self._set_log("修改图片已更新。")
        self._show_toast(f"已导入 {copied} 张图片。", "success")
        self._update_step_indicator()

    def _on_timing_changed(self, timing_path: str) -> None:
        self.current_timing_path = Path(timing_path) if timing_path else None
        if self.current_timing_path and self.current_timing_path.exists():
            info = self.project_manager.read_timing_info(self.current_timing_path)
            self.combine_panel.set_timing_info(info)
            self._set_log(f"已选择时间文件：{self.current_timing_path.name}")
        else:
            self.combine_panel.set_timing_info({})
        self._update_step_indicator()

    def _on_start_combine(self, timing_path: str) -> None:
        if not self.current_project:
            self._show_toast("请先选择项目。", "warning")
            return
        if not timing_path:
            self._show_toast("请选择时间文件。", "warning")
            return
        modified_images = self.project_manager.list_images(self.current_project.modified_dir)
        if not modified_images:
            self._show_toast("请先上传修改后的图片。", "warning")
            return

        timing = Path(timing_path)
        if not timing.exists():
            self._show_toast("时间文件不存在。", "error")
            return

        self.combine_panel.reset_progress()
        self.combine_panel.set_combine_running(True)
        self.combine_panel.open_output_btn.setEnabled(False)
        self.combine_panel.play_output_btn.setEnabled(False)

        self.combine_thread = QThread(self)
        self.combine_task = CombineTask(
            timing_json=timing,
            modified_dir=self.current_project.modified_dir,
            output_dir=self.current_project.output_dir,
            project_name=self.current_project.name,
        )
        self.combine_task.moveToThread(self.combine_thread)
        self.combine_thread.started.connect(self.combine_task.run)
        self.combine_task.progress.connect(self._on_combine_progress)
        self.combine_task.finished.connect(self._on_combine_finished)
        self.combine_task.failed.connect(self._on_combine_failed)
        self.combine_task.log.connect(self._set_log)
        self.combine_task.finished.connect(self.combine_thread.quit)
        self.combine_task.failed.connect(self.combine_thread.quit)
        self.combine_thread.finished.connect(self._cleanup_combine_thread)
        self.combine_thread.start()

        self._set_status("正在合成视频...")
        self._set_log("合成任务已开始。")

    def _cleanup_combine_thread(self) -> None:
        if self.combine_task:
            self.combine_task.deleteLater()
            self.combine_task = None
        if self.combine_thread:
            self.combine_thread.deleteLater()
            self.combine_thread = None

    def _on_combine_progress(self, current: int, total: int) -> None:
        self.combine_panel.update_progress(current, total)
        self._set_status(f"正在合成... {current}/{total}")

    def _on_combine_finished(self, result: dict) -> None:
        self.combine_panel.set_combine_running(False)
        self.combine_panel.show_result(result)
        output_video = result.get("output_video", "")
        self.latest_output_path = Path(output_video) if output_video else None
        self._set_status("合成完成。")
        self._set_log(f"输出视频已生成：{Path(output_video).name if output_video else '-'}")
        self._show_toast("合成完成。", "success")
        self._update_step_indicator()

    def _on_combine_failed(self, error_message: str) -> None:
        self.combine_panel.set_combine_running(False)
        self._set_status("合成失败。")
        self._set_log(error_message)
        self._show_toast(f"合成失败：{error_message}", "error")

    def _open_frames_folder(self) -> None:
        if self.current_project:
            self._open_path(self.current_project.frames_dir)

    def _open_output_folder(self) -> None:
        if self.current_project:
            self._open_path(self.current_project.output_dir)

    def _play_output_video(self) -> None:
        if self.latest_output_path and self.latest_output_path.exists():
            self._open_path(self.latest_output_path)

    def _open_path(self, path: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _set_log(self, message: str) -> None:
        self.log_label.setText(message)

    def _show_toast(self, message: str, level: str = "info") -> None:
        toast = ToastWidget(self, message, level=level)
        toast.adjustSize()
        margin = 16
        x = self.width() - toast.width() - margin
        y = margin + 28
        toast.move(max(x, margin), y)
        opacity = QGraphicsOpacityEffect(toast)
        opacity.setOpacity(0.0)
        toast.setGraphicsEffect(opacity)
        toast.show()
        toast.raise_()
        fade_in = QPropertyAnimation(opacity, b"opacity", toast)
        fade_in.setDuration(180)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()

        def _fade_out_toast() -> None:
            fade_out = QPropertyAnimation(opacity, b"opacity", toast)
            fade_out.setDuration(220)
            fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
            fade_out.setStartValue(opacity.opacity())
            fade_out.setEndValue(0.0)
            fade_out.finished.connect(toast.close)
            toast._fade_out_anim = fade_out
            fade_out.start()

        QTimer.singleShot(2600, _fade_out_toast)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if self._window_fade_anim is not None:
            return
        self.setWindowOpacity(0.0)
        self._window_fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._window_fade_anim.setDuration(240)
        self._window_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._window_fade_anim.setStartValue(0.0)
        self._window_fade_anim.setEndValue(1.0)
        self._window_fade_anim.start()

    def _update_step_indicator(self) -> None:
        state = [False] * 6
        current_step = 0

        if self.current_project:
            has_video = self.current_project.original_video is not None and self.current_project.original_video.exists()
            frame_count = len(self.project_manager.list_images(self.current_project.frames_dir))
            modified_count = len(self.project_manager.list_images(self.current_project.modified_dir))
            has_timing = self.current_timing_path is not None and self.current_timing_path.exists()
            has_output = self.latest_output_path is not None and self.latest_output_path.exists()

            state[0] = has_video
            state[1] = frame_count > 0
            state[3] = modified_count > 0
            state[2] = state[1] and state[3]
            state[4] = has_timing
            state[5] = has_output

            for idx, completed in enumerate(state):
                if not completed:
                    current_step = idx
                    break
            else:
                current_step = 5
        self.steps_widget.set_state(state, current_step)
