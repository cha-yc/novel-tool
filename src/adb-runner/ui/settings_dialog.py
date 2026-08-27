# -*- coding: utf-8 -*-
"""设置对话框：脚本目录 / 日志目录 / 日志配置。"""

import os

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QVBoxLayout,
)

LOG_MODES = [
    ("all", "记录全部"),
    ("error_only", "仅错误（默认）"),
    ("off", "不记录"),
]


class SettingsDialog(QDialog):
    """设置页：打开脚本/日志目录，配置日志模式、保留天数、大小上限。"""

    def __init__(self, settings: dict, data_dir, log_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(380)
        self._data_dir = str(data_dir)
        self._log_dir = str(log_dir)

        form = QFormLayout()
        form.setSpacing(10)

        # 脚本目录
        data_path = QLineEdit(self._data_dir)
        data_path.setReadOnly(True)
        open_data = QPushButton("打开")
        open_data.clicked.connect(lambda: self._open(self._data_dir))
        data_row = QHBoxLayout()
        data_row.addWidget(data_path, 1)
        data_row.addWidget(open_data)
        form.addRow("脚本目录", data_row)

        # 日志目录
        open_log = QPushButton("打开日志目录")
        open_log.clicked.connect(lambda: self._open(self._log_dir))
        form.addRow("日志目录", open_log)

        # 日志配置
        self._mode = QComboBox()
        for val, label in LOG_MODES:
            self._mode.addItem(label, val)
        cur = settings.get("log_mode", "error_only")
        idx = next((i for i in range(self._mode.count())
                    if self._mode.itemData(i) == cur), 1)
        self._mode.setCurrentIndex(idx)

        self._keep = QSpinBox()
        self._keep.setRange(1, 90)
        self._keep.setValue(int(settings.get("log_keep_days", 7)))
        self._keep.setSuffix(" 天")

        self._max = QSpinBox()
        self._max.setRange(1, 500)
        self._max.setValue(int(settings.get("log_max_mb", 10)))
        self._max.setSuffix(" MB")

        form.addRow("日志模式", self._mode)
        form.addRow("保留天数", self._keep)
        form.addRow("单日志上限", self._max)

        hint = QLabel(
            "脚本目录位于程序（exe）同目录下的 data 文件夹，可直接编辑其中的 JSON。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#8A8A8A; font-size:11px;")

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(hint)
        lay.addWidget(btns)

    @staticmethod
    def _open(path):
        try:
            os.startfile(path)
        except OSError:
            pass

    def values(self) -> dict:
        return {
            "log_mode": self._mode.currentData(),
            "log_keep_days": self._keep.value(),
            "log_max_mb": self._max.value(),
        }
