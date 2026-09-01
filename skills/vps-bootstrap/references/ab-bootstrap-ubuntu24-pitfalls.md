# Ubuntu 24.04 新机 A+B 实战坑（2026-07-21）

## 场景
空壳 Ubuntu 24.04 KVM，厂商已开非标 SSH 端口；用户授权 A+B，保留密码，监控自理。

## 必做顺序（摘要）
1. 主机名 + `manage_etc_hosts: false` + 时区 `Asia/Shanghai`
2. 基础包 + 2G swap + apt 双源清理
3. `apt upgrade`（可能含 openssh）→ **`mkdir -p /run/sshd`** → 再改 sshd
4. 专用 ed25519 key 部署并 `KEY_OK`
5. drop-in 加固 **PasswordAuthentication yes** + 中和 cloud-init/allow_root 冲突
6. fail2ban（`port=<实际端口>` + 管理 IP ignoreip）
7. UFW 仅放行 SSH 端口（空壳）
8. BBR + fq
9. 本地 alias：`IdentityFile` + `PreferredAuthentications publickey,password`
10. 验收：KEY / PASSWORD / ufw / fail2ban / bbr

## 已知断点
| 症状 | 原因 | 修复 |
|---|---|---|
| `Missing privilege separation directory: /run/sshd` | openssh 升级后 /run 目录未就绪 | `mkdir -p /run/sshd` 再 `sshd -t` |
| bootstrap 半成功 | `set -e` 卡在 sshd -t | 读 residual，只补 UFW/f2b/BBR |
| `apt` multiverse configured multiple times | classic sources.list + ubuntu.sources | 清空/注释 classic list |
| 内核 kept-back | linux-generic 等需 install+reboot | 远端 `shutdown -r now` + 轮询；复验密码 |
| 用户说监控已挂 | 勿装 Komari/agent | 跳过 C |

## 远端吃内核（kept-back）

```bash
apt-get install -y linux-generic linux-headers-generic linux-image-generic fwupd
# uname -r 仍旧 → 必须重启
ssh host 'nohup sh -c "sleep 2; /sbin/shutdown -r now" >/tmp/reboot.log 2>&1 & echo REBOOT_SCHEDULED'
# 轮询：先 down 再 nc + key SSH，直到 uname -r 为新核
```

重启后复验：密码、key、UFW、fail2ban、BBR、hostname。

## 用户口头约束

| 用户话 | 动作 |
|---|---|
| 密码要留 / 密码登录保留 | `PasswordAuthentication yes` + 密码实弹；不锁 key-only |
| 监控我已经挂了 | 跳过 Komari/同类 agent |
| 升级（在 A+B 语境） | 只做 kept-back/内核，不扩展 Docker/业务 |

## 验收口令（给用户）
- `KEY_OK` / `PASSWORD_OK` / `ALIAS_KEY_OK`
- `uname -r` 与安装的 linux-image 一致（重启后）
- 密码列不出现在 memory/表格明文