---
name: human-voice-writing
description: Use when writing technical tutorials, engineering blogs, and articles that sound like a real person with technical depth rather than robotic AI prose.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [content-creation, technical-writing, anti-ai, blogging]
  related_skills: [humanizer, multi-platform-distribution]
---

# Human Voice Technical Writing

## Overview

A systematic writing methodology that eliminates synthetic "AI-isms" (filler phrases, robotic customer-service tone, repetitive conclusions) and produces technical content with authentic human voice, grounded engineering insights, and engaging rhythm.

## When to Use & When NOT to Use

### When to Use
- Writing tech blog posts, tutorials, and architecture case studies.
- Refining AI-generated drafts into natural, engaging prose.
- Creating developer-focused changelogs, README showcases, and social posts.

### When NOT to Use
- Strict API documentation or JSON schema specs requiring purely mechanical descriptions.
- Formal legal compliance disclosures or raw telemetry logging.

## Core Writing Rules & Negative List

| Category | ❌ Strict Negative List (Never Use) | ✅ Human Alternative (Use Instead) |
|---|---|---|
| **AI Clichés** | "In today's fast-paced digital world...", "Delve into", "Tapestry" | Start directly with the core problem or command |
| **Robotic Openings** | "First and foremost...", "Let's embark on a journey..." | "Here is the exact setup that works in production:" |
| **Empty Summaries** | "In conclusion...", "It is important to remember that..." | End with a verification command, next step, or sharp tip |
| **Fluff Transitions** | "Moreover, it is worth noting that...", "Furthermore..." | Use clean bullet points or jump straight to the point |

## Structure of a Top-Tier Technical Post

1. **🎯 The Hook & Core Goal** (1-2 sentences: what we are building, without preamble).
2. **💻 Production-Ready Code / Config Block** (Full copy-pasteable configuration).
3. **🔍 Step-by-Step Practical Walkthrough** (Real commands with inline annotations).
4. **⚠️ Pitfalls & Real Battle Scars** (Actual bugs encountered and exact fixes).
5. **✅ Grounded Verification** (Exact command to confirm everything works).

## Common Pitfalls

1. **Over-polishing into corporate buzzwords**: Keep the conversational, grounded tone of an experienced engineer explaining things over coffee.
2. **Hiding critical config in prose**: Always put paths, flags, and environment variables into distinct code blocks or Markdown tables.
3. **Omitting the verification step**: A tutorial is incomplete without showing how to test and verify the final result.

## Verification Checklist

- [ ] Zero AI clichés (e.g. "delve", "testament", "tapestry", "furthermore") present.
- [ ] No boilerplate introductory paragraph before the first heading.
- [ ] All commands have been tested and include expected output.
