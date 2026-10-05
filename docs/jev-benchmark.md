# Jev 评分费用与耗时对照

2026-10-05 已完成真实 API 对照。固定同一份 30 篇候选、同一研究兴趣、同一五级相关性 rubric、同一最低分，两组均选出 10 篇。

## 结果

| 指标 | GPT-6 Astra | Jev 1.13.0 |
| --- | ---: | ---: |
| 输入 token | 11,665（其中缓存 2,304） | 13,724 |
| 输出 token | 267 | 474 |
| 总 token | 11,932 | 14,198 |
| API 调用墙钟耗时 | 10.3487 秒 | 0.5187 秒 |
| 官方标准 API 标价折算 | $0.109264 | $0.000576408 |
| 入选数量 | 10 | 10 |

**标价折算费用降低 99.47%，此次评分约快 19.95 倍。** 两组入选论文重合 9/10；这不是人工质量评审，也不证明排序质量完全等价。单次快照和单次测量不代表长期平均速度或每个研究方向的效果。

Jev 总 token 比主模型多 18.99%，但单位价格低得多。因此这里展示费用与耗时收益，不宣传总 token 更少。相对首版 Jev 请求，优化版总 token 从 18,960 降到 14,198，减少 25.12%；前后入选重合 9/10，不能称作无损等价优化。

## 费用计算及实际账户边界

价格核实日期：2026-10-05。以下均为美元 / 百万 token：

- [TypeSafe 官方模型价格](https://docs.typesafe.ai/models)：Jev 输入 $0.042，输出免费。
- [OpenAI 官方 GPT-6 Astra 价格](https://developers.openai.com/api/docs/models/gpt-6-astra)：标准短上下文输入 $10、缓存输入 $1、输出 $50。

```text
GPT-6 Astra = ((11,665 - 2,304) × 10 + 2,304 × 1 + 267 × 50) / 1,000,000
            = $0.109264
Jev         = (13,724 × 0.042 + 474 × 0) / 1,000,000
            = $0.000576408
节省比例     = 1 - 0.000576408 / 0.109264 = 99.47246%
```

这是**实测 token 按官方标准 API 价格折算**，不是账户实际扣款。主模型通过本机 ChatGPT 账号中转调用，订阅额度不能直接换算为这次调用的现金账单；本次没有读取两家账户的扣款明细。也不把其他服务档位、套餐折扣或税费当作已测事实。

仅计算语义评分阶段，未计宿主 Agent 编排、富化后的点评、PDF 精读和笔记生成。原项目的 Python 关键词评分本来就不消耗模型 token；此处比较的是通用模型与 Jev 两种语义评分方案。

## 实现与实验记录

Jev 使用本机已有 `TYPESAFE_API_KEY` 对 `https://api.typesafe.ai/v1/systemone` 的真实调用。优化采用简洁的五级 rubric、移除判断不需要的 URL，并把 30 道独立问题放入一个批次，共享研究兴趣。论文标题与完整摘要均保留，不截断论文内容。默认 `ranking.batch_size` 从 10 改为 30。

主模型使用 `gpt-6-astra`，把同一批论文和共享 rubric 一次性提交，仅要求 ID 与分数，不强制长解释。基准脚本完整读取 SSE 到 `[DONE]` 和 EOF，保留最终 usage、缓存信息及原始事件，避免把中间片段或缺失用量当成完整结果。测试专用临时中转凭据在每次运行后撤销，未写入仓库。

候选来自 2026-10-04 的一次日常抓取：HF Daily / Trending 与近期 arXiv 合并 443 篇，关键词召回 30 篇。周末快照包含近期与热门论文，不限当天发表。Jev 优化测量与主模型对照是分开执行的网络请求，耗时也包含各自网络条件；不是同硬件吞吐测试。

原始证据：

- [候选快照](benchmarks/2026-10-04/candidates.json)
- [最终完整对照：请求、SSE、实际 usage、输入与代码 SHA-256](benchmarks/2026-10-05/scoring-benchmark-final.json)
- [优化版 Jev 请求与答案](benchmarks/2026-10-05/jev-compact.json)
- [费用计算与价格来源](benchmarks/2026-10-05/cost-comparison.json)
- [首版 Jev 与主模型对照](benchmarks/2026-10-05/scoring-benchmark-stream.json)
- [失败尝试记录](benchmarks/2026-10-05/attempts.json)
- [2026-10-04 初始测量清单](benchmarks/2026-10-04/manifest.json)

此前旧接口返回 401 / 502；恢复本机中转后，旧模型名被账号拒绝，非流式请求也被拒绝。保留这些失败，不将缺失用量记为零。额外探针和开发重复测量不算作一次日常运行用量。

## 复跑

Python 3.10+，无需模型 SDK。使用同一份有效配置，在环境中设置 `TYPESAFE_API_KEY`、`OPENAI_API_KEY` 和可选的 `OPENAI_BASE_URL`；不得将密钥写入报告。

```bash
python3 scripts/benchmark_scoring.py docs/benchmarks/2026-10-04/candidates.json \
  --model gpt-6-astra --output scoring-benchmark.json
```

可追加 `--jev-report docs/benchmarks/2026-10-05/jev-compact.json` 复用本次真实 Jev 测量。脚本逐项校验候选、配置、rubric、模型、选择阈值及原始用量，不匹配就停止。旧版 Jev 报告的 rubric 不同，不能在当前配置下复用。

报告路径必须是新文件，失败也保存已完成部分。费用复算使用上方公式或 [cost-comparison.json](benchmarks/2026-10-05/cost-comparison.json) 中的价格与实际 usage；价格未来变化时应重新核实。
