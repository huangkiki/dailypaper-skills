# 在不同 Agent 中运行

这套技能共用一份工作流，所需能力是：读取指令与论文、运行 Python/命令行、联网获取来源、写入 Markdown。使用当前宿主实际提供的工具；不要求某个品牌或模型。

## 路径与配置

- 相对路径以**当前 `SKILL.md` 所在目录**为基准，不以用户项目的工作目录为基准。执行脚本时指定该目录为工作目录，或将路径转换为绝对路径；含空格的路径要加引号。
- 保留完整安装布局：所有技能目录和 `_shared` 同级。不要单独复制一个 `SKILL.md`。
- 用当前可用的 Python 3.10+ 运行 `../_shared/user_config.py`，读取输出 JSON 中的有效配置和 `runtime.temp_dir`。示例中的 `python3` 在 Windows 可换成 `py -3` 或 `python`。
- 配置按顺序合并：内置默认值 → `_shared/user-config.json` → `_shared/user-config.local.json` → `~/.config/dailypaper-skills/user-config.json`（遵循 `XDG_CONFIG_HOME`）→ `DAILYPAPER_CONFIG` 指定的 JSON。`OBSIDIAN_VAULT_PATH` 最后覆盖笔记库路径。不要仅阅读某个模板后忽略覆盖值。
- 将 `runtime.temp_dir` 记为 `TEMP_DIR`。文档中的 `{TEMP_DIR}` 是待替换的绝对路径，不是字面量。各阶段必须使用同一目录；同时运行多个流水线时，为每次运行设置不同的 `DAILYPAPER_TEMP_DIR`，并传给后续阶段。

## 调用与工具

- 宿主支持 Skill 调用时，用它的原生入口；例如 Claude Code 的 `/daily-papers` 或 Codex 的 `$daily-papers`。这些写法是对话指令，不是 shell 命令。
- 宿主没有 Skill 调用工具时，读取目标技能目录的 `SKILL.md`，按其要求执行，并按需读取它引用的模板和参考文件。三步流水线按顺序执行，上一阶段成功后再进入下一阶段。
- `Bash` 表示命令执行能力，`Read/Write/Edit/Glob/Grep` 表示文件读写与搜索，`WebFetch/WebSearch` 表示网页获取与检索。它们是能力示例，不是必须存在的工具名称。没有 PDF 阅读工具时，可用 `pdftotext` 和 `pdfimages` 提取文字与图片。
- 宿主支持且允许子 Agent 时，可以把单篇 `paper-reader` 放入独立上下文，传入 Skill 路径、论文来源、配置和临时目录。否则在当前会话逐篇执行同一 Skill，遵循相同模板与质量要求。缺少子 Agent 不是跳过笔记的理由。
- 无法联网、运行命令或访问笔记库时，报告具体缺失能力和已完成阶段；不要将未执行的阶段报告为成功。

## 权限与可选入口

遵循用户与宿主的文件、网络和 Git 授权；不要求关闭权限检查。默认只生成本地笔记，自动 Git 提交与推送取决于共享配置和已有授权。

`paper_daemon.py` 和 Web Viewer 的 Claude 对话按钮是可选的 Claude CLI 扩展。其他 Agent 在自己的会话里使用上述技能；Web Viewer 的笔记浏览不依赖 Claude。
