# -*- coding: utf-8 -*-
"""分组胶囊条（Segmented Pills）——可勾选 QPushButton 实现 HTML 式胶囊效果。
支持：横滑 + 滚轮横滚 + 上一页/下一页翻页 + 细滚动条提示（超出时出现）。
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QScrollArea, QWidget,
)


class _HPillScroll(QScrollArea):
    """横向胶囊滚动区：鼠标滚轮 → 水平滚动（分组多时方便左右浏览）。"""

    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        if delta != 0:
            bar = self.horizontalScrollBar()
            bar.setValue(bar.value() - delta)
            e.accept()
        else:
            super().wheelEvent(e)


class GroupPills(QWidget):
    """横滑分组胶囊：名称+计数，选中=主题色填充，右键管理，尾部＋新建。
    分组过多时可左右滚动 / 滚轮横滚 / 上一页下一页翻页。
    """

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
        container.setLayout(self._flow)

        self._scroll = _HPillScroll()
        self._scroll.setWidget(container)
        self._scroll.setWidgetResizable(False)  # 容器尺寸由 _update_scroll 手动管理，滚动范围才准确
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.horizontalScrollBar().valueChanged.connect(self._update_nav)

        def _nav_button(symbol, tooltip):
            b = QPushButton(symbol)
            b.setObjectName("pillNav")
            b.setToolTip(tooltip)
            b.setFixedSize(26, 26)
            b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.PointingHandCursor)
            b.setEnabled(False)
            return b

        self._prev_btn = _nav_button("‹", "上一页分组")
        self._next_btn = _nav_button("›", "下一页分组")
        self._prev_btn.clicked.connect(lambda: self._page(-1))
        self._next_btn.clicked.connect(lambda: self._page(1))

        self._add_btn = QPushButton("＋")
        self._add_btn.setObjectName("pillAdd")
        self._add_btn.setToolTip("新建分组")
        self._add_btn.setFocusPolicy(Qt.NoFocus)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(self.add_requested)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self._prev_btn)
        lay.addWidget(self._scroll, 1)
        lay.addWidget(self._next_btn)
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
        QTimer.singleShot(0, self._update_scroll)  # 等布局重算后刷新尺寸/范围/翻页状态

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self._update_scroll)

    def _update_scroll(self):
        """按内容实际宽度重设容器尺寸与滚动范围，保证分组增删/窗口缩放后准确。"""
        cont = self._scroll.widget()
        vp = self._scroll.viewport()
        bar = self._scroll.horizontalScrollBar()
        if cont is None or vp is None:
            return
        need_w = max(cont.sizeHint().width(), vp.width())
        need_h = max(cont.sizeHint().height(), vp.height())
        if cont.width() != need_w or cont.height() != need_h:
            cont.resize(need_w, need_h)
        bar.setRange(0, max(0, cont.width() - vp.width()))
        self._update_nav()

    def _page(self, direction):
        bar = self._scroll.horizontalScrollBar()
        step = max(self._scroll.viewport().width() - 40, 40)
        bar.setValue(bar.value() + direction * step)

    def _update_nav(self):
        """根据是否还能滚动，启用/禁用上一页下一页按钮（视觉提示）。"""
        bar = self._scroll.horizontalScrollBar()
        self._prev_btn.setEnabled(bar.value() > 0)
        self._next_btn.setEnabled(bar.value() < bar.maximum())

    def _select(self, name):
        if name == self._current:
            return
        self._current = name
        for n, b in self._buttons.items():
            b.setChecked(n == name)
        self.group_changed.emit(name)
