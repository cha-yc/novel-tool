# -*- coding: utf-8 -*-
"""设备胶囊：状态点 + 设备下拉 + 刷新。多设备连接时单选当前执行设备。

刷新走 refresh_requested 信号由主窗口后台线程执行（adb devices 可能耗时数秒）。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QToolButton, QWidget

from ui.icons import NEUTRAL, svg_icon

_DOT_ONLINE = "#34C759"
_DOT_OFFLINE = "#8F959E"


class DevicePanel(QWidget):
    """设备选择器：绿点=在线，灰点=离线；下拉单选当前执行设备。"""

    device_changed = Signal(str)  # 当前有效设备 serial；无在线设备时为空串
    refresh_requested = Signal()  # 点击刷新按钮（由主窗口走后台线程，避免阻塞 UI）

    def __init__(self, last_serial="", parent=None):
        super().__init__(parent)
        self.setObjectName("deviceCapsule")
        self.setAttribute(Qt.WA_StyledBackground, True)  # 让 QSS 胶囊背景生效
        self._devices = []

        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        self._dot.setStyleSheet(f"border-radius:5px; background:{_DOT_OFFLINE};")

        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_index_changed)

        self.refresh_btn = QToolButton()
        self.refresh_btn.setIcon(svg_icon("refresh", NEUTRAL, 20))
        self.refresh_btn.setToolTip("刷新设备")
        self.refresh_btn.setFocusPolicy(Qt.NoFocus)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 6, 0)
        lay.setSpacing(10)
        lay.addWidget(self._dot)
        lay.addWidget(self.combo, 1)
        lay.addWidget(self.refresh_btn)

        # 不在构造时同步执行 adb devices（可能阻塞 1-2 秒，拖慢启动）。
        # 先占位"未连接设备"，由主窗口的异步刷新线程在窗口显示后填充。
        self.set_devices([], last_serial)

    def set_devices(self, devices, last_serial=""):
        prev = self.current_serial()
        self._devices = list(devices)
        self.combo.blockSignals(True)
        self.combo.clear()
        for d in self._devices:
            label = d["serial"]
            if d.get("model"):
                label += f" · {d['model']}"
            if d.get("state") != "device":
                label += f"（{d['state']}）"
            self.combo.addItem(label, d["serial"])
        if not self._devices:
            self.combo.addItem("未连接设备", "")
            self.combo.setEnabled(False)
        else:
            self.combo.setEnabled(True)
            idx = 0
            if prev:
                i = self.combo.findData(prev)
                if i >= 0:
                    idx = i
            elif last_serial:
                i = self.combo.findData(last_serial)
                if i >= 0:
                    idx = i
            self.combo.setCurrentIndex(idx)
        self.combo.blockSignals(False)
        self._update_dot()
        self._on_index_changed()

    def _update_dot(self):
        color = _DOT_ONLINE if self.current_serial() else _DOT_OFFLINE
        self._dot.setStyleSheet(f"border-radius:5px; background:{color};")

    def current_serial(self) -> str:
        """仅当选中设备在线（state==device）时返回其序列号，否则返回空串。"""
        serial = self.combo.currentData() or ""
        for d in self._devices:
            if d["serial"] == serial and d["state"] == "device":
                return serial
        return ""

    def _on_index_changed(self):
        self._update_dot()
        self.device_changed.emit(self.current_serial())
