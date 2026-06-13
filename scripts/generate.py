#!/usr/bin/env python3
"""
日知录 - 内容生成脚本
每天自动生成一篇跨学科概念解读文章。

用法：
  python generate.py                          # 自动按星期选择领域
  python generate.py --topic "熵与时间箭头"    # 指定主题
  python generate.py --category 哲学           # 指定领域，随机选题
  python generate.py --dry-run                # 仅打印 prompt，不调 API
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# 配置区
# ============================================================

# 北京时间
TZ = timezone(timedelta(hours=8))

# 加载 .env 文件
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    with open(_ENV_FILE, "r", encoding="utf-8-sig") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

# API 配置 — 优先从环境变量读取
API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 星期 → 领域映射（0=周一, 6=周日）
WEEKDAY_CATEGORY = {
    0: "哲学",
    1: "科学",
    2: "经济/社会",
    3: "文学/艺术",
    4: "思想实验",
    5: "认知偏误",
    6: None,  # 周日休息
}

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
TOPICS_FILE = Path(__file__).resolve().parent / "topics.json"

# ============================================================
# 工具函数
# ============================================================

def load_topics() -> dict:
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_today_china() -> datetime:
    return datetime.now(TZ)


def pick_topic(category: str, used_topics: set = None) -> str:
    """从选题池中随机选一个，避开近期已用的"""
    topics_dict = load_topics()
    pool = topics_dict.get(category, [])
    if not pool:
        raise ValueError(f"领域「{category}」没有选题，请检查 topics.json")

    if used_topics:
        available = [t for t in pool if t not in used_topics]
        if available:
            return random.choice(available)

    return random.choice(pool)


def build_prompt(topic: str, category: str) -> str:
    """构建 AI 生成提示词"""
    return """你是一个跨学科知识写作者，风格类似「得到」的深度解读和 Wait But Why 的通俗类比。你的任务是每天解读一个概念，让读者花 3 分钟就能真正理解它，并且记住它。

## 写作规范

1. **一句话概括**：开篇用一句话说清这个概念是什么（加在 > 引用块里）
2. **一个类比**：必须用生活中常见的场景做类比，让抽象概念可以触摸
3. **为什么重要**：讲清楚这个概念为什么值得普通人知道
4. **生活里的影子**：举 2-3 个日常中能感受到的例子
5. **想一想**：结尾抛一个开放问题，让读者把概念和自己生活联系起来
6. **字数**：800-1200 字
7. **风格**：像深夜和朋友聊天，不端着、不说教、不用术语砸人。从底层原理出发，用类比落地。偶尔可以有一点点幽默，但不要刻意搞笑。

## 领域约束

当前领域：{category}
话题：{topic}

请围绕这个话题展开，但不要写成百科词条。找一个刁钻的角度切入，比如：
- 如果讲「熵」：从「为什么你的房间总会变乱」切入
- 如果讲「机会成本」：从「你刷手机的每一分钟在放弃什么」切入
- 如果讲「决定论」：从「你今天中午为什么选了那家店吃饭」切入

## 输出格式

直接输出 Markdown 正文，不需要在前面加「好的」或任何确认语。格式如下：

> 一句话：[用一句话概括这个概念]

## 换个方式理解

（这里放类比）

## 为什么这件事很重要

（这里讲深层意义）

## 生活里的影子

（2-3 个日常例子）

## 想一想

（开放式问题）

---
*由 AI 生成并人工审校。发现错误？[提 Issue](https://github.com/your/repo/issues)*
""".format(category=category, topic=topic)


def call_api(prompt: str) -> str:
    """调用 AI API 生成内容"""
    try:
        from openai import OpenAI
    except ImportError:
        print("请先安装 openai 库：pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个跨学科知识写作者。你的文章让复杂概念变得可触摸、可记住。你从不使用模板化的开头和结尾，每篇文章都有自己独特的声音。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def generate_frontmatter(title: str, category: str, tags: list[str], date_str: str) -> str:
    """生成 YAML 头部"""
    tags_str = ", ".join(tags)
    return f"""---
date: {date_str}
title: {title}
category: {category}
tags: [{tags_str}]
---"""


def extract_title(body: str, topic: str) -> str:
    """从正文提取标题，或回退到话题本身"""
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    # 回退：用话题作为标题
    return topic


def extract_tags(body: str) -> list[str]:
    """简单提取可能的标签"""
    # 第一版简单返回空列表，后续可做关键词提取
    return []


def save_post(date_str: str, category: str, body: str, topic: str) -> Path:
    """保存文章到 content/YYYY/MM/YYYY-MM-DD.md"""
    year, month, day = date_str.split("-")
    post_dir = CONTENT_DIR / year / month
    post_dir.mkdir(parents=True, exist_ok=True)

    title = extract_title(body, topic)
    tags = extract_tags(body)
    frontmatter = generate_frontmatter(title, category, tags, date_str)

    filepath = post_dir / f"{date_str}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + "\n\n" + body + "\n")

    return filepath


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="日知录内容生成器")
    parser.add_argument("--topic", type=str, help="指定话题")
    parser.add_argument("--category", type=str, help="指定领域（覆盖星期自动选择）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 prompt，不调用 API")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD（默认今天）")
    args = parser.parse_args()

    # 确定日期
    today = get_today_china()
    date_str = args.date or today.strftime("%Y-%m-%d")

    # 确定领域
    if args.category:
        category = args.category
    else:
        weekday = today.weekday()
        category = WEEKDAY_CATEGORY.get(weekday)
        if category is None:
            print(f"今天是周日，休息日。如需强制生成，请用 --category 指定领域。")
            return

    # 确定话题
    if args.topic:
        topic = args.topic
    else:
        topics_dict = load_topics()
        pool = topics_dict.get(category, [])
        if not pool:
            print(f"❌ 领域「{category}」在 topics.json 中没有选题")
            sys.exit(1)
        topic = random.choice(pool)
        # 提取短标题（冒号前的部分）
        short_topic = topic.split("：")[0] if "：" in topic else topic
        print(f"📌 今日领域：{category}")
        print(f"📌 选题：{short_topic}")

    # 构建 prompt
    prompt = build_prompt(topic, category)

    if args.dry_run:
        print("\n" + "=" * 50)
        print("DRY RUN — 以下是发送给 AI 的 prompt：")
        print("=" * 50)
        print(prompt)
        return

    # 检查 API Key
    if not API_KEY:
        print("❌ 未设置 API Key！请设置环境变量 DEEPSEEK_API_KEY")
        print("   export DEEPSEEK_API_KEY=sk-xxx")
        sys.exit(1)

    # 调用 API
    print("🤖 正在调用 AI 生成文章...")
    try:
        body = call_api(prompt)
    except Exception as e:
        print(f"❌ API 调用失败：{e}")
        sys.exit(1)

    if not body:
        print("❌ AI 返回了空内容")
        sys.exit(1)

    # 保存
    filepath = save_post(date_str, category, body, topic)
    print(f"✅ 文章已保存：{filepath}")
    print(f"   字数约：{len(body)} 字")


if __name__ == "__main__":
    main()
