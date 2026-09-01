# OC2API / CF Worker：现役盘点与凭据交付

**日期**：历史记录  
**触发**：盘点自部署 Cloudflare Worker 模型代理

## 流程

1. 扫 `~/.hermes/config.yaml` → `providers.*`，过滤 `workers.dev` / `retired-cf-worker` / `cloudflare`。
2. 读 `base_url`、`model`、`api_key`、`api_mode`、`context_length`。
3. 主人私聊明确索要 → **完整交付**，不中段打码。
4. 可选：用短 chat 探活验收（不把 key 写进 skill）。

## 交付表模板

| 项 | 值 |
|---|---|
| Provider | `cf-worker` |
| Base URL | `https://….workers.dev/v1` |
| 模型 | 配置中的 model |
| API Key | 配置中的完整 key |
| 协议 | OpenAI `/v1/chat/completions` |

## curl 模板

```bash
curl -sS "$BASE_URL/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MODEL","messages":[{"role":"user","content":"只回复OK"}]}'
```

## 不要做的

- 凭 MEMORY 旧 key 交差（可能已轮换）
- 把完整 key 写入 skill / notes / MEMORY
- 用户已说「发我」仍只给 `len` / head-tail 打码

## 与其他 skill

- 部署/换密：本 umbrella 主文「标准部署流程」
- Hermes 入链/免疫：`hermes-provider-config`
- 群 bot 导出 runtime DB：`telegram-llm-group-bot-deploy` + achai 参考
