# -*- coding: utf-8 -*-
"""路径解析：保证数据/日志目录始终在 exe（或源码）同目录，打包后可迁移。"""

import sys
from pathlib import Path


def app_base_dir() -> Path:
    """程序根目录：PyInstaller 打包后为 exe 所在目录；开发时为 src/adb-runner。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """脚本数据目录（exe 同目录下 data）。"""
    return app_base_dir() / "data"


def log_dir() -> Path:
    """日志目录（exe 同目录下 logs）。"""
    return app_base_dir() / "logs"
