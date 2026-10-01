from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication
    from .ui import MainWindow

    smoke_test = "--smoke-test" in sys.argv
    app = QApplication(sys.argv)
    app.setApplicationName("PaperSort Desktop")
    app.setOrganizationName("MeowBuild Lab")

    if smoke_test:
        from PySide6.QtCore import QSettings
        QSettings("MeowBuild Lab", "PaperSort Desktop").setValue("first_run_shown", True)

    window = MainWindow()
    window.show()
    if smoke_test:
        app.processEvents()
        window.close()
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
