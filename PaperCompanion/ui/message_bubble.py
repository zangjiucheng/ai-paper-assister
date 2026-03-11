import html
import os
import re

import markdown
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from ..paths import get_asset_path


class BubbleWebView(QWebEngineView):
    """用于消息气泡的轻量Web渲染视图（支持 Markdown + LaTeX）"""

    def __init__(self, bg_color, parent=None):
        super().__init__(parent)
        self._min_content_height = 28
        self._bg_color = bg_color
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(self._min_content_height)
        self.setMaximumHeight(2000)
        self.setStyleSheet(f"background: {bg_color}; border: none;")
        self.page().setBackgroundColor(QColor(bg_color))
        self.loadFinished.connect(self._schedule_height_updates)

    def _schedule_height_updates(self, _success):
        for delay in (0, 60, 180, 420):
            QTimer.singleShot(delay, self._update_height)

    def _update_height(self):
        script = """
        (() => {
            const body = document.body;
            const doc = document.documentElement;
            if (!body && !doc) return null;
            const bodyHeight = body ? body.scrollHeight : 0;
            const docHeight = doc ? doc.scrollHeight : 0;
            return Math.max(bodyHeight, docHeight);
        })()
        """
        try:
            self.page().runJavaScript(script, self._on_height_ready)
        except RuntimeError:
            # WebEngine page may already be destroyed during widget teardown.
            return

    def _on_height_ready(self, value):
        try:
            height = int(value)
        except (TypeError, ValueError):
            return
        height = max(self._min_content_height, height + 2)
        if self.height() != height:
            self.setFixedHeight(height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 宽度变化后，公式换行会改变总高度，需要重新测量。
        QTimer.singleShot(0, self._update_height)


class MessageBubble(QWidget):
    """
    单个消息气泡组件
    
    用于在聊天界面中显示用户或AI消息，气泡样式根据发送者不同而不同
    """
    def __init__(self, message, is_user=True, parent=None):
        """
        初始化消息气泡
        
        Args:
            message (str): 消息内容
            is_user (bool): 是否为用户消息，True为用户消息，False为AI消息
            parent: 父组件
        """
        super().__init__(parent)
        self.is_user = is_user
        self.message = message
        self.init_ui()

    @staticmethod
    def _needs_rich_render(message):
        if not message:
            return False
        # 数学公式或常见 Markdown 语法时启用 Web 渲染。
        math_patterns = [
            r"\$\$[\s\S]+?\$\$",
            r"(?<!\$)\$[^$\n]+\$(?!\$)",
            r"\\\([\s\S]+?\\\)",
            r"\\\[[\s\S]+?\\\]",
        ]
        markdown_patterns = [
            r"```[\s\S]+?```",
            r"(^|\n)\s*[-*+]\s+",
            r"(^|\n)\s*\d+\.\s+",
            r"`[^`\n]+`",
        ]
        for pattern in math_patterns + markdown_patterns:
            if re.search(pattern, message):
                return True
        return False

    @staticmethod
    def _build_message_html(message, text_color, bg_color):
        safe_text = html.escape(message or "")
        try:
            body_html = markdown.markdown(
                safe_text,
                extensions=[
                    "tables",
                    "fenced_code",
                    "extra",
                    "pymdownx.arithmatex",
                ],
                extension_configs={
                    "pymdownx.arithmatex": {"generic": True},
                },
            )
        except Exception:
            body_html = "<p>{}</p>".format(html.escape(safe_text).replace("\n", "<br>"))

        katex_css_path = get_asset_path("katex/katex.min.css")
        katex_js_path = get_asset_path("katex/katex.min.js")
        katex_autorender_path = get_asset_path("katex/contrib/auto-render.min.js")
        katex_css_url = QUrl.fromLocalFile(katex_css_path).toString()
        katex_js_url = QUrl.fromLocalFile(katex_js_path).toString()
        katex_autorender_url = QUrl.fromLocalFile(katex_autorender_path).toString()

        return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="{katex_css_url}">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: {bg_color};
      color: {text_color};
      overflow-x: hidden;
      font-family: 'Source Han Sans SC', 'Segoe UI', sans-serif;
      font-size: 14px;
      line-height: 1.5;
      word-break: break-word;
    }}
    .msg-root {{
      padding: 0;
      margin: 0;
    }}
    p {{
      margin: 0.2em 0;
    }}
    pre {{
      background-color: rgba(255, 255, 255, 0.55);
      border-radius: 6px;
      padding: 0.6em;
      overflow-x: auto;
      margin: 0.4em 0;
    }}
    code {{
      background-color: rgba(255, 255, 255, 0.5);
      border-radius: 4px;
      padding: 0.1em 0.3em;
      font-family: Consolas, Monaco, monospace;
    }}
    pre code {{
      background-color: transparent;
      padding: 0;
    }}
    .arithmatex {{
      overflow-x: auto;
      max-width: 100%;
    }}
    .katex-display > .katex {{
      max-width: 100%;
      overflow-x: auto;
      overflow-y: hidden;
      padding: 4px 0;
    }}
  </style>
  <script defer src="{katex_js_url}"></script>
  <script defer src="{katex_autorender_url}"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (window.renderMathInElement) {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}},
            {{left: '\\\\(', right: '\\\\)', display: false}},
            {{left: '\\\\[', right: '\\\\]', display: true}}
          ],
          throwOnError: false,
          strict: false,
          trust: true
        }});
      }}
    }});
  </script>
</head>
<body>
  <div class="msg-root">{body_html}</div>
</body>
</html>
"""
        
    def init_ui(self):
        """初始化气泡UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        if self.is_user:
            self.setup_user_bubble(main_layout)
        else:
            self.setup_ai_bubble(main_layout)
    
    def setup_user_bubble(self, layout):
        """
        设置用户消息气泡
        
        Args:
            layout: 要添加气泡的布局
        """
        # 用户消息靠右
        layout.addStretch(1)  # 左侧弹性空间
        
        # 创建气泡及容器
        bubble_container, bubble = self.create_bubble(
            self.message,
            "userBubble",
            "#DCF8C6",  # 背景色
            "#B0F2B6",  # 边框色
            "#2C3E50",  # 文字色
            "15px 15px 0 15px"  # 圆角
        )
        
        # 创建头像
        avatar = self.create_avatar("user_avatar.svg")
        
        # 添加到布局
        layout.addWidget(bubble_container)
        layout.addWidget(avatar)

        # 设置头像顶部对齐
        layout.setAlignment(avatar, Qt.AlignmentFlag.AlignTop)
        layout.setAlignment(bubble_container, Qt.AlignmentFlag.AlignRight)
    
    def setup_ai_bubble(self, layout):
        """
        设置AI消息气泡
        
        Args:
            layout: 要添加气泡的布局
        """
        # AI消息靠左
        # 创建头像
        avatar = self.create_avatar("ai_avatar.svg")
        
        # 创建气泡及容器
        bubble_container, bubble = self.create_bubble(
            self.message,
            "aiBubble",
            "#E3F2FD",  # 背景色
            "#BBDEFB",  # 边框色
            "#1A237E",  # 文字色
            "15px 15px 15px 0"  # 圆角
        )
        
        # 添加到布局
        layout.addWidget(avatar)
        layout.addWidget(bubble_container, 7)
        layout.addStretch(3)  # 右侧弹性空间

        # 设置头像顶部对齐
        layout.setAlignment(avatar, Qt.AlignmentFlag.AlignTop)
        
    def create_bubble(self, message, object_name, bg_color, border_color, text_color, border_radius):
        """
        创建消息气泡
        
        Args:
            message: 消息内容
            object_name: 气泡的对象名称
            bg_color: 背景颜色
            border_color: 边框颜色
            text_color: 文本颜色
            border_radius: 边框圆角
            
        Returns:
            tuple: (气泡容器, 气泡)
        """
        # 创建气泡
        bubble = QFrame()
        bubble.setObjectName(object_name)
        bubble.setStyleSheet(f"""
            #{object_name} {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius};
            padding: 8px;
            min-width: 0px;
            max-width: none;
            }}
        """)
        
        # 气泡内布局
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(8, 8, 8, 8)
        
        if self._needs_rich_render(message):
            msg_view = BubbleWebView(bg_color, bubble)
            msg_view.setObjectName("messageWebView")
            msg_view.setStyleSheet(f"background: {bg_color}; border: none;")
            message_html = self._build_message_html(message, text_color, bg_color)
            # 以 assets 目录为 base_url，确保本地 KaTeX 资源可被加载。
            assets_dir = os.path.dirname(get_asset_path("katex/katex.min.js"))
            msg_view.setHtml(message_html, QUrl.fromLocalFile(assets_dir + os.sep))
            bubble_layout.addWidget(msg_view)
        else:
            # 纯文本走 QLabel，保持轻量。
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet(f"color: {text_color}; font-size: 14px;")
            msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            bubble_layout.addWidget(msg_label)
        
        # 创建容器（用于控制气泡大小比例）
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(bubble)
        container_layout.setStretch(0, 4)  # 让气泡占据更多空间
        
        return container, bubble

    def resizeEvent(self, event):
        """根据聊天区宽度限制气泡最大宽度"""
        super().resizeEvent(event)
        available = max(0, self.width())
        max_width = int(available * 0.7)
        for bubble in self.findChildren(QFrame):
            bubble.setMaximumWidth(max_width)
    
    def create_avatar(self, avatar_filename):
        """
        创建头像标签
        
        Args:
            avatar_filename: 头像文件名
            
        Returns:
            QLabel: 包含头像的标签
        """
        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("border-radius: 16px;")
        
        # 获取头像路径并加载
        avatar_path = get_asset_path(avatar_filename)
        avatar.setPixmap(QPixmap(avatar_path).scaled(
            32, 32, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        ))
        
        return avatar
    

class LoadingBubble(QWidget):
    """
    显示加载动画的气泡组件
    
    用于在等待AI响应时显示动画效果
    """
    def __init__(self, parent=None):
        """初始化加载气泡"""
        super().__init__(parent)
        
        # 设置布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建气泡框架
        bubble = QFrame()
        bubble.setObjectName("loadingBubble")
        bubble.setStyleSheet("""
            #loadingBubble {
                background-color: #E3F2FD;
                border: 1px solid #BBDEFB;
                border-radius: 15px 15px 15px 0;
                padding: 8px;
                min-width: 80px;
            }
        """)
        
        # 气泡内布局
        bubble_layout = QHBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        
        # 加载文本
        self.loading_label = QLabel("AI思考中")
        self.loading_label.setStyleSheet("color: #1A237E; font-size: 14px;")
        
        bubble_layout.addWidget(self.loading_label)
        layout.addWidget(bubble)
        layout.addStretch(1)
        
        # 设置动画计时器
        self.dots_count = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(500)  # 每500ms更新一次
    
    def update_animation(self):
        """更新加载动画文本"""
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.loading_label.setText(f"AI思考中{dots}")
    
    def stop_animation(self):
        """停止动画"""
        self.animation_timer.stop()
