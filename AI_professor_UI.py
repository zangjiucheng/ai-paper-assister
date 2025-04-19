import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QSplitter, 
                           QLabel, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.markdown_view import MarkdownView
from ui.sidebar_widget import SidebarWidget
from data_manager import DataManager
from AI_manager import AIManager

class AIProfessorUI(QMainWindow):
    """
    主窗口类 - 学术论文AI助手的主界面
    
    负责创建和管理整个应用的UI布局、样式和交互逻辑，
    包括侧边栏、文档查看区和AI聊天区
    """
    def __init__(self):
        """初始化主窗口及所有子组件"""
        super().__init__()
        
        # 初始化数据管理器和AI管理器
        self.data_manager = DataManager()
        self.ai_manager = AIManager()
        
        # 设置两者互相引用
        self.ai_manager.set_data_manager(self.data_manager)
        self.data_manager.set_ai_manager(self.ai_manager)
        
        # 设置UI元素
        self.init_window_properties()
        self.init_custom_titlebar()
        self.init_ui_components()
        
        # 连接数据管理器信号
        self.connect_signals()
        
        # 加载论文数据
        self.data_manager.load_papers_index()
        
        # 在后台预加载所有论文向量库
        self.ai_manager.init_rag_retriever("output")

    def init_window_properties(self):
        """初始化窗口属性：大小、图标、状态栏和窗口风格"""
        # 设置窗口标题和初始大小
        self.setWindowTitle("读论文助手")
        self.setGeometry(100, 100, 1400, 900)
        
        # 添加状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #303F9F;
                color: white;
                padding: 2px;
                font-size: 11px;
            }
        """)
        
        # 设置无边框窗口，但允许调整大小
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowMaximizeButtonHint | 
                          Qt.WindowType.WindowMinimizeButtonHint | 
                          Qt.WindowType.WindowCloseButtonHint)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8EAF6;
            }
        """)

    def init_custom_titlebar(self):
        """
        初始化自定义标题栏
        
        创建一个美观的自定义标题栏，包含应用图标、标题和窗口控制按钮，
        并实现拖拽移动和双击最大化的功能
        """
        # 创建标题栏框架
        self.titlebar = QFrame(self)
        self.titlebar.setObjectName("customTitleBar")
        self.titlebar.setFixedHeight(30)
        self.titlebar.setStyleSheet("""
            #customTitleBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 #0D47A1, stop:0.5 #1A237E, stop:1 #0D47A1);
                color: white;
            }
        """)
        
        # 设置布局
        titlebar_layout = QHBoxLayout(self.titlebar)
        titlebar_layout.setContentsMargins(10, 0, 10, 0)
        titlebar_layout.setSpacing(5)
        
        # 设置应用图标
        app_icon = QLabel()
        # 使用应用程序图标渲染到标题栏
        app_icon.setPixmap(self.windowIcon().pixmap(16, 16))
        
        # 设置应用标题
        app_title = QLabel("读论文助手")
        app_title.setStyleSheet("color: white; font-weight: bold;")
        
        # 创建窗口控制按钮
        self.create_window_control_buttons()
        
        # 添加组件到布局
        titlebar_layout.addWidget(app_icon)
        titlebar_layout.addWidget(app_title)
        titlebar_layout.addStretch(1)
        titlebar_layout.addWidget(self.btn_minimize)
        titlebar_layout.addWidget(self.btn_maximize)
        titlebar_layout.addWidget(self.btn_close)
        
        # 绑定拖动和双击事件
        self.titlebar.mousePressEvent = self.titlebar_mousePressEvent
        self.titlebar.mouseMoveEvent = self.titlebar_mouseMoveEvent
        self.titlebar.mouseDoubleClickEvent = self.titlebar_doubleClickEvent
        
        # 将标题栏添加到主窗口
        self.layout().setMenuBar(self.titlebar)

    def create_window_control_buttons(self):
        """创建窗口控制按钮：最小化、最大化和关闭"""
        # 通用按钮样式
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """
        
        # 最小化按钮
        self.btn_minimize = QPushButton("﹣")
        self.btn_minimize.setStyleSheet(btn_style)
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_minimize.setToolTip("最小化")
        self.btn_minimize.setShortcut("Ctrl+M")
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 最大化/还原按钮
        self.btn_maximize = QPushButton("z")
        self.btn_maximize.setStyleSheet(btn_style)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_maximize.setShortcut("Ctrl+F")
        self.btn_maximize.setToolTip("最大化")
        self.btn_maximize.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 关闭按钮
        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-family: Arial;
                font-weight: bold;
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF3B30; /* macOS close button red */
                border-radius: 4px;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setToolTip("关闭")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)

    def titlebar_mousePressEvent(self, event):
        """处理标题栏的鼠标按下事件，用于实现窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()
            event.accept()
    
    def titlebar_mouseMoveEvent(self, event):
        """处理标题栏的鼠标移动事件，实现窗口拖动"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            if hasattr(self, 'dragPos'):
                self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
                self.dragPos = event.globalPosition().toPoint()
                event.accept()
    
    def titlebar_doubleClickEvent(self, event):
        """处理标题栏的双击事件，切换窗口最大化状态"""
        self.toggle_maximize()
    
    def toggle_maximize(self):
        """切换窗口最大化/还原状态"""
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("z")
            self.btn_maximize.setToolTip("最大化")
        else:
            self.showMaximized()
            self.btn_maximize.setText("r")
            self.btn_maximize.setToolTip("还原")
        self.btn_maximize.setShortcut("Ctrl+F")

    def init_ui_components(self):
        """
        初始化UI组件和布局
        
        创建应用的主要UI组件，包括:
        - 侧边栏：用于显示和选择论文
        - 文档查看区：显示论文内容，支持中英文切换
        - 聊天区域：用于与AI助手交互
        """
        # 设置中心部件和主布局
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 初始化侧边栏
        self.sidebar = SidebarWidget()
        
        # 初始化主内容区域
        content_container = self.create_content_container()
        
        # 添加到主布局
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_container)
        
        # 应用全局样式
        self.apply_global_styles()

    def create_content_container(self):
        """创建主内容区域容器，包含文档查看区和聊天区域"""
        # 主内容区域容器
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet("""
            #contentContainer {
                background-color: #E8EAF6;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            #contentWidget {
                background-color: #E8EAF6;
                border: 1px solid rgba(0,0,0,0.1);
            }
        """)
        
        content_inner_layout = QHBoxLayout(content_widget)
        content_inner_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分隔器和内容区域组件
        splitter = self.create_content_splitter()
        content_inner_layout.addWidget(splitter)
        content_layout.addWidget(content_widget)
        
        return content_container

    def create_content_splitter(self):
        """创建内容区域分隔器，用于调整文档和聊天区域的比例"""
        # 分隔器，用于调整文档和聊天的宽度比例
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)  # 设置分隔条宽度
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #C5CAE9;
            }
        """)
        
        # 创建Markdown显示区域
        md_container = self.create_markdown_container()
        
        # 添加到分隔器并设置初始比例
        splitter.addWidget(md_container)
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        return splitter

    def create_markdown_container(self):
        """创建Markdown文档显示区域"""
        # Markdown显示区域容器
        md_container = QWidget()
        md_container.setObjectName("mdContainer")
        md_layout = QVBoxLayout(md_container)
        md_layout.setContentsMargins(0, 0, 0, 0)
        md_layout.setSpacing(0)
        
        # 创建文档工具栏
        toolbar = self.create_doc_toolbar()
        
        # 创建Markdown视图容器
        md_view_container = QFrame()
        md_view_container.setObjectName("mdViewContainer")
        md_view_container.setStyleSheet("""
            #mdViewContainer {
                background-color: #FFFFFF;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                border-left: 1px solid #CFD8DC;
                border-right: 1px solid #CFD8DC;
                border-bottom: 1px solid #CFD8DC;
            }
        """)
        md_view_layout = QVBoxLayout(md_view_container)
        md_view_layout.setContentsMargins(5, 5, 5, 10)

        # 创建Markdown视图并传入数据管理器
        self.md_view = MarkdownView()
        self.md_view.set_data_manager(self.data_manager)  # 设置数据管理器
        self.md_view.setStyleSheet("background-color: #FFFFFF;")
        md_view_layout.addWidget(self.md_view)
        
        # 添加到布局
        md_layout.addWidget(toolbar)
        md_layout.addWidget(md_view_container)
        
        return md_container

    def create_doc_toolbar(self):
        """创建文档工具栏，包含标题和语言切换按钮"""
        # 工具栏容器
        toolbar = QFrame()
        toolbar.setObjectName("docToolbar")
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("""
            #docToolbar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 #303F9F, stop:1 #1A237E);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                color: white;
            }
        """)
        
        # 工具栏布局
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 0, 15, 0)
        
        # 工具栏标题
        title_font = QFont("Source Han Sans SC", 11, QFont.Weight.Bold)
        doc_title = QLabel("论文阅读")
        doc_title.setFont(title_font)
        doc_title.setStyleSheet("color: white; font-weight: bold;")
        
        # 语言切换按钮
        self.lang_button = QPushButton("切换为英文")
        self.lang_button.setObjectName("langButton")
        self.lang_button.setStyleSheet("""
            #langButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 5px 15px;
                font-weight: bold;
            }
            #langButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.lang_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_button.clicked.connect(self.toggle_language)
        
        # 添加到布局
        toolbar_layout.addWidget(doc_title, 0, Qt.AlignmentFlag.AlignLeft)
        toolbar_layout.addWidget(self.lang_button, 0, Qt.AlignmentFlag.AlignRight)
        
        return toolbar

    def apply_global_styles(self):
        """应用全局样式，主要用于统一滚动条风格"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8EAF6;
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C5CAE9;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7986CB;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def connect_signals(self):
        """连接数据管理器和UI组件的信号和槽"""
        # 连接侧边栏上传信号
        self.sidebar.upload_file.connect(self.data_manager.upload_file)
        self.sidebar.pause_processing.connect(self.data_manager.pause_processing)
        self.sidebar.resume_processing.connect(self.data_manager.resume_processing)

        # 连接数据管理器的论文数据信号
        self.sidebar.resume_processing.connect(self.data_manager.resume_processing)

        # 连接数据管理器的论文数据信号
        self.data_manager.papers_loaded.connect(self.on_papers_loaded)  # 这是关键连接
        self.data_manager.paper_content_loaded.connect(self.on_paper_content_loaded)
        self.data_manager.loading_error.connect(self.on_loading_error)
        self.data_manager.message.connect(self.on_message)
        
        # 连接侧边栏的论文选择信号
        self.sidebar.paper_selected.connect(self.on_paper_selected)

        # 连接处理进度信号
        self.data_manager.processing_progress.connect(self.on_processing_progress)
        self.data_manager.processing_finished.connect(self.on_processing_finished)
        self.data_manager.processing_error.connect(self.on_processing_error)
        self.data_manager.queue_updated.connect(self.on_queue_updated)

        # 初始化处理系统
        self.data_manager.initialize_processing_system()

    def on_papers_loaded(self, papers):
        """
        处理论文列表加载完成的信号
        
        Args:
            papers: 论文数据列表
        """
        self.sidebar.load_papers(papers)
        
    def on_paper_selected(self, paper_id):
        """
        处理论文选择事件
        
        当用户在侧边栏选择一篇论文时，通知数据管理器加载相应内容
        
        Args:
            paper_id: 选择的论文ID
        """
        # 通知数据管理器加载选定的论文
        self.data_manager.load_paper_content(paper_id)

    def on_paper_content_loaded(self, paper, zh_content, en_content):
        """
        处理论文内容加载完成的信号
        
        Args:
            paper: 论文数据字典
            zh_content: 中文内容
            en_content: 英文内容
        """
        # 加载文档内容到Markdown视图
        self.md_view.load_markdown(zh_content, "zh", render=False)  # 不立即渲染
        self.md_view.load_markdown(en_content, "en", render=False)  # 不立即渲染
        self.md_view.set_language("zh")  # 默认显示中文
        
        # 更新语言按钮文本
        self.lang_button.setText("切换为英文")
        self.lang_button.setShortcut("Ctrl+L")
        self.lang_button.setStyleSheet("""
            #langButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 5px 15px;
                font-weight: bold;
            }
            #langButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        # 更新状态栏
        title = paper.get('translated_title', '') or paper.get('title', '')
        self.statusBar().showMessage(f"已加载论文: {title}")

    def on_loading_error(self, error_message):
        """
        处理加载错误的信号
        
        Args:
            error_message: 错误信息
        """
        # 更新状态栏显示错误
        self.statusBar().showMessage(f"错误: {error_message}")
        
        # 也可以在这里添加更明显的错误提示，如弹窗等

    def on_message(self, message):
        """
        处理一般消息的信号
        
        Args:
            message: 消息内容
        """
        # 更新状态栏
        self.statusBar().showMessage(message)

    def toggle_language(self):
        """
        切换文档语言
        
        在中文和英文之间切换文档显示语言，并更新按钮状态和样式
        """
        lang = self.md_view.toggle_language()
        
        # 设置按钮文本和样式
        if lang == "zh":
            btn_text = "切换为英文"
            self.lang_button.setStyleSheet("""
                #langButton {
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                #langButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
            """)
        else:
            btn_text = "切换为中文"
            self.lang_button.setStyleSheet("""
                #langButton {
                    background-color: rgba(65, 105, 225, 0.3);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                #langButton:hover {
                    background-color: rgba(65, 105, 225, 0.4);
                }
            """)
            
        self.lang_button.setText(btn_text)
        self.lang_button.setShortcut("Ctrl+L")
        
        # 更新状态栏
        current_paper = self.data_manager.current_paper
        if current_paper:
            language_text = "英文" if lang == "en" else "中文"
            title = current_paper.get('title' if lang == "en" else 'translated_title', '')
            self.statusBar().showMessage(f"已切换到{language_text}版本: {title}")

    def on_processing_progress(self, file_name, stage, progress, remaining):
        self.sidebar.update_upload_status(file_name, stage, progress, remaining)
        
    def on_processing_finished(self, paper_id):
        self.data_manager.load_papers_index()
        
    def on_processing_error(self, paper_id, error_msg):
        self.statusBar().showMessage(f"处理论文出错: {error_msg}")
        
    def on_queue_updated(self, queue):
        """处理队列更新回调"""
        # 获取待处理文件数量
        pending_count = len(queue)
        
        # 更新状态栏显示
        if pending_count > 0:
            self.statusBar().showMessage(f"队列中有 {pending_count} 个文件待处理")
        else:
            self.statusBar().showMessage("处理队列为空")
        
        # 更新上传组件UI
        if pending_count == 0:
            # 队列空时更新UI为完成状态
            self.sidebar.update_upload_status("", "全部完成", 100, 0)
        elif not self.data_manager.is_processing and pending_count > 0:
            # 有待处理文件但当前没在处理时，显示下一个要处理的文件
            next_item = queue[0]
            self.sidebar.update_upload_status(
                os.path.basename(next_item['path']), 
                "等待处理", 
                0, 
                pending_count
            )

    def closeEvent(self, event):
        """处理窗口关闭事件 - 确保所有线程停止"""
        # 调用聊天部件的closeEvent
        # 清理AI管理器资源
        if hasattr(self, 'ai_manager'):
            self.ai_manager.cleanup()
        
        # 停止任何正在运行的处理线程
        if self.data_manager.current_thread is not None and self.data_manager.current_thread.isRunning():
            self.data_manager.current_thread.stop()
            self.data_manager.current_thread.wait(1000)  # 等待线程完成，最多1秒
        
        # 调用父类的closeEvent
        super().closeEvent(event)