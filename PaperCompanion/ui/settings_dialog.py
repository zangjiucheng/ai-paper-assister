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
    QComboBox,
    QTextEdit,
    QFrame,
)
from PyQt6.QtCore import Qt
from ..config import (
    get_api_key,
    get_api_base_url,
    get_config_env_path,
    save_api_config,
    get_prompt_override_dir,
    resolve_prompt_path,
    is_prompt_overridden,
    read_prompt_content,
    save_prompt_override,
    list_available_prompt_files,
)


class SettingsDialog(QDialog):
    """应用设置对话框（当前提供API配置）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应用设置")
        self.setModal(True)
        self.setMinimumWidth(760)
        self.setMinimumHeight(680)
        self._init_ui()
        self._load_current_values()
        self._load_prompt_list()

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

        api_button_row = QHBoxLayout()
        api_button_row.addStretch(1)
        self.save_api_button = QPushButton("保存API配置")
        self.save_api_button.clicked.connect(self._save_settings)
        api_button_row.addWidget(self.save_api_button)
        root.addLayout(api_button_row)

        split_line = QFrame()
        split_line.setFrameShape(QFrame.Shape.HLine)
        split_line.setStyleSheet("color: #c5cae9;")
        root.addWidget(split_line)

        prompt_title = QLabel("Prompt 配置")
        prompt_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a237e;")
        root.addWidget(prompt_title)

        selector_row = QHBoxLayout()
        selector_label = QLabel("选择Prompt文件")
        self.prompt_selector = QComboBox()
        self.prompt_selector.currentIndexChanged.connect(self._on_prompt_changed)
        selector_row.addWidget(selector_label)
        selector_row.addWidget(self.prompt_selector, 1)
        root.addLayout(selector_row)

        self.prompt_path_label = QLabel("")
        self.prompt_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.prompt_path_label.setStyleSheet("color: #455a64; font-size: 11px;")
        root.addWidget(self.prompt_path_label)

        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlaceholderText("在此编辑 prompt 内容...")
        self.prompt_editor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #c5cae9;
                border-radius: 8px;
                padding: 8px;
                background: #fafbff;
            }
        """)
        root.addWidget(self.prompt_editor, 1)

        prompt_button_row = QHBoxLayout()
        self.prompt_reload_button = QPushButton("重新加载")
        self.prompt_save_button = QPushButton("保存当前Prompt")
        self.prompt_reload_button.clicked.connect(self._reload_current_prompt)
        self.prompt_save_button.clicked.connect(self._save_current_prompt)
        prompt_button_row.addStretch(1)
        prompt_button_row.addWidget(self.prompt_reload_button)
        prompt_button_row.addWidget(self.prompt_save_button)
        root.addLayout(prompt_button_row)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

    def _load_current_values(self):
        self.base_url_input.setText(get_api_base_url())
        self.api_key_input.setText(get_api_key())

    def _toggle_key_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.api_key_input.setEchoMode(mode)

    def _load_prompt_list(self):
        self.prompt_selector.clear()
        prompt_files = list_available_prompt_files()
        if not prompt_files:
            self.prompt_path_label.setText(
                f"未找到Prompt文件。默认目录或覆盖目录为空。\n覆盖目录：{get_prompt_override_dir()}"
            )
            self.prompt_editor.setPlainText("")
            self.prompt_selector.setEnabled(False)
            self.prompt_save_button.setEnabled(False)
            self.prompt_reload_button.setEnabled(False)
            return

        self.prompt_selector.setEnabled(True)
        self.prompt_save_button.setEnabled(True)
        self.prompt_reload_button.setEnabled(True)
        for prompt_name in prompt_files:
            self.prompt_selector.addItem(prompt_name, prompt_name)

        self.prompt_selector.setCurrentIndex(0)
        self._on_prompt_changed(0)

    def _on_prompt_changed(self, index):
        prompt_name = self._current_prompt_name(index)
        if prompt_name is None:
            return
        active_path = resolve_prompt_path(prompt_name)
        source = "用户覆盖" if is_prompt_overridden(prompt_name) else "默认内置"
        self.prompt_path_label.setText(
            f"来源：{source}\n当前读取：{active_path}\n覆盖目录：{get_prompt_override_dir()}"
        )
        try:
            content = read_prompt_content(prompt_name)
            self.prompt_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"读取 Prompt 失败：{e}")

    def _current_prompt_name(self, index=None):
        idx = self.prompt_selector.currentIndex() if index is None else index
        if idx < 0:
            return None
        data = self.prompt_selector.itemData(idx)
        if not data:
            return None
        return data

    def _reload_current_prompt(self):
        index = self.prompt_selector.currentIndex()
        self._on_prompt_changed(index)

    def _save_current_prompt(self):
        prompt_name = self._current_prompt_name()
        if prompt_name is None:
            QMessageBox.warning(self, "保存失败", "未选择 Prompt 文件。")
            return
        try:
            saved_path = save_prompt_override(prompt_name, self.prompt_editor.toPlainText())
            self._on_prompt_changed(self.prompt_selector.currentIndex())
            QMessageBox.information(self, "保存成功", f"Prompt 已保存到用户目录：\n{saved_path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"写入 Prompt 失败：{e}")

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
