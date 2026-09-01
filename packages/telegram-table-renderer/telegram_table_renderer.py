"""
Telegram Table Renderer & CJK Aligner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zero-dependency Python module for formatting Markdown tables for Telegram,
with accurate CJK (Chinese, Japanese, Korean) display width compensation,
and graceful degradation for mobile / narrow viewports.

Author: shali10 & Hermes Community
License: MIT
"""

import re
import unicodedata
from typing import List, Tuple, Optional

def get_display_width(text: str) -> int:
    """
    Calculate the actual visual width of a string in monospace/terminal font.
    CJK fullwidth/wide characters (W, F) count as 2 units, others count as 1 unit.
    """
    width = 0
    for ch in text:
        status = unicodedata.east_asian_width(ch)
        if status in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width

def pad_cjk(text: str, target_width: int, align: str = 'left') -> str:
    """
    Pad a string containing CJK characters to a specific visual width.
    """
    current_width = get_display_width(text)
    pad_len = max(0, target_width - current_width)
    if align == 'right':
        return ' ' * pad_len + text
    elif align == 'center':
        left = pad_len // 2
        right = pad_len - left
        return ' ' * left + text + ' ' * right
    else: # left
        return text + ' ' * pad_len

class TableParser:
    """Parses and formats GFM Markdown pipe tables."""

    @staticmethod
    def is_table_divider(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            return False
        cells = [c.strip() for c in stripped[1:-1].split('|')]
        return all(re.match(r'^:?-+:?$', c) for c in cells if c)

    @classmethod
    def parse_table(cls, table_lines: List[str]) -> Tuple[List[str], List[str], List[List[str]]]:
        """
        Parses table lines into headers, alignments, and rows.
        Alignments: 'left', 'right', 'center'.
        """
        if len(table_lines) < 2:
            return [], [], []

        # Header
        headers = [c.strip() for c in table_lines[0].strip()[1:-1].split('|')]

        # Alignments from divider
        alignments = []
        if cls.is_table_divider(table_lines[1]):
            div_cells = [c.strip() for c in table_lines[1].strip()[1:-1].split('|')]
            for cell in div_cells:
                if cell.startswith(':') and cell.endswith(':'):
                    alignments.append('center')
                elif cell.endswith(':'):
                    alignments.append('right')
                else:
                    alignments.append('left')
            data_start = 2
        else:
            alignments = ['left'] * len(headers)
            data_start = 1

        # Pad alignments if mismatched
        while len(alignments) < len(headers):
            alignments.append('left')

        rows = []
        for line in table_lines[data_start:]:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                cells = [c.strip() for c in stripped[1:-1].split('|')]
                # Pad/truncate cells to header count
                if len(cells) < len(headers):
                    cells.extend([''] * (len(headers) - len(cells)))
                rows.append(cells[:len(headers)])

        return headers, alignments, rows

    @classmethod
    def render_aligned_table(cls, headers: List[str], alignments: List[str], rows: List[List[str]]) -> str:
        """
        Renders a GFM table with visual CJK alignment.
        """
        if not headers:
            return ""

        num_cols = len(headers)
        col_widths = [get_display_width(h) for h in headers]

        for row in rows:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_widths[i] = max(col_widths[i], get_display_width(cell))

        # Ensure minimum column width
        col_widths = [max(w, 3) for w in col_widths]

        lines = []

        # Header line
        header_cells = [pad_cjk(h, col_widths[i], alignments[i]) for i, h in enumerate(headers)]
        lines.append(f"| {' | '.join(header_cells)} |")

        # Divider line
        div_cells = []
        for i, align in enumerate(alignments):
            w = col_widths[i]
            if align == 'center':
                div_cells.append(':' + '-' * max(1, w - 2) + ':')
            elif align == 'right':
                div_cells.append('-' * max(1, w - 1) + ':')
            else:
                div_cells.append('-' * w)
        lines.append(f"|{'-|-'.join(div_cells)}|")

        # Row lines
        for row in rows:
            row_cells = [pad_cjk(cell, col_widths[i], alignments[i]) for i, cell in enumerate(row)]
            lines.append(f"| {' | '.join(row_cells)} |")

        return "\n".join(lines)

    @classmethod
    def table_to_bullets(cls, headers: List[str], rows: List[List[str]]) -> str:
        """
        Degrades a wide table into a clean, readable structured card/bullet list for mobile screens.
        """
        if not headers or not rows:
            return ""

        output = []
        for idx, row in enumerate(rows, 1):
            title_cell = row[0] if row else f"Item {idx}"
            output.append(f"🔹 **{title_cell}**")
            for h, val in zip(headers[1:], row[1:]):
                if val:
                    output.append(f"  • {h}: {val}")
            output.append("") # Blank line separator between cards

        return "\n".join(output).strip()


def format_telegram_markdown(text: str, max_table_cols: int = 5, degrade_wide: bool = True) -> str:
    """
    Scans Markdown text, finds GFM pipe tables, and formats them:
    - Tables <= max_table_cols: Perfectly aligned with CJK width compensation.
    - Tables > max_table_cols (if degrade_wide=True): Gracefully converted to mobile-friendly structured cards.
    """
    lines = text.split("\n")
    result_lines = []
    in_table = False
    table_buffer = []

    for line in lines:
        stripped = line.strip()
        is_table_line = stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 2

        if is_table_line:
            in_table = True
            table_buffer.append(line)
        else:
            if in_table:
                # Process accumulated table
                headers, aligns, rows = TableParser.parse_table(table_buffer)
                if headers:
                    if degrade_wide and len(headers) > max_table_cols:
                        result_lines.append(TableParser.table_to_bullets(headers, rows))
                    else:
                        result_lines.append(TableParser.render_aligned_table(headers, aligns, rows))
                else:
                    result_lines.extend(table_buffer)
                table_buffer = []
                in_table = False

            result_lines.append(line)

    if in_table and table_buffer:
        headers, aligns, rows = TableParser.parse_table(table_buffer)
        if headers:
            if degrade_wide and len(headers) > max_table_cols:
                result_lines.append(TableParser.table_to_bullets(headers, rows))
            else:
                result_lines.append(TableParser.render_aligned_table(headers, aligns, rows))
        else:
            result_lines.extend(table_buffer)

    return "\n".join(result_lines)


if __name__ == "__main__":
    test_md = """
# System Health Check

| 节点名称 | 状态 | 内存占用 | 延迟 | 判定 |
|:---|:---:|---:|---:|:---:|
| 主控节点 Hytron (Debian 13) | 🟢 在线 | 1.2G / 3.8G | 12ms | 卓越 |
| 生产业务集群 Raksmart | 🟢 在线 | 4.8G / 8.0G | 45ms | 正常 |
| 异地温备节点 London | 🟢 备用 | 512M / 1.0G | 120ms | 健康 |
| 香港业务节点 zhououou | 🟢 在线 | 800M / 3.8G | 28ms | 极速 |

Enjoy your day!
"""
    print("--- Aligned Output ---")
    print(format_telegram_markdown(test_md))
