# 文章归档约定

这个仓库按年份和日期保存个人公众号文章。Markdown 是编辑源。同目录的 HTML 是给微信阅读的内联样式正文，图片使用仓库内相对路径。

## 目录

```text
articles/
  index.yaml
  2026/
    2026-11-15-github-trend-workflow/
      article.md
      article.html
      metadata.yaml
      assets/
        cover-magazine-16x9.jpg
        workflow-infographic.svg
        workflow-infographic.png
        covers-optional/
          cover-option-dark-isometric-16x9.jpg
          cover-option-minimal-line-16x9.jpg
templates/
  article.md
  metadata.yaml
```

新文章复制 `templates/` 下的两个文件，放到：

```text
articles/<四位年份>/<YYYY-MM-DD>-<英文短横线 slug>/
```

`YYYY-MM-DD` 用这一版正文定稿的日期。若后来有修订版，另开一个日期目录，并在两篇 `metadata.yaml` 里互相写下关系。不要把旧版正文覆盖掉。

slug 用小写英文和数字，方便路径稳定。中文标题写在 `title` 字段和 Markdown 一级标题里。

## 每篇必填

`articles/index.yaml` 和该篇 `metadata.yaml` 都要写：

| 字段 | 含义 |
| --- | --- |
| `title` | 文章标题 |
| `author` | 作者 |
| `source` | 正文原始出处的公开地址 |
| `version_date` | 这一版定稿日期，`YYYY-MM-DD` |
| `status` | 见下方状态 |
| `editor_source` | 固定写 `markdown` |

建议同时写下 `first_published`（首次公开或首次成稿的日期）、`version` 和一句 `status_note`。

`articles/index.yaml` 的 `path` 相对于 `articles/`，并与目录名一致。索引和目录要互相覆盖：多出来的目录或索引里的空路径都会被 `scripts/verify_archive.py` 拒绝。

## 状态

- `drafting`：还在写，没有进公众号草稿箱
- `draft_created_unpublished`：草稿箱里已有一篇未发布草稿
- `published`：作者已在公众号后台发布
- `withdrawn`：作者撤回，或不再准备发布

状态只描述进度。不要在元数据、索引或正文文件名里写草稿标识、素材标识、公众号原始 ID。

## 封面和配图

`cover.role` 为 `selected` 的那一张才是选用封面。文件名保留画风，避免和备选混放。备选放在 `assets/covers-optional/`，`role` 写 `optional`。正文 Markdown 和 HTML 不引用备选封面。

信息图同时保留可编辑的 SVG 和微信正文用的 PNG。Markdown 指向本地 SVG，并在图下保留公开出处。HTML 的 `img src` 指向同目录下的 PNG，使用相对路径 `assets/...`。

外部图片改为本地文件时，出处留在图注或元数据的 `source` / `credit` 里。

## 正文怎么改

先改 `article.md`。HTML 是排版结果，只在排版或图片相对路径需要更新时一起改。改完后重算两个文件的 SHA-256，写入 `integrity`，再运行：

```bash
python3 scripts/verify_archive.py
```

当前这篇 v2 的哈希被检查脚本钉住。改字、删表或换图都会使检查失败，需要同时更新元数据里的哈希和结构计数。

## 不入库的东西

`.gitignore` 已排除本机配置、环境文件、`draft.json`、文件名带 `-wechat-body.html` 的替换稿、提示词输出和日志。这些文件即使出现在工作区，也不要 `git add -f`。
