# -*- coding: utf-8 -*-
"""Material 风格深浅主题 QSS + 运行时颜色查询。"""

DARK = """
QMainWindow, QDialog {
    background-color: #121212; color: #ECECEC;
}
QWidget {
    color: #ECECEC; font-size: 13px; font-family: "Microsoft YaHei", "Segoe UI", "PingFang SC";
}
QLabel { color: #ECECEC; background: transparent; }
QLabel#idx { color: #9AA0A6; font-size: 12px; font-weight: 600; }
QLabel#row_preview { color: #9AA0A6; font-size: 11px; background: transparent; }
QLabel#row_name { color: #ECECEC; font-size: 14px; font-weight: 600; background: transparent; }
QLabel#tag {
    background: #2A4A80; color: #9CC0FF; border-radius: 8px; padding: 1px 7px;
    font-size: 10px; font-weight: 600;
}
QLineEdit, QPlainTextEdit {
    background-color: #262626; border: 1px solid #2E2E2E; border-radius: 14px;
    padding: 8px 12px; color: #ECECEC; selection-background-color: #4F8CFF;
}
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #4F8CFF; }
QComboBox, QComboBox QAbstractItemView {
    background-color: #262626; border: 1px solid #2E2E2E; border-radius: 12px;
    padding: 6px 10px; color: #ECECEC; selection-background-color: #4F8CFF;
}
QPushButton {
    background-color: #262626; border: 1px solid #2E2E2E; border-radius: 12px;
    padding: 8px 14px; color: #ECECEC;
}
QPushButton:hover { background-color: #313131; }
QPushButton:pressed { background-color: #1E1E1E; }
QPushButton#primary {
    background-color: #4F8CFF; border: none; border-radius: 14px; color: #FFFFFF; padding: 8px 16px;
}
QPushButton#primary:hover { background-color: #6B9EFF; }
QPushButton#play {
    background-color: #4F8CFF; border: none; border-radius: 18px;
    min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 0;
}
QPushButton#play:hover { background-color: #6B9EFF; }
QToolButton { background: transparent; border: none; border-radius: 50%; color: #ECECEC; padding: 6px; }
QToolButton:hover { background: rgba(255,255,255,0.08); }
QToolButton#addGroup { border-radius: 10px; color: #9AA0A6; font-size: 18px; font-weight: 600; }
QToolButton#addGroup:hover { color: #ECECEC; background: #262626; }
QListWidget { background-color: transparent; border: none; outline: none; padding: 2px; }
QListWidget::item { border-radius: 16px; border: 1px solid transparent; }
QListWidget::item:selected { background: rgba(79,140,255,0.10); border: 1px solid rgba(79,140,255,0.45); }
QScrollBar:vertical { background: transparent; width: 6px; margin: 2px; }
QScrollBar::handle:vertical { background: #444444; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { background: transparent; height: 6px; margin: 2px; }
QScrollBar::handle:horizontal { background: #444444; border-radius: 3px; min-width: 30px; }
QMenu {
    background-color: #262626; border: 1px solid #2E2E2E; border-radius: 12px; padding: 6px;
}
QMenu::item { padding: 8px 16px; border-radius: 8px; color: #ECECEC; }
QMenu::item:selected { background-color: #4F8CFF; color: #FFFFFF; }
QMenu::separator { height: 1px; background: #2E2E2E; margin: 6px 8px; }
QToolTip { background-color: #313131; color: #ECECEC; border: 1px solid #2E2E2E; padding: 6px; }
QTabBar::tab {
    background: #1E1E1E; border: 1px solid #2E2E2E; border-radius: 999px;
    padding: 7px 14px; margin-right: 6px; color: #9AA0A6; font-weight: 600;
}
QTabBar::tab:selected { background: #4F8CFF; border-color: #4F8CFF; color: #FFFFFF; }
QTabBar QToolButton { background: #262626; border: none; border-radius: 8px; }
QTabBar QToolButton:hover { background: #313131; }
QTabWidget::pane { border: none; top: -1px; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; border: none; }
/* 脚本卡片：圆角 + 描边 + hover + 选中 */
ScriptItemWidget {
    background-color: #1E1E1E; border: 1px solid #2E2E2E; border-radius: 16px;
}
ScriptItemWidget:hover { background-color: #242424; border-color: #3A3A3A; }
ScriptItemWidget[selected="true"] {
    background-color: rgba(79,140,255,0.08); border: 1px solid #4F8CFF;
}
/* 设备胶囊容器 */
QWidget#deviceCapsule {
    background-color: #1E1E1E; border: 1px solid #2E2E2E; border-radius: 16px;
}
/* 分组胶囊 */
QPushButton#pill {
    background-color: #1E1E1E; border: 1px solid #2E2E2E; border-radius: 999px;
    padding: 7px 16px; color: #9AA0A6; font-weight: 600;
}
QPushButton#pill:hover { color: #ECECEC; border-color: #4F8CFF; }
QPushButton#pill:checked {
    background-color: #4F8CFF; border-color: #4F8CFF; color: #FFFFFF;
}
QPushButton#pillAdd {
    background: transparent; border: 1px dashed #3A3A3A; border-radius: 999px;
    padding: 7px 14px; color: #9AA0A6; font-size: 15px; font-weight: 600;
}
QPushButton#pillAdd:hover { color: #ECECEC; border-color: #4F8CFF; }
QPushButton#pillNav {
    background: transparent; border: 1px solid #2E2E2E; border-radius: 13px;
    color: #9AA0A6; font-size: 15px; font-weight: 700;
}
QPushButton#pillNav:hover:enabled { color: #ECECEC; border-color: #4F8CFF; }
QPushButton#pillNav:disabled { color: #4A4A4A; border-color: #2A2A2A; }
/* 设备胶囊内下拉透明，融入胶囊（统一感） */
QWidget#deviceCapsule QComboBox {
    background: transparent; border: none; padding: 2px 4px; color: #ECECEC;
}
QWidget#deviceCapsule QComboBox::drop-down { border: none; width: 20px; }
/* 输出区设备 Tab：小型中性标签，避免大块蓝色 */
QTabWidget#outputTabs QTabBar::tab {
    background: transparent; border: none; border-radius: 8px;
    padding: 4px 10px; color: #9AA0A6; font-weight: 600;
}
QTabWidget#outputTabs QTabBar::tab:selected { background: #2A2A2A; color: #ECECEC; }
QTabWidget#outputTabs QTabBar::tab:hover { color: #ECECEC; }
"""

LIGHT = """
QMainWindow, QDialog {
    background-color: #F4F5F7; color: #111827;
}
QWidget {
    color: #111827; font-size: 13px; font-family: "Microsoft YaHei", "Segoe UI", "PingFang SC";
}
QLabel { color: #111827; background: transparent; }
QLabel#idx { color: #6B7280; font-size: 12px; font-weight: 600; }
QLabel#row_preview { color: #6B7280; font-size: 11px; background: transparent; }
QLabel#row_name { color: #111827; font-size: 14px; font-weight: 600; background: transparent; }
QLabel#tag {
    background: #E3EDFB; color: #1E88E5; border-radius: 8px; padding: 1px 7px;
    font-size: 10px; font-weight: 600;
}
QLineEdit, QPlainTextEdit {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px;
    padding: 8px 12px; color: #111827; selection-background-color: #1E88E5;
}
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #1E88E5; }
QComboBox, QComboBox QAbstractItemView {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
    padding: 6px 10px; color: #111827; selection-background-color: #1E88E5;
}
QPushButton {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
    padding: 8px 14px; color: #111827;
}
QPushButton:hover { background-color: #F1F3F5; }
QPushButton:pressed { background-color: #E9ECEF; }
QPushButton#primary {
    background-color: #1E88E5; border: none; border-radius: 14px; color: #FFFFFF; padding: 8px 16px;
}
QPushButton#primary:hover { background-color: #3B9AF2; }
QPushButton#play {
    background-color: #1E88E5; border: none; border-radius: 18px;
    min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 0;
}
QPushButton#play:hover { background-color: #3B9AF2; }
QToolButton { background: transparent; border: none; border-radius: 50%; color: #111827; padding: 6px; }
QToolButton:hover { background: rgba(17,24,39,0.08); }
QToolButton#addGroup { border-radius: 10px; color: #6B7280; font-size: 18px; font-weight: 600; }
QToolButton#addGroup:hover { color: #111827; background: #F1F3F5; }
QListWidget { background-color: transparent; border: none; outline: none; padding: 2px; }
QListWidget::item { border-radius: 16px; border: 1px solid transparent; }
QListWidget::item:selected { background: rgba(30,136,229,0.10); border: 1px solid rgba(30,136,229,0.45); }
QScrollBar:vertical { background: transparent; width: 6px; margin: 2px; }
QScrollBar::handle:vertical { background: #D3D7DE; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { background: transparent; height: 6px; margin: 2px; }
QScrollBar::handle:horizontal { background: #D3D7DE; border-radius: 3px; min-width: 30px; }
QMenu {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 6px;
}
QMenu::item { padding: 8px 16px; border-radius: 8px; color: #111827; }
QMenu::item:selected { background-color: #1E88E5; color: #FFFFFF; }
QMenu::separator { height: 1px; background: #E5E7EB; margin: 6px 8px; }
QToolTip { background-color: #FFFFFF; color: #111827; border: 1px solid #E5E7EB; padding: 6px; }
QTabBar::tab {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 999px;
    padding: 7px 14px; margin-right: 6px; color: #6B7280; font-weight: 600;
}
QTabBar::tab:selected { background: #1E88E5; border-color: #1E88E5; color: #FFFFFF; }
QTabBar QToolButton { background: #FFFFFF; border: none; border-radius: 8px; }
QTabBar QToolButton:hover { background: #F1F3F5; }
QTabWidget::pane { border: none; top: -1px; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; border: none; }
/* 脚本卡片：圆角 + 描边 + hover + 选中 */
ScriptItemWidget {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px;
}
ScriptItemWidget:hover { background-color: #F7F9FC; border-color: #CBD5E1; }
ScriptItemWidget[selected="true"] {
    background-color: rgba(30,136,229,0.06); border: 1px solid #1E88E5;
}
/* 设备胶囊容器 */
QWidget#deviceCapsule {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px;
}
/* 分组胶囊 */
QPushButton#pill {
    background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 999px;
    padding: 7px 16px; color: #374151; font-weight: 600;
}
QPushButton#pill:hover { color: #111827; border-color: #1E88E5; }
QPushButton#pill:checked {
    background-color: #1E88E5; border-color: #1E88E5; color: #FFFFFF;
}
QPushButton#pillAdd {
    background: transparent; border: 1px dashed #C7CDD6; border-radius: 999px;
    padding: 7px 14px; color: #6B7280; font-size: 15px; font-weight: 600;
}
QPushButton#pillAdd:hover { color: #111827; border-color: #1E88E5; }
QPushButton#pillNav {
    background: transparent; border: 1px solid #E5E7EB; border-radius: 13px;
    color: #6B7280; font-size: 15px; font-weight: 700;
}
QPushButton#pillNav:hover:enabled { color: #111827; border-color: #1E88E5; }
QPushButton#pillNav:disabled { color: #C7CDD6; border-color: #F0F1F3; }
/* 设备胶囊内下拉透明，融入胶囊（统一感） */
QWidget#deviceCapsule QComboBox {
    background: transparent; border: none; padding: 2px 4px; color: #111827;
}
QWidget#deviceCapsule QComboBox::drop-down { border: none; width: 20px; }
/* 输出区设备 Tab：小型中性标签，避免大块蓝色 */
QTabWidget#outputTabs QTabBar::tab {
    background: transparent; border: none; border-radius: 8px;
    padding: 4px 10px; color: #6B7280; font-weight: 600;
}
QTabWidget#outputTabs QTabBar::tab:selected { background: #E9ECEF; color: #111827; }
QTabWidget#outputTabs QTabBar::tab:hover { color: #111827; }
"""

_COLORS = {
    "dark": {"accent": "#4F8CFF", "surface": "#1E1E1E", "surface2": "#262626",
             "border": "#2E2E2E", "text": "#ECECEC", "sub": "#9AA0A6"},
    "light": {"accent": "#1E88E5", "surface": "#FFFFFF", "surface2": "#F1F3F5",
              "border": "#E5E7EB", "text": "#111827", "sub": "#6B7280"},
}

CURRENT = "dark"


def set_theme(name):
    """记录当前主题名，供动态样式（拖拽托起等）取色。"""
    global CURRENT
    CURRENT = name if name in _COLORS else "dark"


def color(key):
    return _COLORS[CURRENT][key]


def apply_theme(app, name="dark"):
    set_theme(name)
    app.setStyleSheet(DARK if name == "dark" else LIGHT)
