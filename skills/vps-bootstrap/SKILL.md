---
name: vps-bootstrap
description: 新 VPS 开箱全流程：SSH 排障、硬件巡检、安全加固、信息输出。含 fail2ban/改端⼝/UFW 标准步骤。输出格式遵循用户偏好。
---

# VPS 开箱即用引导

## 触发条件
用户提供了新 VPS 的 IP 和密码，或用「新买了台服务器」「看看配置/状态」「帮我装机」「还是老规矩，新机该做什么」等信号。

> 商家/系统识别坑：**alicloud 前缀 ≠ 阿里云**（实测见过 alicloud-xxx 主机名但实际是其他商家的机器），别按前缀猜厂商，以实际 IP 归属/系统信息为准。

## 用户「老规矩」交付形状（2026-07-21 确认）

新机接入并巡检后，**先评后改**，用表格交付，**等用户点头再执行**：

| 档 | 内容 | 何时做 |
|---|---|---|
| **A 基础开箱** | 主机名、时区 `Asia/Shanghai`、apt 清理+安全更新、基础工具、2G swap（4G 机无 swap 必做） | 几乎每台新机 |
| **B 安全加固** | 部署管理机公钥（**先验 key**）；**默认保留密码登录**（用户偏好）；收紧 `LoginGraceTime`/`MaxAuthTries`/`MaxStartups`；fail2ban（非标端口写进 jail）；UFW 只放行已监听端口；BBR+fq | 生产向空壳默认 A+B |
| **C 可选** | Docker、监控 agent、性能快测、业务部署 | 用户点用途后再做 |

默认建议话术：**「建议 A+B；C 等用途」**；用户回「听你的/搞/来吧」再执行。
**（2026-08-01 用户纠正）**：用户问「不是默认 ab 吗」= 生产向空壳**默认直接执行 A+B**，不要每次先问「要不要做」；巡检完直接开干，做完再汇报。C 档仍等用途。  \n用户说「先优化再跑NQ」= A+B 做完紧接着跑 NodeQuality 默认（参考 `vps-benchmarking` skill），优化和测绑定为同一操作的两段，不要等用户再催。**合并汇报：** apt upgrade 和 NQ 完成后**一起汇报**，不分开报。用户催进度时可短暂通报「还在跑，等一起出」，但最终报告必须两段状态 + NQ 结果一并交付。  \n**不要**在未授权时默认 key-only 锁死密码。  \n厂商**已**非标 SSH 端口时：B 档 **不强制再改端口**，fail2ban/UFW 跟现网端口即可。

### 空壳基线速查（装前对照）

| 项 | 常见「未开箱」状态 |
|---|---|
| UFW | 已装或未装，`Status: inactive` |
| fail2ban | 未装 |
| Swap | 无 |
| BBR | `cubic` + `fq_codel` |
| 监听 | 仅 sshd（可能非 22） |
| Docker | 常无 |
| cloud-init | `degraded done` 仅 deprecation 警告时可忽略，先不重跑 |

**注意：部分厂商（ColoCrossing 等）可能预配了 BBR 和 swap。** 硬件巡检时先查这些项的状态，已配置的直接跳过，不需要重新 `mkswap` 或覆写 BBR sysctl。

## WebSSH 用户代执行的可靠性边界

通过浏览器 WebSSH 让用户代执行时，必须把它当作受限的交互终端，而不是可靠的脚本传输通道：

- 长命令、多行 heredoc、复杂引号、嵌套 `&&` 和多命令串容易被粘贴截断；优先给一条短命令，等待实际输出后再继续。
- 不要把说明文字（例如“正常”“执行成功”）混入可复制命令块；用户可能整段粘贴，导致 `command not found`。
- 每一步只要求一个可验证动作；不要一次给完整初始化脚本。涉及路由、WireGuard、DNS 或防火墙时，先检查再变更。
- 浏览器工具无法建立或无法返回远端终端输出时，不得声称“已代执行”；必须明确区分“用户执行”和“代理实际验证”。
- 用户已经在远端 shell 中时，优先让用户执行短命令；不要反复刷新 WebSSH 或把失败的长命令换一种引号继续尝试。

## 步骤

### 0. Telegram 输出与 SSH 就绪判定

- **前台会话中的后台任务通知防刷屏**：在即时对话（Telegram/QQ 等）中启动后台脚本时，避免使用 `notify_on_complete=true` 导致平台触发系统层日志通知推送（用户容易产生“这啥/你怎么又来了”的困惑）。凡在交互 turn 中放后台的任务，设 `notify_on_complete=false`，并通过进程轮询或结果解析后统一汇报。
- **短时 SSH 验证**不要用后台任务 + `notify_on_complete=true`：SSH 密码提示、远程安装的原始日志（apt 输出、binary 下载进度、failed services 列表）和后台完成通知会被直接推送给用户。选方案：
  1. 前台执行（设长 timeout 即可，返回即时）
  2. 后台任务但输出落本地文件，完成后只读日志提取结论
  3. 不能本机控制的交互式 PTY（如 `read -s -p` 输密码的 bash 调用）不要用 notify_on_complete
- **单次 `Connection refused`** 只能证明 TCP 连接在某个节点被主动拒绝，**不能直接断言**“端口错了”或“服务器里的 sshd 没启动”。安全组/上游防火墙的 REJECT 策略也可能呈现同样结果。
- 用户刚调整安全组、重启实例或在 VNC 启动 SSH 后，应重新执行 TCP 连通和 SSH banner 探测；再结合控制台的 `systemctl status ssh` 启动时间、`ss -lntp` 监听情况判断。仅在多次复测与远端证据一致时才下结论。
- Hermes terminal 可能拦截**本地** `systemctl reboot`。**远端**吃内核时优先：`ssh host 'nohup sh -c "sleep 2; /sbin/shutdown -r now" >/tmp/reboot.log 2>&1 & echo REBOOT_SCHEDULED'`，再 `nc`/SSH 轮询（先 down 再 up，约 1–3 分钟）。仅远端也被拦或起不来才上 VNC，不要默认甩锅用户。

### 1. 首次 SSH 登录
```bash
sshpass -p '<password>' ssh -o StrictHostKeyChecking=no root@<ip>
```
- 如果 Permission denied → 换密码 → 试不同 user（root/ubuntu/admin/debian）
- 如果 Connection refused → 等重启 + 轮询
- 如果 `no supported methods remain` → 服务器可能禁了密码认证，建议用户进面板重置/用 VNC
- 多试几次可能是 fail2ban 封了，等一会再试

**排障瀑布流：**
1. 确认能 Ping 通
2. `nmap -sV -p 22 <ip>` 看 SSH 版本
3. `ssh -v` 看 debug 输出
4. 试 expect 交互式登录
5. 都不行 → 让用户进面板 Reset Root Password

### 1.5 前置依赖检查

Debian 12/13 最小化镜像可能缺 `wget`、`fio`、`jq`、`time`。在跑任何脚本前先检查：

```bash
for cmd in curl wget python3 jq fio; do
  command -v "$cmd" >/dev/null && printf '%s=present\n' "$cmd" || printf '%s=missing\n' "$cmd"
done
```

- GSNode / IP.Check.Place 等脚本默认用 `curl`，但用户可能习惯用 `wget`，不要假设两者都可用。
- **如果 `wget` 缺失**：所有安装类命令优先用 `curl -fsSL <url> | bash`，不要不加检测就用 `wget -qO-`。
- 把缺的包先装：`apt-get install -y curl wget ca-certificates`。

### 纯 IPv6 Debian 13 的 WARP/IPv4 验收

- Debian 13 可能没有 `systemd-resolved.service`；不要无条件执行 `systemctl disable systemd-resolved --now`。
- 纯 IPv6 主机不能依赖 `8.8.8.8`/`1.1.1.1` 这类 IPv4 DNS；优先使用 IPv6 DNS，且不要默认 `chattr +i /etc/resolv.conf`，避免 WARP/网络管理后续无法更新。
- WARP 菜单提示“检测不到任何 IPv4 或 IPv6”可能是脚本自有 IP 检测 API 无法解析，不代表真实接口没有 IPv6；先用已知 IPv6 地址绕过 DNS 验证 HTTPS，再读取脚本实际调用的 API。
- KVM + 新版 Debian 内核优先 WireGuard 内核方式；接口只有在 `ip -br addr` 有 IPv4、`wg show` 有 `latest handshake`、`ip -4 route` 有路由，并且 `curl -4` 实测出口时才算成功。
- `wg-quick` 可能改写路由并影响 SSH；卡住时不要重复 `systemctl start`，先中断并查看接口、路由、WireGuard 状态和 journal。


**IPv6-only/DNS/WARP 细节**：见 `references/ipv6-only-dns-and-warp.md`。核心门控是先区分 IPv6 端到端连通、DNS、APT 索引和第三方脚本 API；不要用 `systemd-resolved` 不存在的报错推断网络故障，也不要用 `chattr +i` 锁死 `resolv.conf`。WARP 接口创建后必须以 `wg show` 的握手和实际 IPv4 出口作为成功标准。

不要把“`apt-get update` 已执行”当作成功。Debian 13 可能使用 deb822 的 `/etc/apt/sources.list.d/*.sources`，传统 `/etc/apt/sources.list` 为空；如果 `main` 源缺失或索引刷新失败，多个常规包会同时报 `Unable to locate package` / `no installation candidate`。

安装前先做可验证门控：

```bash
printf '%s\\n' '=== sources ==='
grep -RhvE '^[[:space:]]*(#|$)' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null || true
printf '%s\\n' '=== apt update ==='
apt-get update
printf '%s\\n' '=== package candidates ==='
apt-cache policy curl ca-certificates htop jq fail2ban ufw
```

只有 `apt-get update` 退出码为 0，且 `apt-cache policy` 对所需包显示候选版本，才继续安装。多个基础包同时无候选版本时，先修复仓库配置或 DNS/网络；不要把问题误判为单个包从 Debian 删除。

**纯 IPv6 新机的网络分层验证**：`ip -6 route` 有默认路由只证明本地路由选择存在，不代表端到端可达。先用 `ip -6 route get <known_ipv6>` 检查源地址/网关，再用 `ping -6`（仅作辅助，ICMP 可能被禁）和 `curl -6 --resolve 'deb.debian.org:443:[<known_ipv6>]' https://deb.debian.org/` 绕过 DNS 验证 HTTPS。只有 HTTPS 直连成功后，才处理 DNS；不要直接 `chattr +i /etc/resolv.conf`，否则会锁死后续修复路径。若只能临时绕过解析，可短期写 `/etc/hosts`，并记录静态地址可能变化，网络恢复后删除临时条目。

**APT 源格式**：Debian 13 可能使用 deb822 的 `mirror+file:///etc/apt/mirrors/*.list`；不要仅因出现 `mirror+file` 就盲改源。读取 mirrorlist，并根据 `apt-get update` 的真实错误区分 DNS、路由、TLS、签名和仓库配置问题。

长初始化脚本应把“更新索引”“安装依赖”“系统修改”分段，并在依赖安装失败时立即退出；不要继续执行 Swap、UFW、fail2ban 或 SSH 配置，避免造成半配置状态。通过 WebSSH 手动执行时，优先提供短的、可分段复制命令，而非一条可能长时间无输出的 heredoc。网页 SSH 的初始命令可能不建立会话、丢失输出或截断多行粘贴；按钮点击和页面无错误都不是远端成功证据，必须取得实际 stdout/stderr 后再进入下一步。

### 2. 硬件巡检（统一命令集）
登录后用一条命令查全：
```bash
echo '=== 系统 ==='; cat /etc/os-release | head -5; echo; \
echo '=== CPU ==='; nproc; lscpu | grep 'Model name'; echo; \
echo '=== 内存 ==='; free -h; echo; \
echo '=== 磁盘 ==='; lsblk -d -o NAME,SIZE; df -h /; echo; \
echo '=== 网络 ==='; ip addr | grep 'inet '; curl -s ip.sb; echo; \
echo '=== 虚拟化 ==='; systemd-detect-virt; echo; \
echo '=== 运行时间 ==='; uptime
```
附加检查（按需）：
- `swapon --show` — Swap
- `ss -tlnp` — 开放端口
- `ps aux --sort=-%cpu | head -8` — 高 CPU 进程
- `lastb | head -5` — 登录失败记录（爆破检测）
- `ufw status` — 防火墙状态

### 2.5 性能评估与决策

**核心流程**：先评后改。先跑评估展示结果，用户点头（"听你的""搞""来吧"）再进硬化和安全加固。

用 `scripts/new-vps-quick-eval.sh`（本 skill 自带的轻量测评脚本）一键跑关键项。也可以按需拆开跑：

```bash
# 磁盘顺序写吞吐（真实块设备性能）
rm -f /tmp/iotest.bin
dd if=/dev/zero of=/tmp/iotest.bin bs=16M count=32 conv=fdatasync status=progress 2>&1
rm -f /tmp/iotest.bin

# CPU SHA-256 吞吐（openssl 多核）
openssl speed -seconds 5 sha256 2>&1 | tail -4 | head -1

# 单连接下载吞吐
curl -4 -sS -o /dev/null -w "url=%{url_effective} avg_Bps=%{speed_download} t=%{time_total}s\n" \
  --max-time 30 "https://speed.cloudflare.com/__down?bytes=10000000"

# 关键节点延迟
for h in 1.1.1.1 8.8.8.8 223.5.5.5 119.29.29.29; do
  printf '%s=' "$h"
  ping -4 -c 4 -W 2 "$h" 2>/dev/null | tail -1 | sed -n 's/.*= \([^/]*\)\/.*/\1 ms/p' || echo timeout
done
```

评估结果用 Markdown 双表格输出（核心指标表 + 分级概况表），分 ABCD 级评定。

**注意**：
- **GSNode 检测唯一正规命令**：`curl -fsSL https://dl.gsvps.com/install.sh | sh`（官方 Go 纯净版，生成 `gsvps.com/report/<id>`，1~2 分钟自动清理）。**严禁跑成旧版 Bash 融合怪 `ecs.sh`**。
- 单连接下载不能代表多线程上限，晚高峰与工作日不同，注明这是"单次快照"。
- 纯 tmpfs 的磁盘分不代表真实块设备速度；用 `dd conv=fdatasync` 补测。

### 3. 安全加固（用户点头后执行）
**默认路径（本用户 A+B）**: 部署管理机专用 key → **保留密码** → 收紧 preauth → fail2ban（写实端口）→ UFW → BBR。  
**不要**默认 key-only；只有用户明确「禁密码/只用 key」才锁密码。  
「密码要留 / 密码登录给我保留」= 硬约束，验收必须 `sshd -T` + 密码实弹 `PASSWORD_OK`。  
「监控我已经挂了 / 监控不用装」= **跳过 C 档监控 agent**，禁止再装 Komari/同类。

#### 3.0 大版本 apt 与脚本分段
A 档 `apt upgrade` 含 **openssh-server** 时常见：
1. `sshd -t` → `Missing privilege separation directory: /run/sshd`
2. 整段 bootstrap 在 hardening 前 `set -e` 退出（hostname/swap 已好，UFW/f2b/BBR 未做）

**处理**：
```bash
mkdir -p /run/sshd && chmod 755 /run/sshd
/usr/sbin/sshd -t
systemctl reload ssh || systemctl restart ssh
```
断点后**读 residual state** 只补缺项，不要整脚本无脑重跑。Ubuntu 24.04 classic `sources.list` 与 `ubuntu.sources` 双开时备份后清空 classic。kept-back 内核需 install + 重启后 `uname -r` 才新；重启后复验密码+key+UFW+f2b+BBR。详见 `references/ab-bootstrap-ubuntu24-pitfalls.md`。

#### 3.1 部署 SSH key +（默认）保留密码
```bash
# 1. 本机专用 key（例 id_ed25519_<alias>）→ 远端 authorized_keys（追加，700/600）
# 2. 先验 key
ssh -i <本地key> -o IdentitiesOnly=yes -o PasswordAuthentication=no -o BatchMode=yes \
  -p <port> root@<host> 'echo KEY_OK'
# 3. drop-in 加固但 PasswordAuthentication yes（server-hardening §5）；中和 50-cloud-init/allow_root
# 4. 密码路径也实测
# export SSHPASS=...; sshpass -e ssh -o PreferredAuthentications=password \
#   -o PubkeyAuthentication=no -p <port> root@<host> 'echo PASSWORD_OK'
```

**仅当用户明确禁密码**再走 key-only（中和 cloud-init → `PasswordAuthentication no` → 验密码被拒）。

**注意**:
- `sshd_config.d/50-cloud-init.conf` / `allow_root.conf` 可能先匹配生效；要中和冲突指令，最终以 `sshd -T` 为准
- 默认**不**禁用密码；禁密码前必须 key 登录已 `KEY_OK`

#### 3.2 fail2ban
```bash
apt-get install -y fail2ban

# 预检 log 文件是否存在（Debian 12 最小化镜像可能缺 /var/log/auth.log）
if [ ! -f /var/log/auth.log ]; then
  # 没有传统日志文件 → 用 systemd journal backend
  cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = <ssh_port>
backend = systemd
journalmatch = _SYSTEMD_UNIT=ssh.service + _SYSTEMD_UNIT=sshd.service
EOF
else
  # 有传统日志 → 用默认 file backend
  cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = <ssh_port>
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF
fi
systemctl enable --now fail2ban
```

#### 3.3 改 SSH 端口（建议 22222）— 用稳固的 sed 避免双重替换陷阱
```bash
sed -i 's/^#\\?Port 22/Port 22222/' /etc/ssh/sshd_config
```

#### 3.4 防火墙 — 必须先枚举所有监听端口再放行

**两层防火墙模型**：VPS 的连通性受两层防火墙影响——宿主机/面板级（hypervisor firewall）和 Guest 内部（iptables/UFW）。排查时先分清哪层在拦。

```bash
# 预检：外部视角
nmap -Pn -p <port> <public_ip>       # filtered = 外层防火墙拦
ssh -v -p <port> root@<public_ip>    # timeout = 外层拦；refused = 内层拦

# 预检：内部视角
iptables -L INPUT -n --line-numbers  # policy + 规则
ufw status                           # 仅当 UFW 启用时有效
ss -tlnp4 | grep -v 127.0.0.1       # 实际监听的对外端口
```

**陷阱 1：UFW inactive 但 iptables INPUT policy DROP（ColoCrossing / 部分 budget VPS）**

新机 `ufw status` 显示 `inactive`（或未安装），以为防火墙全开——但某些 budget VPS 厂商在系统镜像里预设了 iptables 规则，INPUT 链默认 **DROP**，只放行了 22 口：

```
Chain INPUT (policy DROP)          ← 默认全拒！
num  target     prot opt source
1    f2b-sshd   tcp  --  0.0.0.0/0  multiport dports 22
```

此时装 Docker 容器监听 80/443 或跑 Caddy/Nginx，外网全部超时。Let's Encrypt http-01 挑战报 `Timeout during connect (likely firewall problem)`。

**修复**：直接加 iptables 规则放行业务端口（重启后丢失，需在安全加固阶段持久化）：
```bash
iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
```

如果系统装过 `iptables-persistent`，记得 `netfilter-persistent save`；否则重启后回默认 DROP。

**陷阱 2：UFW 只放行了 SSH 和面板端口（常见于 1Panel 安装后）**
- Debian 新机装 1Panel(quick_start.sh) → UFW 启用但只开了 `22/tcp` 和 `<面板端口>/tcp`
- 同时装 OpenResty/Docker 容器监听 80/443 时这些端口会被 DROP
- Cloudflare CDN 回源失败（curl 返回 000），容易误判为 DNS 没生效
- **修复**：`ufw allow 80/tcp && ufw allow 443/tcp` 加上容器映射的其他端口

```bash
# 放行业务端口
for p in 80 443 8080 9091 ...; do ufw allow $p/tcp; done  # 端口来自 ss 输出
ufw --force enable
ufw status verbose
```

**统一验证（从外网测）**：
```bash
curl -sS -o /dev/null -w '%{http_code}' http://<public_ip>/
```

#### 3.5 BBR 网络优化（新 VPS 开箱常规项）

Ubuntu/Debian KVM VPS 默认常见是 `cubic + fq_codel`。开箱时应检查 BBR；用户追问「BBR 呢」通常表示这项漏做。

```bash
# 检查当前状态
sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc
lsmod | grep -E '^(tcp_bbr|sch_fq)' || true

# ⚠️ 注意：`lsmod` 显示 tcp_bbr 已加载 ≠ BBR 已启用
# 常见陷阱：模块已装载（镜像自带或之前安装过）但 sysctl 未配置，
# 实际拥塞算法仍是 cubic。必须用 `sysctl net.ipv4.tcp_congestion_control`
# 验证当前生效值，不能只看 `lsmod`。

# 启用 BBR + fq
modprobe tcp_bbr || true
modprobe sch_fq || true
cat > /etc/sysctl.d/99-hermes-bbr.conf <<'EOF'
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
sysctl --system

# 验证
sysctl net.core.default_qdisc net.ipv4.tcp_congestion_control
lsmod | grep -E '^(tcp_bbr|sch_fq)'
```

验收应看到：

```text
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
tcp_bbr ...
sch_fq ...
```

#### 3.6 主机名改名（避免 cloud-init 覆盖）

新机默认主机名常是 `kvm` / `ubuntu`。用户说「改个用户名」时先澄清是不是改主机名。改主机名时同时处理 `/etc/hosts` 和 cloud-init：

```bash
NEW=rackeye
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p /root/bootstrap-backup-$TS
cp -a /etc/hostname /etc/hosts /etc/cloud/cloud.cfg /root/bootstrap-backup-$TS/ 2>/dev/null || true
hostnamectl set-hostname "$NEW"

python3 - <<'PY'
from pathlib import Path
p=Path('/etc/cloud/cloud.cfg')
if p.exists():
    s=p.read_text()
    if 'manage_etc_hosts:' in s:
        s=s.replace('manage_etc_hosts: true','manage_etc_hosts: false').replace('manage_etc_hosts: True','manage_etc_hosts: false')
    else:
        s += '\nmanage_etc_hosts: false\n'
    p.write_text(s)
PY

python3 - <<'PY'
from pathlib import Path
new='rackeye'
p=Path('/etc/hosts')
lines=p.read_text().splitlines()
out=[]; done=False
for line in lines:
    if line.startswith('127.0.1.1'):
        out.append(f'127.0.1.1 {new} {new}')
        done=True
    else:
        out.append(line)
if not done:
    out.insert(0, f'127.0.1.1 {new} {new}')
p.write_text('\n'.join(out)+'\n')
PY

hostname
hostnamectl --static
getent hosts "$NEW"
grep -n '^manage_etc_hosts' /etc/cloud/cloud.cfg || true
```

#### 3.7 重启服务
```bash
systemctl restart fail2ban
systemctl reload ssh || systemctl restart ssh || systemctl restart ssh.socket
```
> **注**：Debian 12/13 与 Ubuntu 24.04+ 的 systemd 服务名包含 `ssh` / `ssh.socket`。`%(sshd_backend)s` 在 auth.log 存在时可自动对接；若 auth.log 缺失（常见于 Debian 12 最小镜像），必须显式设置 `backend = systemd` + `journalmatch`（见 §3.2 的分支写法）。重启后用 `fail2ban-client status sshd` 验证即可。

⚠️ 改端口后务必立即测试新端口连接，确认成功再收工。若用户偏好保留 22/密码登录，不改端口、不禁密码；只做 `LoginGraceTime`、`MaxAuthTries`、`MaxStartups`、fail2ban、UFW 兜底，并用 `sshd -T` 验证真实生效值。

### 4. 输出格式（用户偏好）
服务器信息一律用 **Markdown 表格** 输出，字段统一：

```markdown
| 项目 | 规格 |
|---|---|
| 厂商 | RackNerd / 海创 / 旧主机 / ... |
| IP | `x.x.x.x`（非标端口加 :port） |
| 密码 | `xxxxx` |
| 虚拟化 | KVM / LXC / ... |
| 系统 | Ubuntu 22.04 / Debian 13 / ... |
| CPU | N vCores · 型号 @ 频率 |
| 内存 | X.X GiB |
| 交换 | X.X GiB |
| 磁盘 | X GiB（已用 Y GiB，Z%） |
| 延迟 | X ms |
| 状态 | ✅/⚠️/🔴 + 负载 |
| 防护 | fail2ban / UFW / 改端口（如有） |
```

多台服务器对比时用带编号的 Markdown 表格按台列出。

### 4.5 临时/试用主机不留痕清理（2026-08-01 实测）

用户说「这台服务器不用记 / 试用 X 天 / 临时的」时，本机必须把所有与该主机关联的痕迹清干净，让机器像从没出现过一样。全链路 6 类位置：

| # | 位置 | 命令 |
|---|---|---|
| 1 | 为它生成的 SSH 密钥 | `rm -f ~/.ssh/<key> ~/.ssh/<key>.pub`（若密钥是通用的/复用的则保留） |
| 2 | `~/.ssh/known_hosts` | `ssh-keygen -R <IP>`（会留 `.old` 备份，确认后一并删） |
| 3 | `~/.ssh/config` Host 块 | 删对应 Host 块（若有）；检查无 ProxyJump 残留 |
| 4 | `~/.hermes/secrets/` | 删 `<ip>_ssh` / `<alias>_ssh` 凭据文件（若有） |
| 5 | MEMORY.md / USER.md | memory tool `remove` 删资产条目；`grep -c` 验证 0 |
| 6 | Honcho 结论库 | `honcho_conclude list` 查 IP/主机名 → 逐条 `delete_id`（会话中可能实时生成新条目，多查一轮） |

**别忘了派生痕迹**（grep 全盘后常发现）：
- `/root/.hermes/logs/agent.log`、`gateway.log` — 会话日志含 IP，用 `sed -i 's/<IP>/[REDACTED-IP]/g'` 脱敏
- `/root/.hermes/state/rich_sent_index.json` — 富文本索引会存消息原文，同样替换脱敏
- `state.db` 会话历史保留（消息本体，盲删会破坏 FTS/会话完整性；需要彻底清除时走 credential-history-sanitization 流程）

**⚠️ 删私钥前先确认没有活依赖（2026-08-01 实测锁死教训）**：清理临时机时如果删了「专门为它生成的私钥」，而服务器只认该 key（无密码、VNC 不可用、厂商面板无法注入新 key），就永久锁死了——公钥无法反推私钥，之后想再连（如跑 GSNode）完全进不去。教训：**临时机还没到期/还可能再连时，私钥先留着，等机器彻底作废再删**；删之前用 `ssh-keygen -F <IP>` + `grep <keyname> ~/.ssh/config` 确认无依赖。用户要删时明确提醒「删了就永久锁死」。

**验收**：`grep -rl "<IP>\|<hostname>" /root/.hermes/ /root/.ssh/ 2>/dev/null | grep -v state.db` 无输出（state.db 单独判断）。临时机的远端配置（探针/systemd）不用拆，试用到期自然作废。

### 5. 记忆持久化
- 资产身份（厂商/地区/IP/别名/SSH 端口/系统/主机名）可保存；**密码、私钥、PAT 等凭据绝不写入 memory、user profile、skill 或报告**。凭据仅存入权限为 `600` 的本机 secrets 文件或受控密钥路径。
- 非标端口在资产条目中记录；不保存临时测评过程和短期故障。
- 接入时同时写 `~/.hermes/secrets/<ip_underscored>_ssh` **和** `~/.hermes/secrets/<alias>_ssh`；本机 SSH alias 写入见 `hermes-ssh-and-remote-exec`（**`~/.ssh/config` 只能用 shell 写，file 工具会拒**）。
- Ubuntu 24.04 A+B 断点、`/run/sshd`、kept-back 内核重启：`references/ab-bootstrap-ubuntu24-pitfalls.md`。

## 坑

- **纯 IPv6 Debian 新机的 DNS/APT 处理**：如果 `ip -6 addr` 和 `ip -6 route` 正常，但 `apt-get update` 报 `Temporary failure resolving 'deb.debian.org'`，先验证 IPv6 端到端，而不是反复改 APT 源：
  1. 用 `curl -6 -kI --connect-timeout 10 --resolve 'deb.debian.org:443:[<known_ipv6>]' https://deb.debian.org/` 绕过 DNS 测试；收到 HTTP 响应即证明路由/HTTPS 正常。
  2. 临时用 `/etc/hosts` 固定 Debian 站点的 AAAA 地址后再 `apt-get update`，先备份 `/etc/hosts`；不要默认 `chattr +i /etc/resolv.conf` 或禁用 `systemd-resolved`，避免把恢复路径锁死。
  3. 这种 hosts 映射是临时旁路；DNS 恢复后删除并重新验证 `getent hosts`。
  4. 第三方脚本可能依赖额外的 IP 检测域名；脚本报“检测不到任何 IPv4 或 IPv6”时，先读脚本实际调用的 API，再判断是网络故障还是 DNS/API 故障，不能据此断言 VPS 没有地址。

- **WebSSH/受限终端的粘贴可靠性**：首次接入、DNS 修复和初始化阶段，优先逐条执行短命令；多行 heredoc、嵌套引号、长串 `&&` 容易被 WebSSH 截断或改写。每一步都用实际输出验收后再继续，避免一次粘贴整段 bootstrap 导致失败位置不清。

- **第三方初始化脚本的旁路解析**：如果脚本下载本身能成功，但运行时因其自有 API 域名解析失败而误报“无 IPv4/IPv6”，不要盲目重跑或修改路由。先读取脚本中的实际 API 调用，短期用 `/etc/hosts` 旁路解析仅作为已验证的临时措施；如果连单条短命令都无法可靠执行，停止自动化操作，保留当前 SSH 会话和已验证的基础网络结论，不把未完成的脚本尝试写成成功流程。

- **Ubuntu 24.04+ SSH 使用 systemd socket 激活**（而非 sshd_config）：
  - 改 `/etc/ssh/sshd_config` 的 `Port` **不会改变监听端口**
  - 必须创建 drop-in：`/etc/systemd/system/ssh.socket.d/port.conf`。内容：
    ```
    [Socket]
    ListenStream=
    ListenStream=<new_port>
    ```
  - 然后 `systemctl daemon-reload && systemctl restart ssh.socket`
  - **改 SSH 端口前必须先确认目标端口在 VPS 面板防火墙已放行**
  - 验证：`ss -tlnp | grep sshd`

- **宿主机/面板级防火墙（hypervisor firewall）**：
 - 许多 VPS 商家（ColoCrossing、、旧主机 等）在控制面板有独立防火墙
  - VM 内部的 ufw/iptables 开放端口 ≠ 端口能从外网访问
  - **必须先确认面板防火墙已放行**目标端口
  - 排查：从外部 `nc -zv <IP> <port>` 测，不通就查面板
  - 常见面板位置：安全组 / 防火墙 / Firewall / Network Security
  - 面板本身也可能崩：`nmap -Pn` 先确认 host 存活，再查 provider 面板不同子域名（portal/cloud/billing/manage/solusvm）。面板崩了不等于服务器不行
  - **ColoCrossing 实测**：`cloud.colocrossing.com` 后端无响应（Cloudflare 超时回源）但 `portal.colocrossing.com` 在线；`nmap -Pn` 确认 host 存活但端口 filtered → 等面板恢复后关 hypervisor 防火墙即可。详见 `references/provider-portal-diagnosis-20260725.md`

- `sshpass` 重试次数多了可能触发 fail2ban，隔 5 秒再试
- 特殊字符密码用 `export SSHPASS` + `sshpass -e`，禁止 `sshpass -p`
- RackNerd/SolusVM 面板重置密码后可能需要重启才生效
- **Debian/Ubuntu 最小镜像缺 `wget`**：优先 `curl -fsSL`；缺则 `apt-get install -y curl wget ca-certificates`。
- **纯 IPv6 Debian VPS 的 DNS/初始化顺序**：先用 `ip -br addr`、`ip -6 route` 和 `ip -6 route get <known_ipv6>` 确认地址与路由；再用 `curl -6 --resolve '<host>:443:[<known_aaaa>]'` 绕过 DNS 验证 HTTPS。APT 报 `Temporary failure resolving` 时，先修复 DNS 或用已验证的静态 `/etc/hosts` 记录临时恢复 APT，不能把它误判为软件源缺失。Debian 13 可能没有 `systemd-resolved.service`，不要无条件执行 `systemctl disable systemd-resolved --now`；纯 IPv6 主机也不能依赖 `8.8.8.8`/`1.1.1.1` 这类 IPv4 DNS。不要默认 `chattr +i /etc/resolv.conf`，它会阻止 WARP/网络管理后续更新。
- **IPv6-only 主机运行 WARP 菜单**：菜单提示“检测不到任何 IPv4 或 IPv6”也可能只是脚本的外部 IP 检测 API 无法解析；先核对真实接口和路由。KVM + 新版 Debian 内核优先 WireGuard 内核方式；完成后必须验收 `ip -br addr`、`ip -4 route`、`wg show`、`journalctl -u wg-quick@warp`，确认接口地址、peer `latest handshake` 和实际 IPv4 出口。创建接口或 `active (exited)` 不等于 WARP 成功；远程启动可能改路由并影响 SSH，卡住时先 Ctrl+C/查状态，禁止重复叠加启动。
- **WebSSH 命令输入**：长命令、多行 heredoc、复杂引号和连续 `&&` 容易被粘贴截断；通过 WebSSH 初始化时优先一次一条短命令，执行后读取真实输出再继续，避免把说明文字（如“正常”）一起粘进 shell。
- **默认保留密码**；「SSH key 先验再锁」只用于用户明确禁密码。key 被拒时查 `PubkeyAuthentication`/authorized_keys 权限
- **`Missing privilege separation directory: /run/sshd`**：openssh 升级后 `mkdir -p /run/sshd` 再 `sshd -t`；A+B 脚本 upgrade 与校验之间必插
- **bootstrap 半成功**：先盘点 hostname/swap/ufw/f2b/`sshd -T`，只补缺；禁止重复 `mkswap`/盲 `ufw --force reset` 而不枚举端口
- **厂商已非标 SSH 端口**：B 档不改端口；fail2ban `port=<实端口>`，空壳 UFW 只放行该端口
- **用户已挂监控**：C 档 Docker/Komari 未点名不装
- **密码永不进 memory/报告明文**；表格写 secrets 或省略
- **Welcome 邮件密码可能不准确**：Provisioning 系统（SolusVM/Virtualizor）生成的密码可能跟 welcome 邮件不一致。先试邮件密码，不行就试用户常用密码，或让用户进面板确认/重置。ColoCrossing、RackNerd 等均有此现象。
- Ubuntu 24.04 清单：`references/ab-bootstrap-ubuntu24-pitfalls.md`
- **GSNode 测评规范**：用户要求「GSNode」测评时，一律执行 `curl -fsSL https://dl.gsvps.com/install.sh | sh`，产出 `https://www.gsvps.com/report/<id>` 报告，耗时 1~2 分钟且纯净自动清理。禁止执行旧版 Bash 融合怪 `ecs.sh`。

- **`apt upgrade` 不更新内核 meta-package**：Ubuntu 的 `linux-image-generic` 等内核 meta-package 在 `apt upgrade` 中被视为「新安装」而非「升级」，不会自动拉新。典型场景：新 VPS 跑完 A 档 `apt upgrade` 后内核仍是出厂版本（5.15.0-46），而可用版已到 5.15.0-186（差 140+ 小版本）。用户一问「不是才更新 apt 吗」才暴露。处理：
  - `apt list --upgradable 2>/dev/null | grep linux` — 先查内核包是否有更新待装
  - `apt-get install -y linux-image-generic linux-headers-generic` — 显式安装最新内核 meta-package
  - 重启后 `uname -r` 验证新内核生效
  - 用 `apt-get install` 而非 `full-upgrade`（后者可能意外移除包）；显式 install kernel meta 更安全
  - **A 档执行时就要告知用户**：「apt upgrade 不会自动升级内核，内核需要单独拉」——管理用户预期，避免事后解释

- **极慢 I/O VPS（如 ColoCrossing 经济型）的 apt 处理**：某些 budget VPS 磁盘 I/O 极差（`jbd2_log_wait_commit` 卡住，4K 写 <1MB/s），前台 `apt-get upgrade` 会超时（>600s 跑不完 318 个包）。`nohup` 后台跑是最可靠的方案。排障：`ps aux | grep dpkg` 看到 `D` 状态 + `cat /proc/<pid>/stack` 显示 `jbd2_log_wait_commit` → 确认 I/O 瓶颈而非进程死锁。处理流程：
  1. `killall -9 dpkg apt-get apt` 杀卡住进程（安全——dpkg 在 `D` 状态卡 fsync，非关键写入）
  2. `rm -f /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend /var/cache/apt/archives/lock` 清锁
  3. `export DEBIAN_FRONTEND=noninteractive; nohup apt-get upgrade -y -qq > /tmp/apt-upgrade.log 2>&1 &` 后台跑
  4. 用 `tail -f /tmp/apt-upgrade.log` 轮询进度，不阻塞用户
  5. 同时可先装关键包（`apt-get install -y fail2ban ufw curl`），apt 锁释放后会排队，不影响最终升级\n- **极慢 I/O VPS 的 GSNode 耗时**：磁盘 4K 写 <1MB/s 的机器跑融合怪全量测试约需 **18-20 分钟**（正常 VPS 5-7 分钟）。主要是磁盘 dd 测试（`100MB-4K Block`）卡在写阶段。用 `nohup` 跑并定期 tail 日志即可，不影响用户继续操作。

- **`apt upgrade` 卡 debconf 交互弹窗（openssh-server 配置冲突）**：A 档 `apt upgrade` 含 `openssh-server` 时，如果之前已修改过 `/etc/ssh/sshd_config`（例如 B 档做了 SSH 加固），升级过程会弹交互对话框问「配置文件 sshd_config 已被修改，如何处理？」。非交互 SSH 会话（无 TTY）会卡死，直至超时。
  - **症状**：`ps aux | grep -E 'apt|dpkg'` 显示 `dpkg --configure --pending` + `/usr/bin/perl /usr/share/debconf/frontend`，进程长时间无进展
  - **排查**：`tail -20 /var/log/apt/term.log` 看到 `What do you want to do about modified configuration file sshd_config?`
  - **处理**：
    1. 杀卡住进程：`killall -9 dpkg apt-get apt`（安全——dpkg 卡在 debconf 用户交互，非关键写入）
    2. 清锁：`rm -f /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend /var/cache/apt/archives/lock`
    3. 用非交互模式完成配置：`DEBIAN_FRONTEND=noninteractive dpkg --configure -a -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"`
    4. 继续升级：`DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"`
  - **预防**：A 档 `apt upgrade` 前如果已做过 B 档 SSH 加固，直接用 `DEBIAN_FRONTEND=noninteractive` + `--force-confdef --force-confold` 跑，一步跳过所有交互弹窗。非交互模式选择「保留当前修改后的版本」(`--force-confold`)。