# -*- coding: utf-8 -*-
"""管理对话框：脚本编辑 / 分组命名。"""

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QPlainTextEdit, QVBoxLayout,
)


class ScriptEditDialog(QDialog):
    """新建 / 编辑脚本。"""

    def __init__(self, script=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑脚本" if script else "新建脚本")
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
        btns.button(QDialogButtonBox.Ok).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
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
