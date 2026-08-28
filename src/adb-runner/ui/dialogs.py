# -*- coding: utf-8 -*-
"""管理对话框：脚本编辑 / 分组命名。"""

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QPlainTextEdit, QVBoxLayout,
)


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
        self.command.setPlaceholderText("adb 命令，可用 &、&& 连接多条")
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

        layout = QVBoxLayout(self)
        if mode == "copy":
            banner = QLabel("复制模式：保存后将在列表末尾新增一条脚本，原脚本保持不变")
            banner.setWordWrap(True)
            banner.setStyleSheet(self._COPY_BANNER)
            layout.addWidget(banner)
        layout.addLayout(form)
        layout.addWidget(btns)

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
