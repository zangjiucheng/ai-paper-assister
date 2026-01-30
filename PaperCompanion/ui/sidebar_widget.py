from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QListWidget, QListWidgetItem, QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence, QFont, QColor, QBrush

from .upload_widget import UploadWidget  # 导入上传文件窗口类

class SidebarWidget(QWidget):
    """可折叠侧边栏"""
    # 定义信号
    paper_selected = pyqtSignal(str)  # 论文选择信号，传递论文ID
    upload_file = pyqtSignal(str)  # 上传文件信号，传递文件路径（转发）
    upload_zip = pyqtSignal(str)  # 上传压缩文件信号，传递文件路径（转发）
    pause_processing = pyqtSignal()  # 暂停处理信号（转发）
    resume_processing = pyqtSignal()  # 继续处理信号（转发）
    toggle_active = pyqtSignal(str)  # 切换激活状态信号（转发）
    download_selected = pyqtSignal(list)  # 下载选中的论文信号，传递论文ID列表
    reorder_queue = pyqtSignal(str, str)  # 调整处理队列顺序信号 (paper_id, direction)
    clear_queue_and_delete = pyqtSignal()  # 清空队列并删除文件信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsed_width = 50
        self.expanded_width = 250  # 减小侧边栏宽度
        self.is_expanded = True
        self.selected_papers = []  # 存储选中的论文ID列表
        self.setMaximumWidth(self.expanded_width)  # 设置最大宽度
        self.queue_status = {}
        self.queue_entries = []
        self.paper_items = {}
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # 减少间距
        
        # 标题和折叠按钮
        header_frame = QFrame()
        header_frame.setObjectName("sidebarHeader")
        header_frame.setStyleSheet("""
            #sidebarHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #1a237e, stop:1 #0d47a1);
                color: white;
                border-bottom: 1px solid #0a1855;
            }
        """)
        header_frame.setFixedHeight(40)  # 固定高度与其他标题栏一致
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        title_font = QFont("Source Han Sans SC", 11, QFont.Weight.Bold)
        self.title_label = QLabel("论文列表")
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        
        # 固定位置的折叠按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
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
        self.toggle_button.clicked.connect(self.toggle_sidebar)

        self.download_button = QPushButton("Achieve Selected")
        self.download_button.setObjectName("downloadButton")
        self.download_button.setStyleSheet("""
            #downloadButton {
                background-color: #ffb300;
                color: white;
                border: 1px solid #ffa000;
                border-radius: 8px;
                padding: 5px 15px;
                font-weight: bold;
            }
            #downloadButton:hover {
                background-color: #ffa000;
                border: 1px solid #ff6f00;
            }
        """)
        self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_button.clicked.connect(self.on_download_button_clicked)

        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.toggle_button)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(button_container, 0, Qt.AlignmentFlag.AlignRight)
        
        # 论文列表容器
        list_container = QFrame()
        list_container.setObjectName("listContainer")
        list_container.setStyleSheet("""
            #listContainer {
                background-color: #f0f4f8;
            }
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # 论文列表
        self.paper_list = QListWidget()
        self.paper_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.paper_list.setObjectName("paperList")
        self.paper_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.paper_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.paper_list.setStyleSheet("""
            #paperList {
                background-color: #f0f4f8;
                border: none;
                outline: none;
            }
            #paperList QScrollBar:vertical {
                width: 0px;
                background: transparent;
            }
            #paperList QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
            #paperList QScrollBar::handle:vertical,
            #paperList QScrollBar::add-line:vertical,
            #paperList QScrollBar::sub-line:vertical,
            #paperList QScrollBar::add-page:vertical,
            #paperList QScrollBar::sub-page:vertical {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #dbe2ef;
                color: #2c3e50;
                width: 100%;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #1a237e, stop:1 #283593);
                color: white;
                border-radius: 6px;
                margin: 2px 5px;
            }
            QListWidget::item:hover:!selected {
                background-color: #e3f2fd;
                border-radius: 6px;
                margin: 2px 5px;
            }
        """)
        
        # 连接论文列表点击信号
        self.paper_list.itemClicked.connect(self.on_paper_item_clicked)
        
        for i in range(1, 10):  # 支持 1-9 键
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda i=i: self.select_paper_by_index(i - 1))
        
        QShortcut(QKeySequence(f"Ctrl+t"), self).activated.connect(self.toggle_active_paper)
        
        list_layout.addWidget(self.paper_list)
        
        self.queue_info_label = QLabel()
        self.queue_info_label.setObjectName("queueInfoLabel")
        self.queue_info_label.setWordWrap(True)
        self.queue_info_label.setStyleSheet("""
            #queueInfoLabel {
                color: #546e7a;
                font-size: 11px;
                padding: 6px 8px;
            }
        """)
        self.queue_info_label.setVisible(False)
        self.queue_info_label.setTextFormat(Qt.TextFormat.RichText)
        list_layout.addWidget(self.queue_info_label)

        # 队列顺序调整按钮
        reorder_frame = QFrame()
        reorder_layout = QHBoxLayout(reorder_frame)
        reorder_layout.setContentsMargins(8, 4, 8, 8)
        reorder_layout.setSpacing(6)

        reorder_label = QLabel("调整顺序:")
        reorder_label.setStyleSheet("color: #546e7a; font-size: 11px;")

        self.queue_move_up_btn = QPushButton("↑")
        self.queue_move_up_btn.setToolTip("上移队列顺序")
        self.queue_move_down_btn = QPushButton("↓")
        self.queue_move_down_btn.setToolTip("下移队列顺序")
        self.queue_move_top_btn = QPushButton("置顶")
        self.queue_move_top_btn.setToolTip("优先处理该论文")

        for btn in (self.queue_move_up_btn, self.queue_move_down_btn, self.queue_move_top_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e3f2fd;
                    color: #1a237e;
                    border: 1px solid #c5cae9;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                }
                QPushButton:disabled {
                    background-color: #e0e0e0;
                    color: #9e9e9e;
                    border-color: #e0e0e0;
                }
            """)

        self.queue_move_up_btn.clicked.connect(lambda: self._reorder_selected_item("up"))
        self.queue_move_down_btn.clicked.connect(lambda: self._reorder_selected_item("down"))
        self.queue_move_top_btn.clicked.connect(lambda: self._reorder_selected_item("top"))

        reorder_layout.addWidget(reorder_label)
        reorder_layout.addStretch(1)
        reorder_layout.addWidget(self.queue_move_up_btn)
        reorder_layout.addWidget(self.queue_move_down_btn)
        reorder_layout.addWidget(self.queue_move_top_btn)

        list_layout.addWidget(reorder_frame)
        
        # 创建上传文件窗口
        self.upload_widget = UploadWidget()
        
        # 连接上传文件窗口的信号
        self.upload_widget.upload_file.connect(self.on_upload_file)
        self.upload_widget.upload_zip.connect(self.on_upload_zip)
        self.upload_widget.pause_processing.connect(self.on_pause_processing)
        self.upload_widget.resume_processing.connect(self.on_resume_processing)
        self.upload_widget.clear_queue_and_delete.connect(self.on_clear_queue_clicked)
        
        # 添加到布局
        layout.addWidget(header_frame)
        layout.addWidget(list_container)
        layout.addWidget(self.upload_widget)
        
        self.setLayout(layout)
    
    def toggle_sidebar(self):
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
        
        # 显示/隐藏其他内容
        self.title_label.setVisible(self.is_expanded)
        self.paper_list.setVisible(self.is_expanded)
        self.queue_info_label.setVisible(self.is_expanded and bool(self.queue_entries))
        self.upload_widget.setVisible(self.is_expanded)
        self.download_button.setVisible(self.is_expanded)
        
        # 如果正在折叠，且详情面板可见，先隐藏详情面板
        if not self.is_expanded:
            self.upload_widget.close_details_if_open()
        
        # 启动动画
        self.animation.start()
        self.min_anim.start()
    
    def load_papers(self, papers_index):
        """加载论文索引到列表"""
        self.paper_list.clear()
        self.paper_items = {}
        for index, paper in enumerate(papers_index, start=1):
            # 优先使用translated_title作为显示文本
            title = paper.get('translated_title') or paper.get('title') or paper.get('id', '')
            if paper.get('active') == 1:
                title = f"{index}. {title}"
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, paper)
            self.paper_list.addItem(item)
            paper_id = paper.get('id')
            if paper_id:
                self.paper_items[paper_id] = item
                status = self.queue_status.get(paper_id)
                self._apply_item_style(item, status)
        self._refresh_queue_display()
    
    def on_download_button_clicked(self):
        """弹出确认窗口，展示并确认下载选中的论文 ID 列表"""
        if not self.selected_papers:
            return

        # 构造富文本消息
        message = (
            "<b>请确认是否下载以下论文：</b><br>"
            + "<br>".join(f"• {paper_id['translated_title']}" for paper_id in self.selected_papers)
        )

        # 创建并配置对话框
        dialog = QMessageBox(self)
        dialog.setWindowTitle("确认下载")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.button(QMessageBox.StandardButton.Yes).setText("下载")
        dialog.button(QMessageBox.StandardButton.No).setText("取消")

        # 美化样式
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #f0f4f8;
                font-family: 'Source Han Sans SC';
                font-size: 12px;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                margin: 8px;
            }
            QMessageBox QPushButton {
                min-width: 72px;
                margin: 4px;
                padding: 6px 12px;
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #1565c0;
            }
            QMessageBox QPushButton:disabled {
                background-color: #b0bec5;
                color: #ffffff;
            }
        """)
        
        # Get ID list from selected papers
        download_papers = [paper.get('id') for paper in self.selected_papers]

        # 执行并处理用户响应
        if dialog.exec() == QMessageBox.StandardButton.Yes:
            # 在此处执行真正的下载逻辑
            self.selected_papers = []
            print(f"下载选中的论文：{', '.join(download_papers)}")
            self.download_selected.emit(download_papers)

    def on_paper_item_clicked(self, item):
        """处理论文项点击事件，发出paper_selected信号"""
        selected_items = self.paper_list.selectedItems()
        self.selected_papers = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        paper = item.data(Qt.ItemDataRole.UserRole)
        if paper:
            # 发送论文选择信号
            self.paper_selected.emit(paper.get('id'))

    def toggle_active_paper(self):
        """切换指定论文的激活状态"""
        item = self.paper_list.currentItem()
        if item is None:
            return
        paper = item.data(Qt.ItemDataRole.UserRole)
        if paper:
            self.toggle_active.emit(paper.get('id'))
            
    def on_upload_file(self, file_path):
        """处理上传文件事件，转发上传文件信号"""
        self.upload_file.emit(file_path)

    def on_upload_zip(self, file_path):
        """处理上传压缩文件事件，转发上传压缩文件信号"""
        self.upload_zip.emit(file_path)
        
    def on_pause_processing(self):
        """处理暂停处理事件，转发暂停处理信号"""
        self.pause_processing.emit()
        
    def on_resume_processing(self):
        """处理继续处理事件，转发继续处理信号"""
        self.resume_processing.emit()
        
    def select_paper_by_index(self, index):
        """选择指定索引的论文"""
        if 0 <= index < self.paper_list.count():
            item = self.paper_list.item(index)
            self.paper_list.setCurrentItem(item)
            self.on_paper_item_clicked(item)

    def select_paper_by_id(self, paper_id):
        """按论文ID选择并触发加载"""
        item = self.paper_items.get(paper_id)
        if not item:
            return False
        self.paper_list.setCurrentItem(item)
        self.on_paper_item_clicked(item)
        return True

    def update_upload_status(self, file_name, stage, progress, pending_count):
        """更新上传状态
        
        Args:
            file_name: 当前处理的文件名
            stage: 当前处理阶段
            progress: 处理进度值 (0-100)
            pending_count: 待处理文件数量
        """
        self.upload_widget.update_upload_status(file_name, stage, progress, pending_count)
    
    def update_queue_status(self, queue):
        """更新队列状态显示"""
        self.queue_status = {item.get('id'): item.get('status', 'pending') for item in queue}
        self.queue_entries = queue
        self._set_reorder_controls_enabled(bool(queue))
        # 更新已有论文项的样式
        for paper_id, item in self.paper_items.items():
            self._apply_item_style(item, self.queue_status.get(paper_id))
        self._refresh_queue_display()
    
    def _apply_item_style(self, item, status):
        """根据队列状态设置列表项颜色"""
        default_fg = QBrush(QColor("#2c3e50"))
        default_bg = QBrush(QColor("#f0f4f8"))
        pending_bg = QBrush(QColor("#fff3e0"))
        pending_fg = QBrush(QColor("#e65100"))
        processing_bg = QBrush(QColor("#e8f0fe"))
        processing_fg = QBrush(QColor("#1a237e"))
        error_bg = QBrush(QColor("#ffebee"))
        error_fg = QBrush(QColor("#c62828"))
        
        if status == "processing":
            item.setBackground(processing_bg)
            item.setForeground(processing_fg)
        elif status in ("pending", "incomplete"):
            item.setBackground(pending_bg)
            item.setForeground(pending_fg)
        elif status == "error":
            item.setBackground(error_bg)
            item.setForeground(error_fg)
        else:
            item.setBackground(default_bg)
            item.setForeground(default_fg)
    
    def _refresh_queue_display(self):
        """更新队列提示标签"""
        if not self.queue_entries:
            self.queue_info_label.clear()
            self.queue_info_label.setVisible(False)
            return
        
        status_styles = {
            "processing": ("处理中", "#1a237e"),
            "pending": ("等待处理", "#e65100"),
            "incomplete": ("待补充", "#ef6c00"),
            "error": ("处理错误", "#c62828"),
        }
        
        lines = []
        for entry in self.queue_entries:
            paper_id = entry.get('id', '未知ID')
            status_key = entry.get('status', 'pending')
            status_text, color = status_styles.get(status_key, ("等待处理", "#546e7a"))
            display_text = paper_id
            if paper_id in self.paper_items:
                display_text = self.paper_items[paper_id].text()
            lines.append(f"<span style='color:{color}; font-weight:bold;'>{status_text}</span> - {display_text}")
        
        self.queue_info_label.setText("<br>".join(lines))
        self.queue_info_label.setVisible(self.is_expanded)

    def _set_reorder_controls_enabled(self, enabled):
        self.queue_move_up_btn.setEnabled(enabled)
        self.queue_move_down_btn.setEnabled(enabled)
        self.queue_move_top_btn.setEnabled(enabled)

    def _reorder_selected_item(self, direction):
        selected_items = self.paper_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请选择一个待处理的论文以调整顺序。")
            return

        paper = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not paper:
            return

        paper_id = paper.get('id')
        if not paper_id:
            return

        if paper_id not in {entry.get('id') for entry in self.queue_entries}:
            QMessageBox.information(self, "提示", "该论文不在待处理队列中。")
            return

        self.reorder_queue.emit(paper_id, direction)

    def on_clear_queue_clicked(self):
        if not self.queue_entries:
            QMessageBox.information(self, "提示", "当前处理队列为空。")
            return

        count = len(self.queue_entries)
        dialog = QMessageBox(self)
        dialog.setWindowTitle("确认清空队列")
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setText(f"将删除队列中的 {count} 个PDF及对应输出。该操作不可恢复，是否继续？")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.button(QMessageBox.StandardButton.Yes).setText("删除")
        dialog.button(QMessageBox.StandardButton.No).setText("取消")
        if dialog.exec() == QMessageBox.StandardButton.Yes:
            self.clear_queue_and_delete.emit()
