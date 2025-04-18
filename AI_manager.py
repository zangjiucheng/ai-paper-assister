from PyQt6.QtCore import QObject
from rag_retriever import RagRetriever
import os

class AIManager(QObject):
    """
    AI管理类 - 处理所有AI相关的功能
    
    包括:
    - RAG检索增强生成
    """

    def __init__(self):
        """初始化AI管理器"""
        super().__init__()

    def cleanup(self):
        """清理所有资源"""
        pass
    
    def set_data_manager(self, data_manager):
        """设置数据管理器引用"""
        self.data_manager = data_manager
    
    def init_rag_retriever(self, base_path):
        """在后台初始化RAG检索器"""
        try:
            print(f"[INFO] 开始初始化RAG检索器: {base_path}")
            
            # 创建RAG检索器并开始后台加载
            self.retriever = RagRetriever(base_path)
            
            # 连接加载完成信号以进行日志记录
            self.retriever.loading_complete.connect(self._on_retriever_loaded)
            
            return True
        except Exception as e:
            print(f"[ERROR] 初始化RAG检索器失败: {str(e)}")
            return False

    def _on_retriever_loaded(self, success):
        """处理检索器加载完成事件"""
        if success:
            print(f"[INFO] RAG检索器加载完成，共加载了 {len(self.retriever.paper_vector_paths)} 篇论文的向量库索引")
            
            # 可以添加额外验证代码
            for paper_id, path in self.retriever.paper_vector_paths.items():
                if not os.path.exists(path):
                    print(f"[WARNING] 论文 {paper_id} 的向量库路径不存在: {path}")
        else:
            print("[ERROR] RAG检索器加载失败或没有找到论文")

    def add_paper_vector_store(self, paper_id, vector_store_path):
        """添加新论文的向量库
        
        在处理完新论文后调用此方法
        
        Args:
            paper_id: 论文ID
            vector_store_path: 向量库路径
            
        Returns:
            bool: 成功返回True
        """
        if hasattr(self, 'retriever'):
            return self.retriever.add_paper(paper_id, vector_store_path)
        return False

    def _scroll_to_content(self, scroll_info):
        """根据滚动信息滚动到对应内容"""
        if not scroll_info:
            return
            
        # 获取当前语言
        current_lang = self.markdown_view.get_current_language()
        
        # 根据当前语言选择内容
        content = scroll_info['zh_content'] if current_lang == 'zh' else scroll_info['en_content']
        node_type = scroll_info.get('node_type', 'text')
        is_title = scroll_info.get('is_title', False)
        
        # 如果内容为空，尝试使用另一种语言的内容
        if not content:
            content = scroll_info['en_content'] if current_lang == 'zh' else scroll_info['zh_content']
        
        # 执行滚动
        if content:
            # 根据节点类型确定滚动类型
            if is_title:
                self.markdown_view._scroll_to_matching_content(content, 'title')
            else:
                self.markdown_view._scroll_to_matching_content(content, 'text')