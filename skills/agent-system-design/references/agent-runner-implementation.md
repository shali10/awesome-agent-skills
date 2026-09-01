# Agent Runner Implementation Reference

All token-saving strategies implemented as standalone Python modules with unified entry point.

## Module Structure

```
agent/
├── semantic_cache.py      # Semantic cache (exact + Jaccard similarity)
├── budget_manager.py      # Budget control (daily/per-task limits)
├── model_router.py        # Model routing (complexity-based)
├── prompt_compressor.py   # Prompt compression (filler removal, abbreviations)
├── agent_logger.py        # Structured logging + task tracing
├── vector_store.py        # Lightweight vector store (numpy + Jaccard)
├── telegram_reporter.py    # Telegram push notifications
├── early_stop.py          # Early stopping (confidence + pattern matching)
├── batch_processor.py     # Batch processing (merge/split prompts)
├── tool_optimizer.py      # Container pool, search cache, file dedup
├── guardrails_engine.py   # YAML rules engine
└── agent_runner.py        # Unified entry point
```

## Execution Flow

```
User Input
  → Guardrails Input Check (block/redact)
  → Budget Check (allow/block)
  → Prompt Compression
  → Cache Query
  → LLM Call (if miss)
  → Output Check
  → Cache Store
  → Log & Return
```

## Key Bugs Fixed (2026-06-26)

| Bug | Cause | Fix |
|-----|-------|-----|
| Cache miss after put | `put()` doesn't update `model` field on existing entry | Update `entry.model = model` in `put()` |
| Cache not shared between tasks | AgentRunner creates new `SemanticCache()` | Use `get_cache()` global singleton |
| Early stop always false positive | `text.rstrip().endswith("\n\n")` = always False | Use `text.endswith("\n\n")` directly |
| Guardrails init crashes | `~` not expanded when HOME not set | `os.path.expanduser("~")` |
| Prompt compressor not integrated | AgentRunner creates own instance | Use `get_compressor()` global function |

## Test Results

| Module | Test | Result |
|--------|------|--------|
| Semantic Cache | Exact hit | 0ms, $0 |
| Semantic Cache | Jaccard ≥ 0.85 | 0ms, $0 |
| Budget Manager | 3 tasks under budget | All allowed |
| Prompt Compressor | "请你帮我写..." | 30% reduction |
| Early Stop | Code block closed | Stopped |
| Guardrails | Prompt injection | Blocked |
| Agent Runner | Full flow | All checks pass |

## Usage

```python
from agent_runner import AgentRunner, get_agent_runner

# Option 1: Direct instantiation
runner = AgentRunner(model="longcat", daily_budget=5.0)
result = await runner.execute("帮我写一个 Python 脚本")

# Option 2: Global singleton
result = await run_task("帮我写一个 Python 脚本")

# Check stats
stats = get_agent_runner().get_stats()
print(f"Total tasks: {stats['total_tasks']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Total cost: ${stats['total_cost_usd']:.4f}")
```

## Implementation Files

Each module is self-contained and can be used independently. See `agent/` directory for complete implementations.
