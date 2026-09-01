---
name: agent-reach
description: Use when searching or extracting multimedia content including Bilibili/YouTube video subtitles, RSS feeds, and clean web text.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [multimedia, youtube, bilibili, rss, search, scraping]
  related_skills: [multi-platform-distribution, markdown-to-html-report]
---

# Agent Reach — Multimedia & Clean Content Extraction

## Overview

Agent Reach empowers AI Agents to break through plain HTML web boundaries, enabling direct extraction and synthesis of multimedia content including **YouTube subtitles, Bilibili video transcripts, RSS subscription feeds, and clutter-free web markdown**.

## When to Use & When NOT to Use

### When to Use
- Extracting subtitles/transcripts from YouTube or Bilibili videos for summarization.
- Querying RSS/Atom feeds for continuous tracking of newsletters, blogs, and podcasts.
- Extracting clean, ad-free Markdown from web pages via reader APIs.
- Cross-platform technical topic research across video and text sources.

### When NOT to Use
- Simple static web downloads where standard `curl` or `requests` is sufficient.
- Large video/audio binary file processing (use `ffmpeg` or `media_info` instead).
- Platforms requiring active browser UI automation (use CDP browser tools instead).

## Core Workflow & Tool Commands

| Target Source | Tool / Command | Output Format | Key Flags |
|---|---|---|---|
| **YouTube Subtitles** | `yt-dlp --write-auto-subs --sub-lang "zh-Hans,en" --skip-download <URL>` | VTT / SRT Subtitles | `--skip-download` (No heavy video) |
| **Bilibili Transcripts** | `bili video <BV_ID> --subtitles` | JSON / Plain Text | Extracts native AI/CC subtitles |
| **Clean Web Text** | `curl -s https://r.jina.ai/<URL>` | Clean Markdown | Strips ads, navbars, and boilerplate |
| **RSS / Atom Feeds** | `python3 -c "import feedparser; ..."` or `curl -s <Feed_URL>` | Structured Feed XML | Parse titles, links, published dates |

## Common Pitfalls

1. **Downloading entire video files unnecessarily**: Always pass `--skip-download` to `yt-dlp` when only transcript/subtitle metadata is needed.
2. **Cloudflare WAF on RSS feeds**: Direct `curl` to sites like V2EX or forums may return 403 Forbidden; use public RSSHub instances (e.g. `rsshub.app`) as a transparent proxy.
3. **Missing subtitle tracks**: Some videos only have auto-generated subtitles; specify fallback languages like `--sub-lang "zh-Hans,zh,en,auto"`.

## Verification Checklist

- [ ] `yt-dlp --version` returns version ≥ 2024.01.01.
- [ ] Subtitle extraction test: `yt-dlp --list-subs <Test_URL>` lists available tracks.
- [ ] Web reader test: `curl -fsS https://r.jina.ai/https://example.com` returns clean markdown.
