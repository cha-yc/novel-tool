# -*- coding: utf-8 -*-
"""主窗口 — 竖版窄窗（Material）：顶栏 / 设备胶囊 / 分组分段 / 搜索 / 脚本卡片 / 输出。"""

from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu,
    QMessageBox, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from core.adb import AdbService
from core.logger import AppLogger
from core.store import JsonStore
from ui.device_panel import DevicePanel
from ui.dialogs import GroupDialog, ScriptEditDialog
from ui.icons import DARK_TEXT, LIGHT_TEXT, NEUTRAL, WHITE, svg_icon
from ui.output_panel import OutputPanel
from ui.pills import GroupPills
from ui.script_list import ScriptList
from ui.settings_dialog import SettingsDialog
from ui.theme import apply_theme


class DeviceRefreshThread(QThread):
    """后台刷新设备列表，避免阻塞界面（秒开）。"""

    devices_ready = Signal(list)

    def __init__(self, adb: AdbService, parent=None):
        super().__init__(parent)
        self._adb = adb

    def run(self):
        self.devices_ready.emit(self._adb.list_devices())


class ExecThread(QThread):
    """后台执行命令，逐行回传输出。"""

    line_out = Signal(str)
    exec_finished = Signal(int)

    def __init__(self, adb: AdbService, command: str, serial: str, parent=None):
        super().__init__(parent)
        self._adb = adb
        self._command = command
        self._serial = serial

    def run(self):
        code = self._adb.run(self._command, self._serial, output_cb=self.line_out.emit)
        self.exec_finished.emit(code)


# 识别"输出其实失败了"的关键词（adb 返回码常为 0，但消息提示失败）
ERROR_KEYWORDS = (
    "error", "failed", "failure", "cannot", "can not", "not permitted",
    "denied", "unable", "exception", "no such", "not found", "not allowed",
    "not supported", "refused", "错误", "失败", "无法", "不能",
)


def looks_error(line: str) -> bool:
    low = line.lower()
    return any(k in low for k in ERROR_KEYWORDS)


class MainWindow(QMainWindow):
    """ADB 脚本工具主窗口（竖版窄窗，方便边看设备边操作）。"""

    def __init__(self, data_dir, logger=None, log_dir=None, app_logger=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADB 脚本工具")
        self.resize(400, 760)
        self.setMinimumSize(340, 560)
        self._logger = logger or AppLogger.get()
        self._store = JsonStore(data_dir)
        self._adb = AdbService()
        self._data_dir = Path(data_dir)
        self._log_dir = Path(log_dir) if log_dir else self._data_dir.parent / "logs"
        self._app_logger = app_logger
        self._scripts = []
        self._current_set = ""
        self._exec_thread = None
        self._run_index = -1

        script_set = self._store.load_script_set()
        self._settings = script_set["settings"]
        self._theme = self._settings.get("theme", "dark")
        apply_theme(QApplication.instance(), self._theme)
        self._text_icon = DARK_TEXT if self._theme == "dark" else LIGHT_TEXT

        # ---------- 顶栏 ----------
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        title = QLabel("ADB 脚本工具")
        tf = title.font()
        tf.setPointSize(15)
        tf.setBold(True)
        title.setFont(tf)
        self._theme_btn = QToolButton()
        self._theme_btn.setFocusPolicy(Qt.NoFocus)
        self._theme_btn.setToolTip("切换深浅主题")
        self._update_theme_icon()
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._settings_btn = QToolButton()
        self._settings_btn.setFocusPolicy(Qt.NoFocus)
        self._settings_btn.setIcon(svg_icon("gear", self._text_icon, 20))
        self._settings_btn.setToolTip("设置")
        self._settings_btn.clicked.connect(self._open_settings)
        title_bar.addWidget(title)
        title_bar.addStretch(1)
        title_bar.addWidget(self._settings_btn)
        title_bar.addWidget(self._theme_btn)

        # ---------- 设备胶囊 ----------
        self._device_panel = DevicePanel(
            self._adb, last_serial=self._settings.get("last_device", ""))
        self._device_panel.device_changed.connect(self._on_device_changed)

        # ---------- 分组胶囊 ----------
        group_row = QHBoxLayout()
        group_row.setContentsMargins(0, 0, 0, 0)
        group_row.setSpacing(0)
        self._pills = GroupPills()
        self._pills.group_changed.connect(self._on_group_picked)
        self._pills.context_requested.connect(self._on_group_menu)
        self._pills.add_requested.connect(self._new_group)
        group_row.addWidget(self._pills, 1)

        # ---------- 搜索 + 添加脚本 ----------
        tool_row = QHBoxLayout()
        tool_row.setContentsMargins(0, 0, 0, 0)
        tool_row.setSpacing(8)
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索脚本…")
        self._search.setClearButtonEnabled(True)
        self._search.addAction(svg_icon("search", NEUTRAL, 16), QLineEdit.LeadingPosition)
        self._search.textChanged.connect(self._apply_filter)
        self._add_btn = QPushButton("添加脚本")
        self._add_btn.setObjectName("primary")
        self._add_btn.setIcon(svg_icon("plus", WHITE, 18))
        self._add_btn.setFocusPolicy(Qt.NoFocus)
        self._add_btn.clicked.connect(lambda: self._add_script())
        tool_row.addWidget(self._search, 1)
        tool_row.addWidget(self._add_btn)

        # ---------- 脚本卡片列表 ----------
        self._list = ScriptList(self._settings.get("long_press_ms", 600))
        self._list.execute_index.connect(self._on_execute)
        self._list.edit_index.connect(self._edit_script)
        self._list.reordered.connect(self._on_reordered)
        self._list.context_index.connect(self._on_script_menu)

        # ---------- 输出面板 ----------
        self._output = OutputPanel()

        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(12, 8, 12, 10)
        v.setSpacing(8)
        v.addLayout(title_bar)
        v.addWidget(self._device_panel)
        v.addLayout(group_row)
        v.addLayout(tool_row)
        # 脚本列表自动占满剩余空间；输出区可折叠，收起时归还空间
        v.addWidget(self._list, 1)
        v.addWidget(self._output)
        self.setCentralWidget(central)

        # ---------- 数据 ----------
        self._rebuild_groups()
        # 设备刷新延后到窗口显示后再启动（避免显示瞬间后台线程/更新造成二次闪烁）
        QTimer.singleShot(0, self._refresh_devices)

    def event(self, e):
        """窗口失焦时取消拖拽，避免对话框/切窗口后拖拽状态卡死。"""
        if e.type() == QEvent.WindowDeactivate:
            self._list.cancel_drag()
        return super().event(e)

    # ================= 主题 =================

    def _update_theme_icon(self):
        name = "sun" if self._theme == "dark" else "moon"
        self._theme_btn.setIcon(svg_icon(name, self._text_icon, 22))

    def _toggle_theme(self):
        self._theme = "light" if self._theme == "dark" else "dark"
        self._settings["theme"] = self._theme
        self._store.save_script_set()
        self._text_icon = DARK_TEXT if self._theme == "dark" else LIGHT_TEXT
        apply_theme(QApplication.instance(), self._theme)
        self._update_theme_icon()
        self._repolish_tree()  # 修复 QScrollArea 内部控件不随主题刷新（QTBUG-25374）

    def _repolish_tree(self):
        """主题切换后强制全树重新抛光，避免滚动条/胶囊残留旧主题颜色。"""
        def _polish(w):
            w.style().unpolish(w)
            w.style().polish(w)
        _polish(self)
        for w in self.findChildren(QWidget):
            _polish(w)

    # ================= 设置 =================

    def _open_settings(self):
        self._list.cancel_drag()
        dlg = SettingsDialog(self._settings, self._data_dir, self._log_dir, self)
        if dlg.exec():
            vals = dlg.values()
            self._settings.update(vals)
            self._store.save_script_set()
            if self._app_logger is not None:
                self._app_logger.reconfigure(**vals)
            self._logger.info("设置已保存: %s", vals)

    # ================= 分组 =================

    def _rebuild_groups(self):
        script_set = self._store.load_script_set()
        groups = [(s["name"], len(self._store.load_scripts(s["name"])))
                  for s in script_set["sets"]]
        current = script_set["current_set"]
        self._pills.set_groups(groups, current)
        self._current_set = current if current in [n for n, _ in groups] else ""
        self._load_scripts()

    def _refresh_group_counts(self):
        self._rebuild_groups()

    def _on_group_picked(self, name):
        self._current_set = name
        self._store.switch_set(name)
        self._load_scripts()

    def _on_group_menu(self, name, gpos):
        menu = QMenu(self)
        new_act = menu.addAction("新建分组")
        rename_act = menu.addAction("重命名分组")
        del_act = menu.addAction("删除分组")
        act = menu.exec(gpos)
        if act == new_act:
            self._new_group()
        elif act == rename_act:
            self._rename_group(name)
        elif act == del_act:
            self._delete_group(name)

    def _new_group(self):
        self._list.cancel_drag()
        name = GroupDialog.get_name("新建分组", parent=self)
        if not name:
            return
        if not self._store.create_group(name):
            QMessageBox.information(self, "提示", f"分组「{name}」已存在。")
            return
        self._rebuild_groups()

    def _rename_group(self, name):
        self._list.cancel_drag()
        sets = self._store.load_script_set()["sets"]
        if name not in [s["name"] for s in sets]:
            return
        new = GroupDialog.get_name("重命名分组", name, self)
        if not new or new == name:
            return
        if not self._store.rename_group(name, new):
            QMessageBox.information(self, "提示", f"分组「{new}」已存在。")
            return
        self._rebuild_groups()

    def _delete_group(self, name):
        self._list.cancel_drag()
        sets = self._store.load_script_set()["sets"]
        if name not in [s["name"] for s in sets]:
            return
        count = len(self._store.load_scripts(name))
        ret = QMessageBox.question(
            self, "删除分组",
            f"确定删除分组「{name}」吗？\n（含 {count} 条脚本，将永久删除，不可恢复）",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            self._store.delete_group(name)
            self._rebuild_groups()

    # ================= 脚本 =================

    def _load_scripts(self):
        self._scripts = self._store.load_scripts(self._current_set) if self._current_set else []
        self._list.set_scripts(self._scripts)

    def _next_id(self) -> int:
        ids = [s.get("id", 0) for s in self._scripts]
        return (max(ids) + 1) if ids else 1

    def _add_script(self, data=None, mode="new"):
        self._list.cancel_drag()
        dlg = ScriptEditDialog(data, mode, self)
        if not dlg.exec():
            return
        d = dlg.data()
        if not d["name"]:
            QMessageBox.warning(self, "提示", "脚本名称不能为空。")
            return
        d["id"] = self._next_id()
        self._scripts.append(d)
        self._store.save_scripts(self._current_set, self._scripts)
        self._load_scripts()
        self._refresh_group_counts()

    def _edit_script(self, index):
        if not (0 <= index < len(self._scripts)):
            return
        self._list.cancel_drag()
        dlg = ScriptEditDialog(self._scripts[index], self)
        if not dlg.exec():
            return
        d = dlg.data()
        if not d["name"]:
            QMessageBox.warning(self, "提示", "脚本名称不能为空。")
            return
        d["id"] = self._scripts[index].get("id")
        self._scripts[index] = d
        self._store.save_scripts(self._current_set, self._scripts)
        self._load_scripts()

    def _delete_script(self, index):
        if not (0 <= index < len(self._scripts)):
            return
        name = self._scripts[index].get("name", "")
        ret = QMessageBox.question(
            self, "删除脚本", f"确定删除脚本「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            self._scripts.pop(index)
            self._store.save_scripts(self._current_set, self._scripts)
            self._load_scripts()
            self._refresh_group_counts()

    def _move_script(self, index, delta):
        target = index + delta
        if not (0 <= index < len(self._scripts) and 0 <= target < len(self._scripts)):
            return
        item = self._scripts.pop(index)
        self._scripts.insert(target, item)
        self._store.save_scripts(self._current_set, self._scripts)
        self._load_scripts()
        self._list.setCurrentRow(target)

    def _on_script_menu(self, index, gpos):
        if not (0 <= index < len(self._scripts)):
            return
        menu = QMenu(self)
        edit_act = menu.addAction("编辑")
        copy_act = menu.addAction("复制")
        up_act = menu.addAction("上移")
        down_act = menu.addAction("下移")
        menu.addSeparator()
        del_act = menu.addAction("删除")
        act = menu.exec(gpos)
        if act == edit_act:
            self._edit_script(index)
        elif act == copy_act:
            self._add_script(dict(self._scripts[index]), mode="copy")
        elif act == up_act:
            self._move_script(index, -1)
        elif act == down_act:
            self._move_script(index, 1)
        elif act == del_act:
            self._delete_script(index)

    def _on_reordered(self, src, dst):
        """拖拽落位：更新数据、保存，并按数据重建列表（杜绝空白/消失）。"""
        if not (0 <= src < len(self._scripts) and 0 <= dst <= len(self._scripts)):
            return
        item = self._scripts.pop(src)
        self._scripts.insert(dst, item)
        self._store.save_scripts(self._current_set, self._scripts)
        self._load_scripts()
        self._list.setCurrentRow(min(dst, self._list.count() - 1))
        self._logger.info("分组 %s 排序变更: %d -> %d", self._current_set, src, dst)

    def _apply_filter(self, text):
        text = text.strip().lower()
        active = bool(text)
        self._list.set_drag_enabled(not active)
        for i in range(self._list.count()):
            script = self._scripts[i] if i < len(self._scripts) else {}
            match = (text in script.get("name", "").lower()
                     or text in script.get("command", "").lower())
            self._list.item(i).setHidden(not match)

    # ================= 设备 =================

    def _on_device_changed(self, serial):
        if self._settings.get("last_device") != serial:
            self._settings["last_device"] = serial
            self._store.save_script_set()
        self._output.switch_to(serial)

    def _refresh_devices(self):
        old = getattr(self, "_device_thread", None)
        if old is not None and old.isRunning():
            return  # 上次刷新还在进行：忽略重复点击，避免线程被覆盖销毁而崩溃
        self._device_thread = DeviceRefreshThread(self._adb)
        self._device_thread.devices_ready.connect(self._on_devices_ready)
        self._device_thread.start()

    def _on_devices_ready(self, devices):
        self._device_panel.set_devices(
            devices, last_serial=self._settings.get("last_device", ""))

    # ================= 执行 =================

    def _on_execute(self, index):
        if not (0 <= index < len(self._scripts)):
            return
        script = self._scripts[index]
        serial = self._device_panel.current_serial()
        if not serial:
            QMessageBox.warning(self, "提示", "没有可用的在线设备。\n请连接设备后点击「刷新」。")
            return
        cmd = script.get("command", "")
        if not cmd:
            QMessageBox.warning(self, "提示", f"脚本「{script.get('name', '')}」没有命令。")
            return

        # 收起日志时不自动展开：输出仍写入对应设备的 Tab，用户可自行展开查看
        self._output.ensure_tab(serial, serial)
        self._output.switch_to(serial)
        self._output.append(serial, f"\n▶ [{script.get('name', '')}] {cmd}")
        self._logger.info("执行 [%s] 于 %s", script.get("name", ""), serial)

        # 该卡片显示旋转动画，作为执行反馈
        self._run_index = index
        self._list.set_running_row(index)

        self._run_serial = serial
        self._run_lines = []
        self._exec_thread = ExecThread(self._adb, cmd, serial)
        self._exec_thread.line_out.connect(self._on_exec_line)
        self._exec_thread.exec_finished.connect(self._on_exec_finished)
        self._exec_thread.start()

    def _on_exec_line(self, line):
        """逐行输出：疑似错误内容标红，其余默认色。"""
        color = "#FF5F57" if looks_error(line) else None
        self._output.append(self._run_serial, line, color)
        self._run_lines.append(line)

    def _on_exec_finished(self, code):
        """按退出码 + 输出内容综合判断结果，避免退出码 0 但实际失败被误判成功。"""
        # 停止执行动画反馈
        self._run_index = -1
        self._list.set_running_row(-1)
        failed = (code != 0) or any(looks_error(l) for l in self._run_lines)
        if failed:
            self._output.append(
                self._run_serial,
                f"  ✗ 未成功 · 退出码 {code}",
                "#FF5F57")
        else:
            self._output.append(
                self._run_serial, f"  ✓ 成功 · 退出码 {code}", "#34C759")

    def closeEvent(self, e):
        """干净退出：短等待后台线程结束；停不下的（如 adb 无响应）交给 main 兜底强制退出。"""
        for t in (getattr(self, "_device_thread", None),
                  getattr(self, "_exec_thread", None)):
            if t is not None and t.isRunning():
                t.wait(1500)
        super().closeEvent(e)
