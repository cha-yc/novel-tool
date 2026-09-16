# -*- coding: utf-8 -*-
"""Toast — 顶部悬浮胶囊提示（非阻断的一次性结果反馈）。

规范：
- 触发场景：操作失败/关键结果的即时反馈（执行失败、保存失败、adb 缺失、
  设置已保存等）；需要用户决策的交互（删除确认等）仍使用 QMessageBox。
- 级别与时长：info 2500ms / success 2000ms / error 3500ms；点击立即消失。
- 样式：主窗口顶部居中悬浮胶囊，圆角 16px，主题 surface 背景 + 1px 边框
  （QSS：QFrame#toast），左侧 8px 状态圆点（info 蓝 / success 绿 / error 红）。
- 行为：不抢焦点（WA_ShowWithoutActivating）、淡出消失、窗口缩放时自动重定位。
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QTimer
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
)

_DOT_COLOR = {"info": "#4F8CFF", "success": "#34C759", "error": "#FF5F57"}
_DEFAULT_MS = {"info": 2500, "success": 2000, "error": 3500}


class Toast(QFrame):
    """可复用的单例式提示条：由父窗口（主窗口）持有，show_message 刷新内容与时钟。"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._fading_out = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 9, 16, 9)
        lay.setSpacing(8)
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._dot.setStyleSheet("border-radius:4px; background:#4F8CFF;")
        self._text = QLabel()
        self._text.setWordWrap(True)
        self._text.setMaximumWidth(320)
        lay.addWidget(self._dot)
        lay.addWidget(self._text)

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.finished.connect(self._on_anim_done)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)

    def show_message(self, text: str, kind: str = "info", duration_ms: int = None):
        """显示提示。kind: info | success | error；duration_ms 缺省按级别取默认时长。"""
        kind = kind if kind in _DOT_COLOR else "info"
        self._dot.setStyleSheet(f"border-radius:4px; background:{_DOT_COLOR[kind]};")
        self._text.setText(text)
        # 新消息打断淡出：恢复不透明并重设时钟
        self._anim.stop()
        self._hide_timer.stop()
        self._fading_out = False
        self._effect.setOpacity(1.0)
        self.reposition()
        self.show()
        self.raise_()
        self._hide_timer.start(int(duration_ms or _DEFAULT_MS[kind]))

    def reposition(self):
        """顶部居中（父窗口宽度的中点、顶栏下方）；缩放窗口时再次调用。"""
        p = self.parentWidget()
        if p is None:
            return
        self.adjustSize()
        self.move(max(8, (p.width() - self.width()) // 2), 46)

    def mousePressEvent(self, e):
        self.fade_out()
        super().mousePressEvent(e)

    def fade_out(self):
        if not self.isVisible() or self._fading_out:
            return
        self._hide_timer.stop()
        self._fading_out = True
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _on_anim_done(self):
        if self._fading_out:
            self.hide()
