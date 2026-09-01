# 📱 Telegram Table Renderer & CJK Aligner

Zero-dependency Python module for formatting Markdown tables for Telegram, with accurate CJK (Chinese, Japanese, Korean) display width compensation, and graceful degradation for mobile viewports.

## ✨ Features

- 📏 **Accurate CJK Width Calculation**: Uses `unicodedata.east_asian_width` to correctly handle double-width East Asian characters in monospace fonts.
- 📱 **Mobile Graceful Degradation**: Wide tables (>5 columns) can automatically degrade into clean, readable structured cards.
- ⚡ **Zero Dependencies**: Pure Python standard library.

## 🚀 Quick Start

```python
from telegram_table_renderer import format_telegram_markdown

markdown_text = """
| 节点名称 | 状态 | 内存占用 | 延迟 |
|:---|:---:|---:|---:|
| 主控节点 (Debian 13) | 🟢 在线 | 1.2G / 3.8G | 12ms |
| 异地温备节点 London | 🟢 备用 | 512M / 1.0G | 120ms |
"""

formatted = format_telegram_markdown(markdown_text)
print(formatted)
```
