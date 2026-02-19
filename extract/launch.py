import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def main() -> int:
    if getattr(sys, "frozen", False):
        workspace_root = Path(sys.executable).resolve().parent
        project_root = Path(getattr(sys, "_MEIPASS", workspace_root))
    else:
        project_root = Path(__file__).resolve().parent.parent
        workspace_root = project_root
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("XFY Reframer")
    app.setApplicationDisplayName("XFY Reframer")
    window = MainWindow(workspace_root=workspace_root)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
