---
name: cloudflare-fullstack-ops
description: Cloudflare 全栈运维：Pages/Workers/D1/R2/KV及DNS管理。
category: devops
tags: [cloudflare, pages, workers, d1, r2, kv, dns, waf, edge, ci-cd]
version: 1.0.0
author: Hermes Agent
---

# Cloudflare 全栈运维与边缘开发体系 (cloudflare-fullstack-ops)

## 适用场景
- 管理 Cloudflare Pages 静态网站与博客（如基于 Hugo / Astro 的「林间随笔」导航页）
- 编写、部署与维护 Cloudflare Workers 无服务器 API（如 VPS 计算器 `jsq`、反代代理、短链接）
- 操作 Cloudflare D1 (Serverless SQLite)、KV 键值存储与 R2 图床/对象存储
- 通过 Cloudflare API 自动化管理 DNS 记录、SSL/TLS 模式与 WAF 自定义防火墙规则

---

## 🔑 凭据与鉴权标准（铁律）

在调用 Cloudflare REST API 或编写自动化脚本时，严格遵循唯一正式鉴权规范：
- **凭据存储**：`secrets/cloudflare_token_full`（全权限 API Key `cfk_...`）与 `secrets/cloudflare_email`
- **鉴权 Header**：必须使用 **`X-Auth-Email` + `X-Auth-Key`**（Global API Key 模式）
- ⚠️ **禁忌**：**切勿使用 `Authorization: Bearer`** 传递 Global API Key，否则 Cloudflare 会直接报错 `Code 1000: Invalid request headers`（易被误判为 Key 失效）。

```bash
# 标准 API 调用模板
CF_KEY=$(cat /root/.hermes/secrets/cloudflare_token_full)
CF_EMAIL=$(cat /root/.hermes/secrets/cloudflare_email)

curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "X-Auth-Email: ${CF_EMAIL}" \
  -H "X-Auth-Key: ${CF_KEY}" \
  -H "Content-Type: application/json"
```

---

## 🚀 核心架构与实战 Playbook

### 1. Cloudflare Pages（静态网站与 CI/CD）
- **最佳范式**：`GitHub 仓库 + Cloudflare Pages` 联动自动化构建。
- **Hugo / 静态博客构建参数**：
  - 构建命令：`hugo --gc --minify`
  - 构建输出目录：`public`
  - 环境变量：`HUGO_VERSION = 0.144.0`（或当前稳定版）
- **自定义域名绑定**：在 Pages 控制台「Custom domains」绑定主域名（如 `example.com`），Pages 自动下发边缘 Universal SSL 证书。

### 2. Cloudflare Workers（轻量边缘计算与工具）
- **路由与绑定（国内可达性铁律）**：
  - **默认域名问题**：Cloudflare 默认分配的 `*.workers.dev` 域名在中国大陆已被 SNI 阻断/DNS 污染，无法直连访问。
  - **Custom Domains 绑定**：新部署 Worker 后，必须立即调用 API（`PUT /accounts/:id/workers/domains`）或在控制台绑定自有独立二级域名（如 `forest.example.com`），享受完整 HTTP/2 + HTTP/3 与国内 CDN 边缘节点直连加速。
- **跨域处理**：边缘函数统一补齐 CORS 头：
  ```javascript
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': '*',
  };
  ```

### 3. Cloudflare R2（S3 兼容图床与对象存储）
- **接入标准**：
  - S3 Endpoint：`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
  - 自定义公开访问域名：绑定独立二级域名（如 `img.example.com`），零出口流量费（Zero Egress Fees）。
  - 权限与防盗链：可在 R2 或 WAF 层面配置 `Referer` 校验防恶意盗刷。

### 4. Cloudflare D1 & KV
- **D1 (边缘 SQLite)**：
  - 适用于轻量关系型存储，读多写少场景。
  - 备份策略：通过 API 定时导出 `.sql` 备份快照。
- **KV (超低延迟键值对)**：
  - 适用于配置缓存、短链重定向、Token 校验与速率限制白名单。

---

## 🛡️ WAF 与 DNS 运维避坑

1. **CF 橙云（Proxied）回源 522 / 超时排查**：
   - 先检查源站公网 IP 防火墙（UFW / iptables）是否放行了 Cloudflare 官方 IP 段（IPv4/IPv6）。
   - 检查 OpenResty / Nginx 虚拟主机的 `server_name` 是否包含访问域名，以及 SSL 证书是否匹配。
2. **Flexible vs Full (Strict) SSL**：
   - 生产环境统一建议 **Full** 或 **Full (Strict)** 模式，源站必须配置有效证书（如 Let's Encrypt），避免传输链路明文回源。
3. **缓存干扰（绕过 CF 验证源站）**：
   - 测试真实源站响应时，使用 `curl -sS --resolve <domain>:443:<origin_ip> https://<domain>/`，防止命中 CF 边缘缓存导致假阳性。
4. **边缘应用上线安全与渲染规范（血泪教训）**：
   - **后台入口防泄露**：严禁在公开页脚（Footer）暴露 `/admin/` 等后台管理超链接；严禁在登录表单 Placeholder 或源码中放置默认账号密码提示。
   - **D1 文本换行符转义**：通过 SQL 批量导入 Markdown 正文时，若携带字面量 `\n`，会导致前端/服务端 Markdown 引擎误将其识别为单行超长标题。服务端解析层必须先做 `\n` / `\r\n` 归一化处理。
   - **移动端交互标配**：全站需适配移动端滑出式抽屉（`☰` 悬浮按钮 + 半透明遮罩 + 侧边名片/统计/分类/标签云）。
