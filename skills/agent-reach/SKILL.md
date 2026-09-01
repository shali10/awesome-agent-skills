---
name: agent-reach
description: 搜B站/YouTube字幕/语义搜索/RSS/网页读取时用。调bili/yt-dlp。
---

# Agent Reach 使用

## 触发场景
- 用户说"搜一下B站 xxx" / "B站这个视频讲了什么" → 用 `bili`
- 用户说"这个 YouTube 视频讲了什么/字幕" → 用 `yt-dlp`
- 用户说"语义搜索 xxx" / "全网搜 xxx" → Exa（经 mcporter 配置）
- 用户说"读取/看这个网页" → Jina Reader：`curl https://r.jina.ai/URL`
- 用户说"订阅/拉取 RSS" → feedparser 或 `curl` 直接抓 RSS/Atom

## 工具位置
- `bili`（bilibili-cli）：`/root/.local/bin/bili`，如 `bili search "query"`、`bili video <id>`
- `yt-dlp`：`/opt/agent-reach-venv/bin/yt-dlp`（字幕：`yt-dlp --write-auto-subs --skip-download`）
- `twitter`（twitter-cli）：`/root/.local/bin/twitter`（已配 X cookie：secrets/twitter_cookies.txt + bashrc env + wrapper `twx`，直接可用）
  - 读 X 长文：`twx article <tweet_id> -m -o out.md`（-m markdown，-o 存文件）
  - 验证登录：`twx whoami`（当前账号 @fhjjkn5）
  - cookie 明文仅在 secrets 文件（600），聊天/日志不回显
- `gh`：`/usr/local/bin/gh`（需 `gh auth login` 后可用）
- agent-reach CLI：`/opt/agent-reach-venv/bin/agent-reach`（doctor 体检 / configure 配置）
- 官方 skill 文档：`/root/.agents/skills/agent-reach/`（SKILL.md + references/）

## 环境
- venv：`/opt/agent-reach-venv`（Python 3.11 独立环境，不污染系统）
- 配置目录：`~/.agent-reach/`（config.json、tokens）
- 状态检查：`/opt/agent-reach-venv/bin/agent-reach doctor`

## 注意
- V2EX 官方 API/RSS 被 Cloudflare 403 拦截，需要走 RSSHub 公共实例（如 rsshub.rssforever.com）
- Twitter 需要用户提供登录 Cookie 才能用
- 平台对服务器 IP 有风控，失败时先 `agent-reach doctor` 看哪个渠道挂
