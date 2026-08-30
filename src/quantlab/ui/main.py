"""Canonical desktop entry. No quantitative logic lives here."""

from __future__ import annotations

import os
import sys
from multiprocessing import freeze_support
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    freeze_support()
    try:
        import PySide6.QtWidgets  # noqa: F401 — probe PySide6 install
    except ImportError:
        sys.stderr.write("PySide6 is required for the desktop app. pip install -e '.[dev]'\n")
        return 1

    try:
        return _run_desktop(argv)
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


def _run_desktop(argv: list[str] | None) -> int:
    from PySide6.QtWidgets import QApplication

    from quantlab.app.bootstrap import bootstrap
    from quantlab.ui.main_window import MainWindow
    from quantlab.ui.splash import SplashDialog
    from quantlab.ui.theme import apply_theme
    from quantlab.ui.welcome import WelcomeDialog

    data_env = os.environ.get("QUANT_LAB_DATA_DIR")
    runtime = bootstrap(data_dir=Path(data_env) if data_env else None)
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("NAYAK QUANT LAB")
    app.setOrganizationName("NAYAK QUANT LAB")
    apply_theme(app, runtime.ui_settings.current.theme)

    skip_splash = os.environ.get("QUANT_LAB_SKIP_SPLASH", "").lower() in {"1", "true", "yes"}
    if not skip_splash:
        milestones = runtime.ui_settings.current.milestones
        if "onboarding_complete" not in milestones:
            WelcomeDialog(runtime).exec()
        elif not runtime.health.research_ready():
            SplashDialog(runtime).exec()

    window = MainWindow(runtime)
    window.show()
    window.raise_()
    window.activateWindow()
    if sys.stderr.isatty():
        sys.stderr.write(
            "NAYAK QUANT LAB is running — look for the desktop window. Press Ctrl+C here to quit.\n"
        )
    code = app.exec()
    if not runtime.is_closed:
        runtime.shutdown()
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
