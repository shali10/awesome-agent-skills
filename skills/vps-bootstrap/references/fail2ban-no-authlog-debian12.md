# fail2ban: "Have not found any log file for sshd jail" on Debian 12 minimal

## 症状

```log
# systemctl status fail2ban
× fail2ban.service - Fail2Ban Service
     Active: failed (Result: exit-code)
    Process: ExecStart=/usr/bin/fail2ban-server -xf start (code=exited, status=255/EXCEPTION)

# journalctl -u fail2ban -n 5
fail2ban-server: ERROR   Failed during configuration: Have not found any log file for sshd jail
fail2ban-server: ERROR   Async configuration of server failed
```

## 根因

Debian 12 最小化镜像（cloud-init 预置）可能没有 `/var/log/auth.log`。sshd 日志全走 journald，文件系统上无传统 log 文件。`%(sshd_backend)s` 在此环境下无法自动 fallback 到 systemd backend。

## 修复

```bash
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = 22
backend = systemd
journalmatch = _SYSTEMD_UNIT=ssh.service + _SYSTEMD_UNIT=sshd.service
EOF

systemctl restart fail2ban
```

## 验证

```bash
fail2ban-client status sshd
# Status for the jail: sshd
# |- Filter
# |  |- Currently failed:	10
# |  |- Total failed:	54
# |  `- Journal matches:	_SYSTEMD_UNIT=ssh.service + _SYSTEMD_UNIT=sshd.service
# `- Actions
#    |- Currently banned:	7
#    |- Total banned:	7
#    `- Banned IP list:	...
```

## 发生环境

- Debian 12 (bookworm), kernel 6.1.0-10-amd64
- Catixs Ltd (AS48266) KVM VPS, London
- 394 packages total（最小化镜像）
- 2026-07-27
