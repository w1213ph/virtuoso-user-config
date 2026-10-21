# 发布内容与隐私

只把这个独立仓库目录上传到 GitHub。上一级私人维护目录、旧压缩包、原始记录和截图不属于发布包。

发布目录使用白名单重建，未复制连接配置、服务器 IP/主机名、SSH 账号/私钥位置、个人用户目录、VNC/桥接端口、令牌或原始运行日志。默认工作区名称已改成 Design_Default。没有携带旧 Git 历史。

模型映射、器件清单及绝对安装路径在使用者本机生成。`.install.json` 内含备份，`local/`、`*.local.json` 和运行日志必须保持私有。`.gitignore` 是辅助防线，不替代发布检查。

```sh
python3 scripts/check_release.py
python3 -m unittest discover -s tests -v
git diff --cached --stat
```

检查器递归检查源文件，拒绝常见私有地址、个人 home 路径、私钥、凭据赋值、二进制/日志/模型/电路文件和符号链接，不打印敏感匹配原文。它不能证明任意新增文件都不含隐私；提交前仍需审阅内容。`.git` 与 Python 缓存不属于源码检查范围，正式 ZIP 使用明确文件清单，不纳入缓存。

公开项目位于 [w1213ph/virtuoso-user-config](https://github.com/w1213ph/virtuoso-user-config)。本独立目录是 Git 仓库根目录；不要从上级私人维护目录执行 `git add .`。分支或二次发布时，也应保留同样的内容审查和隐私边界。

LICENSE 为 Apache-2.0，NOTICE 保留早期偏好的上游出处及本项目修改说明。许可证适用于这里的配置/代码/文档；不附带 Cadence 软件、供应商模板、模型、规则、论文 PDF 或专有手册的再分发许可。
