# -*- coding: utf-8 -*-
"""AdbService — 设备枚举、命令 -s 替换与执行（纯逻辑，Qt 无关，便于测试）。"""

import os
import re
import shutil
import subprocess

# GUI 程序拉起控制台子进程（adb/cmd）时，禁止 Windows 为子进程创建控制台窗口（避免闪烁终端）
_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# 匹配独立的 "adb" 令牌；若其后已跟 "-s"（已是 adb -s ... 形式）则不替换
_ADB_RE = re.compile(r"(?<![\w.])adb(?![\w-])(?!\s+-s\b)")


def adb_available() -> bool:
    return bool(shutil.which("adb"))


class AdbService:
    """封装与 adb 命令行的交互。"""

    def __init__(self):
        self._adb = shutil.which("adb") or "adb"

    @property
    def available(self) -> bool:
        return bool(self._adb and self._adb != "adb" or shutil.which("adb"))

    def list_devices(self):
        """枚举连接设备，返回 [{'serial','model','state'}]。"""
        try:
            out = subprocess.run(
                [self._adb, "devices", "-l"],
                capture_output=True, text=True, timeout=5,
                creationflags=_CREATE_NO_WINDOW,
            ).stdout
        except (OSError, subprocess.TimeoutExpired):
            return []
        devices = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial, state = parts[0], parts[1]
            model = ""
            for p in parts[2:]:
                if p.startswith("model:"):
                    model = p.split(":", 1)[1].strip()
            devices.append({"serial": serial, "model": model, "state": state})
        return devices

    @staticmethod
    def build_command(command: str, serial: str = None) -> str:
        """把命令中的 adb 替换为 adb -s <serial>；serial 为空或已带 -s 时保持原样。"""
        if not serial or not command:
            return command
        return _ADB_RE.sub(f"adb -s {serial}", command)

    def run(self, command: str, serial: str = None, output_cb=None) -> int:
        """阻塞执行命令，output_cb(line) 逐行回调输出（合并 stdout/stderr）。返回退出码。"""
        cmd = self.build_command(command, serial)
        try:
            proc = subprocess.Popen(
                cmd, shell=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
                creationflags=_CREATE_NO_WINDOW,
            )
        except OSError as e:
            if output_cb:
                output_cb(f"[错误] 无法执行: {e}")
            return -1
        for line in proc.stdout:
            line = line.rstrip("\r\n")
            if output_cb:
                output_cb(line)
        proc.wait()
        return proc.returncode
