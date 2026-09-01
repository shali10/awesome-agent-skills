---
name: markdown-to-html-report
description: Use when converting plain Markdown documents into magazine-grade, responsive HTML reports and printable PDF documents with modern typography and card layouts.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [reporting, html, pdf, typography, css-design, export]
  related_skills: [large-file-data-analysis, human-voice-writing]
---

# Markdown to Magazine-Grade HTML & PDF Reports

## Overview

A high-aesthetic document compiler for AI Agents. It transforms dry Markdown into **comfortable, responsive, modern HTML5 reports** with soft shadows, sticky sidebar navigation, syntax-highlighted codeblocks, and automatic Mermaid diagram support, suitable for one-click PDF printing.

## When to Use & When NOT to Use

### When to Use
- Compiling research briefs, system audit reports, and whitepapers into standalone HTML files.
- Exporting client deliverables to high-resolution PDF via Headless Chromium.
- Fixing Markdown table misalignment and embedding images as base64 for offline sharing.

### When NOT to Use
- Generating simple raw terminal markdown or plain text logs.
- Interactive multi-page web applications with complex client-side state.

## Core Compilation Workflow

```bash
# Render markdown to standalone HTML with embedded images
python3 scripts/render_report.py input.md output.html --embed-images --with-js

# Verify image references and asset integrity
python3 scripts/check_image_refs.py output.html
```

| Key CLI Options | Description | Default |
|---|---|:---:|
| `--embed-images` | Embeds local images as Base64 data URIs for single-file sharing | `True` |
| `--with-js` | Adds reading progress bar, table-of-contents highlight, and back-to-top | `True` |
| `--mermaid-source auto` | Automatically renders ````mermaid```` diagram blocks via CDN/local | `auto` |
| `--title-style comfortable` | Clean magazine layout with balanced padding and font hierarchy | `comfortable` |

## Design Tokens & Layout Specs

- **Canvas & Card**: Soft neutral background (`#f8fafc`), pure white content article (`#ffffff`), 8px subtle border radius, soft 28px ambient drop shadow.
- **Typography**: System font stack with `line-height: 1.75`, clear heading scaling (`clamp(24px, 3vw, 42px)`), high contrast headers (`#0f172a`).
- **Responsive Tables**: Full-width container with `.table-scroll` horizontal overflow on mobile viewports.

## Common Pitfalls

1. **Broken table pipes in source markdown**: Full-width Chinese pipes (`｜`) cause table parser drops; the renderer automatically normalizes them to standard half-width `|`.
2. **Missing linebreaks before bullet lists**: Lists attached directly after colons without preceding empty lines fail to render in standard CommonMark; normalize whitespace before compilation.
3. **Huge file size from embedded images**: Optimize high-res PNG/JPEG assets before base64 embedding to prevent generating >50MB HTML files.

## Verification Checklist

- [ ] HTML output opens locally in any browser with zero network dependencies (when `--embed-images` enabled).
- [ ] Sticky table-of-contents navigates correctly to all section anchors.
- [ ] Tables scroll horizontally on viewports < 768px without breaking container width.
