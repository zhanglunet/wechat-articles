#!/usr/bin/env python3
"""Check the article archive locally. No network and no credentials."""

from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"
INDEX_PATH = ARTICLES / "index.yaml"

REQUIRED_META = ("title", "author", "source", "version_date", "status", "editor_source")
STATUSES = {
    "drafting",
    "draft_created_unpublished",
    "published",
    "withdrawn",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")

# Pins for the imported v2 article. Updating the prose means updating these.
PINNED = {
    "2026-11-15-github-trend-workflow": {
        "markdown_sha256": "5e95d707ed08a5bd46c291b68ab9a61aeeb44400d6df0f5f24a70ce071a6f34f",
        "html_sha256": "5976dadd83e2560f3b2b8ef4c19fa2d63cfd8672c8e128c4f785665ef96eac05",
        "chapters": 8,
        "cases": 5,
        "table_data_rows": [5, 7, 16],
        "files": {
            "assets/cover-magazine-16x9.jpg": "7f9c8e6c081dfb2c5c9ac40fb52ef1760a6bfdd70090980bb65e6898f7ec7c17",
            "assets/covers-optional/cover-option-dark-isometric-16x9.jpg": "8e94a0bdd152ade7ce45d2041a17e4030fc1cd837cf0507d60d208185a22d0d8",
            "assets/covers-optional/cover-option-minimal-line-16x9.jpg": "c5fe1f51abd521e422bb9ac395845be34df965689448369d863da3aed18e3875",
            "assets/workflow-infographic.png": "dd424a504f45038afa4ef7f98edc2d26dc403c6476a2d1a13a20deaf1343a3fe",
            "assets/workflow-infographic.svg": "e67a17352a5713553bcdca8ce2b06af12d022444fab95140eb2aa58fe93fcde8",
        },
    }
}

MARKERS = (
    "default_pr_gate",
    "PRD-441",
    "REVIEW_INCOMPLETE",
    "24 个核心仓库",
    "23 个持续演进仓",
    "115 个 PR",
    "2026-10-18",
    "2026-11-15",
    "mksglu/context-mode",
    "debpalash/VoiceStudio",
    "HKUDS/CLI-Anything",
    "alibaba/open-code-review",
    "来源：张路",
)

SECRET_RES = (
    re.compile(r"mmbiz\.qpic\.cn", re.I),
    re.compile(r"mmbiz\.qlogo\.cn", re.I),
    re.compile(r"\bwx[0-9a-fA-F]{16}\b"),
    re.compile(r"\bgh_[0-9a-fA-F]{8,}\b"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile("x-access-" + "token", re.I),
    re.compile(
        r"""(?i)["'](?:thumb_media_id|media_id)["']\s*:\s*["'][A-Za-z0-9_-]{8,}["']"""
    ),
)
# 键名可带引号。值可以是引号字符串，也可以是 YAML 里不带引号的一串字符。
# 以 < 开头的是文档占位符，不当作凭证。
CREDENTIAL_ASSIGNMENT = re.compile(
    r"""(?i)
    ["']?(?:appsecret|api[_-]?key|secret)["']?
    \s*[:=]\s*
    (?:
        "(?!<)[^"\s]{8,}"
        |
        '(?!<)[^'\s]{8,}'
        |
        (?!["'<])\S{8,}
    )
    """,
    re.VERBOSE,
)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
FORBIDDEN_NAMES = {
    "draft.json",
    ".env",
    "config.yaml",
    "md2wechat.yaml",
    "credentials.json",
    "secrets.json",
}


class ArchiveError(Exception):
    pass


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_scalar(value: str):
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in inner.split(",")]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value in {"true", "false"}:
        return value == "true"
    return value


def split_kv(text: str) -> tuple[str, str]:
    if text.endswith(":"):
        return text[:-1].strip(), ""
    mark = text.find(": ")
    if mark == -1:
        raise ArchiveError(f"无法解析字段：{text}")
    return text[:mark].strip(), text[mark + 2 :].strip()


def parse_yaml(text: str):
    """Parse the small YAML subset used by this archive."""
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith(" ") and (len(raw) - len(raw.lstrip(" "))) % 2:
            raise ArchiveError(f"缩进必须是 2 的倍数：{stripped}")
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, stripped))

    def parse_block(index: int, indent: int):
        if index >= len(lines):
            return {}, index
        if lines[index][0] != indent:
            raise ArchiveError(f"缩进不符合预期：{lines[index][1]}")
        if lines[index][1].startswith("- "):
            items = []
            while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
                payload = lines[index][1][2:].strip()
                index += 1
                if ": " in payload or payload.endswith(":"):
                    key, rest = split_kv(payload)
                    node = {}
                    if rest:
                        node[key] = parse_scalar(rest)
                    else:
                        child, index = parse_block(index, indent + 2)
                        node[key] = child
                    while (
                        index < len(lines)
                        and lines[index][0] == indent + 2
                        and not lines[index][1].startswith("- ")
                    ):
                        key, rest = split_kv(lines[index][1])
                        index += 1
                        if rest:
                            node[key] = parse_scalar(rest)
                        else:
                            child, index = parse_block(index, indent + 4)
                            node[key] = child
                    items.append(node)
                else:
                    items.append(parse_scalar(payload))
            return items, index
        node = {}
        while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith("- "):
            key, rest = split_kv(lines[index][1])
            index += 1
            if rest:
                node[key] = parse_scalar(rest)
            else:
                child, index = parse_block(index, indent + 2)
                node[key] = child
        return node, index

    parsed, index = parse_block(0, 0)
    if index != len(lines):
        raise ArchiveError(f"元数据后还有未能解析的内容：{lines[index][1]}")
    return parsed


def load_yaml(path: Path):
    try:
        return parse_yaml(path.read_text(encoding="utf-8"))
    except ArchiveError:
        raise
    except OSError as exc:
        raise ArchiveError(f"无法读取 {path.relative_to(ROOT)}：{exc}") from exc


def jpeg_size(data: bytes) -> tuple[int, int] | None:
    if data[:2] != b"\xff\xd8":
        return None
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in {0xC0, 0xC1, 0xC2}:
            height, width = struct.unpack(">HH", data[index + 5 : index + 9])
            return width, height
        if marker in {0xD8, 0xD9}:
            index += 2
            continue
        if index + 4 > len(data):
            return None
        segment = struct.unpack(">H", data[index + 2 : index + 4])[0]
        index += 2 + segment
    return None


def png_size(data: bytes) -> tuple[int, int] | None:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def image_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if path.suffix.lower() == ".png":
        return png_size(data)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return jpeg_size(data)
    return None


def markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    tables = []
    index = 0
    while index < len(lines):
        separator = index + 1 < len(lines) and re.match(r"^\|\s*-+", lines[index + 1])
        if lines[index].startswith("|") and separator:
            header = split_row(lines[index])
            index += 2
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append(split_row(lines[index]))
                index += 1
            tables.append((header, rows))
        else:
            index += 1
    return tables


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def html_tables(text: str) -> list[list[list[str]]]:
    tables = []
    for table in re.findall(r"<table\b[^>]*>(.*?)</table>", text, flags=re.I | re.S):
        rows = []
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, flags=re.I | re.S):
            cells = re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", row, flags=re.I | re.S)
            rows.append([re.sub(r"<[^>]+>", "", cell).strip() for cell in cells])
        tables.append(rows)
    return tables


def is_remote(url: str) -> bool:
    return url.startswith(("http://", "https://", "mailto:", "#", "data:"))


def local_targets(text: str, kind: str) -> list[str]:
    if kind == "markdown":
        found = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", text)
        found += re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)", text)
        return found
    found = re.findall(r"""(?:src|href)=["']([^"']+)["']""", text)
    return found


def candidate_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    files = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = ROOT / raw.decode("utf-8")
        if path.is_file():
            files.append(path)
    return files


def check_secrets(errors: list[str]) -> None:
    for path in candidate_files():
        rel = path.relative_to(ROOT).as_posix()
        name = path.name
        if name in FORBIDDEN_NAMES or name.endswith("-wechat-body.html") or name.endswith(".prompt.txt"):
            fail(errors, f"跟踪文件名属于禁止入库的运行产物或配置：{rel}")
        if b"\0" in path.read_bytes()[:4096]:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in (*SECRET_RES, CREDENTIAL_ASSIGNMENT):
            match = pattern.search(text)
            if match:
                fail(errors, f"{rel} 含有疑似凭证或微信素材标识：{match.group(0)[:48]}")
        for match in IPV4_RE.finditer(text):
            octets = [int(part) for part in match.group(0).split(".")]
            if all(0 <= part <= 255 for part in octets):
                fail(errors, f"{rel} 含有公网地址形态的数字：{match.group(0)}")


def check_repo_links(errors: list[str]) -> None:
    for path in candidate_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("templates/") or path.suffix.lower() not in {".md", ".html"}:
            continue
        if rel.startswith("articles/") and path.name not in {"article.md", "article.html"}:
            continue
        text = path.read_text(encoding="utf-8")
        kind = "markdown" if path.suffix.lower() == ".md" else "html"
        for url in local_targets(text, kind):
            if is_remote(url):
                continue
            target = (path.parent / url.split("#", 1)[0]).resolve()
            if not target.is_file():
                fail(errors, f"{rel} 的相对链接不存在：{url}")


def check_article(entry: dict, errors: list[str]) -> None:
    slug = entry.get("slug")
    rel = entry.get("path")
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        fail(errors, f"索引 slug 不符合 YYYY-MM-DD-english-words：{slug}")
        return
    directory = ARTICLES / rel
    meta_path = directory / "metadata.yaml"
    if not meta_path.is_file():
        fail(errors, f"缺少元数据：{meta_path.relative_to(ROOT)}")
        return
    meta = load_yaml(meta_path)
    for field in REQUIRED_META:
        value = meta.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(errors, f"{slug} 缺少 {field}")
    if meta.get("author") != entry.get("author") or meta.get("title") != entry.get("title"):
        fail(errors, f"{slug} 的标题或作者与索引不一致")
    if meta.get("source") != entry.get("source") or meta.get("status") != entry.get("status"):
        fail(errors, f"{slug} 的来源或状态与索引不一致")
    if meta.get("version_date") != entry.get("version_date"):
        fail(errors, f"{slug} 的定稿日期与索引不一致")
    if meta.get("status") not in STATUSES:
        fail(errors, f"{slug} 的状态不在约定枚举内：{meta.get('status')}")
    if meta.get("editor_source") != "markdown":
        fail(errors, f"{slug} 的编辑源必须是 markdown")
    for date_field in ("version_date", "first_published"):
        value = meta.get(date_field)
        if value and not DATE_RE.fullmatch(str(value)):
            fail(errors, f"{slug} 的 {date_field} 不是 YYYY-MM-DD")
    source = meta.get("source", "")
    if isinstance(source, str) and not source.startswith("https://"):
        fail(errors, f"{slug} 的来源需要是 https 地址")
    if meta.get("status") == "published":
        for field in ("wechat_url", "wechat_account", "wechat_published_date"):
            value = meta.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(errors, f"{slug} 已发布但缺少 {field}")
            elif value != entry.get(field):
                fail(errors, f"{slug} 的 {field} 与索引不一致")
        wechat_url = str(meta.get("wechat_url", ""))
        if wechat_url and not wechat_url.startswith("https://"):
            fail(errors, f"{slug} 的 wechat_url 需要是 https 地址")
        published_on = str(meta.get("wechat_published_date", ""))
        if published_on and not DATE_RE.fullmatch(published_on):
            fail(errors, f"{slug} 的 wechat_published_date 不是 YYYY-MM-DD")

    files = meta.get("files") or {}
    markdown = directory / files.get("markdown", "")
    html = directory / files.get("html", "")
    if not markdown.is_file() or not html.is_file():
        fail(errors, f"{slug} 缺少 article.md 或 article.html")
        return
    md_text = markdown.read_text(encoding="utf-8")
    html_text = html.read_text(encoding="utf-8")

    cover = meta.get("cover") or {}
    if cover.get("role") != "selected":
        fail(errors, f"{slug} 的 cover.role 必须是 selected")
    cover_path = directory / cover.get("path", "")
    if not cover_path.is_file():
        fail(errors, f"{slug} 的选用封面不存在：{cover.get('path')}")
    elif image_size(cover_path) != (cover.get("width"), cover.get("height")):
        fail(errors, f"{slug} 的选用封面尺寸与元数据不一致")
    if "magazine" not in Path(str(cover.get("path", ""))).name and slug in PINNED:
        fail(errors, f"{slug} 的选用封面文件名应保留 magazine，以免和备选混淆")

    optional_names = []
    for item in meta.get("optional_covers") or []:
        if item.get("role") != "optional":
            fail(errors, f"{slug} 的备选封面 role 必须是 optional")
        item_path = directory / item.get("path", "")
        optional_names.append(Path(str(item.get("path", ""))).name)
        if not item_path.is_file():
            fail(errors, f"{slug} 的备选封面不存在：{item.get('path')}")
        elif image_size(item_path) != (item.get("width"), item.get("height")):
            fail(errors, f"{slug} 的备选封面尺寸与元数据不一致：{item.get('path')}")
        if item_path.is_file() and cover_path.is_file() and sha256(item_path) == sha256(cover_path):
            fail(errors, f"{slug} 的备选封面与选用封面是同一文件")

    for name in optional_names:
        if name and (name in md_text or name in html_text):
            fail(errors, f"{slug} 的正文引用了备选封面 {name}")

    info = meta.get("infographic") or {}
    for key in ("svg", "png"):
        value = info.get(key) or ""
        if value and not (directory / value).is_file():
            fail(errors, f"{slug} 的信息图不存在：{value}")

    tables = markdown_tables(md_text)
    expected_rows = (meta.get("structure") or {}).get("table_data_rows")
    if not isinstance(expected_rows, list):
        fail(errors, f"{slug} 缺少 structure.table_data_rows")
    else:
        actual = [len(rows) for _, rows in tables]
        if actual != expected_rows:
            fail(errors, f"{slug} 的 Markdown 表数据行是 {actual}，元数据写的是 {expected_rows}")
        for number, (header, rows) in enumerate(tables, start=1):
            for row_number, row in enumerate(rows, start=1):
                if len(row) != len(header) or any(cell == "" for cell in row):
                    fail(errors, f"{slug} 的第 {number} 张表第 {row_number} 行缺列或空单元格")
    html_rows = html_tables(html_text)
    if [len(rows) - 1 for rows in html_rows] != [len(rows) for _, rows in tables]:
        fail(errors, f"{slug} 的 HTML 表行数与 Markdown 不一致")
    for number, rows in enumerate(html_rows, start=1):
        width = len(rows[0]) if rows else 0
        for row_number, row in enumerate(rows, start=1):
            if len(row) != width or any(cell == "" for cell in row):
                fail(errors, f"{slug} 的 HTML 第 {number} 张表第 {row_number} 行缺列或空单元格")

    chapters = len(re.findall(r"^## ", md_text, flags=re.M))
    cases = len(re.findall(r"\*\*案例 \d+", md_text))
    structure = meta.get("structure") or {}
    if chapters != structure.get("chapters"):
        fail(errors, f"{slug} 的二级标题数是 {chapters}，元数据写的是 {structure.get('chapters')}")
    if cases != structure.get("cases"):
        fail(errors, f"{slug} 的案例数是 {cases}，元数据写的是 {structure.get('cases')}")

    integrity = meta.get("integrity") or {}
    if integrity.get("markdown_sha256") != sha256(markdown):
        fail(errors, f"{slug} 的 Markdown 哈希与元数据不一致")
    if integrity.get("html_sha256") != sha256(html):
        fail(errors, f"{slug} 的 HTML 哈希与元数据不一致")

    pin = PINNED.get(slug)
    if pin:
        if sha256(markdown) != pin["markdown_sha256"] or sha256(html) != pin["html_sha256"]:
            fail(errors, f"{slug} 与已导入的 v2 全文哈希不一致")
        if chapters != pin["chapters"] or cases != pin["cases"]:
            fail(errors, f"{slug} 的章节或案例数量偏离 v2")
        if expected_rows != pin["table_data_rows"]:
            fail(errors, f"{slug} 的三张表行数偏离 v2：{expected_rows}")
        for rel_file, digest in pin["files"].items():
            target = directory / rel_file
            if not target.is_file() or sha256(target) != digest:
                fail(errors, f"{slug} 的图片与导入时不一致：{rel_file}")
        if "](https://trend.zhanglu.net/brand/workflow-infographic.svg)" in md_text:
            fail(errors, f"{slug} 的 Markdown 图片仍指向远程 SVG")
        if "](./assets/workflow-infographic.svg)" not in md_text:
            fail(errors, f"{slug} 的 Markdown 未指向本地 SVG")
        if "https://trend.zhanglu.net/brand/workflow-infographic.svg" not in md_text:
            fail(errors, f"{slug} 的信息图出处丢失")
        if 'src="assets/workflow-infographic.png"' not in html_text:
            fail(errors, f"{slug} 的 HTML 未指向 assets 下的 PNG")
        if 'src="workflow-infographic.png"' in html_text:
            fail(errors, f"{slug} 的 HTML 仍使用同目录 PNG 相对路径")
        for marker in MARKERS:
            if marker not in md_text:
                fail(errors, f"{slug} 缺少审核稿标识：{marker}")


def check_credential_examples() -> None:
    """Lock the assignment forms the archive scan must accept or reject."""
    token = "01234567" + "89abcdef" * 2
    detected = (
        "secret: " + token,
        '"secret": "' + token + '"',
        "api_key: " + token,
        'SECRET="' + token + '"',
    )
    allowed = (
        'SECRET="<' + "placeholder>",
        "secret: <" + "placeholder>",
        '"api_key": "<' + 'placeholder>"',
    )
    for sample in detected:
        if CREDENTIAL_ASSIGNMENT.search(sample) is None:
            raise ArchiveError("凭证赋值没有被识别")
    for sample in allowed:
        if CREDENTIAL_ASSIGNMENT.search(sample) is not None:
            raise ArchiveError("尖括号占位符被误判为凭证")


def main() -> int:
    errors: list[str] = []
    try:
        check_credential_examples()
    except ArchiveError as exc:
        print(exc)
        return 1
    try:
        index = load_yaml(INDEX_PATH)
    except ArchiveError as exc:
        print(exc)
        return 1
    entries = index.get("articles") if isinstance(index, dict) else None
    if not isinstance(entries, list) or not entries:
        print("articles/index.yaml 里没有文章")
        return 1

    seen = set()
    for entry in entries:
        path = entry.get("path")
        if path in seen:
            fail(errors, f"索引路径重复：{path}")
        seen.add(path)
        try:
            check_article(entry, errors)
        except ArchiveError as exc:
            fail(errors, str(exc))

    on_disk = set()
    for meta in ARTICLES.glob("*/*/metadata.yaml"):
        on_disk.add(meta.parent.relative_to(ARTICLES).as_posix())
    listed = {entry.get("path") for entry in entries}
    for extra in sorted(on_disk - listed):
        fail(errors, f"磁盘上的文章没有写入索引：{extra}")
    for missing in sorted(listed - on_disk):
        fail(errors, f"索引指向的目录没有 metadata.yaml：{missing}")

    try:
        check_secrets(errors)
        check_repo_links(errors)
    except subprocess.CalledProcessError as exc:
        fail(errors, f"无法列出 git 文件：{exc}")

    if errors:
        print(f"检查未通过，共 {len(errors)} 项：")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"检查通过：{len(entries)} 篇文章，索引、相对路径、表格和敏感信息扫描均未发现问题。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
