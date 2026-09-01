---
name: telegram-pipe-table-rendering
description: Use when sending Markdown tables to Telegram, resolving table degradation, CJK East Asian character alignment, and mobile viewport wrapping.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [telegram, markdown, pipe-table, formatting, bot-api, cjk-alignment]
  related_skills: [multi-platform-distribution]
---

# Telegram Markdown Pipe Table Rendering & CJK Alignment

## Overview

A comprehensive engineering guide and solution for rendering Markdown pipe tables in Telegram bots without broken layouts. It covers **Bot API native rendering, CJK character width compensation, standalone cron delivery bypass, and automatic mobile card degradation**.

## When to Use & When NOT to Use

### When to Use
- Formatting LLM tabular output for Telegram bots (Hermes, python-telegram-bot, Aiogram).
- Fixing character misalignment caused by mixed Chinese/Japanese/Korean and ASCII characters in Monospace tables.
- Preventing wide tables (>5 columns) from turning into mangled text on mobile Telegram clients.

### When NOT to Use
- Standard web browsers or HTML-native rendering environments where CSS handles table layouts.
- Platforms with native rich table APIs (e.g. Discord embeds or Slack blocks).

## The Telegram Table Truth & Solutions Matrix

| Delivery Path | Native Table Support | What Actually Happens | Best Solution |
|---|:---:|---|---|
| **Bot API `sendRichMessage`** | ✅ Yes | Renders native GFM pipe tables | Pass raw markdown directly to `sendRichMessage` endpoint |
| **Standard `sendMessage` (MarkdownV2)** | ❌ No | Telegram has no table syntax in MarkdownV2; `|` is just a char | Pre-format with CJK padding or degrade wide tables to cards |
| **Standalone Cron / Webhook** | ⚠️ Partial | Often converted to bullet points by intermediary adapters | Direct Bot API webhook or use `telegram-table-renderer` package |

## Python CJK Padding Algorithm

```python
import unicodedata

def get_cjk_width(text: str) -> int:
    """Calculate visual width in monospace terminal font."""
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in text)

def pad_cjk_cell(text: str, target_width: int, align: str = 'left') -> str:
    current_width = get_cjk_width(text)
    pad = max(0, target_width - current_width)
    if align == 'right':
        return ' ' * pad + text
    elif align == 'center':
        left = pad // 2
        return ' ' * left + text + ' ' * (pad - left)
    return text + ' ' * pad
```

## Common Pitfalls

1. **Tables with ≥6 columns on mobile**: Telegram mobile screens are too narrow for 6-column tables; automatically degrade tables with >5 columns into structured bullet cards (`🔹 Key: Value`).
2. **MarkdownV2 character escaping errors**: In MarkdownV2 mode, unescaped reserved characters (`_`, `*`, `[`, `]`, `(`, `)`, `~`, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`) cause delivery failure.
3. **Double delivery on standalone scripts**: When writing direct Bot API delivery scripts, ensure output is not printed to stdout if cron delivery is also enabled.

## Verification Checklist

- [ ] Table borders align vertically in Telegram desktop and web clients.
- [ ] CJK characters count as 2 width units during cell padding calculation.
- [ ] Tables with >5 columns gracefully convert to card format when mobile mode is enabled.
