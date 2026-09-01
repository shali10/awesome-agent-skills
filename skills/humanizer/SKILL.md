---
name: humanizer
description: Use when stripping AI writing patterns, corporate fluff, and synthetic tone from drafts to restore natural human cadence.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [editing, humanize, text-processing, style-guide]
  related_skills: [human-voice-writing]
---

# Text Humanizer & Anti-AI Tone Filter

## Overview

A specialized text purification skill that systematically scans, detects, and purges syntactic and semantic markers of LLM-generated text, transforming stiff output into natural, authentic human communication.

## When to Use & When NOT to Use

### When to Use
- Rewriting LLM output for developer blogs, emails, announcements, and documentation.
- Removing excessive hedging ("it may be beneficial to consider...") and passive voice.
- Enforcing concise, punchy technical communication.

### When NOT to Use
- Translating structured data tables or code blocks.
- Tasks requiring formal academic third-person passive syntax.

## Transformation Matrix

| LLM Pattern | Why It Feels Synthetic | Transformation Strategy |
|---|---|---|
| **Sycophantic Agreement** | "You make a great point! Absolutely..." | Delete entirely; answer the question directly |
| **Rule-of-Three Adjectives** | "Seamless, robust, and scalable solution" | Use one precise, factual description |
| **Passive Hedging** | "It could potentially be argued that..." | "In our tests, X caused Y." |
| **Synthetic Summaries** | "By following these steps, you will unlock..." | Replace with a concise summary table or next actions |

## Common Pitfalls

1. **Replacing AI fluff with informal slang**: Maintain professional engineering rigor while removing robotic phrasing.
2. **Changing factual meaning during simplification**: Ensure technical parameters, numbers, and commands remain identical.

## Verification Checklist

- [ ] Removed all instances of sycophantic opening filler.
- [ ] Converted passive hedges into direct, verifiable statements.
- [ ] Maintained 100% of original technical facts and parameter values.
