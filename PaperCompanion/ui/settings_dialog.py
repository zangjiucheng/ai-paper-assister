import os
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from ..config import (
    get_api_key,
    get_api_base_url,
    get_config_env_path,
    save_api_config,
)


class SettingsDialog(QDialog):
    """应用设置对话框（当前提供API配置）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应用设置")
        self.setModal(True)
        self.setMinimumWidth(520)
        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("API 配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a237e;")
        root.addWidget(title)

        env_path = QLabel(f"配置文件：{get_config_env_path()}")
        env_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        env_path.setStyleSheet("color: #455a64;")
        root.addWidget(env_path)

        base_url_label = QLabel("API_BASE_URL")
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("例如：https://api.deepseek.com/v1")
        root.addWidget(base_url_label)
        root.addWidget(self.base_url_input)

        api_key_label = QLabel("API_KEY")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("请输入 API Key")
        root.addWidget(api_key_label)
        root.addWidget(self.api_key_input)

        self.show_key_checkbox = QCheckBox("显示 API_KEY")
        self.show_key_checkbox.toggled.connect(self._toggle_key_visibility)
        root.addWidget(self.show_key_checkbox)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.cancel_button = QPushButton("取消")
        self.save_button = QPushButton("保存")
        self.save_button.setDefault(True)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save_settings)
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.save_button)
        root.addLayout(button_row)

    def _load_current_values(self):
        self.base_url_input.setText(get_api_base_url())
        self.api_key_input.setText(get_api_key())

    def _toggle_key_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.api_key_input.setEchoMode(mode)

    def _save_settings(self):
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "保存失败", "API_KEY 不能为空。")
            return
        if not base_url:
            QMessageBox.warning(self, "保存失败", "API_BASE_URL 不能为空。")
            return

        try:
            save_api_config(api_key=api_key, api_base_url=base_url)
            os.environ["API_KEY"] = api_key
            os.environ["API_BASE_URL"] = base_url
            QMessageBox.information(self, "保存成功", "设置已保存，建议重启应用以完全生效。")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"写入配置失败：{e}")
