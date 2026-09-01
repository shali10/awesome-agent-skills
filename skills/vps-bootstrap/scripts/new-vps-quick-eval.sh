#!/usr/bin/env bash
# new-vps-quick-eval.sh — lightweight VPS evaluation probe
# Part of vps-bootstrap skill. Runs on the target via ssh.
# Usage: ssh root@<host> 'bash -s' < /path/to/new-vps-quick-eval.sh
set -u
printf '===IDENTITY===\n'
printf 'hostname='; hostname
printf 'os='; . /etc/os-release 2>/dev/null && printf "%s %s\n" "$ID" "$VERSION_ID" || echo unknown
printf 'kernel='; uname -r
printf 'virt='; systemd-detect-virt || echo none

printf '===CPU===\n'
printf 'nproc='; nproc
lscpu 2>/dev/null | awk -F: '/Model name/{gsub(/^ +/,"",$2); print "model=" $2; exit}'
printf 'aes_ni='; grep -q aes /proc/cpuinfo 2>/dev/null && echo yes || echo no
openssl speed -seconds 3 sha256 2>&1 | tail -3 | head -1

printf '===MEMORY===\n'
free -h | awk 'NR==2{print "total=" $2 " avail=" $7} NR==3{print "swap_total=" $2 " swap_used=" $3}'

printf '===DISK===\n'
lsblk -bd -o NAME,SIZE,TYPE 2>/dev/null | awk '$3=="disk"{sum+=$2; print $1" "$2} END {printf "total_bytes=%s\n", sum}'
rm -f /tmp/iotest.bin
dd if=/dev/zero of=/tmp/iotest.bin bs=16M count=16 conv=fdatasync status=none 2>&1
dd_result=$(dd if=/dev/zero of=/tmp/iotest.bin bs=16M count=16 conv=fdatasync 2>&1 | awk '/copied/{printf "%s MB/s", $NF/(1024*1024); exit}')
rm -f /tmp/iotest.bin
printf 'disk_write_Bps=%s\n' "$dd_result"

printf '===NETWORK===\n'
printf 'ipv4='; curl -4fsS --max-time 8 https://api.ipify.org 2>/dev/null || echo unknown
printf 'tcp_cc='; sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo unknown
printf 'qdisc='; sysctl -n net.core.default_qdisc 2>/dev/null || echo unknown
for h in 1.1.1.1 8.8.8.8 223.5.5.5 119.29.29.29; do
  printf '%s=' "$h"
  ping -4 -c 3 -W 2 "$h" 2>/dev/null | tail -1 | sed -n 's/.*= \([^/]*\)\/.*/\1 ms/p' || echo timeout
done
printf 'download_Bps='
curl -4 -sS -o /dev/null -w '%{speed_download}\n' --max-time 20 'https://speed.cloudflare.com/__down?bytes=5000000' 2>/dev/null || echo 0

printf '===SECURITY===\n'
printf 'ufw='; ufw status 2>/dev/null | head -1 || echo absent
printf 'fail2ban='; if command -v fail2ban-client >/dev/null 2>&1; then echo present; else echo absent; fi
printf 'ssh_key_only='; sshd -T 2>/dev/null | awk '/passwordauthentication/{print $2}' || echo unknown
printf 'updates='; if command -v apt >/dev/null 2>&1; then apt list --upgradable 2>/dev/null | sed -1d | wc -l; else echo unknown; fi

printf '===HEALTH===\n'
printf 'load='; cut -d' ' -f1-3 /proc/loadavg
printf 'failed_units='; systemctl --failed --no-legend --plain 2>/dev/null | wc -l
printf 'uptime='; uptime -p

printf '===DONE===\n'
