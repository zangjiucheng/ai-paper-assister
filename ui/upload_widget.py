from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, time, timezone, date
import os

class UploadWidget(QWidget):
    """上传文件窗口类"""
    
    # 定义信号
    upload_file = pyqtSignal(str)  # 上传文件信号，传递文件路径
    pause_processing = pyqtSignal()  # 暂停处理信号
    resume_processing = pyqtSignal()  # 继续处理信号
    
    def __init__(self, parent=None):
        """初始化上传文件窗口"""
        super().__init__(parent)
        self.is_details_expanded = False
        self.setObjectName("uploadWidget")
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 上传按钮框架
        upload_button_frame = self.create_upload_button_frame()
        
        # 上传详情容器
        self.upload_details = self.create_upload_details()
        
        # 添加到主布局
        layout.addWidget(upload_button_frame)
        layout.addWidget(self.upload_details)
        
        # 设置样式
        self.setStyleSheet("""
            #uploadWidget {
                background-color: #e8eaf6;
                border-top: 1px solid #c5cae9;
            }
        """)
        
    def create_upload_button_frame(self):
        """创建上传按钮框架"""
        upload_button_frame = QFrame()
        upload_button_frame.setObjectName("uploadButtonFrame")
        upload_button_frame.setStyleSheet("""
            #uploadButtonFrame {
                background-color: #3f51b5;
                color: white;
            }
        """)
        upload_button_frame.setFixedHeight(40)
        
        upload_button_layout = QHBoxLayout(upload_button_frame)
        upload_button_layout.setContentsMargins(10, 0, 10, 0)
        
        # 上传按钮标题
        self.upload_title = QLabel("上传论文")
        self.upload_title.setFont(QFont("Source Han Sans SC", 11, QFont.Weight.Bold))
        self.upload_title.setStyleSheet("color: white; font-weight: bold;")
        
        # 上传按钮
        self.upload_button = QPushButton("📄")
        self.upload_button.setToolTip("上传论文文件")
        self.upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: white;
                font-size: 16px;
                background-color: transparent;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.upload_button.clicked.connect(self.show_file_dialog)
        
        # 展开按钮
        self.expand_upload_button = QPushButton("▲")
        self.expand_upload_button.setToolTip("显示上传详情")
        self.expand_upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_upload_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: white;
                font-size: 12px;
                background-color: transparent;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.expand_upload_button.clicked.connect(self.toggle_upload_details)
        
        upload_button_layout.addWidget(self.upload_title)
        upload_button_layout.addStretch(1)
        upload_button_layout.addWidget(self.upload_button)
        upload_button_layout.addWidget(self.expand_upload_button)
        
        return upload_button_frame
        
    def create_upload_details(self):
        """创建上传详情容器"""
        upload_details = QFrame()
        upload_details.setObjectName("uploadDetails")
        upload_details.setStyleSheet("""
            #uploadDetails {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }
        """)
        upload_details.setVisible(False)  # 默认隐藏
        upload_details.setMaximumHeight(0)  # 初始高度为0
        
        details_layout = QVBoxLayout(upload_details)
        details_layout.setContentsMargins(10, 10, 10, 10)
        
        # 当前处理文件
        current_file_layout = QHBoxLayout()
        current_file_label = QLabel("当前文件:")
        current_file_label.setStyleSheet("font-weight: bold;")
        self.current_file_name = QLabel("无")
        self.current_file_name.setStyleSheet("color: #1a237e;")
        current_file_layout.addWidget(current_file_label)
        current_file_layout.addWidget(self.current_file_name)
        
        # 当前处理阶段
        stage_layout = QHBoxLayout()
        stage_label = QLabel("处理阶段:")
        stage_label.setStyleSheet("font-weight: bold;")
        self.stage_name = QLabel("无")
        self.stage_name.setStyleSheet("color: #1a237e;")
        stage_layout.addWidget(stage_label)
        stage_layout.addWidget(self.stage_name)
        
        # 处理进度条
        progress_layout = QVBoxLayout()
        progress_bar_label = QLabel("处理进度:")
        progress_bar_label.setStyleSheet("font-weight: bold;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #c5cae9;
                border-radius: 5px;
                text-align: center;
                background-color: #e8eaf6;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #1a237e, stop:1 #3f51b5);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(progress_bar_label)
        progress_layout.addWidget(self.progress_bar)
        
        # 待处理文件
        pending_layout = QHBoxLayout()
        pending_label = QLabel("待处理文件:")
        pending_label.setStyleSheet("font-weight: bold;")
        self.pending_count = QLabel("0")
        self.pending_count.setStyleSheet("color: #1a237e;")
        pending_layout.addWidget(pending_label)
        pending_layout.addWidget(self.pending_count)
        
        # 控制按钮
        controls_layout = QHBoxLayout()
        self.pause_button = QPushButton("暂停")
        self.pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
        """)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.pause_button.setEnabled(False)  # 初始状态下禁用暂停按钮
        
        self.resume_button = QPushButton("继续")
        self.resume_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.resume_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
        """)
        self.resume_button.clicked.connect(self.on_resume_clicked)
        self.resume_button.setEnabled(True)  # 初始状态下启用继续按钮
        
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.resume_button)
        
        # 添加到详情布局
        details_layout.addLayout(current_file_layout)
        details_layout.addLayout(stage_layout)
        details_layout.addLayout(progress_layout)
        details_layout.addLayout(pending_layout)
        details_layout.addLayout(controls_layout)
        
        return upload_details
        
    def toggle_upload_details(self):
        """切换上传详情显示/隐藏状态"""
        self.is_details_expanded = not self.is_details_expanded
        target_height = 200 if self.is_details_expanded else 0  # 设置详情面板高度
        
        # 创建动画
        self.details_animation = QPropertyAnimation(self.upload_details, b"maximumHeight")
        self.details_animation.setDuration(300)
        self.details_animation.setStartValue(0 if self.is_details_expanded else 200)
        self.details_animation.setEndValue(target_height)
        self.details_animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        # 更新按钮文本
        if self.is_details_expanded:
            self.expand_upload_button.setText("▼")
            self.expand_upload_button.setToolTip("隐藏上传详情")
            # 显示详情面板
            self.upload_details.setVisible(True)
        else:
            self.expand_upload_button.setText("▲")
            self.expand_upload_button.setToolTip("显示上传详情")
            # 动画结束后隐藏详情面板
            self.details_animation.finished.connect(
                lambda: self.upload_details.setVisible(False)
            )
        
        # 启动动画
        self.details_animation.start()
        
    def show_file_dialog(self):
        """显示文件选择对话框"""
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要上传的论文PDF文件", "",
            "PDF 文件 (*.pdf)", options=options
        )
        if file_path:
            # 发送上传文件信号
            self.upload_file.emit(file_path)
            # 更新界面 - 暂时显示为"处理中"状态，实际数量将由数据管理器更新
            self.update_upload_status(os.path.basename(file_path), "初始化", 0, "...")
            # 打开上传详情面板
            if not self.is_details_expanded:
                self.toggle_upload_details()
                    
    def update_upload_status(self, file_name, stage, progress, pending_count):
        """更新上传状态"""
        self.current_file_name.setText(file_name)
        self.stage_name.setText(stage)
        
        # 确保进度是整数
        if isinstance(progress, float):
            progress = int(progress)
            
        # 更新进度条
        self.progress_bar.setValue(progress)

        # 更新待处理文件数量
        if pending_count == "...":  # 处理占位符情况
            # 保持当前显示，等待真实更新
            pass
        else:
            self.pending_count.setText(str(pending_count))
        
    def on_pause_clicked(self):
        """暂停处理按钮点击事件"""
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
        # 发送暂停信号
        self.pause_processing.emit()
        
    def on_resume_clicked(self):
        """继续处理按钮点击事件"""
        if not self._is_discount_api_available():
            # 显示一个警告对话框，询问用户是否要继续
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("折扣API不可用")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f5f5f5;
                    font-family: "Source Han Sans SC";
                    font-size: 12px;
                }
                QMessageBox QLabel {
                    color: #1a237e;
                }
                QMessageBox QPushButton {
                    background-color: #3f51b5;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background-color: #303f9f;
                }
            """)
            LOCAL_ZONE = datetime.now().astimezone().tzinfo
            utc_to_local = lambda t: (
                datetime
                .combine(date.today(), t, tzinfo=timezone.utc)  # mark t as UTC
                .astimezone(LOCAL_ZONE)                          # convert to local
                .strftime("%H:%M")                               # format
            )
            msg_box.setText(f"当前折扣API暂不可用（服务时间为当地时间 {utc_to_local(time(16, 30))} 至 {utc_to_local(time(0, 30))}）。您确定要继续吗？")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            response = msg_box.exec()

            if response == QMessageBox.StandardButton.No:
                self.is_paused = False
                self.is_processing = False 
                return
        self.resume_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        # 发送继续信号
        self.resume_processing.emit()
    
    def _is_discount_api_available(self):
        """检查当前折扣API是否可用"""
        # 这里可以添加逻辑来检查当前折扣API的可用性
        # 例如，检查是否有可用的API密钥或是否达到使用限制
        current_time = datetime.now(timezone.utc).time()
        if time(16, 30) <= current_time or current_time <= time(0, 30):
            return True
        return False
        
    def set_title_visible(self, visible):
        """设置标题是否可见"""
        self.upload_title.setVisible(visible)
        
    def close_details_if_open(self):
        """如果详情面板打开，则关闭它"""
        if self.is_details_expanded:
            self.toggle_upload_details()