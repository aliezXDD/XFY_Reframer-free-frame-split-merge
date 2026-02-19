def get_stylesheet() -> str:
    return """
QMainWindow {
    background: #1c1c1e;
    color: #f2f2f7;
}
QWidget {
    color: #f2f2f7;
    font-size: 13px;
    font-family: "SF Pro Text", "PingFang SC", "Segoe UI", "Microsoft YaHei UI", sans-serif;
    letter-spacing: 0.2px;
}
QLabel#titleLabel {
    font-size: 19px;
    font-weight: 600;
    color: #ffffff;
}
QLabel#subtitleLabel {
    font-size: 13px;
    color: #b3b3ba;
}
QLabel[role="label"] {
    font-size: 12px;
    color: #8f8f96;
}
QLabel[role="value"] {
    font-size: 13px;
    color: #f5f5f7;
}
QLabel[role="helper"] {
    font-size: 12px;
    color: #9c9ca3;
}
QLabel[role="metric"] {
    font-family: "SF Mono", "Cascadia Mono", "Consolas", monospace;
    color: #e7e7ec;
}
QFrame[class="panel"] {
    background: #252528;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
}
QFrame[class="subpanel"] {
    background: #2a2a2d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
}
QFrame[role="divider"] {
    background: rgba(255, 255, 255, 0.08);
    border: none;
}
QPushButton {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    background: #9b8cff;
    color: #ffffff;
    padding: 8px 12px;
    font-weight: 500;
}
QPushButton:hover {
    background: #a89bff;
}
QPushButton:pressed {
    background: #8d7df4;
}
QPushButton:disabled {
    background: #35353a;
    color: #777780;
    border-color: rgba(255, 255, 255, 0.04);
}
QPushButton[class="secondary"] {
    background: #343439;
    color: #f2f2f7;
}
QPushButton[class="secondary"]:hover {
    background: #3b3b41;
}
QPushButton[class="secondary"]:pressed {
    background: #2f2f34;
}
QPushButton[role="toggle"] {
    padding: 0px;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
}
QPushButton[state="loading"] {
    background: #6a628f;
}
QPushButton[state="done"] {
    background: #7d72b8;
}
QListWidget, QComboBox, QLineEdit, QSpinBox {
    background: #2f2f33;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 8px;
    color: #f2f2f7;
}
QListWidget::item {
    padding: 4px;
    border-radius: 8px;
}
QListWidget::item:hover {
    background: #3a3a40;
}
QListWidget::item:selected {
    background: #413d52;
}
QComboBox QAbstractItemView {
    background: #2f2f33;
    color: #f2f2f7;
    border: 1px solid rgba(255, 255, 255, 0.08);
    selection-background-color: #3a3a40;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #3f3f45;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #9b8cff;
    border-radius: 3px;
}
QSlider::add-page:horizontal {
    background: #3f3f45;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 7px;
    background: #b7adff;
}
QSlider::handle:horizontal:hover {
    background: #c3bbff;
}
QSlider::handle:horizontal:pressed {
    background: #9f94ea;
}
QTabWidget::pane {
    border: none;
}
QTabBar {
    margin-top: -20px;
}
QTabBar::tab {
    background: #2a2a2d;
    color: #9c9ca3;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px 14px;
    margin-right: 8px;
}
QTabBar::tab:selected {
    background: #333338;
    color: #f5f5f7;
}
QTabBar::tab:hover {
    background: #303035;
}
QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: #303035;
    border-radius: 10px;
    text-align: center;
    color: #d3d3d9;
}
QProgressBar::chunk {
    border-radius: 9px;
    background: #9b8cff;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #44444a;
    border-radius: 5px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QFrame#dropArea {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    background: #27272a;
}
QFrame#dropArea[dragActive="true"] {
    background: #322f3d;
}
QLabel#thumbPreview {
    background: #2a2a2d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    color: #7d7d84;
}
QFrame#stepItem {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    background: #2a2a2d;
}
QFrame#stepItem QLabel {
    color: #a5a5ac;
    font-size: 13px;
}
QFrame#stepItem[state="done"] {
    background: #313136;
}
QFrame#stepItem[state="done"] QLabel {
    color: #d3d3d8;
}
QFrame#stepItem[state="current"] {
    background: #342f42;
}
QFrame#stepItem[state="current"] QLabel {
    color: #f5f5f7;
}
QStatusBar {
    background: #1c1c1e;
    border: none;
}
QStatusBar QLabel {
    color: #a4a4ab;
}
QWidget#toast {
    background: #2f2f33;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 8px 12px;
}
QWidget#toast[level="success"],
QWidget#toast[level="warning"],
QWidget#toast[level="error"],
QWidget#toast[level="info"] {
    background: #2f2f33;
}
"""
