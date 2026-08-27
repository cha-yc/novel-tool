# -*- coding: utf-8 -*-
"""ADB 脚本工具 — 入口（单实例 + 秒开加载）。"""

import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from core.paths import app_base_dir, data_dir, log_dir

BASE_DIR = app_base_dir()
DATA_DIR = data_dir()
LOG_DIR = log_dir()
LOCK_FILE = BASE_DIR / "adb-runner.lock"


def icon_path() -> str:
    """程序图标：打包后取自 exe 内嵌资源（_MEIPASS），开发时取源码目录。"""
    if getattr(sys, "frozen", False):
        return str(Path(getattr(sys, "_MEIPASS", "") or ".") / "icon.ico")
    return str(Path(__file__).resolve().parent / "icon.ico")


def _acquire_lock() -> bool:
    """单实例锁：重复启动时提示并退出。"""
    lock = QLockFile(str(LOCK_FILE))
    if not lock.tryLock(100):
        return False
    return True


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ADB 脚本工具")
    app.setWindowIcon(QIcon(icon_path()))

    if not _acquire_lock():
        QMessageBox.information(None, "ADB 脚本工具", "程序已在运行。")
        return 0

    # 秒开：JSON 数据很小，同步加载极快；设备列表在窗口显示后后台刷新
    from core.logger import AppLogger
    from core.store import JsonStore
    from ui.main_window import MainWindow

    settings = JsonStore(DATA_DIR).load_script_set()["settings"]
    logger = AppLogger(
        LOG_DIR,
        mode=settings.get("log_mode", "error_only"),
        keep_days=settings.get("log_keep_days", 7),
        max_mb=settings.get("log_max_mb", 10),
    )
    logger.get().info("启动 ADB 脚本工具，data=%s logs=%s", DATA_DIR, LOG_DIR)

    win = MainWindow(DATA_DIR, logger.get(), log_dir=LOG_DIR, app_logger=logger)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
