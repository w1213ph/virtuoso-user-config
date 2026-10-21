# 让 AI 连接 Virtuoso

[返回首页](../README.md) · [安装配置](INSTALL.md) · [AI 操作说明](AI_HANDOFF.md)

本项目配合 [Arcadia-1/virtuoso-bridge-lite](https://github.com/Arcadia-1/virtuoso-bridge-lite) 使用。AI 通过它向 Virtuoso 发送 SKILL、读取执行结果；选好的配置再由本仓库的 `install.py` 写入用户启动文件。

下面是单台远程 Virtuoso 主机的连接步骤，依据上游 [README](https://github.com/Arcadia-1/virtuoso-bridge-lite#readme) 和[连接指南](https://github.com/Arcadia-1/virtuoso-bridge-lite/blob/main/skills/virtuoso/references/connection.md)整理。更复杂的跳板机、多主机与多配置场景，以所安装版本的上游说明为准。

## 先确认两边的环境

| 位置 | 需要准备 |
| --- | --- |
| AI 所在机器 | 能执行终端命令的 AI 助手；Git、uv、bridge 客户端。当前上游客户端要求 Python 3.9+ |
| Virtuoso 主机 | 已安装并授权的 Virtuoso；一个指定的测试会话；正常可用的 SSH 访问 |
| 安装本包的位置 | Virtuoso 所在 Linux 用户环境；配置安装器要求 Python 3.6+ |

这两个 Python 要求属于不同程序。AI 可以在 Windows 上操作 bridge，配置安装器则放在 Linux 端。只运行本包的手动安装流程时，可以直接在 Linux 使用安装器。

## 1. 安装 bridge 客户端

在 **AI 所在机器** 下载上游项目。以下以 sh/bash 为例，选择 Python 3.11 创建虚拟环境：

```sh
git clone https://github.com/Arcadia-1/virtuoso-bridge-lite.git
cd virtuoso-bridge-lite
uv venv .venv --python 3.11
. .venv/bin/activate
uv pip install -e .
```

uv 本身的安装方法见 [uv 官方说明](https://docs.astral.sh/uv/getting-started/installation/)。已有可用 bridge 环境时，继续使用它，无需重新安装或覆盖配置。

<details>
<summary>Windows PowerShell</summary>

进入上游项目目录后，可以直接使用虚拟环境内的可执行文件，省去激活步骤：

```powershell
uv venv .venv --python 3.11
uv pip install --python .venv/Scripts/python.exe -e .
.\.venv\Scripts\virtuoso-bridge.exe init your-user@your-server
.\.venv\Scripts\virtuoso-bridge.exe start
```

后续的 `status`、`eval` 等命令也使用这个可执行文件。其余步骤相同。

</details>

## 2. 填自己的 SSH 目标

先确保自己的 SSH 登录可用，再初始化桥接。将占位符换为自己的用户名和 Virtuoso 主机：

```sh
virtuoso-bridge init your-user@your-server
```

当前上游默认写入 `~/.virtuoso-bridge/.env`。连接参数、账号和密钥选择只保存在本机，按上游及站点现有 SSH 配置填写，不放进这个公开仓库。已有配置时，`init` 默认不会覆盖它。

如需指定独立配置文件，使用上游支持的 `--env FILE`；`start`、`status`、`eval` 使用同一份文件，避免检查和操作落到不同会话。

## 3. 启动桥接，在 CIW 加载

准备一个**专用 Virtuoso 测试会话**，然后在 AI 所在机器运行：

```sh
virtuoso-bridge start
```

它会准备连接，并打印一条 `load("...")`。把**这次输出的完整命令**粘贴到指定测试会话的 CIW 中。命令里的文件路径由上游生成，不要照抄其他人的路径。

这一条加载用于启用桥接，不是安装本包的界面配置。不要为了接通测试而停止、重载或切换用户正在使用的共享会话；已有可用桥接时先复用并核实目标。

## 4. 检查请求是否真的到了会话

```sh
virtuoso-bridge status
virtuoso-bridge eval '1+2'
```

确认会话连接成功，SKILL 求值结果为 `3`。还可以只读查询版本：

```sh
virtuoso-bridge eval 'getVersion(t)'
```

隧道进程存在，只说明连接的一部分已启动。只有 CIW 侧已加载并能返回 SKILL 结果，才能开始读取和验证设置。保持上游的身份核对和认证机制启用。

## 5. 把配置任务交给 AI

让 AI 读取本仓库的 [AGENTS.md](../AGENTS.md)、[功能清单](FEATURES.md)和 [AI 交接说明](AI_HANDOFF.md)。告诉它要用哪个测试会话、哪些功能，以及实际启动入口。

操作分别发生在两处：

| 工作 | 在哪里执行 |
| --- | --- |
| 读取当前参数、检查候选加载、查询报错 | AI 通过 bridge 在已核实的 Virtuoso 测试会话执行 SKILL |
| `plan / install / status / rollback` | AI 通过终端或既有 SSH，在 Linux 端运行本包安装器 |
| 正式配置生效 | 保存工作后，从相应工程正常新开 Virtuoso 会话 |

配置包需要在 Linux 上有副本；可以由 AI 下载或通过已有 SSH 传入。不要把 Windows 客户端路径直接写进 Linux `.cdsinit`。先在测试入口演练安装和回退，再接入实际入口。

参数加载检查通过后，还应按模块做实际操作和目视检查。例如 Q 属性要单选、多选并重开表单，ViVA 要新建波形窗口。没有 GUI 条件时，分别说明已经检查的参数和仍未完成的图形验收。

## 常见连接问题

| 现象 | 先查什么 |
| --- | --- |
| SSH 登录失败 | 本机网络、VPN、SSH 目标及现有认证是否可用 |
| `start` 后仍不能执行 SKILL | 是否在正确测试会话加载了这次生成的完整 CIW 命令 |
| CIW 提示找不到加载文件 | SSH 与图形会话是否能看到同一部署目录；上游支持配置共享 scratch 路径 |
| 已有会话或桥接正忙 | 核实目标和状态，保留已有任务，不直接重启或重复提交不确定请求 |
| 连接检查包含无关的仿真器提示 | 当前任务首先需要可用的 Virtuoso / SKILL 通道；区分桥接问题与站点已有初始化问题 |

所用上游版本提供 `doctor` 时，可运行只读诊断：

```sh
virtuoso-bridge doctor
```

诊断不会替你启动或修复所有服务。具体字段及处理方法参考上游当前版本的[连接指南](https://github.com/Arcadia-1/virtuoso-bridge-lite/blob/main/skills/virtuoso/references/connection.md)。本次只核对文档和命令实现，没有替使用者建立或验证新的服务器连接。
