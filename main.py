import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from ui.loading_screen import LoadingScreen
from ui.terms_dialog import TermsDialog
from ui.main_window import MainWindow
from core.paths import app_data_dir, app_icon_path  # noqa: F401  (app_data_dir ensures data dir exists on import)

_TERMS_ACCEPTED_FLAG = "_terms_accepted"


def _terms_flag_path():
    import os
    from core.paths import app_data_dir
    return os.path.join(app_data_dir(), ".terms_accepted")


def _terms_already_accepted() -> bool:
    import os
    return os.path.exists(_terms_flag_path())


def _mark_terms_accepted():
    with open(_terms_flag_path(), "w", encoding="utf-8") as f:
        f.write("ok")


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # keep alive when minimized to tray

    icon = QIcon(app_icon_path())
    if not icon.isNull():
        app.setWindowIcon(icon)  # taskbar icon for every window/dialog in the app

    loading = LoadingScreen()
    main_window_holder = {}

    def on_loading_ready():
        loading.close()

        if not _terms_already_accepted():
            dialog = TermsDialog()
            if dialog.exec_() != dialog.Accepted or not dialog.accepted_terms:
                sys.exit(0)
            _mark_terms_accepted()

        window = MainWindow()
        main_window_holder["window"] = window
        window.show()

    loading.ready.connect(on_loading_ready)
    loading.show()
    loading.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
