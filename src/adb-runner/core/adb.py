# -*- coding: utf-8 -*-
"""AdbService — 设备枚举、命令 -s 替换、脚本解析与多步执行（纯逻辑，Qt 无关，便于测试）。

脚本语法（parse_script 约定）：
  - 每行一条命令，按行顺序执行；行内 &、&&、|| 的顺序/短路语义交给 shell
  - 任一命令行退出码非 0 → 立即停止后续步骤（等价 && 语义）
  - "sleep N" / "wait N" / "等待 N"（秒，支持小数）→ 步骤间等待
  - 空行与 # 开头的行为注释，跳过
  - 循环/条件判断不单独造语法：单行内用 shell 原生 for/if 即可
    （如 adb shell "for i in 1 2 3; do ...; done"）
"""

import os
import re
import shutil
import subprocess
import time

# GUI 程序拉起控制台子进程（adb/cmd）时，禁止 Windows 为子进程创建控制台窗口（避免闪烁终端）
_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# 匹配独立的 "adb" 令牌；若其后已跟 "-s"（已是 adb -s ... 形式）则不替换
_ADB_RE = re.compile(r"(?<![\w.])adb(?![\w-])(?!\s+-s\b)")

# 间隔行：sleep 2 / wait 1.5 / 等待 2（单位秒，支持小数）
_SLEEP_RE = re.compile(r"^(?:sleep|wait|等待)\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)


def adb_available() -> bool:
    return bool(shutil.which("adb"))


def parse_script(command: str):
    """把脚本文本解析为步骤列表，元素为 ("sleep", 秒) 或 ("cmd", 命令行)。"""
    steps = []
    for raw in (command or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _SLEEP_RE.match(line)
        if m:
            steps.append(("sleep", float(m.group(1))))
        else:
            steps.append(("cmd", line))
    return steps


class AdbService:
    """封装与 adb 命令行的交互。"""

    def __init__(self, logger=None):
        self._adb = shutil.which("adb") or "adb"
        self._log = logger  # 可选 logging.Logger，用于记录基础设施错误

    def list_devices(self):
        """枚举连接设备，返回 [{'serial','model','state'}]。"""
        try:
            out = subprocess.run(
                [self._adb, "devices", "-l"],
                capture_output=True, text=True, timeout=5,
                creationflags=_CREATE_NO_WINDOW,
            ).stdout
        except (OSError, subprocess.TimeoutExpired) as e:
            if self._log:
                self._log.warning("adb devices 枚举失败: %s", e)
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
        """阻塞执行单条命令，output_cb(line) 逐行回调输出（合并 stdout/stderr）。返回退出码。"""
        cmd = self.build_command(command, serial)
        try:
            proc = subprocess.Popen(
                cmd, shell=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
                creationflags=_CREATE_NO_WINDOW,
            )
        except OSError as e:
            if self._log:
                self._log.error("命令无法执行(cmd=%s): %s", cmd, e)
            if output_cb:
                output_cb(f"[错误] 无法执行: {e}")
            return -1
        for line in proc.stdout:
            line = line.rstrip("\r\n")
            if output_cb:
                output_cb(line)
        proc.wait()
        return proc.returncode

    def run_script(self, command: str, serial: str = None, output_cb=None) -> int:
        """按步骤顺序执行脚本文本；任一命令步骤失败（退出码非 0）即停止后续步骤。

        返回第一个失败步骤的退出码；全部成功返回 0。
        """
        steps = parse_script(command)
        total = len(steps)
        multi = total > 1  # 单步骤脚本不加步骤头，输出与旧版一致
        for i, (kind, val) in enumerate(steps, 1):
            if kind == "sleep":
                if output_cb:
                    output_cb(f"⏳ 等待 {val:g} 秒…")
                time.sleep(val)
                continue
            if multi and output_cb:
                output_cb(f"▶ [{i}/{total}] {val}")
            code = self.run(val, serial, output_cb)
            if code != 0:
                if multi and output_cb:
                    output_cb(f"✗ 步骤 [{i}/{total}] 失败（退出码 {code}），停止后续步骤")
                return code
        return 0
