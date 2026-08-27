# -*- coding: utf-8 -*-
"""脚本卡片列表：排序序号 + ▶执行 + 名称/预览 + 分类标签 + ⋯菜单 + 卡片悬浮拖拽。"""

from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from ui import theme
from ui.icons import NEUTRAL, WHITE, svg_icon

ROW_HEIGHT = 60  # 脚本卡片行高（item 与 widget 必须一致，否则互相覆盖）


class ScriptItemWidget(QWidget):
    """脚本卡片行。长按行背景触发卡片悬浮拖拽。"""

    execute_requested = Signal()
    row_clicked = Signal()
    row_double_clicked = Signal()
    context_requested = Signal(object)   # 全局坐标
    drag_triggered = Signal(object)      # 长按触发，arg=self
    drag_move = Signal(object)           # 拖拽移动，arg=全局QPoint
    drag_release = Signal()

    def __init__(self, script: dict, order: int, long_press_ms=600, parent=None):
        super().__init__(parent)
        # 让 QSS 的 background/border/圆角在自定义 QWidget 上生效（关键！）
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._long_press_ms = long_press_ms
        self._pressed = False
        self._dragging = False
        self._lift_effect = None
        self._shadow = None
        self._full_name = script.get("name", "")
        self._full_preview = self._preview_text(script.get("command", ""))
        category = script.get("category", "")

        self.setFixedHeight(ROW_HEIGHT)
        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.timeout.connect(self._fire_drag)

        # 排序序号
        self._idx = QLabel()
        self._idx.setObjectName("idx")
        self.set_order(order)

        # ▶ 执行键
        self._play = QPushButton()
        self._play.setObjectName("play")
        self._play.setIcon(svg_icon("play", WHITE, 18))
        self._play.setIconSize(self._play.iconSize())
        self._play.setCursor(Qt.PointingHandCursor)
        self._play.setFocusPolicy(Qt.NoFocus)
        self._play.setToolTip("执行")
        self._play.clicked.connect(self.execute_requested)

        # 名称 + 元信息（分类标签 + 命令预览）
        self._name = QLabel()
        self._name.setObjectName("row_name")
        self._tag = QLabel(category)
        self._tag.setObjectName("tag")
        self._tag.setVisible(bool(category))
        self._preview = QLabel()
        self._preview.setObjectName("row_preview")

        meta = QHBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(6)
        if category:
            meta.addWidget(self._tag)
        meta.addWidget(self._preview, 1)

        self._body = QWidget()
        bv = QVBoxLayout(self._body)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(2)
        bv.addWidget(self._name)
        bv.addLayout(meta)

        # ⋯ 菜单键
        self._more = QPushButton()
        self._more.setObjectName("more")
        self._more.setIcon(svg_icon("more", NEUTRAL, 20))
        self._more.setFixedSize(32, 32)
        self._more.setCursor(Qt.PointingHandCursor)
        self._more.setFocusPolicy(Qt.NoFocus)
        self._more.setToolTip("更多")
        self._more.clicked.connect(lambda: self.context_requested.emit(
            self._more.mapToGlobal(self._more.rect().bottomRight())))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 6, 6)
        lay.setSpacing(8)
        lay.addWidget(self._idx, 0, Qt.AlignVCenter)
        lay.addWidget(self._play)
        lay.addWidget(self._body, 1)
        lay.addWidget(self._more)

        # 行内文字区域鼠标事件穿透到行背景（用于长按拖拽）
        for w in (self._idx, self._name, self._tag, self._preview, self._body):
            w.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._is_placeholder = False
        self._update_elide()

    # ---------- 序号 / 预览 ----------

    def set_order(self, n: int):
        self._idx.setText(f"{n:02d}")

    @staticmethod
    def _preview_text(command: str) -> str:
        return " ".join(command.split())

    def _update_elide(self):
        """按当前宽度智能省略，避免文字被截断/遮挡。"""
        avail = self.width() - 10 - 6 - 22 - 36 - 32 - 8 * 4  # 边距+idx+play+more+间距
        if avail <= 30:
            return
        name_fm = QFontMetrics(self._name.font())
        self._name.setText(name_fm.elidedText(self._full_name, Qt.ElideRight, avail))
        tag_w = self._tag.width() + 6 if self._tag.isVisible() else 0
        pv_avail = max(20, avail - tag_w)
        pv_fm = QFontMetrics(self._preview.font())
        self._preview.setText(pv_fm.elidedText(self._full_preview, Qt.ElideRight, pv_avail))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_elide()

    # ---------- 选中 / 拖拽占位 视觉 ----------

    def set_selected(self, on: bool):
        self.setProperty("selected", on)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_placeholder(self, on: bool):
        """拖拽时原位置变成空白占位（虚线槽），松开/取消后恢复。"""
        if on:
            self._is_placeholder = True
            for w in (self._idx, self._play, self._body, self._more):
                w.setVisible(False)
            self.setStyleSheet(
                f"ScriptItemWidget{{background:transparent;"
                f"border:2px dashed {theme.color('border')};border-radius:16px;}}")
        else:
            self._is_placeholder = False
            for w in (self._idx, self._play, self._body, self._more):
                w.setVisible(True)
            self.setStyleSheet("")

    def reset_press(self):
        """复位按压/长按状态：双击打开弹窗、取消弹窗后调用，避免误触发拖拽。"""
        self._press_timer.stop()
        self._pressed = False
        self._dragging = False

    # ---------- 鼠标：点击 / 长按拖拽 ----------

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pressed = True
            self._dragging = False
            self._press_timer.start(self._long_press_ms)
            self.row_clicked.emit()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging and (e.buttons() & Qt.LeftButton):
            self.drag_move.emit(e.globalPosition().toPoint())
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._press_timer.stop()
        if self._dragging:
            self.drag_release.emit()
        self._pressed = False
        self._dragging = False
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        # 双击会打开编辑对话框（模态），必须先取消拖拽并复位按压，
        # 否则释放事件被对话框吃掉、残留按压状态在取消后误触发拖拽。
        # 注意：不再调用 super()——基类默认实现会重新触发按压/长按计时器。
        self.reset_press()
        if e.button() == Qt.LeftButton:
            self.row_double_clicked.emit()

    def contextMenuEvent(self, e):
        self.context_requested.emit(e.globalPos())

    def _fire_drag(self):
        if self._pressed:
            self._dragging = True
            self.drag_triggered.emit(self)


class _DragCardOverlay(QWidget):
    """拖拽浮动卡片：列表视口内的子控件，置顶 + 鼠标穿透（安全、始终在最上层）。"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFixedSize(270, 78)
        self._name = ""
        self._preview = ""
        self.hide()

    def set_data(self, name, preview):
        self._name = name
        self._preview = preview
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(theme.color("accent")), 2))
        p.setBrush(QColor(theme.color("surface2")))
        p.drawRoundedRect(rect, 14, 14)
        # 名称（上）
        p.setPen(QColor(theme.color("text")))
        f = p.font()
        f.setPointSize(13)
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect.adjusted(14, 12, -10, -38),
                   Qt.AlignLeft | Qt.AlignVCenter, self._name)
        # 命令预览（下，不挤占名称）
        p.setPen(QColor(theme.color("sub")))
        f2 = p.font()
        f2.setPointSize(10)
        f2.setBold(False)
        p.setFont(f2)
        p.drawText(rect.adjusted(14, 42, -10, -8),
                   Qt.AlignLeft | Qt.AlignTop, self._preview[:44])
        p.end()


class ScriptList(QListWidget):
    """脚本卡片列表：负责行定位、卡片悬浮拖拽（实时交换）、边界自动滚动。"""

    execute_index = Signal(int)
    edit_index = Signal(int)
    reordered = Signal(int, int)
    context_index = Signal(int, object)

    def __init__(self, long_press_ms=600, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSpacing(6)  # 卡片间距
        self._long_press_ms = long_press_ms
        self._drag_enabled = True
        self._drag_orig = -1
        self._target_row = -1
        self._dragging = False
        self._valid_drop = True
        self._scroll_dir = 0
        self._selected_row = -1
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(30)
        self._scroll_timer.timeout.connect(self._on_auto_scroll)
        # 拖拽浮动卡片：视口内覆盖层（置顶 + 鼠标穿透，安全且始终在最上层）
        self._overlay = _DragCardOverlay(self.viewport())
        self._overlay.hide()

    def set_drag_enabled(self, on: bool):
        self._drag_enabled = on

    # ---------- 数据填充 ----------

    def set_scripts(self, scripts):
        bar = self.verticalScrollBar()
        pos = bar.value()
        self.clear()
        self._selected_row = -1
        for i, s in enumerate(scripts):
            self.add_script_item(s, i + 1)
        # 重建后恢复滚动位置（拖拽排序后不跳回顶部）
        if pos > 0:
            QTimer.singleShot(0, lambda: bar.setValue(min(pos, bar.maximum())))

    def add_script_item(self, script: dict, order: int):
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, ROW_HEIGHT))  # 关键：显式行高，否则与卡片高度不一致会互相覆盖
        widget = ScriptItemWidget(script, order, self._long_press_ms)
        widget.execute_requested.connect(lambda w=widget: self._on_execute(w))
        widget.row_clicked.connect(lambda w=widget: self._on_row_clicked(w))
        widget.row_double_clicked.connect(lambda w=widget: self._on_edit(w))
        widget.context_requested.connect(lambda g, w=widget: self._on_context(w, g))
        widget.drag_triggered.connect(self._on_drag_triggered)
        widget.drag_move.connect(self._on_drag_move)
        widget.drag_release.connect(self._on_drag_release)
        self.addItem(item)
        self.setItemWidget(item, widget)

    def _row_of(self, widget) -> int:
        for i in range(self.count()):
            if self.itemWidget(self.item(i)) is widget:
                return i
        return -1

    # ---------- 行事件 ----------

    def _on_execute(self, widget):
        i = self._row_of(widget)
        if i >= 0:
            self.execute_index.emit(i)

    def _on_row_clicked(self, widget):
        if self._dragging:
            # 拖拽进行中再次按下 → 立即取消拖拽（防止双击/再次点击后状态卡死）
            self.cancel_drag()
            return
        i = self._row_of(widget)
        if i >= 0:
            self.setCurrentRow(i)
            self._set_selected_row(i)

    def _set_selected_row(self, i: int):
        if i == self._selected_row:
            return
        self._selected_row = i
        for j in range(self.count()):
            w = self.itemWidget(self.item(j))
            if w is not None:
                w.set_selected(j == i)

    def _on_edit(self, widget):
        i = self._row_of(widget)
        if i >= 0:
            self.edit_index.emit(i)

    def _on_context(self, widget, gpos):
        i = self._row_of(widget)
        if i >= 0:
            self.context_index.emit(i, gpos)

    # ---------- 卡片悬浮拖拽（paint 绘制浮动卡片 + 插入线，无顶层窗口，杜绝崩溃） ----------

    def _on_drag_triggered(self, widget):
        i = self._row_of(widget)
        if i >= 0 and self._drag_enabled:
            self._drag_orig = i
            self._target_row = i
            self._valid_drop = True
            self._dragging = True
            self._overlay.set_data(getattr(widget, "_full_name", ""),
                                   getattr(widget, "_full_preview", ""))
            self._position_overlay()
            self._overlay.show()
            self._overlay.raise_()
            widget.set_placeholder(True)  # 原位置变空白占位
            self._scroll_timer.start()

    def _position_overlay(self):
        """让浮动卡片跟随光标（视口坐标，居中）。"""
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        self._overlay.move(pos.x() - self._overlay.width() // 2,
                           pos.y() - self._overlay.height() // 2)

    def _on_drag_move(self, gpos):
        if not self._dragging:
            return
        vp = self.viewport()
        pos = vp.mapFromGlobal(gpos)
        self._position_overlay()
        # 光标在列表内才算有效落点；拖出列表 = 无效，不排序
        self._valid_drop = vp.rect().contains(pos)
        self._target_row = self._target_from_pos(pos) if self._valid_drop else self._drag_orig
        h = vp.height()
        zone = max(h // 4, 24)
        if pos.y() < zone:
            self._scroll_dir = -1
        elif pos.y() > h - zone:
            self._scroll_dir = 1
        else:
            self._scroll_dir = 0
        vp.update()

    def _target_from_pos(self, pos) -> int:
        """由指针位置推断插入点：命中行→其序号；下方空区→末尾。"""
        item = self.itemAt(pos)
        if item is not None:
            return self.row(item)
        if self.count() > 0:
            last_rect = self.visualItemRect(self.item(self.count() - 1))
            if pos.y() > last_rect.bottom():
                return self.count()
        return 0

    def _on_auto_scroll(self):
        if not self._dragging:
            return
        # 定时轮询光标位置 → 浮动卡片始终跟手（快速移动也不掉队）
        self._position_overlay()
        if self._scroll_dir != 0:
            bar = self.verticalScrollBar()
            bar.setValue(bar.value() + self._scroll_dir * 8)
            self._on_drag_move(QCursor.pos())
        self.viewport().update()

    def _on_drag_release(self):
        self._scroll_timer.stop()
        if self._dragging:
            w = self.itemWidget(self.item(self._drag_orig))
            if w is not None:
                w.set_placeholder(False)
            # 无效落点（拖出列表）或原地松开 → 不排序
            if self._valid_drop and self._drag_orig != self._target_row:
                self.reordered.emit(self._drag_orig, self._target_row)
        self._reset_drag()

    def cancel_drag(self):
        """取消进行中的拖拽（打开对话框/窗口失焦时），并复位所有行的按压状态。"""
        self._scroll_timer.stop()
        if self._dragging:
            w = self.itemWidget(self.item(self._drag_orig))
            if w is not None:
                w.set_placeholder(False)
        for j in range(self.count()):
            w = self.itemWidget(self.item(j))
            if w is not None:
                w.reset_press()
        self._reset_drag()

    def _reset_drag(self):
        self._dragging = False
        self._drag_orig = -1
        self._target_row = -1
        self._valid_drop = True
        self._scroll_dir = 0
        self._overlay.hide()
        self.viewport().update()

    def paintEvent(self, e):
        """绘制拖拽插入线（浮动卡片由视口内覆盖层绘制，置顶显示）。"""
        super().paintEvent(e)
        if not self._dragging:
            return
        vp = self.viewport()
        p = QPainter(vp)
        p.setRenderHint(QPainter.Antialiasing)
        # 插入线
        if self._valid_drop and 0 <= self._target_row <= self.count():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.color("accent")))
            if self._target_row < self.count():
                r = self.visualItemRect(self.item(self._target_row))
                y = max(r.top() - 3, 0)
            elif self.count() > 0:
                r = self.visualItemRect(self.item(self.count() - 1))
                y = r.bottom()
            else:
                y = 2
            p.drawRoundedRect(QRect(6, y, max(vp.width() - 12, 20), 3), 2, 2)
        p.end()
