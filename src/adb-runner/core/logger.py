# -*- coding: utf-8 -*-
"""AppLogger — 三档日志（all / error_only / off）+ 定期清理。

- 日志文件：{log_dir}/app.log，按天轮转，保留最近 keep_days 天
- 启动时清理过期日志；单文件超过 max_mb 触发一次轮转
"""

import logging
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_NAME = "adb-runner"


class AppLogger:
    """三档日志控制器。mode: all | error_only | off"""

    def __init__(self, log_dir, mode="error_only", keep_days=7, max_mb=10):
        self.log_dir = Path(log_dir)
        self.mode = mode
        self.keep_days = max(1, int(keep_days or 7))
        self.max_mb = max(1, int(max_mb or 10))
        self.logger = logging.getLogger(LOG_NAME)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        self.logger.propagate = False

        # 控制台（开发/排错用；off 模式下不输出）
        console = logging.StreamHandler()
        console.setLevel(logging.INFO if mode != "off" else logging.CRITICAL)
        self.logger.addHandler(console)

        if mode in ("all", "error_only"):
            self.log_dir.mkdir(parents=True, exist_ok=True)
            handler = TimedRotatingFileHandler(
                self.log_dir / "app.log",
                when="midnight",
                backupCount=self.keep_days,
                encoding="utf-8",
            )
            handler.setLevel(logging.ERROR if mode == "error_only" else logging.DEBUG)
            self.logger.addHandler(handler)

        self.cleanup()
        self.logger.info(
            "AppLogger 初始化: mode=%s keep_days=%d max_mb=%d dir=%s",
            mode, self.keep_days, self.max_mb, self.log_dir,
        )

    def cleanup(self):
        """删除超过保留天数的日志；单文件超限触发一次轮转。"""
        try:
            if not self.log_dir.exists():
                return
            now = time.time()
            cutoff = now - self.keep_days * 86400
            for p in self.log_dir.glob("app.log*"):
                if p.is_file() and p.stat().st_mtime < cutoff:
                    try:
                        p.unlink()
                    except OSError:
                        pass
            main = self.log_dir / "app.log"
            if main.exists() and main.stat().st_size > self.max_mb * 1024 * 1024:
                for h in self.logger.handlers:
                    if isinstance(h, TimedRotatingFileHandler):
                        h.doRollover()
        except OSError:
            pass

    def reconfigure(self, log_mode=None, log_keep_days=None, log_max_mb=None):
        """运行时更新日志配置（设置页保存后实时生效）。"""
        if log_mode is not None:
            self.mode = log_mode
        if log_keep_days is not None:
            self.keep_days = max(1, int(log_keep_days))
        if log_max_mb is not None:
            self.max_mb = max(1, int(log_max_mb))

        self.logger.handlers.clear()
        console = logging.StreamHandler()
        console.setLevel(logging.INFO if self.mode != "off" else logging.CRITICAL)
        self.logger.addHandler(console)
        if self.mode in ("all", "error_only"):
            self.log_dir.mkdir(parents=True, exist_ok=True)
            handler = TimedRotatingFileHandler(
                self.log_dir / "app.log", when="midnight",
                backupCount=self.keep_days, encoding="utf-8")
            handler.setLevel(logging.ERROR if self.mode == "error_only" else logging.DEBUG)
            self.logger.addHandler(handler)
        self.cleanup()
        self.logger.info(
            "日志配置更新: mode=%s keep_days=%d max_mb=%d",
            self.mode, self.keep_days, self.max_mb)

    @staticmethod
    def get(name=None):
        """获取带子命名空间的 logger。"""
        return logging.getLogger(LOG_NAME + (f".{name}" if name else ""))
