# -*- coding: utf-8 -*-
"""底部输出面板：可折叠，按设备分 Tab 展示执行结果。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)

from ui.icons import NEUTRAL, svg_icon


class OutputPanel(QWidget):
    """可折叠输出区，每个在线设备一个 Tab。收起时归还占用的空间。"""

    _CONSOLE_MIN = 150

    expand_changed = Signal(bool)  # 收起/展开状态变化（供外部记忆持久化）

    def __init__(self, expanded=True, parent=None):
        super().__init__(parent)
        self._pages = {}  # serial -> QPlainTextEdit
        self._expanded = bool(expanded)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        head = QHBoxLayout()
        head.setContentsMargins(4, 0, 0, 0)
        head.setSpacing(4)
        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(svg_icon("chevron", NEUTRAL, 16))
        self.toggle_btn.setToolTip("折叠 / 展开输出")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(self._expanded)
        self.toggle_btn.setFocusPolicy(Qt.NoFocus)
        self.toggle_btn.toggled.connect(self._toggle)
        head.addWidget(self.toggle_btn)
        lbl = QLabel("输出")
        lbl.setStyleSheet("font-weight:600;")
        head.addWidget(lbl)
        head.addStretch(1)
        self.clear_btn = QToolButton()
        self.clear_btn.setIcon(svg_icon("trash", NEUTRAL, 15))
        self.clear_btn.setToolTip("清空当前设备的输出")
        self.clear_btn.setFocusPolicy(Qt.NoFocus)
        self.clear_btn.clicked.connect(self._clear_current)
        head.addWidget(self.clear_btn)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("outputTabs")  # 触发中性小标签样式（去掉大块蓝色）
        self.tabs.setDocumentMode(True)
        self._empty = QPlainTextEdit("选择在线设备后，点 ▶ 执行脚本。")
        self._empty.setReadOnly(True)
        self._empty.setMaximumBlockCount(1)
        self._empty.setMinimumHeight(self._CONSOLE_MIN)
        self.tabs.addTab(self._empty, "输出设备")

        lay.addLayout(head)
        lay.addWidget(self.tabs, 1)

        # 按记忆的初始状态应用收起/展开（初始化时未连接信号，不触发保存）
        self.tabs.setVisible(self._expanded)
        self.tabs.setMinimumHeight(self._CONSOLE_MIN if self._expanded else 0)

    def _toggle(self, on):
        self._expanded = on
        self.tabs.setVisible(on)
        # 收起时把最小高度归零，布局才会把空间还给脚本列表
        self.tabs.setMinimumHeight(self._CONSOLE_MIN if on else 0)
        self.expand_changed.emit(on)

    def expand(self):
        self._expanded = True
        self.toggle_btn.setChecked(True)
        self.tabs.setVisible(True)

    def ensure_tab(self, serial: str, title: str) -> QPlainTextEdit:
        if serial not in self._pages:
            edit = QPlainTextEdit()
            edit.setReadOnly(True)
            edit.setMaximumBlockCount(5000)
            edit.setMinimumHeight(self._CONSOLE_MIN)
            f = edit.font()
            f.setFamily("Consolas")
            edit.setFont(f)
            self._pages[serial] = edit
            self.tabs.addTab(edit, title)
        return self._pages[serial]

    def append(self, serial: str, text: str, color=None):
        """追加一行输出；color 为十六进制颜色时该行着色（如错误红/成功绿）。"""
        edit = self.ensure_tab(serial, serial)
        cursor = edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        if color:
            fmt.setForeground(QColor(color))
        cursor.insertText(text + "\n", fmt)
        edit.setTextCursor(cursor)
        edit.verticalScrollBar().setValue(edit.verticalScrollBar().maximum())

    def switch_to(self, serial: str):
        if serial and serial in self._pages:
            self.tabs.setCurrentWidget(self._pages[serial])

    def _clear_current(self):
        """清空当前设备 Tab 的输出内容（占位页忽略）。"""
        w = self.tabs.currentWidget()
        if w is not None and w is not self._empty:
            w.clear()
