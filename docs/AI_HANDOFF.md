# 把项目交给 AI

将完整仓库交给能执行终端命令的 AI 助手。读取和验证 Virtuoso 会话时，通过 [virtuoso-bridge-lite](https://github.com/Arcadia-1/virtuoso-bridge-lite)连接，步骤见 [CONNECT.md](CONNECT.md)。配置安装器在 Virtuoso 所在 Linux 环境运行。

```text
请先读这个项目的 AGENTS.md 和 README.md。
我只想启用以下功能：[填写模块 ID，例如 q-scope,viva]。
使用 virtuoso-bridge-lite 连接我的专用测试会话，先核实连接目标及 SKILL 只读请求。
请检查我的 Virtuoso 版本、已有配置和实际 .cdsinit 入口，保留其他配置。
每个功能分别安装到独立 --root，确保可以单独回退。
先在专用测试目录演练 plan、安装、验证和回退，再应用到实际入口。
不要关闭或注入我的现有 Virtuoso 会话，不要修改真实设计和 PDK。
若我没有给出 PDK 模型/器件清单，不要开启模型或工艺工作点模块。
完成后列出实际文件、启用模块、验证边界和每个模块的回退命令。
```

模块 ID 与功能在 README 中逐一对应。只需要一个功能时，把列表缩成一个 ID；不要使用 recommended 或 all。

AI 应做的最小流程：

1. 需要操作会话时，先按 CONNECT.md 使用已有桥接或连接用户指定的测试会话。核对目标后再读已有启动文件及环境，确认实际入口和已配置功能。仅整理文件或修改文档不需要建立桥接。
2. 对每个所选 ID，先在新测试目录中创建空测试 `.cdsinit`，明确指定 `--root` 和 `--cdsinit`，运行 plan。workspace 候选安装还须为安装器指定临时 HOME，避免测试阶段提前修改真实默认工作区。
3. 安装候选；用新的专用 Virtuoso 会话验证生成的 `verify.il`，按 docs/VALIDATION.md 检查行为。使用测试库，不能用真实设计做破坏性测试。
4. 执行候选 rollback，确认文件恢复。测试范围不足时如实说明，不把参数检查当成行为或视觉验收。
5. 正式安装时指定所有实际启动入口，每组使用独立目录。运行 status，保留 `.install.json`。
6. 提供每个功能对应的 rollback 命令；让用户自行选择保存工作后正常启动新会话的时机。

桥接用于执行 SKILL 和回读，持久配置由本包安装器生成。安装器文件操作通过已有终端或 SSH 在 Linux 执行；桥接的身份凭据、`.env` 和部署目录不随配置包发布。不要把一次桥接加载写成已经永久安装配置，也不要为测试强制重载共享会话。

若目标环境没有可用 Virtuoso，可以完成静态配置和安装器测试，但只能报告“尚未进行本机 Virtuoso 运行验证”。不同模型文件、corner 和器件工作点名称需要使用者自己的授权 PDK 信息；本仓库不会自动生成可替代 PDK 的内容。
