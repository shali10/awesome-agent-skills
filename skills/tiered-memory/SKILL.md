---
name: tiered-memory
description: Use when designing or managing AI Agent persistent memory architectures to prevent context overflow while preserving durable facts.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [agent-architecture, memory, context-management, prompt-engineering]
  related_skills: [agent-system-design]
---

# Tiered Memory Architecture for Autonomous Agents

## Overview

A deterministic, layered memory engineering framework that replaces naive full-context injection. It organizes agent memory into **4 distinct tiers (Core Injected, Topic Notes, Searchable Session History, and Ephemeral Working Memory)**, ensuring high signal-to-noise ratio and zero context bloating.

## When to Use & When NOT to Use

### When to Use
- Agent system design where memory exceeds 5,000 characters and causes context degradation.
- Multi-session persistence: preserving stable user preferences and environmental facts across restarts.
- Preventing memory drift and hallucinatory rule overrides.

### When NOT to Use
- Short, one-shot CLI tasks with no cross-session continuity requirements.
- Raw logging or storing multi-megabyte datasets (store in database / file assets instead).

## The 4-Tier Memory Hierarchy

| Tier | Name | Storage Location | Injected Every Turn? | Capacity Budget | Contents & Purpose |
|---|---|---|:---:|---|---|
| **L1** | **Core Memory** | `MEMORY.md` & `USER.md` | ✅ Yes | ≤ 10,000 chars (15%) | Durable user preferences, hard security redlines, production anchors |
| **L2** | **Topic Notes** | `notes/*.md` | ❌ On-demand | Uncapped (file-based) | Detailed architecture specs, server inventory, API docs read as needed |
| **L3** | **Session History** | SQLite `state.db` (FTS5) | ❌ Via search | Millions of messages | FTS5/Vector searchable past conversations and exact debug logs |
| **L4** | **Ephemeral Scratchpad** | Session context / `/tmp` | 🔄 Current turn | Cleared on exit | Intermediate tool results, active plan steps, disposable data |

## Common Pitfalls

1. **Saving transient task progress to L1 Core Memory**: Never record PR numbers, bug fixes, or step counts to `MEMORY.md`; they become stale in 7 days. Use session search instead.
2. **Imperative phrasing in memory**: Write memories as declarative facts (`"User prefers concise tables" ✓`), not directives (`"Always output tables" ✗`), to avoid overriding runtime instructions.
3. **Memory Sprawl**: When L1 exceeds 70% capacity, trigger automatic consolidation: merge duplicates, prune obsolete entries, and offload detailed guides to L2 notes.

## Verification Checklist

- [ ] L1 Core Memory is ≤ 70% of configured char budget.
- [ ] No temporary TODO state or session logs exist in `MEMORY.md`.
- [ ] Topic notes in `notes/` contain structured YAML frontmatter.
- [ ] Database FTS5 index is synchronized with message store.
