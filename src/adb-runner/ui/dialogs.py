# -*- coding: utf-8 -*-
"""管理对话框：脚本编辑 / 分组命名。"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QToolButton, QVBoxLayout,
)

# 脚本语法说明（工具层解析 sleep/注释/分行；单行内的 &、&& 及
# adb shell "..." 引号内的 for/if 交给 shell，详见 core/adb.py 模块文档）
SYNTAX_HELP = """执行规则
• 每行一条命令，按顺序执行；任一步退出码非 0，立即停止后续步骤
• 命令里的 adb 会自动替换为 adb -s <当前设备序列号>

本工具处理（执行前解析，不进入 shell）
• sleep 2 / wait 1.5 / 等待 2 —— 步骤间等待 N 秒（支持小数）
• # 开头的行、空行 —— 注释，跳过

单行内写多条（交给电脑的 cmd 处理）
• 命令A & 命令B —— 顺序执行，A 的成败不影响 B
• 命令A && 命令B —— A 成功才执行 B

循环 / 条件：不单独造语法，直接写 shell 原生写法，例如
adb shell "for i in 1 2 3; do input tap 100 200; sleep 1; done"
（引号内的 for/if/sleep 在手机端 shell 中执行）"""


class SyntaxHelpDialog(QDialog):
    """脚本语法说明：内容可选中（长按/拖选后 Ctrl+C 或右键复制），另有一键复制全部。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("脚本语法说明")
        self.setMinimumSize(430, 400)

        text = QPlainTextEdit(SYNTAX_HELP)
        text.setReadOnly(True)
        # 允许鼠标选中复制（只读框默认可选中，显式声明意图）
        text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        copy_btn = QPushButton("复制全部")
        copy_btn.clicked.connect(self._copy_all)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addWidget(copy_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)

        lay = QVBoxLayout(self)
        lay.addWidget(text, 1)
        lay.addLayout(btn_row)

    def _copy_all(self):
        QGuiApplication.clipboard().setText(SYNTAX_HELP)
        copy_btn = self.sender()
        if isinstance(copy_btn, QPushButton):
            copy_btn.setText("已复制")
            QTimer.singleShot(1500, lambda: copy_btn.setText("复制全部"))


class ScriptEditDialog(QDialog):
    """新建 / 编辑 / 复制 脚本。mode: new | edit | copy。

    复制模式与编辑模式视觉区分：橙色横幅 + 专属标题，
    用户一眼可辨"保存后会新增一条脚本"，避免与修改原脚本混淆。
    """

    # 复制模式的横幅配色（深浅主题通用，橙色高辨识度）
    _COPY_BANNER = (
        "color:#FFA726; border-left:3px solid #FFA726; background:transparent;"
        "padding:6px 10px; font-size:12px;"
    )
    _TITLES = {"new": "新建脚本", "edit": "编辑脚本", "copy": "复制脚本"}

    def __init__(self, script=None, mode="new", parent=None):
        super().__init__(parent)
        mode = mode if mode in self._TITLES else "new"
        self.setWindowTitle(self._TITLES[mode])
        self.setMinimumWidth(380)
        s = script or {}

        form = QFormLayout()
        form.setSpacing(8)
        self.name = QLineEdit(s.get("name", ""))
        self.name.setPlaceholderText("脚本名称，如：root")
        self.command = QPlainTextEdit(s.get("command", ""))
        self.command.setPlaceholderText(
            "adb 命令；每行一条按顺序执行，任一步失败即停止\n"
            "行内可用 &、&& 连接；sleep 2 插入等待（秒）；# 为注释")
        self.category = QLineEdit(s.get("category", ""))
        self.category.setPlaceholderText("分类（可留空），如：泊车类")
        self.description = QLineEdit(s.get("description", ""))
        self.description.setPlaceholderText("备注说明（可选）")

        form.addRow("名称", self.name)
        form.addRow("命令", self.command)
        form.addRow("分类", self.category)
        form.addRow("备注", self.description)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        if mode == "copy":
            btns.button(QDialogButtonBox.Ok).setText("保存为新脚本")
        else:
            btns.button(QDialogButtonBox.Ok).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        # 底部行：语法说明靠左（帮助类操作惯例位置，不挤占表单标签列）
        help_btn = QToolButton()
        help_btn.setText("语法说明")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setToolTip("查看脚本语法与示例（内容可复制）")
        help_btn.clicked.connect(lambda: SyntaxHelpDialog(self).exec())
        bottom = QHBoxLayout()
        bottom.addWidget(help_btn)
        bottom.addStretch(1)
        bottom.addWidget(btns)

        layout = QVBoxLayout(self)
        if mode == "copy":
            banner = QLabel("复制模式：保存后将在列表末尾新增一条脚本，原脚本保持不变")
            banner.setWordWrap(True)
            banner.setStyleSheet(self._COPY_BANNER)
            layout.addWidget(banner)
        layout.addLayout(form)
        layout.addLayout(bottom)

    def data(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "command": self.command.toPlainText().strip(),
            "category": self.category.text().strip(),
            "description": self.description.text().strip(),
        }


class GroupDialog(QDialog):
    """新建 / 重命名分组。"""

    def __init__(self, title="新建分组", initial="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(280)
        self.name = QLineEdit(initial)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("确定")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("分组名称:"))
        layout.addWidget(self.name)
        layout.addWidget(btns)

    @staticmethod
    def get_name(title="新建分组", initial="", parent=None):
        dlg = GroupDialog(title, initial, parent)
        if dlg.exec() == QDialog.Accepted and dlg.name.text().strip():
            return dlg.name.text().strip()
        return None
