# Budget VPS 极慢 I/O 恢复记录

适用场景：ColoCrossing、RackNerd、GreenCloud 等经济型 KVM VPS，磁盘为共享存储或低速 SSD 缓存。
症状：apt-get/dpkg 卡死，一次 `apt-get upgrade -y` 跑 30+ 分钟未完成。

## 诊断

```bash
# 1. 检查 dpkg 是否在 D 状态（uninterruptible sleep）
ps aux | grep dpkg
# 看到 "Ds+" 状态 → I/O 阻塞

# 2. 查内核栈确认根因
cat /proc/<dpkg_pid>/stack
# 典型值: jbd2_log_wait_commit → ext4 日志提交等待
# 这意味着磁盘无法在合理时间内完成 fsync

# 3. 测真实 4K 写性能
dd if=/dev/zero of=/tmp/iotest.bin bs=4k count=25600 conv=fdatasync 2>&1
# 正常 SSD: >50 MB/s
# 慢盘: <1 MB/s（ColoCrossing 实测 266 KB/s）
```

## 恢复流程

```bash
# 1. 杀卡住进程
killall -9 dpkg apt-get apt 2>/dev/null
sleep 2

# 2. 清锁
rm -f /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend /var/cache/apt/archives/lock

# 3. 恢复 dpkg 状态（这一步也可能卡，给 60s 超时）
timeout 60 dpkg --configure -a --force-depends 2>&1

# 4. 后台跑完整升级（不阻塞用户）
export DEBIAN_FRONTEND=noninteractive
nohup apt-get upgrade -y -qq > /tmp/apt-upgrade.log 2>&1 &

# 5. 同时装关键包（apt 排队执行，不影响最终结果）
apt-get install -y -qq fail2ban ufw curl wget 2>&1
```

## 前台 vs 后台耗时对比（ColoCrossing 4K 写 266KB/s）

| 阶段 | 前台（预期） | 后台（实际） |
|------|------------|------------|
| 163 个安全更新 | ~5 min | 15+ min |
| 完整 318 包升级 | ~10 min | 30+ min |
| GSNode/ecs.sh 全量 | ~7 min | 18 min |

## 重要注意

- **D 状态进程不能 kill -15，必须 kill -9**。D 状态是内核态，kill -9 会标记进程退出但实际等待 I/O 完成才释放。
- 清锁后不要立即重试前台 apt，锁释放后后台进程会更快。等 `tail -f /tmp/apt-upgrade.log` 显示完成再验证。
- 系统升级期间磁盘 iowait 常 >30%，不影响 SSH 操作但影响新进程启动速度。
- GSNode 的磁盘 dd 测试（`100MB-4K Block`）在慢盘上会卡 6-7 分钟，耐心等。

## 慢 apt 完成后的内核检查

Ubuntu 的 `apt upgrade` **不会**更新内核 meta-package（`linux-image-generic` 等被视为「新安装」而非「升级」）。慢盘上 apt 跑完后**必须单独检查并拉新内核**：

```bash
# 查是否有内核更新待装
apt list --upgradable 2>/dev/null | grep linux

# 显式拉最新内核（比 full-upgrade 更安全）
apt-get install -y linux-image-generic linux-headers-generic

# 重启后验证
uname -r
```

**用户预期管理**：apt upgrade 完成后如果用户问「不是才更新 apt 吗」，不要只说「内核没跟上」——说明慢盘的 apt upgrade 和内核升级是两个独立步骤，需要显式拉内核。
