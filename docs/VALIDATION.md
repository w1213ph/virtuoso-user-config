# 验证层次

每次报告分别标注：参数已加载、实际行为已验证、GUI 已目视检查。后一项不能从前一项推断。

## 安装器

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
```

测试使用临时目录，不需要 Virtuoso。覆盖单模块隔离、互不重叠的组合、独立撤回、多启动入口、原始字节保留、后续无关改动保留、受管理块冲突拒绝、安装失败恢复、模型输入检查和工作区备份。

## Virtuoso 参数

在独立测试入口安装所选模块，再从该入口新启动专用测试会话。加载安装目录生成的 `verify.il`，确认 `VUC_VERIFICATION_FAILURES=0`，检查打印的字体及缩放环境。脚本只断言所选模块的环境参数，不运行仿真，不修改设计，不自动退出会话。

对每个实际入口分别记录不带候选设置的基线和带候选设置的日志，比较相同操作产生的错误/警告。临时文件名与 PID 可以规范化后比较，但不能隐藏新的错误类别。

## 行为及目视清单

| 模块 | 实际操作 | 图形检查 |
| --- | --- | --- |
| ciw/form-fonts | 新开 CIW、Direct Plot | 字体可读；标签、单选项和边框无挤压 |
| labels | 在测试库新建各类标签 | Roman 生效；已有标签不改写 |
| viva | 新建波形图和标记 | 白底、线条、图例、字体和数字格式 |
| q-scope | 单选、多选器件后按 Q，关闭再开 | all selected，原 same master 保留 |
| undo-history | 在测试库执行可逆编辑和 undo/redo | 历史面板显示；不测试保存后撤销承诺 |
| ade-ui | 打开 Corners Setup，增删测试 corner | 同步及 Run Preview；Refresh 保持原流程 |
| op-annotations | 专用 NMOS/PMOS DC 仿真；参数→模型→DC→参数→DC | 正常器件参数与真实工作点气泡都能恢复 |
| ade-models | 不同技术关联新 ADE、保存/恢复非默认 corner | 模型表单与原厂清单及保存状态一致 |
| workspace | 新开只读测试原理图，加载并保存工作区 | Navigator、Property Editor 等面板可用 |
| 不缩放启动 | 从可能带遗留变量的终端启动 | Direct Plot 与原理图画布底部均完整 |

工作点、ADE 模型的历史行为测试来自 IC6.1.8 的限定专用库和流程，不等于任意 PDK、所有 IC 版本或所有 Explorer/Assembler/GXL 入口都通过。

发布版的移植改动另见 CURRENT_STATE.md；不得把原环境历史结果直接标作使用者本机已通过。
