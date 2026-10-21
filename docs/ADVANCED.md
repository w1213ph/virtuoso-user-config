# 高级配置

先用[功能手册](FEATURES.md)确认要启用的模块；本页说明工艺工作点、模型映射和本机工作区需要填写什么。普通界面与波形配置不需要这些工艺输入，[首页](../README.md)提供了单项安装和回退示例。

## MOS 工作点

`op-annotations` 独立于字体、ViVA 外观和 ADE 模型模块。初始显示模式为器件参数；点击原有 DC Operating Points 菜单后才应用扩展工作点。画布最多五项 `id/vgs/vds/vth/gm`，气泡保留十项，后五项是 `region/gmoverid/rout/ron/cgg`。

默认清单仅包含 `examples/devices.analoglib.json` 中的 analogLib MOS；其符号通常只有三个 cdsParam 位置，因此常驻前三项。工艺器件使用本机 JSON，格式见 `examples/devices.pdk.example.json`。`inline_slots` 是符号可显示的位置数，0–5；库名、单元名须与实际一致。多类器件可放在同一清单中。

```sh
mkdir -p local
# 在 local/devices.local.json 中填写本机授权 PDK 的 MOS 库/单元清单
python3 install.py plan --features op-annotations \
  --devices local/devices.local.json \
  --root "$HOME/.cadence/virtuoso-user-config/op-annotations"
```

确认后用同一参数执行 install。未提供 `--devices` 时只启用 analogLib 清单。`--op` 是在所选功能之外添加该模块的便利选项；若只想工作点，应明确使用 `--features op-annotations`。

安装器生成两个 `.as` 文件：默认 `parameter` 和供 DC 菜单使用的 `opPoint`。不要把后者设成初始全局文件，否则可能使参数显示无法恢复。模块用菜单后处理保留原生切换，使用 `_ann*` 等内部 API，其他版本需要重新测试。

必须已经仿真并保存相应 DC 工作点数据；本模块不会改变 Spectre save 设置。不是每个模型都有十个字段，也不是每个符号都有五个位置。没有数据时不得伪造显示值。气泡需要开启原生 File → Show Balloons，仍使用原生滚动尺寸。

## 新 ADE 模型默认值

依据实际设计库的技术关联和技术库的 `readPath` 精确匹配；不会根据名字选择相近 PDK。先用本机 CIW 查询：

```skill
techGetTechLibName(ddGetObj("yourDesignLib"))
ddGetObj("yourTechnologyLib")~>readPath
```

复制 `examples/models.example.json` 到 `local/models.local.json` 后修改。每个 `technology_read_path` 是上述实际值，每个 `models` 行是原厂推荐文件和 section；路径必须存在。文件存在检查不等于 section、corner 或器件仿真已验证，应与原厂默认值逐项核对。

```sh
python3 install.py plan --features ade-models \
  --models local/models.local.json \
  --root "$HOME/.cadence/virtuoso-user-config/ade-models"
```

`--models` 会选择此模块，只写本机路径清单，不复制或修改模型内容。它链式保留已有 `asimenv.startup/sessInitTrigFunc`，对 Spectre 新会话初始化一次。不批量重写保存状态、手动选择或已有 corner。已有状态中的错误模型仍需用户另行处理。目标版本须验证载入保存状态的顺序；不能仅凭 hook 注册就宣称恢复 corner 已通过。

## 工作区

不分发 Cadence 二进制模板。读取使用者本机安装目录的 `share/cdssetup/dfII/workspaces/Schematics/Basic.workspace`，在本机创建 `Design_Default.workspace` 和 `workspace.default`。已有默认指针会备份，已有同名目标工作区会拒绝覆盖。

```sh
python3 install.py plan --features workspace \
  --workspace-template "$CDS_INST_DIR/share/cdssetup/dfII/workspaces/Schematics/Basic.workspace" \
  --root "$HOME/.cadence/virtuoso-user-config/workspace"
```

`CDS_INST_DIR` 由本机安装位置设置；不是每个站点都会定义这个变量。可替换成实际绝对路径。仅设置 Schematics；不设置 XL、Layout、Symbol，也不在每次启动时重置用户后来保存的默认工作区。

## 仅本次启动不缩放

```sh
sh bin/virtuoso-unscaled
```

此脚本要求 `virtuoso` 已在 PATH 中，其他参数原样传递。它清除本次进程继承的 `QT_SCALE_FACTOR`。历史上 1.2 倍缩放在 IC6.1.8/VNC 下导致原理图底部裁切；不据此批量更改其他应用的缩放。本项目不自动改 `.cshrc`、`.bashrc` 或 VNC 分辨率。
