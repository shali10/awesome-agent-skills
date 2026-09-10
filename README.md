<div align="center">

# 🧰 Awesome AI Agent Skills & Toolbox

**精选生产级 AI Agent 实战技能包与工具集**  
*Production-ready skills, tools & architectures for AI Coding Agents (Hermes, Claude, OpenClaw, Cursor, etc.)*

[![Validate Skills](https://github.com/shali10/awesome-agent-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/shali10/awesome-agent-skills/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Hermes Agent: v0.21+](https://img.shields.io/badge/Hermes_Agent-Compatible-purple.svg)](https://hermes-agent.nousresearch.com/)
[![Zero-Ops](https://img.shields.io/badge/Architecture-Zero--Ops-orange.svg)]()

[English](#-overview-en) | [简体中文](#-技能全景一览)

</div>

---

## 📖 仓库简介 (Overview)

本项目收录了在真实复杂生产环境与多服务器集群中验证并沉淀的 **核心 Agent 技能包 (Skills)、独立 Python 中间件与运维自动化工具**。

无论你使用的是 **Hermes Agent**、**OpenClaw**、**Claude Code / Desktop**，还是自建的 AI Agent 系统，本项目所有技能均遵循业界标杆架构标准：
- 🎯 **清晰的适用边界**：明确包含「何时使用」与「何时不用 (When NOT to use)」；
- 🛡️ **负向清单与避坑指南**：提供 3~5 条经过真实验证的 `Common Pitfalls`；
- ⚡ **可验证的完成判据**：每项技能提供直接可复制执行的 `Verification Checklist`；
- 🔒 **100% 物理脱敏**：全量剥离私有凭据与 IP，纯净开箱即用！

---

## 🧭 技能全景一览 (Skills Matrix)

| 分类 | 技能目录 / 工具名称 | 核心能力与解决痛点 | 适用场景 |
|:---|---|---|:---:|
| 📱 **通信与排版** | [**`telegram-table-renderer`**](packages/telegram-table-renderer/) *(Python包)*<br>[**`telegram-pipe-table-rendering`**](skills/telegram-pipe-table-rendering/) | 解决 Telegram Markdown 表格被吞、CJK 中文宽度对齐与移动端超宽降级 | Telegram Bot / 消息投递 |
| 🔍 **多模态与调研** | [**`agent-reach`**](skills/agent-reach/) | 调用 `yt-dlp` / B站字幕引擎 / RSS / 网页正文，一键提取视频中文字幕与播客 | 深度研究 / 媒体转录 |
| 📑 **报告与设计** | [**`markdown-to-html-report`**](skills/markdown-to-html-report/) | 内置高颜值现代 CSS，将普通 Markdown 编译为杂志级 HTML / PDF 报告 | 成果汇报 / 设计感长文 |
| 📊 **数据与大文件** | [**`large-file-data-analysis`**](skills/large-file-data-analysis/) | 基于 `openpyxl read_only` 流式解析 10 万行大 Excel / Word / PDF，防止上下文爆炸 | 大数据集分析 / 财报审计 |
| ✍️ **文风与去AI味** | [**`human-voice-writing`**](skills/human-voice-writing/)<br>[**`humanizer`**](skills/humanizer/) | 彻底剔除机器套话与客服腔，输出自然、干练、有真实技术人温度的内容 | 技术博客 / 教程 / 文案 |
| 🌐 **内容全网分发** | [**`multi-platform-distribution`**](skills/multi-platform-distribution/) | 一键将标准 Markdown 适配转换为 Telegram、知乎、微信公众号、Twitter/X、QQ 专属格式 | 多平台内容分发 / 自媒体 |
| 🚀 **社交媒体发布** | [**BulkPublish Social Media Content Skills**](https://github.com/azeemkafridi/bulkpublish-api/tree/main/skills/social-media-content-skills) | 审核后将内容适配、排期并通过 BulkPublish API / MCP 发布到支持的社交渠道 | 审核优先的多平台发布 |
| 🤖 **智能体任务编排** | [**YYLO Agent Task Skills**](https://github.com/yylo-dev/yylo-skills) | 为 AI 编码智能体提供带验证边界的任务编排技能包：Kanban 任务管理、任务规划、单任务执行循环，以及 Wiki 知识、工作流与证据 Records | Claude Code / Codex / Pi 编码智能体 |
| 🧠 **记忆与系统架构**| [**`agent-system-design`**](skills/agent-system-design/)<br>[**`tiered-memory`**](skills/tiered-memory/) | 业内前沿的四层分层记忆架构设计（核心注入 + 详细笔记 + 历史检索 + 语义缓存） | Agent 系统设计 / 记忆治理 |
| ☁️ **边缘云与网络** | [**`cloudflare-fullstack-ops`**](skills/cloudflare-fullstack-ops/)<br>[**`cloudflare-worker-api-proxy`**](skills/cloudflare-worker-api-proxy/) | CF Pages/Workers/D1/R2/KV 全栈运维 + 零成本自建 OpenAI-compatible 代理 | Serverless / API 中转 |
| 💻 **Linux 基础设施**| [**`vps-bootstrap`**](skills/vps-bootstrap/) | 新 Linux VPS 一键硬件巡检、三网回程测试、BBR+FQ 加速与 UFW/Fail2ban 安全基线加固 | 服务器开箱 / 运维初始化 |

---

## 🌟 核心技能深度亮点

### 1. 📱 Telegram Table Renderer & CJK Aligner
> 位于 `packages/telegram-table-renderer/` 与 `skills/telegram-pipe-table-rendering/`

- **CJK 视觉宽度自适应**：使用 `unicodedata.east_asian_width` 自动计算中日韩全角字符宽度，在 Monospace 字体下实现完美的像素级表格竖线对齐；
- **智能移动端优雅降级**：超过 5 列的大表自动优雅降级为清晰的键值结构化卡片，彻底告别移动端 Telegram 格式炸裂。

```python
from telegram_table_renderer import format_telegram_markdown

raw_md = """
| 节点名称 | 状态 | 内存占用 | 延迟 |
|:---|:---:|---:|---:|
| 主控节点 Hytron (Debian 13) | 🟢 在线 | 1.2G / 3.8G | 12ms |
| 异地温备节点 London | 🟢 备用 | 512M / 1.0G | 120ms |
"""

# 输出完美对齐且兼容 Telegram 渲染的文本
formatted_text = format_telegram_markdown(raw_md)
```

---

### 2. 🔍 Agent Reach（全网全媒体提取器）
> 位于 `skills/agent-reach/`

让 Agent 突破纯文本网页抓取的限制，直接获取丰富的音视频与订阅流：
- **YouTube / Bilibili 字幕直提**：通过 `yt-dlp` 提取视频的中文/双语字幕；
- **RSS / 播客解析**：自动追踪并解析 RSS 订阅源最新动态；
- **Clean Markdown 抓取**：自动剔除网页广告与导航杂音，提取核心正文。

---

### 3. 📑 Markdown to Magazine-level Report
> 位于 `skills/markdown-to-html-report/`

将大模型输出的干燥 Markdown，一键渲染为具备以下特性的**现代响应式长篇报告**：
- 优雅的浅灰背景、柔和卡片阴影与目录跟随导航；
- 移动端表格横向滚动与图片自适应嵌入；
- 支持一键调用 Headless Chromium 打印为高精度商业级 PDF。

---

### 4. 📊 Large File Streaming Analysis
> 位于 `skills/large-file-data-analysis/`

- 针对 ≥10,000 行、多 Sheet 的大型 Excel 文件，采用 `openpyxl(read_only=True)` 流式扫描，内存占用恒定低于 50MB；
- 自动提取 Schema、汇总行数与数值分布，避免将庞大文件全量灌入大模型 Context 导致崩溃。

---

## 🚀 安装与使用指引 (Installation)

### 在 Hermes Agent 中使用
将需要的技能目录直接复制到你的 Hermes skills 路径下：
```bash
# 复制全部技能
cp -r skills/* ~/.hermes/skills/

# 通过 Hermes CLI 检查加载
hermes skills list
```

### 在 Claude Desktop / Cursor / OpenClaw 中使用
每个技能目录下的 `SKILL.md` 均遵循标准的 YAML Frontmatter + Markdown 规范，可直接作为 Prompt 模块或 Knowledge Base 导入。

### 安装 Telegram 表格渲染 Python 包
```bash
cd packages/telegram-table-renderer
pip install .
```

---

## 🧪 自动化测试 (Testing)

本项目自带完整的语法合规与安全性测试套件：
```bash
python tests/test_skills.py
```

---

## 🤝 贡献与许可 (License)

欢迎提交 Issue 和 Pull Request 来补充更多高质量的 Agent 技能！

本项目采用 [MIT License](LICENSE) 开源协议。
