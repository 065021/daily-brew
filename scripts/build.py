#!/usr/bin/env python3
"""
日知录 - 索引构建脚本
扫描 content/ 目录下所有 Markdown 文章，提取元数据，
生成 web/posts.json 供前端使用。
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
WEB_DIR = ROOT / "web"
WEB_CONTENT_DIR = WEB_DIR / "content"
OUTPUT_FILE = WEB_DIR / "posts.json"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 YAML frontmatter，返回 (元数据, 正文)"""
    meta = {}
    body = text

    # 匹配 --- ... --- 开头的 YAML
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if match:
        fm_text = match.group(1)
        body = text[match.end():]

        # 简单 YAML 解析（只处理单行 key: value）
        for line in fm_text.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                # 尝试解析数组
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
                # 去掉引号
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                meta[key] = value

    return meta, body


def extract_summary(body: str, max_len: int = 120) -> str:
    """从正文提取摘要（前几个非标题、非空行）"""
    lines = []
    for line in body.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            # 引用块里的「一句话」很适合做摘要
            lines.append(stripped.lstrip("> "))
        elif stripped.startswith("---") or stripped.startswith("*"):
            continue
        else:
            lines.append(stripped)

        if len(" ".join(lines)) >= max_len:
            break

    summary = " ".join(lines)
    if len(summary) > max_len:
        summary = summary[:max_len] + "..."
    return summary


def build_index() -> list[dict]:
    """扫描文章目录，构建索引"""
    posts = []

    if not CONTENT_DIR.exists():
        print(f"content/ 目录不存在，创建空索引")
        return posts

    for md_file in sorted(CONTENT_DIR.rglob("*.md"), reverse=True):
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()

        meta, body = parse_frontmatter(text)

        # 构建文章条目（路径相对于 web/ 目录）
        rel = md_file.relative_to(CONTENT_DIR)
        post = {
            "slug": md_file.stem,
            "path": f"content/{rel.as_posix()}",
            "date": meta.get("date", md_file.stem),
            "title": meta.get("title", md_file.stem),
            "category": meta.get("category", ""),
            "tags": meta.get("tags", []),
            "summary": extract_summary(body),
        }
        posts.append(post)

    return posts


def main():
    print("🔍 扫描 content/ 目录...")
    posts = build_index()
    print(f"   找到 {len(posts)} 篇文章")

    # 复制文章到 web/ 目录
    if WEB_CONTENT_DIR.exists():
        shutil.rmtree(WEB_CONTENT_DIR)
    shutil.copytree(CONTENT_DIR, WEB_CONTENT_DIR)
    print(f"📋 文章已复制到 {WEB_CONTENT_DIR}")

    # 写入 JSON
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"✅ 索引已生成：{OUTPUT_FILE}")

    # 打印最近的 5 篇
    if posts:
        print("\n📋 最近文章：")
        for p in posts[:5]:
            print(f"   {p['date']}  [{p['category']}] {p['title']}")


if __name__ == "__main__":
    main()
