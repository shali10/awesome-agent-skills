---
name: multi-platform-distribution
description: Use when adapting a single piece of Markdown content into tailored, platform-compliant formats for Telegram, WeChat, Zhihu, Twitter/X, and QQ.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [distribution, cross-platform, social-media, formatting, markdown]
  related_skills: [human-voice-writing, telegram-pipe-table-rendering]
---

# Multi-Platform Content Distribution & Formatting

## Overview

An intelligent content syndication and adaptation engine. It takes a master Markdown article and automatically transforms it into 5 platform-native formats, strictly adhering to each platform's distinct syntax quirks, character limits, escaping rules, and visual style.

## When to Use & When NOT to Use

### When to Use
- Cross-posting technical articles, product announcements, or newsletters to multiple platforms.
- Formatting Telegram posts with MarkdownV2 escaping and rich tables.
- Splitting long-form essays into structured Twitter/X threads.
- Optimizing codeblocks and image layouts for WeChat Official Accounts and Zhihu.

### When NOT to Use
- Single-target internal notes or local documentation.
- Automated spamming or unreviewed bulk posting.

## Platform Formatting Rules Matrix

| Platform | Syntax Support | Key Adaptation Rules | Max Length / Limits |
|---|---|---|---|
| **Telegram** | HTML / MarkdownV2 | Escape special chars (`_`, `*`, `[`, `]`); convert wide tables to cards; use native pipe tables | 4,096 chars per message |
| **WeChat (公众号)** | Rich Text HTML | Inline CSS styles; codeblocks inside distinct containers; high-contrast headings | Unlimited (Rich editor) |
| **Zhihu (知乎)** | GFM Markdown | Standard headers; convert unsupported HTML tags; ensure code fences specify language | Standard article format |
| **Twitter / X** | Plain text + Media | Split into numbered thread (1/N); extract key hook & stats in tweet 1; keep hashtags to ≤2 | 280 chars (free) / thread |
| **QQ / QQBot** | Markdown (Subset) | Avoid nested blockquotes; keep tables ≤4 columns; use emoji badges for visual hierarchy | 2,000 chars per message |

## Multi-Platform Generation Pipeline

1. **Input**: Master source Markdown text with images and tables.
2. **Analysis**: Detect target platforms requested by user.
3. **Transformation**:
   - Apply platform-specific parser rules and delimiter cleaners.
   - Truncate / split long text at logical section boundaries.
4. **Verification**: Confirm zero unescaped MarkdownV2 errors for Telegram and valid thread sequencing for Twitter.

## Common Pitfalls

1. **Unescaped entities in Telegram MarkdownV2**: Characters like `.` and `-` in plain text outside codeblocks will trigger `Bad Request` if unescaped; use proper entity escaping or raw HTML mode.
2. **Missing language tags in Zhihu code blocks**: Bare ```` ```` without language specification degrades syntax highlighting on Zhihu.
3. **Overcrowded tweets in threads**: Each tweet in a thread should deliver a standalone insight or takeaway, not cut sentences mid-thought.

## Verification Checklist

- [ ] Telegram output passes character escaping checks.
- [ ] Twitter thread output splits at paragraph ends with `(1/N)` numbering.
- [ ] Zhihu / WeChat outputs have formatted code fences.
