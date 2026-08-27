# -*- coding: utf-8 -*-
"""分组胶囊条（Segmented Pills）——用可勾选 QPushButton 实现 HTML 式胶囊效果。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


class GroupPills(QWidget):
    """横滑胶囊分组：名称+计数，选中=主题色填充，右键管理，尾部＋新建。"""

    group_changed = Signal(str)
    context_requested = Signal(str, object)  # 组名, 全局坐标
    add_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}   # name -> QPushButton
        self._current = ""

        self._flow = QHBoxLayout()
        self._flow.setContentsMargins(0, 0, 0, 0)
        self._flow.setSpacing(6)
        container = QWidget()
        # 不设置容器样式表/透明属性，透明度由应用级 QSS 统一控制
        container.setLayout(self._flow)

        self._scroll = QScrollArea()
        self._scroll.setWidget(container)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._add_btn = QPushButton("＋")
        self._add_btn.setObjectName("pillAdd")
        self._add_btn.setToolTip("新建分组")
        self._add_btn.setFocusPolicy(Qt.NoFocus)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(self.add_requested)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self._scroll, 1)
        lay.addWidget(self._add_btn)

    def set_groups(self, groups, current):
        """groups: [(name, count), ...]"""
        while self._flow.count():
            item = self._flow.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._buttons.clear()
        self._current = current
        for name, count in groups:
            btn = QPushButton(f"{name} ({count})")
            btn.setObjectName("pill")
            btn.setCheckable(True)
            btn.setChecked(name == current)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self._select(n))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, n=name, b=btn: self.context_requested.emit(
                    n, b.mapToGlobal(pos)))
            self._buttons[name] = btn
            self._flow.addWidget(btn)
        self._flow.addStretch(1)

    def _select(self, name):
        if name == self._current:
            return
        self._current = name
        for n, b in self._buttons.items():
            b.setChecked(n == name)
        self.group_changed.emit(name)
