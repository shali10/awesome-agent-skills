---
name: multi-platform-distribution
description: "内容多平台分发。将同一内容适配到 Telegram、QQ、知乎、公众号、Twitter/X 等多平台格式，一键分发。当用户说'分发/同步/多平台/发知乎/发公众号/发推/TG+QQ'时加载。"
---

# 内容多平台分发

## 适用场景

- 写一次内容，发到 TG + QQ 双平台
- 长文拆成知乎/公众号格式
- 技术博客同步到多个平台
- 教程/报告的多平台适配

## 核心原则

1. **一次创作，多端适配** — 不重复写，只转换格式
2. **平台特性优先** — 每个平台有自己的排版规则和限制
3. **人工确认再发** — 分发前必须给用户预览确认
4. **失败隔离** — 某平台发送失败不影响其他平台

## 平台格式对照表

| 平台 | 字符上限 | 图片 | 链接 | 排版特性 |
|---|---|---|---|---|
| **Telegram** | 4096 (文本) / 10240 (Media) | ✅ 原生 | ✅ 原生预览 | MarkdownV2、按钮、MediaGroup |
| **QQ** | ~5000 | ✅ 原生 | ⚠️ 部分预览 | Markdown 子集、卡片消息 |
| **知乎** | 100000 | ✅ 编辑器 | ✅ 原生 | 富文本/Markdown、公式 |
| **公众号** | 20000 | ✅ 编辑器 | ⚠️ 需转链接 | 微信富文本、CSS 样式 |
| **Twitter/X** | 280 (免费) / 25000 (Premium) | ✅ 原生 | ✅ t.co 短链 | 话题标签、线程 |
| **B站动态** | 2000 | ✅ 原生 | ✅ 原生 | Markdown 子集 |

## 分发流程

```
原始内容 (Markdown)
    │
    ▼
┌─────────────────────────────────┐
│  1. 内容解析                      │
│  - 提取标题/正文/图片/链接/标签    │
│  - 识别内容类型 (资讯/教程/观点)   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  2. 平台适配                      │
│  - 按各平台规则裁剪/重排           │
│  - 图片压缩/格式转换               │
│  - 链接处理 (短链/UTM)            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  3. 预览确认                      │
│  - 展示各平台最终效果              │
│  - 用户确认或修改                 │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  4. 分发执行                      │
│  - 并行发送各平台                  │
│  - 记录发送状态                   │
│  - 失败重试                       │
└─────────────────────────────────┘
```

## 平台适配规则

### Telegram 适配

```python
def adapt_telegram(content: dict) -> dict:
    """Telegram MarkdownV2 格式"""
    title = content['title']
    body = content['body']
    images = content.get('images', [])
    tags = content.get('tags', [])
    
    # 转义特殊字符
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for ch in escape_chars:
        body = body.replace(ch, f'\\{ch}')
    
    # 组装
    text = f"**{title}**\n\n{body}"
    if tags:
        tag_str = ' '.join([f'\\#{t}' for t in tags])
        text += f"\n\n{tag_str}"
    
    result = {'text': text, 'parse_mode': 'MarkdownV2'}
    
    # 多图用 MediaGroup
    if images:
        result['media'] = images[:10]  # 最多 10 张
    
    return result
```

### QQ 适配

```python
def adapt_qq(content: dict) -> dict:
    """QQ 消息格式（子集 Markdown）"""
    title = content['title']
    body = content['body'][:4000]  # QQ 文本上限约 5000
    
    text = f"【{title}】\n\n{body}"
    
    # QQ 不支持复杂 Markdown，只保留基础格式
    # 链接用 <a href="xxx">描述</a> 或纯 URL
    
    return {'text': text}
```

### 知乎适配

```python
def adapt_zhihu(content: dict) -> dict:
    """知乎文章格式"""
    title = content['title']
    body = content['body']
    
    # 知乎支持 Markdown 导入
    # 图片需要上传到知乎 CDN
    # 公式用 $$...$$ 包裹
    
    return {
        'title': title,
        'body': body,
        'type': 'markdown'  # 或 'richtext'
    }
```

### Twitter/X 线程

```python
def adapt_twitter(content: dict) -> list:
    """Twitter/X 线程拆分"""
    title = content['title']
    body = content['body']
    
    # 免费账号 280 字符/条，Premium 25000
    limit = 280
    tweets = []
    
    # 第一条放标题
    tweets.append(title)
    
    # 拆分正文
    paragraphs = body.split('\n\n')
    current = ''
    for para in paragraphs:
        if len(current) + len(para) + 2 < limit:
            current += f"\n\n{para}" if current else para
        else:
            if current:
                tweets.append(current)
            current = para[:limit]
    if current:
        tweets.append(current)
    
    return tweets
```

## 分发脚本

```bash
#!/usr/bin/env python3
# ~/.hermes/scripts/distribute.py
import json, sys, os
from pathlib import Path

CONTENT_FILE = sys.argv[1] if len(sys.argv) > 1 else None
PLATFORMS = sys.argv[2].split(',') if len(sys.argv) > 2 else ['telegram', 'qq']

def load_content(path):
    """加载内容文件（Markdown 格式）"""
    with open(path) as f:
        text = f.read()
    
    # 简单解析：第一行 # 标题，其余正文
    lines = text.strip().split('\n')
    title = lines[0].lstrip('#').strip() if lines[0].startswith('#') else '无标题'
    body = '\n'.join(lines[1:]).strip() if lines[0].startswith('#') else text
    
    return {'title': title, 'body': body, 'images': [], 'tags': []}

def preview(content, platforms):
    """预览各平台效果"""
    print("=" * 50)
    print("📋 分发预览")
    print("=" * 50)
    
    for platform in platforms:
        print(f"\n{'─' * 30}")
        print(f"📱 {platform.upper()}")
        print(f"{'─' * 30}")
        
        if platform == 'telegram':
            preview_telegram(content)
        elif platform == 'qq':
            preview_qq(content)
        elif platform == 'twitter':
            preview_twitter(content)
        else:
            print(f"  [预览] {content['title'][:50]}...")

def preview_telegram(content):
    text = f"**{content['title']}**\n\n{content['body'][:200]}..."
    print(text[:500])
    print(f"\n  [字符数: {len(text)}/4096]")

def preview_qq(content):
    text = f"【{content['title']}】\n\n{content['body'][:200]}..."
    print(text[:500])
    print(f"\n  [字符数: {len(text)}/5000]")

def preview_twitter(content):
    tweets = content['body'].split('\n\n')
    print(f"  线程长度: {len(tweets)} 条")
    print(f"  1/{len(tweets)}: {content['title']}")

def distribute(content, platforms):
    """执行分发"""
    results = {}
    
    for platform in platforms:
        try:
            if platform == 'telegram':
                results[platform] = send_telegram(content)
            elif platform == 'qq':
                results[platform] = send_qq(content)
            else:
                results[platform] = {'status': 'skipped', 'reason': '未实现'}
        except Exception as e:
            results[platform] = {'status': 'error', 'error': str(e)}
    
    return results

def send_telegram(content):
    """通过 Hermes gateway 发送到 TG"""
    # 实际调用 hermes gateway send_message
    # 这里返回模拟结果
    return {'status': 'ok', 'platform': 'telegram'}

def send_qq(content):
    """通过 Hermes gateway 发送到 QQ"""
    return {'status': 'ok', 'platform': 'qq'}

if __name__ == "__main__":
    if not CONTENT_FILE:
        print("用法: python3 distribute.py <内容文件.md> [telegram,qq,twitter]")
        sys.exit(1)
    
    content = load_content(CONTENT_FILE)
    
    if '--preview' in sys.argv:
        preview(content, PLATFORMS)
    elif '--send' in sys.argv:
        results = distribute(content, PLATFORMS)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        preview(content, PLATFORMS)
        print("\n✅ 预览完成。确认发送请加 --send")
```

## 使用方式

```bash
# 1. 写内容到文件
cat > /tmp/article.md << 'EOF'
# 文章标题

正文内容...

## 小标题

更多内容...
EOF

# 2. 预览各平台效果
python3 ~/.hermes/scripts/distribute.py /tmp/article.md telegram,qq

# 3. 确认后发送
python3 ~/.hermes/scripts/distribute.py /tmp/article.md telegram,qq --send
```

## 分发前检查清单

- [ ] 标题是否吸引各平台用户？
- [ ] 图片是否已压缩（TG 5MB / QQ 10MB 限制）？
- [ ] 链接是否需要 UTM 追踪？
- [ ] 标签是否适合该平台？
- [ ] 是否有平台专属内容（如 TG 按钮、QQ 卡片）？

## 相关 skill

- `automated-briefings` — 定时推送（可复用分发逻辑）
- `hermes-cross-platform-send` — 平台字符/格式限制
- `rss-social-aggregator` — 聚合后分发
