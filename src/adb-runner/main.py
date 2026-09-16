# -*- coding: utf-8 -*-
"""ADB 脚本工具 — 入口（单实例 + 秒开加载）。"""

import os
import sys
import time
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


def _acquire_lock():
    """单实例锁。注意：QLockFile 析构即释放锁，必须由调用方持有到进程结束。"""
    lock = QLockFile(str(LOCK_FILE))
    return lock if lock.tryLock(100) else None


def main() -> int:
    t0 = time.perf_counter()
    app = QApplication(sys.argv)
    app.setApplicationName("ADB 脚本工具")
    app.setWindowIcon(QIcon(icon_path()))

    lock = _acquire_lock()
    if lock is None:
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
    win.setWindowIcon(QIcon(icon_path()))  # 显式设置窗口图标（任务栏不再显示 python 图标）
    # 显示前强制所有控件完成样式抛光：避免首帧以默认样式出现、随后再换主题而闪烁
    for w in QApplication.allWidgets():
        w.style().unpolish(w)
        w.style().polish(w)
    win.ensurePolished()
    win.show()
    # 首帧完整绘制并完成布局后再进入事件循环，避免"窗口先出现→内容后绘制"的二次闪烁
    QApplication.processEvents()
    logger.get().info("窗口已显示，启动耗时 %.2fs", time.perf_counter() - t0)
    rc = app.exec()
    # 兜底：若后台线程仍卡在运行（如 adb 无响应），强制退出，
    # 避免进程残留导致 exe 文件被锁、或销毁运行中线程而崩溃。
    for t in (getattr(win, "_device_thread", None),
              getattr(win, "_exec_thread", None)):
        if t is not None and t.isRunning():
            os._exit(0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
