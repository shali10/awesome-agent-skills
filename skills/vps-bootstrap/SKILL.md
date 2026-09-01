---
name: vps-bootstrap
description: Use when provisioning, benchmarking, and hardening a fresh Linux VPS node with SSH security, UFW firewall, Fail2ban, BBR acceleration, and hardware health inspection.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux]
metadata:
  tags: [vps, linux, devops, hardening, security, ufw, fail2ban, bbr]
  related_skills: [cloudflare-fullstack-ops]
---

# Fresh Linux VPS Bootstrap & Security Hardening

## Overview

A battle-tested initialization and security baseline suite for new Linux VPS nodes (Debian/Ubuntu/AlmaLinux). It automates **hardware & network benchmarking, BBR+FQ TCP acceleration, UFW firewall rules, Fail2ban brute-force protection, SSH key authentication enforcement, and system package updates**.

## When to Use & When NOT to Use

### When to Use
- Initializing a brand-new VPS instance right after purchase/reinstall.
- Establishing standard security baselines on exposed cloud VMs.
- Auditing CPU speed, disk I/O, swap, and three-network routing quality.

### When NOT to Use
- Managing container-internal virtual filesystems where kernel tuning (BBR/Swap) is restricted by host hypervisors.
- Production systems with active complex iptables routing that could be overwritten by naive UFW enable.

## Standard Initialization Pipeline

```bash
# 1. Update packages & install essential tools
apt-get update && apt-get install -y ufw fail2ban curl wget git htop jq iotop

# 2. Enable BBR + FQ TCP Congestion Control
cat << 'EOF' >> /etc/sysctl.conf
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
sysctl -p

# 3. Configure UFW Firewall (Never lock out SSH!)
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH Port'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable

# 4. Configure Fail2ban for SSH Protection
cat << 'EOF' > /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 86400
findtime = 600
EOF
systemctl restart fail2ban
```

## Common Pitfalls

1. **Locking out SSH during UFW enable**: Always explicitly run `ufw allow <YOUR_SSH_PORT>/tcp` BEFORE running `ufw enable`.
2. **Debian 12/13 auth.log missing for Fail2ban**: Debian 12+ defaults to `systemd-journald` instead of `rsyslog`. Set `backend = systemd` in `/etc/fail2ban/jail.local` if `/var/log/auth.log` does not exist.
3. **Docker bypassing UFW**: Docker by default manipulates `iptables` directly and bypasses UFW rules. Bind container ports to `127.0.0.1:<port>` or configure `DOCKER-USER` chain rules.

## Verification Checklist

- [ ] `sysctl net.ipv4.tcp_congestion_control` returns `bbr`.
- [ ] `ufw status verbose` shows active status with open SSH port.
- [ ] `fail2ban-client status sshd` confirms active jail.
- [ ] Root password login is disabled in `/etc/ssh/sshd_config` (`PasswordAuthentication no`).
