# 权利与上游归属

核对日期：2026-11-15。核对对象是 `geekjourneyx/md2wechat-skill` 默认分支上的 `LICENSE`、`VERSION`、`package.json` 和 `docs/INSTALL.md`。

## 本仓库里的文章

文章版权归作者本人。当前文章的作者是张路。作者没有把这些文章授予 MIT、Apache-2.0 或其他开放许可。阅读、引用时请保留作者、标题和来源地址。转载或演绎需要作者另行同意。

本仓库也没有给脚手架、说明和检查脚本加全仓开源许可证。仓库里没有 `LICENSE` 文件。这是故意的：避免一篇未授权的文章被整仓许可证连带放行。

## 上游 md2wechat

命令行工具是外部依赖，仓库地址：

https://github.com/geekjourneyx/md2wechat-skill

本次可复现基线固定为 npm 包 `@geekjourneyx/md2wechat@3.8.0`。核对时三处版本一致：

- 仓库根目录 `VERSION` 的内容是 `3.8.0`
- `package.json` 的 `version` 是 `3.8.0`，`license` 字段是 `SEE LICENSE IN LICENSE`
- `docs/INSTALL.md` 写明当前安装说明对应 v3.8.0，并给出 `npm install -g @geekjourneyx/md2wechat@3.8.0`

上游许可证标题是 **md2wechat Source Available License**，正文标明基于 **Business Source License 1.1（BUSL-1.1）**。许可人是 geekjourneyx，作品版权年份为 2024–2026。许可证定义的 Licensed Work 包含 CLI 源码、主题、排版模块、提示词模板、技能定义，以及该仓库中的相关文档与素材。

这份许可证在变更日之前不按 MIT 授予权利。变更日是 2030-01-01，变更后的许可证是 Apache-2.0。英文条款同时写明：若某一版本在该许可证下首次公开发布满四周年的日子更早，则从这两者中较早的日期起改用 Apache-2.0。许可证里的中文说明写明，中文与英文不一致时以英文为准；该许可证生效前的历史版本仍是 MIT，此点不追溯改写那些历史版本。3.8.0 属于当前这份源码可用许可证，不能当成 MIT 再分发，也不能把上游主题、提示词或技能改标成 MIT。

变更日之前，许可证另有个人非商业用途的附加使用许可。商业用途需要向许可人另行取得书面授权。完整措辞以上游 `LICENSE` 为准：

https://github.com/geekjourneyx/md2wechat-skill/blob/main/LICENSE

本仓库只把上述 npm 包当作本机外部命令使用。这里不复制上游源码、主题、排版模块、提示词、技能、文档或图片素材，也不附上上游许可证全文。`docs/workflow.md` 是根据公开命令行为和这次实际投稿过程单独写的，里面没有嵌入上游提示词。

购买上游专业 API（`MD2WECHAT_API_KEY`）是可选项。购买 API 本身也不等于取得上游商业授权。本次归档采用的路径不购买该 Key。细节见 `docs/workflow.md`。
