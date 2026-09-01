# Provider 面板 / 云控制台诊断记录（2026-07-25）

## 场景
ColoCrossing 新 VPS，SSH 端口 22 被「filtered」（nmap 判定），面板 `cloud.colocrossing.com` 后端无响应超时。用户在国内也打不开。

## 排障流水

### 第 1 轮：基础连通性
```bash
ping 新 VPS            # 100% loss，但主机不一定离线
nmap -Pn -p 22 新VPS # Host is up, port 22 filtered
```
→ **filtered** 说明机房/宿主机防火墙拦截，非系统内 UFW/iptables 问题。

### 第 2 轮：探查 Provider 面板
```bash
# portal（客户区/工单区）
curl -sI https://portal.colocrossing.com   # ✅ 302 → 在线

# cloud（云控制台/管理 VPS）
curl -sI https://cloud.colocrossing.com    # ❌ TLS 握手成功，但后端不回数据
                                           # Cloudflare 超时等待回源

# 其他常见子域名
curl -sI https://manage.colocrossing.com   # ❌ DNS 无解析
curl -sI https://solusvm.colocrossing.com  # ❌ DNS 无解析
curl -sI https://billing.colocrossing.com  # ❌ HTTP 000
```
→ **cloud.colocrossing.com 后端崩了**，不是用户网络问题。列结论。

### 第 3 轮：密码不匹配
Welcome 邮件密码 `j3&9E2&oP12Wm3` SSH 被拒 → 尝试用户另一密码 `[密码已作废-20260808]/` ✅ 成功。

### 第 4 轮：防火墙放行
第一次 SSH：`Connection timed out`（hypervisor 防火墙拦）
第二次 SSH：`Permission denied`（防火墙已放，但 welcome 密码错）
第三次 SSH：用 `[密码已作废-20260808]/` ✅ 进入

→ **防火墙是 ColoCrossing 宿主机层面控制的**，不是 guest UFW（检查 UFW 为 inactive）。

## 关键发现

| 发现 | 说明 |
|------|------|
| **面板多子域名** | portal ≠ cloud ≠ billing。cloud 是 VPS 管理面板，portal 是客户区 |
| **欢迎邮件密码不一定对** | Provisioning 系统(Virtualizor/SolusVM)可能用另一套密码，以面板里设的为准 |
| **hypervisor 防火墙** | ColoCrossing 宿主机级防火墙会拦截 SSH，不在 guest 的管理范围内 |
| **cloud 面板无响应** | 放在 Cloudflare 后面但回源超时 → 服务器崩了，不是用户网络问题 |

## 常用 ColoCrossing 面板地址

| 地址 | 用途 | 状态 |
|------|------|------|
| portal.colocrossing.com | 客户区（登录、工单、账单） | ✅ 活 |
| cloud.colocrossing.com | 云控制台（VPS 管理、防火墙、重装） | ⚠️ 常崩 |
| manage.colocrossing.com | 备用管理 | ❌ 无记录 |
| billing.colocrossing.com | 计费 | ❌ 无记录 |

## VPS 不可达时的标准诊断顺序

1. **ping** — 区分主机离线 vs 防火墙拦 ping
2. **nmap -Pn -p 22 <ip>** — open / filtered / closed
3. **curl 测试 provider 面板** — 确认 provider 服务正常
4. **DNS 查找常见管理子域名** — 不同子域名可能指向不同面板
5. **换密码尝试** — welcome 邮件密码可能不对；试用户常用密码
6. **用户进面板操作** — 关防火墙 / 重置密码 / 重装系统 / 开 VNC
