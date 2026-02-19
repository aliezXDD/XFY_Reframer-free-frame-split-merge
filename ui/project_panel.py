from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.project_manager import ProjectInfo


class ProjectPanel(QWidget):
    project_selected = Signal(str)
    project_delete_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._collapsed = False
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        container = QFrame()
        container.setObjectName("projectPanel")
        container.setProperty("class", "panel")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(14, 14, 14, 14)
        container_layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        self.title_label = QLabel("项目历史")
        self.toggle_btn = QPushButton("<")
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setProperty("class", "secondary")
        self.toggle_btn.setProperty("role", "toggle")
        self.toggle_btn.clicked.connect(self.toggle_collapsed)
        top_row.addWidget(self.title_label)
        top_row.addStretch(1)
        top_row.addWidget(self.toggle_btn)

        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self._emit_project_selected)
        self.project_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self._show_context_menu)

        container_layout.addLayout(top_row)
        container_layout.addWidget(self.project_list)
        root_layout.addWidget(container)
        self.setMinimumWidth(260)

    def set_projects(self, projects: List[ProjectInfo]) -> None:
        self.project_list.clear()
        for project in projects:
            item = QListWidgetItem(f"{project.display_name}\n{project.created_at}")
            item.setData(Qt.ItemDataRole.UserRole, str(project.root_dir))
            self.project_list.addItem(item)

    def set_current_project(self, project_path: Path) -> None:
        target = str(project_path)
        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == target:
                self.project_list.setCurrentRow(index)
                break

    def toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        self.project_list.setVisible(not self._collapsed)
        self.title_label.setVisible(not self._collapsed)
        self.setFixedWidth(56 if self._collapsed else 260)
        self.toggle_btn.setText(">" if self._collapsed else "<")

    def _emit_project_selected(self, item: QListWidgetItem) -> None:
        project_path = item.data(Qt.ItemDataRole.UserRole)
        if project_path:
            self.project_selected.emit(project_path)

    def _show_context_menu(self, pos) -> None:  # type: ignore[override]
        item = self.project_list.itemAt(pos)
        if item is None:
            return
        self.project_list.setCurrentItem(item)
        project_path = item.data(Qt.ItemDataRole.UserRole)
        if not project_path:
            return

        menu = QMenu(self)
        delete_action = menu.addAction("删除项目")
        selected = menu.exec(self.project_list.viewport().mapToGlobal(pos))
        if selected == delete_action:
            self.project_delete_requested.emit(str(project_path))
