# Agent 接入与验证

## 安装依据

安装器只负责复制完整技能包，不安装或登录 Agent，不修改其权限与模型配置。

| 宿主 | 官方 Skill 文档 | 默认个人目录 |
| --- | --- | --- |
| Claude Code | [Extend Claude with skills](https://code.claude.com/docs/en/skills) | `~/.claude/skills` |
| Codex | [Build skills](https://learn.chatgpt.com/docs/build-skills) | `~/.agents/skills` |
| Cursor | [Agent Skills](https://cursor.com/docs/skills) | `~/.cursor/skills` |
| GitHub Copilot | [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | `~/.copilot/skills` |
| Gemini CLI | [Agent Skills](https://geminicli.com/docs/cli/skills/) | `~/.gemini/skills` |
| OpenCode | [Agent Skills](https://opencode.ai/docs/skills/) | `~/.config/opencode/skills` |
| OpenClaw | [Skills](https://docs.openclaw.ai/tools/skills) | `~/.openclaw/skills` |

按 2026-10-04 查阅的官方说明整理。宿主版本、远程模式和沙箱设置可能改变发现位置；可用 `--target` 指向当前环境的实际技能根目录。Codex、Cursor、Copilot、Gemini CLI、OpenCode 等也可发现 `~/.agents/skills`，已共享安装时不必再复制一套。

本项目遵循 [Agent Skills 的基本格式](https://agentskills.io/specification)：名称与触发说明放在 `SKILL.md` 的 YAML frontmatter，执行细节、脚本和模板保留在文件系统中。跨技能引用通过相邻路径解析，因此整包安装包含 `_shared` 和全部七个技能。

## 接入其他 Agent

1. 如果宿主识别 `SKILL.md`，执行 `python3 install.py --target "/actual/skills/root"`，再刷新宿主。
2. 如果宿主不能自动发现技能，但能读取文件、执行 Python 和访问网络，在仓库中直接让它读取 `skills/daily-papers/SKILL.md`。单篇阅读则读取 `skills/paper-reader/SKILL.md`。
3. 若宿主将每个 Skill 放在独立隔离目录，需配置同一个可访问的完整技能包；仅上传单份 `SKILL.md` 不足以运行。
4. 无法访问本地文件的纯聊天环境，需要先提供可执行工作区和持久化输出目录，不能仅靠安装提示词实现本地自动化。

不用把 Claude 的 `Task` / `Skill` / `WebFetch` 工具名伪装成其他宿主的工具；[运行约定](../skills/_shared/agent-runtime.md) 定义的是所需能力，按当前工具实现即可。没有子 Agent 时，逐篇运行 `paper-reader`。

## 配置与迁移

运行目标安装目录中的 `_shared/user_config.py`，可检查实际生效的配置和临时目录。所有 Agent 建议使用一份共享配置；`DAILYPAPER_CONFIG` 可显式指向任意 JSON 配置，`OBSIDIAN_VAULT_PATH` 可临时覆盖笔记库。

旧版 Claude 或 `~/.codex/skills` 安装仍可原地更新：

```bash
python3 install.py --target ~/.codex/skills --update
```

如果当前宿主已不扫描旧目录，应迁到其现行目录，并自行检查旧副本是否还在被加载。安装器不会删除旧安装，避免丢掉用户修改。

原安装目录的 `user-config.json`、`user-config.local.json` 会保留；更新脚本时不要顺手把旧配置替换为仓库模板。迁移到共享配置可从旧安装目录执行 `python3 _shared/user_config.py --init`。共享配置已存在时，该命令不会覆盖或自动合并两个用户配置。

多 Agent 并行使用时，为每次运行设置独立的 `DAILYPAPER_TEMP_DIR`，避免中间 JSON 互相覆盖；同一天的推荐与 `.history.json` 仍应串行写入。

## 验证边界

自动化测试覆盖安装布局、独立工作目录运行、配置优先级、旧配置保留、安装冲突、UTF-8 JSON 输出以及 Web Viewer 回归。CI 在 Linux 与 Windows、Python 3.10 与 3.12 上运行这些测试；具体是否通过，以当前提交的 CI 结果为准。

这些测试不等于各品牌客户端的完整执行测试。新增宿主适配可按以下流程验收：

1. 在空技能目录安装，确认能发现七个 Skill。
2. 指向测试笔记库，运行 `更新索引`，确认产物只写到该库。
3. 运行 `今日论文推荐`，逐阶段核对候选 JSON、推荐页、重点笔记、概念链接和目录。
4. 检查所有“必读”论文是否得到完整笔记，以及失败时是否报告具体阶段。
5. 用同一共享配置换到另一个 Agent，核对笔记库、关键词和输出路径一致。

Web Viewer 的浏览功能可以查看任意 Agent 生成的同格式 Markdown。其 `/api/claude` 对话入口和 `paper_daemon.py` 保留原有 Claude CLI 实现，不计入其他宿主的兼容范围。
