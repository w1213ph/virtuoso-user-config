# Virtuoso User Config

面向 Cadence Virtuoso IC6.1.8 的可选用户配置。可以只安装一个功能，也可以组合安装；每组配置有独立目录、启动块、备份及回退记录。无需连接项目作者的服务器，也无需 AI 才能运行。

默认保留现有快捷键、PDK 初始化和第三方工具入口。配置不会批量改写已有设计标签，不调整仿真求解精度或器件参数。运行环境需要自行安装并授权的 Virtuoso；安装器只依赖 Python 3.6+ 标准库，在 Linux 上运行。

## 获取项目

在运行 Virtuoso 的 Linux 环境中下载，或从 GitHub 下载 ZIP 后解压：

```sh
git clone https://github.com/w1213ph/virtuoso-user-config.git
cd virtuoso-user-config
```

接下来根据下表选择功能；单项功能请明确指定 `--features`。

## 选择功能

| 模块 ID | 功能 | 额外输入 |
| --- | --- | --- |
| `ciw` | CIW 使用 mono 18，输入区 12 行 | 无 |
| `form-fonts` | 表单 label/text 恢复为 11，避免旧表单挤压 | 无 |
| `labels` | 新建原理图、符号、版图标注使用 Roman；部分字高 0.05，标注数字位数 6 | 无 |
| `viva` | 白底、1200×700、中等实线、19 类 Roman 波形字体和标记格式 | 无 |
| `q-scope` | Q 属性窗口默认处理 all selected | 无 |
| `undo-history` | 显示 Undo/Redo History | 无；不启用保存后撤销 |
| `ade-ui` | Corners Setup 同步，默认显示 Run Preview | 无；不自动 Refresh |
| `op-annotations` | MOS 工作点及气泡，并保留参数/模型/DC 模式切换 | 默认仅 analogLib；工艺器件需本机清单 |
| `ade-models` | 按设计关联的技术库实际路径，为新 ADE 选择模型默认值 | 本机模型映射 JSON |
| `workspace` | 从本机 Basic 模板创建 Design_Default 并设为 Schematics 默认 | 本机 Basic.workspace |

`--features recommended` 是前七项，也是省略 `--features` 时的默认值。**只要一个功能时必须显式指定该 ID**。`--features all` 需要模型映射和工作区模板齐全。

Qt 缩放修复另提供 `bin/virtuoso-unscaled` 启动脚本，仅清除本次启动的 `QT_SCALE_FACTOR`，按需执行，不安装全局 shell 设置。

## 只安装一个功能

在解压目录中执行。下面只配置 Q 属性窗口，不设置字体、ViVA、ADE 或工作区：

```sh
python3 install.py plan --features q-scope \
  --root "$HOME/.cadence/virtuoso-user-config/q-scope" \
  --cdsinit "$HOME/.cdsinit"

python3 install.py install --features q-scope \
  --root "$HOME/.cadence/virtuoso-user-config/q-scope" \
  --cdsinit "$HOME/.cdsinit"
```

`plan` 不写文件。`install` 备份原内容，只向指定启动文件追加受管理的块，不覆盖原 `.cdsinit`。安装器不退出、重载或向现有 Virtuoso 进程注入代码。

可以随后独立添加 ViVA：

```sh
python3 install.py install --features viva \
  --root "$HOME/.cadence/virtuoso-user-config/viva" \
  --cdsinit "$HOME/.cdsinit"
```

每个根目录只对应一次安装。需要分别撤销的功能，请像上面一样分别安装。也可以 `--features ciw,labels,viva` 合并安装，合并后的功能按组回退。相同启动文件内的重复功能会被拒绝。

## 验证和回退

保存工作后，自行从相应工程正常新开一个会话。原理图打开后在 CIW 加载该模块的检查脚本：

```skill
load(strcat(getShellEnvVar("HOME") "/.cadence/virtuoso-user-config/q-scope/verify.il"))
```

`VUC_VERIFICATION_FAILURES=0` 只代表所选参数加载正确。还应在专用测试库中执行实际操作，并目视检查窗口。Q 属性需要检查单选、多选和重开；ViVA 需要新建波形窗口；字体需要同时查看 Direct Plot 和原理图画布。更多步骤见 [验证说明](docs/VALIDATION.md)。

```sh
python3 install.py status --root "$HOME/.cadence/virtuoso-user-config/q-scope"
python3 install.py rollback --root "$HOME/.cadence/virtuoso-user-config/q-scope"
```

回退只移除该组启动块和安装文件；保留其他模块及后来追加的无关启动配置。受管理块或安装文件被修改时，回退整体停止，避免覆盖后续修改。安装目录中的 `.install.json` 保留备份和状态，请留在本机。

回退后重新启动才会恢复相应运行时状态。若需重新安装，先把已回退的安装目录移到其他位置保留备份，再按原命令安装。

## 工程有自己的启动文件

Virtuoso 实际读取的 `.cdsinit` 取决于启动目录和站点设置。工程内有自己的 `.cdsinit` 时，不能只安装到用户目录；请确认实际入口，用重复的 `--cdsinit` 指定每一份文件：

```sh
python3 install.py plan --features q-scope \
  --root "$HOME/.cadence/virtuoso-user-config/q-scope" \
  --cdsinit "$HOME/.cdsinit" --cdsinit "$HOME/my-project/.cdsinit"
```

上述目标目录必须已存在。使用 `-nocdsinit` 启动会跳过这些启动块。项目中新建 `.cdsinit` 可能遮蔽站点初始化，安装器不会自行推断或补写站点/PDK 加载逻辑。

## 可选高级功能

工艺工作点清单、ADE 模型映射、工作区及不缩放启动方法见 [高级配置](docs/ADVANCED.md)。这些输入只在使用者本机保存，不把任何人的 PDK 路径作为默认值。高级模块依赖 Cadence 版本及相应 API，建议先在独立测试启动文件上验证。

把本项目交给 AI 时，可直接复制 [AI 操作提示](docs/AI_HANDOFF.md)，项目内 [AGENTS.md](AGENTS.md) 规定了功能隔离、备份、验证和回退边界。

## 历史、验证及发布

- [全部改动整理](docs/CHANGES.md)：包含最终有效功能、已撤回方案及未实现项，也说明电路工程的独立范围。
- [当前发布状态](CURRENT_STATE.md) 与 [更新记录](CHANGELOG.md)。
- [开源及隐私说明](docs/PUBLISHING.md)：发布前执行 `python3 scripts/check_release.py`。
- 采用 Apache-2.0，保留 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。界面偏好的早期来源为 [YiDingg 的初始化文章](https://github.com/YiDingg/YiDingg/blob/main/AnalogIC/Use%20Virtuoso%20Efficiently%20-%201.%20Shortcuts%20and%20Initialization.md)，之后按 IC6.1.8 实测修订；不包含原文正文或供应商软件。
