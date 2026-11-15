# 公众号文章归档

张路的个人文章归档。当前收录《把 GitHub 趋势变成自己仓库的改进》2026-11-15 的 v2.0 定稿。文章版权归作者，本仓库没有全仓开源许可证。权利说明见 [NOTICE.md](NOTICE.md)。

## 这一篇

| 项 | 内容 |
| --- | --- |
| 标题 | 把 GitHub 趋势变成自己仓库的改进 |
| 作者 | 张路 |
| 来源 | https://trend.zhanglu.net/workflow |
| 版本 | v2.0，定稿日 2026-11-15 |
| 首发日期 | 2026-10-18 |
| 状态 | 草稿已创建，未发布，未群发 |
| 编辑源 | [articles/2026/2026-11-15-github-trend-workflow/article.md](articles/2026/2026-11-15-github-trend-workflow/article.md) |
| 微信兼容 HTML | [articles/2026/2026-11-15-github-trend-workflow/article.html](articles/2026/2026-11-15-github-trend-workflow/article.html) |
| 选用封面 | [assets/cover-magazine-16x9.jpg](articles/2026/2026-11-15-github-trend-workflow/assets/cover-magazine-16x9.jpg)（杂志风，1280×720） |

正文有八章、五个案例、三张表。选用封面只有杂志风这一张。暗色等轴测和极简线条两张在 `assets/covers-optional/`，是备选，没有用于这篇草稿。

机器可读索引：[articles/index.yaml](articles/index.yaml)。

## 目录

```text
articles/     按年、按日期 slug 存放的文章、元数据和图片
templates/    下一篇可复制的正文和元数据模板
docs/         归档约定，以及不购买排版 API Key 的投稿笔记
scripts/      只读本地检查，不访问网络
NOTICE.md     文章版权和上游 md2wechat 许可归属
```

新增文章的步骤写在 [docs/archive.md](docs/archive.md)。投稿时如何排版、选封面和写入草稿箱，写在 [docs/workflow.md](docs/workflow.md)。

## 本地检查

```bash
python3 scripts/verify_archive.py
```

脚本只读工作区：核对索引、元数据、相对图片路径、三张表的行数，并扫描已跟踪文件里的凭证形态。它不调用微信，不读取密钥，也不安装外部工具。
