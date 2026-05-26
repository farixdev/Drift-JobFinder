import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import groq_key_status, load_env

load_env()

from PyQt5.QtWidgets import QApplication, QMessageBox

from ui.app import DriftApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("drift.jobs")
    app.setOrganizationName("drift.jobs")

    ok, message = groq_key_status()
    if not ok:
        QMessageBox.warning(None, "Groq API key required", message)

    window = DriftApp()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
