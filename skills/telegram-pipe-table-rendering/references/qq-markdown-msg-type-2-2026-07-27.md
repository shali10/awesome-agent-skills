# QQ Bot API msg_type:2 Markdown 实现参考（2026-07-27）

## 背景

Hermes 的 `_send_qqbot()`（`tools/send_message_tool.py`）使用 `msg_type: 0`（纯文本）发送消息。QQ Bot API 支持 `msg_type: 2`（Markdown），含原生 pipe table 渲染。no_agent cron 脚本通过 cron delivery 路径投递到 QQ 时也走 `msg_type: 0`，导致 Markdown 源码显示为纯文本。

## API 流程

### 1. 获取 Access Token

```
POST https://bots.qq.com/app/getAppAccessToken
Content-Type: application/json

{
    "appId": "1904065356",
    "clientSecret": "QQRSUWZcgkpu06DLTclv5GRdp2FThwBR"
}
```

响应：
```json
{
    "access_token": "xxxx",
    "expires_in": 7200
}
```

### 2. 发送 Markdown 消息

```
POST https://api.sgroup.qq.com/v2/groups/{group_openid}/messages
Authorization: QQBot {access_token}
Content-Type: application/json

{
    "msg_type": 2,
    "markdown": {
        "content": "# 标题\n| 列1 | 列2 |\n|---|---|\n| A | B |"
    }
}
```

### 端点优先级

Hermes 的 `_send_qqbot` 依次尝试三个端点：
1. **Channel**: `https://api.sgroup.qq.com/channels/{chat_id}/messages`（旧端点）
2. **C2C（私聊）**: `https://api.sgroup.qq.com/v2/users/{chat_id}/messages`
3. **Group（群聊）**: `https://api.sgroup.qq.com/v2/groups/{chat_id}/messages`

对于 Markdown 消息（msg_type: 2），推荐直接走 **v2 端点**（Group 或 C2C）。

## 实战代码片段

```python
import json, urllib.request

# 读取凭据
env_path = os.path.expanduser('~/.hermes/.env')
appid = ''; secret = ''; group_id = ''
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('QQ_APP_ID='):
            appid = line.split('=', 1)[1].strip().strip("'\"")
        elif line.startswith('QQ_CLIENT_SECRET='):
            secret = line.split('=', 1)[1].strip().strip("'\"")
        elif line.startswith('QQBOT_HOME_CHANNEL='):
            group_id = line.split('=', 1)[1].strip().strip("'\"")

# Step 1: 获取 access token
token_req = urllib.request.Request(
    'https://bots.qq.com/app/getAppAccessToken',
    data=json.dumps({'appId': appid, 'clientSecret': secret}).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(token_req, timeout=15) as resp:
    access_token = json.loads(resp.read())['access_token']

# Step 2: 发送 Markdown 消息
content = open(content_path).read()
payload = json.dumps({
    'msg_type': 2,
    'markdown': {'content': content}
}).encode()
headers = {
    'Authorization': f'QQBot {access_token}',
    'Content-Type': 'application/json'
}

# 先试 Group 端点
url = f'https://api.sgroup.qq.com/v2/groups/{group_id}/messages'
try:
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        print(f'✅ QQ group: sent (id={result.get("id","?")})')
except urllib.error.HTTPError:
    # 回退 C2C 端点
    url = f'https://api.sgroup.qq.com/v2/users/{group_id}/messages'
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        print(f'✅ QQ C2C: sent (id={result.get("id","?")})')
```

## 组合方案（2026-07-27 生产验证）

每日早报（`daily_briefing_v2.sh`）在 no_agent 模式下同时处理双平台，cron deliver 设为 `local`：

```bash
# 脚本流程：
# 1. 生成内容 + 表格验证
# 2. TG: sendRichMessage 直发（原生表格）
# 3. QQ: msg_type:2 直发（原生表格）
# 4. cron deliver: local（不重复投递）
```

## 注意事项

- QQ Bot API access_token 有效期 7200 秒（2h），每次脚本执行都要重新获取
- `msg_type: 2` 的 Markdown 消息**不支持纯文本 fallback**——如果 Markdown 解析失败，消息可能发空
- QQ 的 Markdown 渲染比 Telegram 更完整——支持 `##` 标题、pipe table、列表等
- `content` 有长度限制（约 4000 字符），超长需分段
- QQ Bot API 有频率限制——建议不要短时间（<3s）内连续发送到同一 chat
