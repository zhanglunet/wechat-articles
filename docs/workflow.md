# 不购买排版 API Key 的投稿笔记

这篇记录 2026-11-15 把《把 GitHub 趋势变成自己仓库的改进》v2.0 送进公众号草稿箱的做法。命令行为按上游 v3.8.0 的公开安装说明、使用说明和配置说明核对过。2026-11-24 之前，上传和建草稿由作者在自己的机器上确认后亲自做；2026-11-24 起，作者确认后改由助手在固定出口服务器上执行，见文末补充。本仓库的检查脚本不会代做。

## 固定哪一版 CLI

```bash
npm install -g @geekjourneyx/md2wechat@3.8.0
md2wechat version --json
```

npm 安装需要 Node.js 18 或更高。这个版本号写死，避免落到以后的 `latest`。上游 `docs/INSTALL.md` 写明，该 npm 包下载与版本号相同的 GitHub Release 二进制并核对 `checksums.txt`。安装是否成功，看 `md2wechat version --json`。配置校验是另一步，不算安装成功本身。

其他安装方式见上游安装文档。无论哪一种，都固定到 v3.8.0，再继续下面的步骤。

https://github.com/geekjourneyx/md2wechat-skill/blob/main/docs/INSTALL.md

## 两条转换路径，这次走哪一条

v3.8.0 里，不写 `--mode` 的 `convert` 默认就是 API 模式，等价于 `--mode api`。API 模式调用上游付费的专业排版服务，需要 `MD2WECHAT_API_KEY`，成功时由服务返回最终 HTML。

这次不购买该 Key，也不设置这个环境变量。排版走 AI 模式：

```bash
md2wechat convert article.md --mode ai --theme custom --json
```

这条命令的设计是把排版提示交给宿主。成功时结果为 `CONVERT_AI_REQUEST_READY`，`status` 为 `action_required`，提示在 `data.prompt`。同一次调用不生成最终 HTML，不上传图片，不创建草稿，也不要求在 md2wechat 里配置模型 Key。宿主读完提示后，自己写出带内联样式的微信兼容 HTML，保存为文章目录里的 `article.html`。

`data.prompt` 属于上游许可证里的提示词材料。可以在本机临时使用，不要提交进这个仓库，也不要改标成 MIT。`.gitignore` 已忽略 `*.prompt.txt`。

`md2wechat preview --mode ai --json` 返回 `PREVIEW_ACTION_REQUIRED`，`output_file` 为空，这次调用不会写出预览 HTML。本地预览就是用浏览器打开仓库里的 `article.html`。

主题的 `type` 必须和 `--mode` 一致，否则 CLI 返回 `THEME_MODE_MISMATCH`。v3.8.0 使用说明把 `default` 列在 API 主题下，把 `custom`、`autumn-warm`、`spring-fresh`、`ocean-calm` 列在 AI 主题下。因此 AI 模式使用 `custom`，不把 API 的 `default` 主题和 `--mode ai` 放在同一次命令里。换版本后先看发现结果，再选主题：

```bash
md2wechat themes list --json
```

选用 `selectable` 为真、且 `type` 与当前模式一致的名字。

付费 API 模式仍然是可选项。需要稳定地由上游直接返回 HTML、使用 API 主题或高级排版模块时，再单独购买 Key。没有 Key 时，不要把默认的 `convert`、`preview` 或 `convert --draft` 当成已经完成排版。命名多账号（`--wechat-account`）在上传和建草稿之前还会要求有效的 `MD2WECHAT_API_KEY`。这次基线是单账号，不使用命名账号。

购买 API 服务也不等于取得上游软件的商业授权。许可边界见 [NOTICE.md](../NOTICE.md)。

## 人先定稿，再碰微信

顺序固定如下。前一步没有完成，不进入后一步。

1. 审正文。编辑源是 `article.md`。保留已审核的表述、数字、技术标识和来源。归档可以改图片的本地路径，同时把原出处留在图注里。
2. 本地预览。打开 `article.html`，看内联样式、表格和配图。这一步不调用微信。
3. 作者选定草稿标题，并从准备好的封面里选一张。这篇准备了三张 16:9 封面，选用的是杂志风 `assets/cover-magazine-16x9.jpg`。另外两张留在 `assets/covers-optional/`，不上传。
4. 确认正文配图。信息图的公开原件是 SVG，微信正文使用由它转出的 PNG。HTML 引用 `assets/workflow-infographic.png`。
5. 作者明确同意后，才上传这一张封面和正文 PNG，并创建草稿。
6. 作者登录公众号后台，自己发布。创建草稿不会群发，本仓库也不提供发布命令、定时任务或带微信凭证的 CI。

微信草稿元数据有长度上限：标题最多 32 个字符，作者最多 16 个字符，摘要最多 128 个字符。归档标题可以按文章原题保存；真正写入草稿的标题以作者当场选定的为准。

## 凭证放在哪里

单账号只用这两个环境变量：

```bash
export WECHAT_APPID="<你的公众号 AppID>"
export WECHAT_SECRET="<你的公众号 AppSecret>"
```

也可以把它们放在本机 `~/.config/md2wechat/config.yaml`。该文件已经被忽略，不要提交，示例里也不写真实值。

已有配置文件时，不要再运行 `md2wechat config init`。v3.8.0 的 `config init` 若发现目标文件已经存在，会报 `config file already exists` 并退出，不会覆盖原文件。不要为了“重新初始化”而删掉现有配置。本仓库没有会自动执行 `config init` 的脚本。

本地可以做只读检查：

```bash
md2wechat config validate --json
md2wechat doctor --json
```

`config validate` 只说明配置能被加载和解析。`doctor` 是本地体检，用 `data.readiness.format_api`、`data.readiness.advanced_layout` 和 `data.readiness.draft` 报告默认 API 转换、默认主题、排版目录和草稿凭证在本机是否看起来齐全。它不调用远程接口，不做在线身份校验，不上传图片，也不创建草稿。

这两项通过，不能证明 AppID 与 AppSecret 属于目标公众号，也不能证明当前机器的公网 IP 已在微信白名单里。身份和白名单要等真正调用微信接口时才知道。

## 白名单只说明机制

上传素材和创建草稿时，微信会核对发起请求的那台机器的公网 IP 是否在公众号 IP 白名单中。家庭宽带、公司和云主机的出口地址都可能变化，所以白名单要按“实际执行命令的那台机器、当时的出口”来维护。

本仓库不记录任何出口 IP，也不提供查询或写入白名单的脚本。需要时由作者在自己的运行环境查看，再登录微信开发者平台的开发接口管理页面自行填写。

上游另有付费的固定出口能力（`wechat.proxy_url`）。那是可选的付费功能，启用后上传和建草稿还会要求 `MD2WECHAT_API_KEY`。这次基线不使用它，文档里也不写代理地址。

## 作者确认之后的命令

在文章目录中，只上传选用封面和正文 PNG：

```bash
md2wechat upload_image ./assets/cover-magazine-16x9.jpg --json
md2wechat upload_image ./assets/workflow-infographic.png --json
```

把终端返回的图片地址写进一份本机 HTML 副本，使正文图指向微信图床。仓库里的 `article.html` 保持本地相对路径，不要改成图床地址。图床副本的文件名使用 `*-wechat-body.html`，已被忽略。

再准备一份本机草稿 JSON，例如 `draft.json`：

```json
{
  "articles": [
    {
      "title": "<作者选定的草稿标题>",
      "author": "<作者名>",
      "digest": "<摘要>",
      "content": "<图床副本中的 HTML>",
      "content_source_url": "https://trend.zhanglu.net/workflow",
      "thumb_media_id": "<封面 upload_image 返回的素材标识>",
      "show_cover_pic": 1
    }
  ]
}
```

然后：

```bash
md2wechat create_draft ./draft.json
```

`create_draft` 读取这个 JSON，调用微信的草稿接口，把文章放进草稿箱。它不群发。命令返回的草稿标识只留在终端，不写回仓库。`draft.json` 已被忽略。

做完后到公众号后台查看草稿。发布、修改可见范围和群发都由作者在后台自己操作。

## 2026-11-24 补充：固定出口服务器上建草稿与推送预览

2026-11-24 第四篇《冷启动 51 秒：八轮调优手记》建草稿时，本 VM 的出口 IP 每跑一次换一个，一上午见了三个不同地址，`test-draft` 三次都报 40164（IP 不在白名单）。逐个加白名单是打地鼠，改走一台固定出口 IP 的服务器：白名单里只加这台服务器的出口地址一次。

- 公众号的 IP 白名单关不掉。官方文档的口径是“只有白名单内的 IP 可以调用服务端 API”，没有关闭开关（小程序那类是“开启后才限制”，公众号不在此列）。
- 建草稿仍用 `test-draft`，在文章目录里一次完成（正文 HTML + 封面）：

  ```bash
  md2wechat test-draft article.html assets/cover-magazine-16x9.jpg --json
  ```

  成功返回 `TEST_DRAFT_CREATED` 与草稿标识 `media_id`。标识不写回仓库。
- 预览推送走公众号的群发预览接口（`message/mass/preview`），用仓库里的 `scripts/preview.py`：

  ```bash
  python3 scripts/preview.py <草稿 media_id> <接收人的微信号>
  ```

  脚本先取 access_token，再以 `mpnews` + `towxname`（微信号）推送，成功返回 `msg_id`。它只推给这一个微信号，不群发。脚本不带任何凭证与标识，凭证从运行机器的 `~/.config/md2wechat/config.yaml` 读（`wechat.appid` / `wechat.secret`），media_id 与微信号每次都由命令行传入。
- 群发预览接口要认证账号：个人主体或未认证的公众号调 `message/mass/preview` 会返回 `48001 api unauthorized`（2026-11-24 实测，本号如此）。这种账号的预览走公众号后台：草稿箱打开草稿 → 预览 → 填微信号 → 发送。脚本留给有群发权限的账号用。
- 凭证只存在那台固定出口服务器的配置文件里（600 权限，仅服务器的属主可读），不在仓库里，不进记忆文件。2026-11-24 之前每次用完即删；作者当天决定以后每天都要发预览，改存下来，用完不再删。想删时说一声就 shred 掉。
- 作者确认的规矩不变：每次建草稿与推预览之前都要作者先点头。建草稿不群发，预览只到指定的微信号，发布仍由作者在后台自己操作。
