---
name: cloudflare-worker-api-proxy
description: 在 Cloudflare Workers 上部署自建 OpenAI-compatible API 代理（如 OC2API）。解决共享上游限速/不稳定的问题，获得私有无限制的 API 端点。
tags: [cloudflare, worker, api-proxy, openai-compatible, self-hosted]
---

# Cloudflare Worker API Proxy

## 何时使用

- 上游 API 免费但共享限速（如 OpenCode Zen 公共端点）
- 不想依赖他人搭建的代理（"只要自己的，别人的共用会限速"）
- 需要一个自治的 API 入口，自己做鉴权和模型白名单
- 用户问「Cloudflare 上部署的模型 / Worker 地址和 key 发我」——先从本机 Hermes 现役配置盘点，不靠记忆猜

## 适用范围

本 skill 以 OC2API（cmliussss2024/OC2API）为例，但模式适用于任何单文件 Cloudflare Worker API 代理。

## 前置条件

- Cloudflare 账号
- 已安装 `node` + `npm` + `wrangler`（`npm install -g wrangler`）
- 认证方式：`wrangler login`（交互）或 `CLOUDFLARE_API_TOKEN` 环境变量（CI/自动化）

## 标准部署流程

### 1. 获取代码

```bash
mkdir -p /root/retired-cf-worker && cd /root/retired-cf-worker
wget -q -O _worker.js "https://raw.githubusercontent.com/cmliussss2024/OC2API/Worker/_worker.js"
```

或从 Worker 分支拉最新版。

### 2. 创建 wrangler.toml

```toml
name = "retired-cf-worker"
main = "_worker.js"
compatibility_date = "2026-07-19"
```

### 3. 设置密钥并部署

```bash
# 生成随机密钥
API_SECRET="oc2_$(openssl rand -hex 16)"

# 写入 secret（Worker 未创建时会自动创建）
echo "$API_SECRET" | wrangler secret put API_KEY

# 部署
wrangler deploy _worker.js --name retired-cf-worker
```

### 4. 验证

```bash
# 健康检查
curl "$URL/health"

# 模型列表
curl -H "Authorization: Bearer $API_SECRET" "$URL/v1/models"

# 对话测试
curl -H "Authorization: Bearer $API_SECRET" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash-free","messages":[{"role":"user","content":"hi"}]}' \
  "$URL/v1/chat/completions"
```

### 5. 接入 Hermes

```bash
hermes config set providers.cf-worker.api_key "$API_SECRET"
hermes config set providers.cf-worker.base_url "https://$WORKER_NAME.$CF_ACCOUNT.workers.dev/v1"
hermes config set providers.cf-worker.model "deepseek-v4-flash-free"
hermes config set providers.cf-worker.context_length "131072"
hermes config set providers.cf-worker.api_mode "chat_completions"
```

## 环境变量

| 名称 | 必需 | 说明 |
|---|---|---|
| `API_KEY` | 是（除非用 `TOKEN`） | 客户端访问 Worker 的鉴权密钥 |
| `TOKEN` | 是（除非用 `API_KEY`） | `API_KEY` 的备用变量名 |
| `DISABLE_AUTH` | 否 | 设为 `true` 关闭客户端鉴权 |
| `DEBUG_LOG` | 否 | 调试日志 |
| `DEBUG_LOG_BODY` | 否 | 输出响应正文预览 |

## 陷阱

| 问题 | 处理 |
|---|---|
| `npx wrangler secret put` 交互 | 用 `echo $KEY | wrangler secret put NAME` 非交互式 |
| `rosie: error: Cannot determine home directory` | `export HOME=/root` 后再跑 wrangler |
| Worker 免费套餐 CPU 限制 10ms/请求 | 纯转发够用；大量流式请求需监控用量 |
| API key 含 `$` 被 bash 变量替换 | 用单引号包裹或 `openssl rand -hex 16` 规避 |

## 可用模型（OC2API 场景）

OC2API 对上游模型做白名单过滤，只暴露 `big-pickle` 和 `*-free` 结尾的模型：

| 模型 | 延迟 | 备注 |
|---|---|---|
| `big-pickle` | ~1.8s | 默认路由模型 |
| `deepseek-v4-flash-free` | ~1.6s | 日常使用推荐 |
| `nemotron-3-ultra-free` | ~1.1s | 轻量，响应快 |
| `hy3-free` | ~1.7s | 腾讯混元 |
| `mimo-v2.5-free` | ~6.9s | 较慢 |
| `north-mini-code-free` | ~0.6s | 代码模型 |

## 现役盘点（用户要地址/key 时）

**触发**：`cloudflare 上部署的模型` / `worker 地址和 key` / `retired-cf-worker 发我` / `workers.dev 凭据`。

### 1. 从 Hermes 读真值

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
c = yaml.safe_load(Path('/root/.hermes/config.yaml').read_text())
for name, p in (c.get('providers') or {}).items():
    if not isinstance(p, dict):
        continue
    base = str(p.get('base_url') or '')
    if any(k in base.lower() or k in name.lower()
           for k in ('workers.dev', 'cloudflare', 'retired-cf-worker', 'zhouou')):
        print('provider:', name)
        print('base_url:', p.get('base_url'))
        print('model:', p.get('model'))
        print('api_key:', p.get('api_key'))  # 主人私聊明确索要时原样输出
PY
```

### 2. 交付纪律

| 场景 | 做法 |
|---|---|
| 主人私聊明确要「地址和 key」 | 从 config **完整交付** base_url + model + api_key，勿中段打码 |
| 公开频道 | 脱敏 |
| skill / notes / MEMORY | 永不写完整 api_key |

### 3. 本部署锚点（无密钥）

| 项 | 值 |
|---|---|
| Provider | `<retired-cf-worker>` |
| Base 形态 | `https://retired-cf-worker.<sub>.workers.dev/v1` |
| 默认模型 | `deepseek-v4-flash-free` |

密钥以磁盘配置为准，禁止固化进 skill。

## 参考

- OC2API 仓库：https://github.com/cmliussss2024/OC2API （Worker 分支）
- OpenCode 上游：`opencode.ai.cmliussss.net`（公共端点，不建议依赖）
- 现役索取：`references/retired-cf-worker-inventory-and-credential-delivery.md`
