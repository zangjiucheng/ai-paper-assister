import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

class JsonProcessor:
    """
    JSON处理器：顺序扫描章节内容，保证文本块的输出顺序与原行一致，
    并能将脚注行（上一行或下一行）合并到图片块的caption中。
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 匹配行间公式：整行只包含 $$...$$
        self.formula_pattern = re.compile(r"^\s*\${2}(?P<formula>.*?)\${2}\s*$", re.DOTALL)

        # 匹配Markdown图片：形如 ![alt](path/to/img.png)
        self.image_pattern = re.compile(r'^!\[.*?\]\(.*?\)')

        # 匹配HTML表格：形如 <html><body><table>...</table></body></html>
        self.table_pattern = re.compile(r'^<html><body><table>.*?</table></body></html>$')

        # 匹配图片说明
        self.figure_caption_pattern = re.compile(r'''
            ^(?:
                (?:Figure|Fig\.)                       # Figure或Fig.
                (?:\s+\(?\d+(?:\.\d+)?\)?\.?:?)       # (1), 1:, 1., (1.1), 1.1:等
                |
                (?:IMAGE|DIAGRAM)                      # IMAGE或DIAGRAM
                (?:\s+\d+:?)                          # 1:, 1
                |
                (?:Figure)                            # Figure
                (?:\s+[IVX]+:?)                       # I:, II, III, IV等
            )
        ''', re.IGNORECASE | re.VERBOSE)

        # 匹配表格说明
        self.table_caption_pattern = re.compile(r'''
            ^(?:
                (?:Table|Tab\.)                        # Table或Tab.
                (?:\s+\(?\d+(?:\.\d+)?\)?\.?:?)       # (1), 1:, 1., (1.1), 1.1:等
                |
                (?:Table)                             # Table
                (?:\s+[IVX]+:?)                       # I:, II, III, IV等
            )
        ''', re.IGNORECASE | re.VERBOSE)

    def process(self, input_path: str, output_path: str) -> Path:
        """
        读取 input.json ，递归地处理其 sections（含子章节），
        对每个section的 content 做顺序扫描拆分，并写入 output.json。
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            self.logger.info(f"开始处理JSON文件: {input_path}")
            with input_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # 处理顶层 sections
            sections = data.get("sections", [])
            processed_sections = []
            for sec in sections:
                processed_sections.append(self._process_section(sec))

            data["sections"] = processed_sections

            # 输出结果
            self.logger.info(f"保存处理结果到: {output_path}")
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return output_path

        except Exception as e:
            self.logger.error(f"JSON处理失败: {str(e)}", exc_info=True)
            raise

    def _process_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个章节：
         - 对当前section的 content 做行级顺序扫描，拆分成 figure / table/ formula / text 块
         - 递归处理其子章节 (children)
        """
        # 如果type为references，直接返回原section
        if section.get("type") == "references":
            return section

        lines = section.get("content", [])
        blocks = self._split_content_with_order(lines)

        # 用处理后的 blocks 替换原 content
        section["content"] = blocks

        # 递归处理子章节
        children = section.get("children", [])
        new_children = []
        for child in children:
            new_children.append(self._process_section(child))
        section["children"] = new_children

        return section

    def _split_content_with_order(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        单次自上而下扫描，保证块的输出顺序与原行顺序一致。
        """
        blocks = []
        n = len(lines)
        used = [False] * n  # 标记哪些行已被处理

        i = 0
        while i < n:
            if used[i]:
                i += 1
                continue

            line = lines[i].rstrip('\n')
            stripped = line.strip()

            # 1) 行间公式
            m_formula = self.formula_pattern.match(stripped)
            if m_formula:
                formula_body = m_formula.group("formula")
                blocks.append({
                    "type": "formula",
                    "content": f"$$ {formula_body} $$"
                })
                used[i] = True
                i += 1
                continue

            # 2) 处理图片
            m_img = self.image_pattern.match(stripped)
            if m_img:
                used[i] = True
                alt_text, src = self._extract_alt_and_src(stripped)
                
                caption_line = ""
                caption_index = None

                # 检查上下文是否有图片说明
                caption_line, caption_index = self._find_caption(
                    lines, i, used, self.figure_caption_pattern
                )

                # 如果找到说明，标记已使用
                if caption_line and caption_index is not None:
                    used[caption_index] = True

                fig_block = {
                    "type": "figure",
                    "src": src,
                    "alt": alt_text
                }
                if caption_line:
                    fig_block["caption"] = caption_line

                blocks.append(fig_block)
                i += 1
                continue

            # 3) 处理表格
            m_table = self.table_pattern.match(stripped)
            if m_table:
                used[i] = True
                
                caption_line = ""
                caption_index = None

                # 检查上下文是否有表格说明
                caption_line, caption_index = self._find_caption(
                    lines, i, used, self.table_caption_pattern
                )

                # 如果找到说明，标记已使用
                if caption_line and caption_index is not None:
                    used[caption_index] = True

                table_block = {
                    "type": "table",
                    "content": stripped
                }
                if caption_line:
                    table_block["caption"] = caption_line

                blocks.append(table_block)
                i += 1
                continue

            # 4) 处理普通文本，跳过caption
            if (not self.figure_caption_pattern.match(stripped) and 
                not self.table_caption_pattern.match(stripped)):
                text_block = {
                    "type": "text",
                    "content": line
                }
                used[i] = True
                blocks.append(text_block)
            else:
                # 如果是caption，仅增加索引
                i += 1
                continue
            
            i += 1

        return blocks

    def _find_caption(self, lines: List[str], current_index: int, used: List[bool], 
                     caption_pattern: re.Pattern) -> Tuple[str, int]:
        """查找图片或表格的说明文字"""
        n = len(lines)
        
        # 优先检查上一行
        if current_index - 1 >= 0 and not used[current_index - 1]:
            prev_stripped = lines[current_index - 1].strip()
            if caption_pattern.match(prev_stripped):
                return prev_stripped, current_index - 1

        # 再检查下一行
        if current_index + 1 < n and not used[current_index + 1]:
            next_stripped = lines[current_index + 1].strip()
            if caption_pattern.match(next_stripped):
                return next_stripped, current_index + 1

        return "", None

    def _extract_alt_and_src(self, image_markdown_line: str) -> Tuple[str, str]:
        """
        从 ![alt文本](path/to/xxx.png) 的行里解析 alt / src。
        """
        pattern = re.compile(r'!\[(?P<alt>.*?)\]\((?P<src>.*?)\)')
        m = pattern.match(image_markdown_line)
        if not m:
            return "", ""
        return m.group("alt"), m.group("src")


if __name__ == "__main__":
    processor = JsonProcessor()
    try:
        output_path = processor.process("input.json","output.json")
        print(f"处理完成，输出文件：{output_path}")
    except Exception as e:
        print(f"处理失败：{e}")