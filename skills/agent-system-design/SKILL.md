---
name: agent-system-design
description: "Agent 系统架构设计：四层记忆 + 语义缓存 + 预算管控 + 模型路由 + Guardrails + 统一执行入口。适用于构建自托管 AI agent 系统（如 Hermes Agent）的架构设计与实现。"
triggers:
  - "agent 架构"
  - "agent 系统设计"
  - "设计一个 agent"
  - "agent 分层"
  - "记忆系统"
  - "token 优化"
  - "预算管控"
  - "模型路由"
  - "guardrails"
  - "安全规则"
---

# Agent 系统架构设计

## 适用场景

构建自托管 AI agent 系统时的完整架构设计与实现，特别关注：
- Token 成本优化（语义缓存、模型路由、Prompt 压缩）
- 记忆分层（Working/Episodic/Semantic/Procedural）
- 安全管控（Guardrails YAML 规则引擎）
- 预算管控（日预算 + 单次上限）
- 可观测性（结构化日志 + 任务追踪）

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Cross-Cutting Concerns               │
│         Guardrails · Observability · Cost Control       │
├─────────────────────────────────────────────────────────┤
│  L5: API Gateway (认证 · 限流 · 路由)                    │
├─────────────────────────────────────────────────────────┤
│  L4: Orchestration (Queue · Router · Planner · Monitor) │
├─────────────────────────────────────────────────────────┤
│  L3: Agent Core (LLM · ReAct · State Machine)          │
├─────────────────────────────────────────────────────────┤
│  L2: Capabilities (Tools · Memory · RAG · Skills · MCP) │
├─────────────────────────────────────────────────────────┤
│  L1: Sandbox & Runtime (Container · VM · Process)       │
├─────────────────────────────────────────────────────────┤
│  L0: Evaluation & Feedback (Metrics · Human Review)     │
└─────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. 语义缓存（省 30-50%）

```python
class SemanticCache:
    def __init__(self, cache_dir="~/.hermes/cache/semantic",
                 similarity_threshold=0.85, max_entries=1000):
        self.cache = {}  # hash -> CacheEntry
    
    def get(self, prompt, model):
        key = self._compute_hash(prompt)
        if key in self._cache and self._cache[key].model == model:
            return self._cache[key].response  # 命中，0ms/$0
        # 语义相似匹配（Jaccard ≥ 0.85）
        for entry in self._cache.values():
            if self._simple_similarity(prompt, entry.prompt_preview) >= self.threshold:
                return entry.response
        return None
    
    def put(self, prompt, response, model, tokens_used):
        key = self._compute_hash(prompt)
        if key in self._cache:
            self._cache[key].model = model  # 必须更新 model 字段！
            self._cache[key].response = response
        else:
            self._cache[key] = CacheEntry(...)
```

**关键 Bug**：
- `put()` 必须更新已有条目的 `model` 字段，否则 `get()` model 匹配失败
- AgentRunner 必须用全局缓存实例（`get_cache()`），不能用 `SemanticCache()` 新实例

### 2. 预算管控（防超支）

```python
class BudgetManager:
    def __init__(self, config: BudgetConfig):
        config.daily_limit_usd = 5.0
        config.per_task_limit_usd = 0.1
        config.alert_threshold = 0.8
    
    def check_task(self, estimated_cost: float) -> tuple[bool, str]:
        if estimated_cost > self.config.per_task_limit_usd:
            return False, "单次超预算"
        if self.daily_spent >= self.config.daily_limit_usd:
            return False, "日预算耗尽"
        if self.daily_spent + estimated_cost > self.config.daily_limit_usd * 0.8:
            return True, "⚠️ 预算紧张"
        return True, "ok"
```

### 3. 模型路由（省 20-40%）

```python
class ModelRouter:
    def route(self, prompt, context, budget_remaining=None):
        complexity = self.estimate_complexity(prompt, context)  # 0-1
        if budget_remaining < 0.5:
            tier = ModelTier.FAST
        elif complexity < 0.3:
            tier = ModelTier.FAST
        elif complexity < 0.7:
            tier = ModelTier.STANDARD
        else:
            tier = ModelTier.PREMIUM
        return self._select_from_tier(tier)
```

**降级链**：premium → standard → fast → 任意可用

### 4. Prompt 压缩（省 10-20%）

```python
class PromptCompressor:
    FILLER_PHRASES = ["请你帮我", "我希望你能", "麻烦你"]
    ABBREVIATIONS = {"例如": "例", "但是": "但", "因为": "因"}
    
    def compress(self, prompt: str) -> dict:
        # 1. 去空白
        # 2. 去废话（正则替换）
        # 3. 缩写（字典替换）
        # 4. 截断（头 80% + 尾 20%）
        return {"compressed": ..., "compression_ratio": 0.85}
```

### 5. Guardrails YAML 规则引擎

```yaml
# guardrails/rules.yaml
rules:
  - name: block_prompt_injection
    layer: input
    type: regex
    patterns: ["ignore.*instructions", "you are now"]
    action: block
    severity: critical
  
  - name: block_dangerous_commands
    layer: execution
    type: regex
    patterns: ["rm\\s+-rf\\s+/", "mkfs\\."]
    action: block
    severity: critical
  
  - name: block_api_key_leak
    layer: output
    type: regex
    patterns: ["sk-[a-zA-Z0-9]{20,}"]
    action: redact
    severity: critical
```

### 6. 四层记忆架构

```
Layer 0: Working Memory (LLM 上下文) — 1M tokens, 0ms
Layer 1: Episodic Memory (SQLite) — 1000 条/30 天, <10ms
Layer 2: Semantic Memory (向量库) — 10K-100K, <50ms
Layer 3: Procedural Memory (skills/) — 无限制, <5ms
```

### 7. 统一执行入口（Agent Runner）

```python
class AgentRunner:
    async def execute(self, prompt, use_cache=True, compress=True):
        # 1. Guardrails 输入检查
        # 2. 预算检查
        # 3. Prompt 压缩
        # 4. 缓存查询
        # 5. LLM 调用
        # 6. 输出检查
        # 7. 结果缓存
        # 8. 日志记录
```

## Phase 实施路线

| 阶段 | 策略 | 预期节省 | 工作量 |
|------|------|---------|--------|
| Phase 1 | 语义缓存 + 预算管控 | 30-40% | 1-2 天 |
| Phase 2 | 模型路由 + Prompt 压缩 | 20-30% | 2-3 天 |
| Phase 3 | 提前终止 + 批处理 + 工具优化 | 10-15% | 3-5 天 |

## 关键 Bug 修复（实测）

1. **Semantic cache model field not updated**: `put()` 只更新 response 不更新 model → `get()` 查不到
2. **AgentRunner cache instance mismatch**: 创建新 `SemanticCache()` 而非用全局 `get_cache()` → 缓存不共享
3. **Early stop newline stripping**: `text.rstrip().endswith("\n\n")` → 永远 False，改用 `text.endswith("\n\n")`
4. **Guardrails path expansion**: `~` 不展开 → 用 `os.path.expanduser("~")`
5. **Prompt compressor not integrated**: AgentRunner 创建自己的 `PromptCompressor()` 而非用全局 `get_compressor()`

## 反模式

- ❌ 每个模块单独实现，不整合 → 无法形成统一入口
- ❌ 先设计完美架构再实现 → 应该先实现核心模块，逐步扩展
- ❌ 忽略 bug 修复记录 → 下次遇到同样问题还要重新排查
- ❌ 不写测试就宣称完成 → 每个模块独立测试通过再整合

## 相关参考

- `references/agent-runner-implementation.md` — 完整代码 + 测试结果
- `references/semantic-cache-pitfalls.md` — 语义缓存常见坑
- `references/guardrails-rules.md` — Guardrails 规则示例
