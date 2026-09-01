# SSH 排障现场记录（2026-06-29）

## 场景
RackNerd 新 VPS `23.254.158.251`，用户说密码是 `[密码已作废-20260808]`（和其他服务器一样）。

## 排障流水

### 第 1 轮：密码被拒
```
sshpass -p '[密码已作废-20260808]' ssh root@23.254.158.251
→ Permission denied (publickey,password).
```

### 第 2 轮：试第二个密码
用户又说 `vOjPWwytR0` → 也不行

### 第 3 轮：debug 分析
```
ssh -v -o PubkeyAuthentication=no root@23.254.158.251
→ Authentications that can continue: publickey,password  ← 密码认证已开
→ read_passphrase: can't open /dev/tty                    ← 正常，非交互模式
```

### 第 4 轮：nmap 验证
```
nmap -sV -p 22 23.254.158.251
→ OpenSSH 8.9p1 Ubuntu 3
```

### 第 5 轮：密码变了
用户从面板改了密码 → `OcZchaujgB` → 还是不行
用户又说 `AL44WZ9n7vc3mtGpT5` → 成功

### 关键发现
- RackNerd SolusVM 面板重置密码后**需要重启服务器**才生效
- 重启等待约 30 秒 SSH 才起来
- 重启后 host key 会变，需 `ssh-keygen -R IP` 清理 known_hosts

## 最终连接命令
```bash
sshpass -p 'AL44WZ9n7vc3mtGpT5' ssh -p 22222 root@23.254.158.251
```

## 安全加固记录
- fail2ban 启动后即刻生效，当场抓到 1 个爆破 IP（`158.51.96.38`）
- SSH 端口从 22 改为 22222
- UFW 启用，只放行 22222/tcp