import json
import logging
from pathlib import Path
from collections import defaultdict

class RestoreProcessor:
    """恢复处理器, 将提供的json文件还原成中英两篇md文档"""

    def __init__(self):
        """初始化恢复处理器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _read_file(self, filepath: str) -> str:
        """读取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            self.logger.warning(f"读取文件 {filepath} 失败: {str(e)}")
            return ""

    def _write_to_md(self, filepath, content):
        """将内容写入md文件"""
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(content + "\n\n")
    
    def _process_section(self, section, output_path_en, output_path_zh, level=1):
        """处理文档的一个章节，递归处理子章节"""
        # 处理标题
        title_prefix = "#" * level
        
        # 英文标题
        en_title = f"{title_prefix} {section['title']}"
        self._write_to_md(output_path_en, en_title)
        
        # 中文标题
        zh_title = f"{title_prefix} {section.get('translated_title')}"
        self._write_to_md(output_path_zh, zh_title)
        
        # 处理正文内容
        if 'content' in section and section['content']:
            # 创建一个有序的结构来存储所有内容项及其位置信息
            ordered_items = []
            
            # 使用字典来存储按索引分组的文本块
            en_text_blocks = defaultdict(list)
            zh_text_blocks = defaultdict(list)
            
            # 第一遍遍历：收集所有内容项
            for item in section['content']:
                if isinstance(item, str):  # 如果直接是字符串（参考文献等）
                    ordered_items.append({
                        'type': 'ref',
                        'content': item,
                        'index': float('inf'),  # 参考文献通常放在最后
                        'part': 0
                    })
                elif isinstance(item, dict):
                    item_type = item.get('type')
                    index = item.get('index', 0)
                    part = item.get('part', 0)
                    
                    if item_type == 'text':
                        # 处理文本内容：先收集起来，稍后合并相同index的
                        en_content = item.get('content', '')
                        zh_content = item.get('translated_content', en_content)
                        
                        # 按索引和部分存储内容
                        en_text_blocks[index].append((part, en_content))
                        zh_text_blocks[index].append((part, zh_content))
                        
                        # 记录这个文本块的位置信息，用于最终有序处理
                        ordered_items.append({
                            'type': 'text',
                            'index': index,
                            'part': part
                        })
                    
                    elif item_type == 'formula':
                        ordered_items.append({
                            'type': 'formula',
                            'content': item.get('content', ''),
                            'index': index,
                            'part': part
                        })
                    
                    elif item_type == 'figure':
                        ordered_items.append({
                            'type': 'figure',
                            'src': item.get('src', ''),
                            'alt': item.get('alt', ''),
                            'en_caption': item.get('caption', ''),
                            'zh_caption': item.get('translated_caption', item.get('caption', '')),
                            'index': index,
                            'part': part
                        })
                    
                    elif item_type == 'table':
                        ordered_items.append({
                            'type': 'table',
                            'content': item.get('content', ''),
                            'en_caption': item.get('caption', ''),
                            'zh_caption': item.get('translated_caption', item.get('caption', '')),
                            'index': index,
                            'part': part
                        })
            
            # 按索引和部分排序所有内容
            ordered_items.sort(key=lambda x: (x['index'], x['part']))
            
            # 处理已合并的文本块索引集合
            processed_text_indices = set()
            
            # 按照排序后的顺序写入内容
            for item in ordered_items:
                if item['type'] == 'text':
                    index = item['index']
                    
                    # 如果这个索引的文本块已经处理过，跳过
                    if index in processed_text_indices:
                        continue
                    
                    # 合并并写入相同索引的文本块
                    # 对相同index的文本块按part排序
                    en_parts = sorted(en_text_blocks[index], key=lambda x: x[0])
                    zh_parts = sorted(zh_text_blocks[index], key=lambda x: x[0])
                    
                    # 合并相同index的文本块
                    en_content = ' '.join([part[1] for part in en_parts])
                    zh_content = ' '.join([part[1] for part in zh_parts])
                    
                    # 写入合并后的内容
                    self._write_to_md(output_path_en, en_content)
                    self._write_to_md(output_path_zh, zh_content)
                    
                    # 标记这个索引已处理
                    processed_text_indices.add(index)
                
                elif item['type'] == 'formula':
                    # 处理公式（公式在中英文文档中保持一致）
                    self._write_to_md(output_path_en, item['content'])
                    self._write_to_md(output_path_zh, item['content'])
                
                elif item['type'] == 'figure':
                    # 英文图片说明
                    en_figure = f"![{item['alt']}]({item['src']})\n\n*{item['en_caption']}*"
                    self._write_to_md(output_path_en, en_figure)
                    
                    # 中文图片说明
                    zh_figure = f"![{item['alt']}]({item['src']})\n\n*{item['zh_caption']}*"
                    self._write_to_md(output_path_zh, zh_figure)
                
                elif item['type'] == 'table':
                    # 表格内容在中英文文档中保持一致
                    self._write_to_md(output_path_en, item['content'])
                    self._write_to_md(output_path_zh, item['content'])
                    
                    # 处理表格标题
                    if item['en_caption']:
                        en_caption = f"*{item['en_caption']}*"
                        self._write_to_md(output_path_en, en_caption)
                        
                        zh_caption = f"*{item['zh_caption']}*"
                        self._write_to_md(output_path_zh, zh_caption)
                
                elif item['type'] == 'ref':
                    # 参考文献保持原样
                    self._write_to_md(output_path_en, item['content'])
                    self._write_to_md(output_path_zh, item['content'])
        
        # 递归处理子章节
        if 'children' in section and section['children']:
            for child in section['children']:
                self._process_section(child, output_path_en, output_path_zh, level + 1)
    
    def process(self, input_path: str, output_path_en: str, output_path_zh: str) -> tuple:
        """
        读取 input.json，恢复成中英文两篇md文档
        1. 中文用翻译部分；如果没有翻译则保留英文原文
        """
        try:
            input_path = Path(input_path)
            output_path_en = Path(output_path_en)
            output_path_zh = Path(output_path_zh)
            
            # 确保输出目录存在
            output_path_en.parent.mkdir(parents=True, exist_ok=True)
            output_path_zh.parent.mkdir(parents=True, exist_ok=True)
            
            # 清空输出文件
            open(output_path_en, 'w', encoding='utf-8').close()
            open(output_path_zh, 'w', encoding='utf-8').close()
            
            self.logger.info(f"开始处理JSON文件: {input_path}")
            with input_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理文档标题
            title_en = data.get('title', '')
            self._write_to_md(output_path_en, f"# {title_en}")
            
            title_zh = data.get('translated_title', title_en)
            self._write_to_md(output_path_zh, f"# {title_zh}")
            
            # 处理作者信息
            if 'authors_info' in data:
                self._write_to_md(output_path_en, data['authors_info'])
                self._write_to_md(output_path_zh, data['authors_info'])
            
            # 处理各个章节
            for section in data['sections']:
                self._process_section(section, output_path_en, output_path_zh)
            
            self.logger.info(f"恢复完成，结果已保存到: {output_path_en} 和 {output_path_zh}")
            return output_path_en, output_path_zh
        except Exception as e:
            self.logger.error(f"JSON处理失败: {str(e)}", exc_info=True)
            raise


# 使用示例
if __name__ == "__main__":
    processor = RestoreProcessor()
    processor.process(
        "output/HUMAN-LIKE EPISODIC MEMORY FOR INFINITE CONTEXT LLMS/HUMAN-LIKE EPISODIC MEMORY FOR INFINITE CONTEXT LLMS_translated.json",
        "output_english.md",
        "output_chinese.md"
    )