from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication
    from .ui import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("PaperSort Desktop")
    app.setOrganizationName("MeowBuild Lab")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
