from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QScrollArea, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve

# 导入自定义组件和工具类
from ..paths import get_asset_path
from .message_bubble import MessageBubble, LoadingBubble
from ..AI_manager import AIManager

class ChatWidget(QWidget):
    """
    AI对话框组件
    
    提供用户与AI助手进行对话的界面，包括消息显示、输入框和控制按钮
    """
    # 颜色常量定义
    COLOR_UNINIT = "#9E9E9E"  # 灰色：未初始化
    COLOR_INIT = "#2196F3"    # 蓝色：初始化完成未激活
    COLOR_ACTIVE = "#4CAF50"  # 绿色：激活待命
    COLOR_VAD = "#FFC107"     # 黄色：检测到语音活动
    COLOR_ERROR = "red"       # 红色：错误状态

    def __init__(self, parent=None):
        """初始化聊天组件"""
        super().__init__(parent)
        self.ai_controller = None  # AI控制器引用
        self.paper_controller = None  # 论文控制器引用
        self.loading_bubble = None  # 加载动画引用
        self.is_voice_active = False  # 语音功能是否激活

        self.collapsed_width = 100
        self.expanded_width = 450  # 减小侧边栏宽度
        self.is_expanded = True
        self.setMaximumWidth(self.expanded_width)  # 设置最大宽度
        
        # 初始化UI
        self.init_ui()
        
        # 界面显示后立即初始化语音功能
        # QTimer.singleShot(500, self.init_voice_recognition)
        
    def set_ai_controller(self, ai_controller:AIManager):
        """设置AI控制器引用"""
        self.ai_controller = ai_controller
        # 连接AI控制器信号
        self.ai_controller.ai_response_ready.connect(self.on_ai_response_ready)
        self.ai_controller.ai_sentence_ready.connect(self.on_ai_sentence_ready)  
        # 新增信号连接
        self.ai_controller.ai_generation_cancelled.connect(self.on_ai_generation_cancelled)
        
        # 保存当前活动请求ID
        self.active_request_id = None
    
    def set_paper_controller(self, paper_controller):
        """设置论文控制器引用"""
        self.paper_controller = paper_controller

    # 修改set_markdown_view方法
    def set_markdown_view(self, markdown_view):
        """设置Markdown视图引用"""
        self.markdown_view = markdown_view
        # 将markdown_view传递给AI管理器
        if self.ai_controller:
            self.ai_controller.markdown_view = markdown_view
            
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建组件
        title_bar = self.create_title_bar()
        chat_container = self.create_chat_container()
        
        # 添加到主布局
        layout.addWidget(title_bar)
        layout.addWidget(chat_container)
    
    def create_title_bar(self):
        """
        创建聊天区域标题栏
        
        Returns:
            QFrame: 配置好的标题栏
        """
        # 标题栏
        title_bar = QFrame()
        title_bar.setObjectName("chatTitleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            #chatTitleBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 #1565C0, stop:1 #0D47A1);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: white;
            }
        """)
        
        # 标题栏布局
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        # 设置标题文本和字体
        title_font = QFont("Source Han Sans SC", 11, QFont.Weight.Bold)
        title_label = QLabel("AI助手")
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; font-weight: bold;")


        self.toggle_button = QPushButton("<<")
        self.toggle_button.setMaximumWidth(30)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: white;
                font-weight: bold;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_ai_chat)
        self.toggle_button.setShortcut("Ctrl+Shift+C")  # 设置快捷键

        title_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.toggle_button, 0, Qt.AlignmentFlag.AlignRight)
        
        return title_bar

    def toggle_ai_chat(self):
        """切换侧边栏展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        
        target_width = self.expanded_width if self.is_expanded else self.collapsed_width
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        # 同时设置最小宽度
        self.min_anim = QPropertyAnimation(self, b"minimumWidth")
        self.min_anim.setDuration(300)
        self.min_anim.setStartValue(self.width())
        self.min_anim.setEndValue(target_width)
        self.min_anim.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        # 更新按钮文本
        if self.is_expanded:
            button_text = "<<"
        else:
            button_text = ">>"
        
        self.toggle_button.setText(button_text)
        self.toggle_button.setShortcut("Ctrl+Shift+C")  # 设置快捷键
        
        # 显示/隐藏其他内容
        self.scroll_area.setVisible(self.is_expanded)
        self.message_input.setVisible(self.is_expanded)
        self.send_button.setVisible(self.is_expanded)
        
        # 启动动画
        self.animation.start()
        self.min_anim.start()
    
    def create_chat_container(self):
        """
        创建聊天内容容器
        
        Returns:
            QFrame: 配置好的聊天容器
        """
        # 聊天容器
        chat_container = QFrame()
        chat_container.setObjectName("chatContainer")
        chat_container.setStyleSheet("""
            #chatContainer {
                background-color: #E8EAF6;
                border-left: 1px solid #CFD8DC;
                border-right: 1px solid #CFD8DC;
                border-bottom: 1px solid #CFD8DC;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(chat_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建消息显示区域
        self.scroll_area = self.create_message_display_area()
        
        # 创建输入区域
        self.input_frame = self.create_input_area()
        
        # 添加到容器布局
        container_layout.addWidget(self.scroll_area, 1)
        container_layout.addWidget(self.input_frame)
        
        return chat_container
    
    def create_message_display_area(self):
        """
        创建消息显示区域
        
        Returns:
            QScrollArea: 配置好的消息滚动区域
        """
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
        """)
        
        # 创建消息容器
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(0, 10, 0, 10)
        self.messages_layout.setSpacing(10)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_container.setStyleSheet("background-color: transparent;")
        
        # 设置滚动区域的内容
        scroll_area.setWidget(self.messages_container)
        
        return scroll_area
    
    def create_input_area(self):
        """
        创建消息输入区域
        
        Returns:
            QFrame: 配置好的输入区域框架
        """
        # 输入区域框架
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_frame.setStyleSheet("""
            #inputFrame {
                background-color: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 12px;
                padding: 5px;
            }
        """)
        
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(10)  # 增加间距
        
        # 创建文本输入框
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("请输入您的问题...")
        self.message_input.setMaximumHeight(100)
        self.message_input.setObjectName("messageInput")
        self.message_input.setStyleSheet("""
            #messageInput {
                border: none;
                background-color: #F5F7FA;
                border-radius: 8px;
                padding: 10px;  /* 增加内边距 */
                font-family: 'Source Han Sans SC', 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QTextEdit[placeholderText] {
            color: #999999;
            font-style: italic;
            }
        """)
        # 连接回车键发送功能
        self.message_input.installEventFilter(self)
        
        # 创建控制区容器
        control_container = QWidget()
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(0, 8, 0, 0)
        control_layout.setSpacing(12)  # 增加控件间距
        
        # 创建发送按钮
        self.send_button = self.create_send_button()
        
        # 添加到控制布局
        control_layout.addStretch(1)
        control_layout.addWidget(self.send_button)
        
        # 添加到主布局
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(control_container)
        
        return input_frame
    
    def create_send_button(self):
        """
        创建发送按钮
        
        Returns:
            QPushButton: 配置好的发送按钮
        """
        send_button = QPushButton("发送")
        send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        send_button.setObjectName("sendButton")
        send_button.setFixedHeight(36)  # 增加高度
        send_button.setMinimumWidth(100)  # 增加宽度
        
        # 美化发送按钮
        send_button.setStyleSheet("""
            #sendButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 #303F9F, stop:1 #1A237E);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            #sendButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 #3949AB, stop:1 #303F9F);
            }
            #sendButton:pressed {
                background: #1A237E;
                padding-left: 22px;
                padding-top: 10px;
            }
        """)
        send_button.clicked.connect(self.send_message)
        
        return send_button
    
    def send_message(self):
        """
        发送用户消息
        
        获取输入框中的消息，创建用户消息气泡并清空输入框
        """
        message = self.message_input.toPlainText().strip()
        if message:
            # 添加用户消息气泡
            user_bubble = MessageBubble(message, is_user=True)
            self.messages_layout.addWidget(user_bubble)
            
            # 清空输入框
            self.message_input.clear()
            
            # 滚动到底部
            QTimer.singleShot(100, self.scroll_to_bottom)
            
            # 处理消息并获取AI响应
            self.process_message(message)
    
    def process_message(self, message):
        """处理用户消息并获取AI响应"""
        if self.loading_bubble:
            self.loading_bubble.stop_animation()
            self.messages_layout.removeWidget(self.loading_bubble)
            self.loading_bubble.deleteLater()
            self.loading_bubble = None

        # 如果有AI控制器，则使用AI控制器处理消息
        if self.ai_controller:
            # 获取当前论文ID，如果有的话
            paper_id = None
            if self.paper_controller and self.paper_controller.current_paper:
                paper_id = self.paper_controller.current_paper.get('id')

            # 获取当前可见文本，如果有的话
            visible_content = None
            if hasattr(self, 'markdown_view') and self.markdown_view:
                visible_content = self.markdown_view.get_current_visible_text()
            
            # 显示加载动画
            self.loading_bubble = LoadingBubble()
            self.messages_layout.addWidget(self.loading_bubble)
            self.scroll_to_bottom()
            
            # 通过AI控制器获取AI响应，同时保存请求ID
            request_id = self.ai_controller.get_ai_response(message, paper_id, visible_content)
            self.active_request_id = request_id
        else:
            # 使用默认响应
            QTimer.singleShot(500, lambda: self.receive_ai_message(
                f"我已收到您的问题：{message}\n\nAI控制器未连接，无法获取具体响应。"))
    
    def receive_ai_message(self, message):
        """
        接收并显示AI消息
        
        Args:
            message: AI返回的消息内容
        """
        # 添加AI消息气泡
        ai_bubble = MessageBubble(message, is_user=False)
        self.messages_layout.addWidget(ai_bubble)
        
        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)

    def on_ai_sentence_ready(self, sentence, request_id):
        """处理单句AI响应"""
        # 如果请求ID不匹配当前活动请求，忽略这句话
        if request_id != self.active_request_id:
            print(f"忽略过时请求的句子: '{sentence[:20]}...' (请求ID: {request_id})")
            return
            
        # 如果有加载动画且这是第一个句子，移除加载动画
        if self.loading_bubble is not None:
            self.loading_bubble.stop_animation()
            self.messages_layout.removeWidget(self.loading_bubble)
            self.loading_bubble.deleteLater()
            self.loading_bubble = None
        
        # 显示单句回复
        ai_bubble = MessageBubble(sentence, is_user=False)
        self.messages_layout.addWidget(ai_bubble)
        
        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def on_ai_response_ready(self, response):
        """
        当完整AI响应准备好时调用（仅用于非流式响应或流式响应结束）
        
        对于流式响应，主要通过on_ai_sentence_ready处理
        """

        # 如果仍有加载动画，说明是非流式响应或没有分句成功，移除加载动画
        if self.loading_bubble is not None:
            self.loading_bubble.stop_animation()
            self.messages_layout.removeWidget(self.loading_bubble)
            self.loading_bubble.deleteLater()
            self.loading_bubble = None

            # 对于非流式响应，才直接显示完整回复
            if not self.ai_controller.ai_response_thread.use_streaming:
                self.receive_ai_message(response)
            # 否则不显示，等TTS播放时显示
    
    def on_ai_generation_cancelled(self):
        """处理AI生成被取消的情况"""
        # 清理loading bubble
        if self.loading_bubble:
            self.loading_bubble.stop_animation()
            self.messages_layout.removeWidget(self.loading_bubble)
            self.loading_bubble.deleteLater()
            self.loading_bubble = None
        
        # 清除当前请求ID，因为请求已被取消
        self.active_request_id = None
    
    def scroll_to_bottom(self):
        """滚动到对话底部"""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    
    def eventFilter(self, obj, event):
        """
        事件过滤器，处理输入框按键事件
        
        当按下回车键且没有按下Shift键时发送消息，
        当按下Shift+回车时插入换行符
        
        Args:
            obj: 事件源对象
            event: 事件对象
            
        Returns:
            bool: 事件是否已处理
        """
        # 检查事件是否来自messageInput，且是键盘按下事件，且按键是回车
        if obj == self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # 回车键按下且没有按下Shift键，触发发送消息
                self.send_message()
                return True  # 事件已处理
            elif event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+回车，插入换行符
                return False  # 让QTextEdit处理这个事件
        
        # 其他事件交给父类处理
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 不再需要手动处理voice_thread，由ai_manager负责清理
        # 如果有父类方法，调用它
        if hasattr(super(), 'closeEvent'):
            super().closeEvent(event)