# Cron 误删恢复：curator 备份是唯一完整定义来源（2026-08-03 实战）

## 场景

清理数据源/资产时连带误删功能型 cron。实例：2026-08-01 清理 czl 数据源时，Hermes 本地的 `VPS优惠监控` cron（每周一 07:00 推送）被一并删除，用户 8/3 周一发现没推送才暴露。当时清理汇报里明确写了「Hermes VPS优惠监控 cron ✅ 已删除」——清理范围扩大化，用户没细看就放过了。

## 排查「cron 怎么没了」的证据链

| 来源 | 能证明什么 | 不能证明什么 |
|---|---|---|
| `~/.hermes/cron/jobs.json` | 当前存在哪些 job | 历史是否曾经存在（被删的已不在） |
| `~/.hermes/cron/executions.db` | job_id 曾执行过（有执行时间范围） | prompt/调度定义（只有 job_id 级记录） |
| `~/.hermes/skills/.curator_backups/<ts>/cron-jobs.json` | **完整 job 定义**（prompt、schedule、deliver、origin、created_at） | —（这是唯一完整来源） |
| `~/.hermes/state.db` messages 表 | 历史会话里提过该 job 名 | 定义细节（工具输出常被截断） |
| Honcho（ai 侧） | 历史结论可能有 job 存在/删除记录 | 定义细节 |

**关键**：`executions.db` 只存 `job_id`，不存 prompt。恢复 prompt 只能靠 curator 备份的 `cron-jobs.json`。

## 恢复步骤

```bash
# 1. 在 curator 备份里找该 job 完整定义
grep -l "任务名" ~/.hermes/skills/.curator_backups/*/cron-jobs.json
# 2. 读出完整 JSON（含 prompt/schedule/deliver/origin）
# 3. cronjob action='create' 重建（用备份里的 prompt + schedule + deliver）
# 4. cronjob action='run' 手动触发一次，确认 last_status=ok 且投递真实到达
```

若该 cron 是内容生成类且要表格投递，重建时直接按 telegram-pipe-table-rendering 的 D 方案变体配 wrapper（`no_agent=True` + 脚本内嵌 `hermes chat` + `deliver=local`），避免重建后又是 bullet。

## 预防纪律

用户说「删除干净 / 清理 X」时：
1. **先 `cronjob list` 全量核对**哪些 job 属于目标（数据源/资产名），只删明确目标
2. 功能型 cron（推送/报告/备份/监控）不是清理目标，**不连带删**
3. 删除前把 `jobs.json` 备份到带时间戳路径（`cp jobs.json jobs.json.bak.$(date +%s)`）
4. 清理汇报里明确列出「本次删除的 cron 清单」，与数据源删除分开列出，让用户能看出范围

## 相关

- 本技能 D 方案变体节：重建内容生成类 cron 的正确投递配置
- `hermes-cron-setup`（user-owned）：cron 常规运维坑位，本恢复路径若需并入请 `hermes curator adopt hermes-cron-setup`

## 后续（2026-08-03 当天结局）

该 cron 恢复重建并验证表格投递成功后，用户最终决定「算了，删除干净吧」——cron、脚本、输出、executions.db 记录、Honcho 结论、MEMORY 引用全部清除（jobs.json 回到 17 个任务）。**教训：恢复能力 ≠ 用户要恢复**。用户可能因为内容质量/折腾成本选择放弃该功能，此时「删除干净」全链路清理（含 executions.db 的 `DELETE FROM executions WHERE job_id=...`，这是 cronjob remove 不会自动做的）。curator 备份仍然留着，用户未来想重建随时可还原。
