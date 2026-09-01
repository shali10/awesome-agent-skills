---
name: human-voice-writing
description: >
  Write technical content that reads like a person wrote it, not a machine.
  Covers positive patterns for injecting author voice, empathy, colloquial phrasing,
  and conversational rhythm into blog posts and tutorials.
  Load when user compares your output to human-written content, says
  "你看看别人写的", or you need to rewrite existing content to sound less AI-generated.
tags:
  - tone
  - voice
  - writing-style
  - human
  - blog
  - tutorial
  - chinese-blog
triggers:
  - "写得像人话"
  - "你看看别人写的"
  - "没有温度"
  - "像说明书"
  - "语气"
  - "AI 腔"
  - "人味"
related_skills:
  - creative/technical-tutorial-writing
version: 1.0.0
author: hermes-agent
created: 2026-07-30
---

# Human Voice Writing for Technical Content

> Write like a person who knows their stuff, not a documentation bot.

## When to load

- User says "你看看别人写的博客文章，再看看你自己写的"
- User asks you to rewrite content to be less "AI-generated"
- User says "写得像人话" or "没有温度"
- You're drafting a long-form blog post or tutorial
- User says "不要像说明书" or "太干巴巴了"

## Core principle

The gap between AI-written and human-written content isn't about accuracy — it's about **author presence**. A human writer leaves fingerprints: shared experience, conversational rhythm, empathy for the reader's struggle, and moments of personality. An AI removes all of these to sound "professional," and the result is hollow.

## 10 positive patterns (what TO do)

### 1. Empathetic opener — assume the reader is struggling

```
❌ 适用系统：Debian / Ubuntu / 大多数 Linux VPS
✅ 当你点进这篇文章时，说明你应该已经遇到了"服务跑起来了但不知道怎么让别人访问"的问题。
```

- Names the pain point the reader is experiencing
- Validates that they came to the right place
- Creates a collaborative "we're in this together" tone
- **Never** start with system requirements or a table of contents

### 2. Shared-experience voice

```
❌ 反向代理的作用是将请求转发到后端服务
✅ 我也是这么过来的。一台 VPS，装了个应用，127.0.0.1:8080 能打开，但发给朋友，朋友打不开。
```

- Establishes credibility through shared journey, not authority
- "我也是这么过来的" is more effective than "我有多年的经验"
- Reader thinks: "这个作者懂我的处境"

### 3. Conversational transitions, not numbered sections

```
❌ ## 3. 安装 Nginx
✅ 好，发车。

❌ ## 4. 确认后端服务
✅ 反代之前，先确认你的服务真的在跑。
```

- Replace "下面我们来…" / "本章节将介绍…" with colloquial resets
- "好，发车" / "完事" / "通杀" / "搞定" work in Chinese tech blogs
- Each transition feels like a person steering the conversation

### 4. Anticipate confusion and dismiss it casually

```
❌ 以下为配置项的解释说明
✅ 你说这些 proxy_set_header 是啥？不用管，抄就完事了。
```

- Reader doesn't need every detail explained on first read
- Acknowledge the potential confusion and explicitly give permission to skip it
- Saves the explanation for when they actually need it
- Builds trust: "this author knows what matters and what doesn't"

### 5. Replace formal instructions with colloquial phrasing

| ❌ AI default | ✅ Human voice |
|---|---|
| "建议使用" / "请确保" | "抄就完事了" / "八成" |
| "您需要" / "您应当" | "你去", "你用" |
| "以下为详细说明" | "其实没那么复杂" |
| "综上所述" / "总而言之" | "说穿了就是" |
| "如有疑问请参考" | "通杀" (covers all cases) |
| "这是一个典型的" | "最常见" |
| "请按照以下步骤" | "来，一步步走" |
| "本教程将介绍" | "核心就一句话" |

**Rule of thumb**: If you wouldn't say it to a friend over a beer, don't write it.

### 6. Table minimalism — only for value-mapping

Tables serve one purpose: letting the reader swap in their own values. Everything else should be narrative.

- ✅ **Use tables for**: domain↔port mapping (reader needs to replace these)
- ❌ **Avoid tables for**: feature comparison, config explanations, pros/cons
- ❌ **Avoid tables for**: every step summary
- ✅ **Use prose for**: what happened, why it matters, what to expect

A page full of tables reads like a spec sheet, not a blog post.

### 7. Author voice in closing

```
❌ 本教程详细介绍了 X 的配置方法，希望对你有所帮助。
✅ 好了，现在去给你的服务上个域名吧。有什么问题评论区见。
```

- Closing should feel like the end of a conversation, not a manual conclusion
- Common human closes: "好了，去试试吧" / "有问题评论区见" / "先这样吧"
- Don't summarize the steps again — the reader just did them
- One playful line near the end humanizes the entire piece

### 8. Code blocks are for machines, prose is for people

- Explanation text NEVER goes inside a code block
- Code blocks must be directly copy-pastable and runnable
- If a value must vary, define it as a shell variable FIRST, then reference it
- Never put `<placeholder>` inside a command — the reader will try to run it literally

### 9. Minimize structural hierarchy

- Avoid deep nesting (1.1 → 1.1.1 → 1.1.1.1)
- Linear flow: opener → prep → steps → pitfalls → closing
- If a table of contents is needed, keep it short (5-8 items, not 19)
- Deep hierarchy screams "AI generated this"

### 10. Allow playfulness and personality

```
❌ 本文采用 CC BY-NC-SA 4.0 许可协议
✅ 只要你不要说：节点怎么用？？？就谢天谢地了。（before license, as closing joke）
```

- One joke or playful line near the end humanizes the entire piece
- Keep it relevant to the reader's journey (the most common dumb question they're about to ask)
- Self-deprecating humor works especially well in blog posts

## The 80/20 rule

If you only do ONE thing differently from your default: **rewrite the opener**. The first paragraph sets the entire tone. A human opener makes everything that follows feel human by association.

```
Default: "本教程将介绍 Nginx 反向代理的配置方法，适用于..."
Human:   "当你点进这篇文章时，说明你应该已经遇到了..."
```

Change the opener, and the rest follows naturally.

## Reference: real examples

### Before (AI-written)

```markdown
## 1. 反向代理是什么

很多服务默认只监听本地端口，例如：
http://127.0.0.1:8080

Nginx 反向代理的作用就是：

用户访问 https://app.example.com → Nginx 接收请求 → Nginx 转发到 http://127.0.0.1:8080 → 后端服务返回结果 → Nginx 再返回给用户

外部用户只看到域名，不需要知道真实端口。
```

### After (human rewrite)

```markdown
当你点进这篇文章时，说明你应该已经遇到了"服务跑起来了，但不知道怎么让别人访问"的问题。

我也是这么过来的。一台 VPS，装了个应用，127.0.0.1:8080 能打开，但发给朋友，朋友打不开。一搜"反向代理"四个字，一堆专业术语直接劝退。

其实没那么复杂。核心就一句话：让用户敲域名访问你的服务，而不是敲 IP 加端口。

好，发车。
```

The "After" has:
- Empathetic opener
- Shared experience
- Simplified explanation
- Conversational transition
- No tables, no numbered sections

## When NOT to use this skill

- User explicitly asks for a terse, documentation-style answer
- User wants a reference card / quick-start (brevity over personality)
- Internal documentation where clarity trumps voice
- Machine-to-machine interface docs
