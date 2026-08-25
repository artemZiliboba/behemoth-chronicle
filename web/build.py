from __future__ import annotations

import html
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
WEB_DIR = ROOT / "web"
SITE_DIR = ROOT / "_site"
ASSETS_DIR = WEB_DIR / "assets"

MONTHS = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

MODE_LABELS = {
    "ordinary-life": "Повседневность",
    "thread-development": "Продолжение",
    "echo": "Эхо прошлого",
    "major-event": "Событие",
}


@dataclass
class Post:
    date: str
    mode: str
    body: str
    path: Path
    preview: str


def parse_frontmatter(text: str) -> tuple[Dict[str, object], str]:
    if not text.startswith("---"):
        return {}, text.strip()

    lines = text.splitlines()
    frontmatter_lines: List[str] = []
    body_start = None

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body_start = i + 1
            break
        frontmatter_lines.append(lines[i])

    if body_start is None:
        return {}, text.strip()

    meta: Dict[str, object] = {}
    current_key = None

    for raw_line in frontmatter_lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue

        list_match = re.match(r"^\s*-\s+(.*)$", line)
        if list_match and current_key:
            meta.setdefault(current_key, [])
            if isinstance(meta[current_key], list):
                meta[current_key].append(list_match.group(1).strip())
            continue

        key_value_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_value_match:
            key = key_value_match.group(1).strip()
            value = key_value_match.group(2).strip()
            current_key = key
            meta[key] = [] if value == "" else value

    body = "\n".join(lines[body_start:]).strip()
    return meta, body


def pretty_date(iso: str) -> str:
    try:
        year, month, day = (int(part) for part in iso.split("-"))
        return f"{day} {MONTHS[month]} {year}"
    except Exception:
        return iso


def extract_preview(body: str, limit: int = 112) -> str:
    one_line = re.sub(r"\s+", " ", body).strip()
    if len(one_line) <= limit:
        return one_line
    clipped = one_line[:limit].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped + "…"


def load_posts() -> List[Post]:
    posts: List[Post] = []
    for path in sorted(POSTS_DIR.glob("*/*/*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        post_date = str(meta.get("date", path.stem))
        mode = str(meta.get("mode", "ordinary-life"))
        posts.append(Post(date=post_date, mode=mode, body=body, path=path, preview=extract_preview(body)))

    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def paragraphize(text: str) -> str:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    rendered = []
    for paragraph in parts:
        safe = html.escape(paragraph).replace("\n", "<br>")
        rendered.append(f"<p>{safe}</p>")
    return "\n".join(rendered)


def mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode, mode.replace("-", " ").title())


def render_history_item(post: Post) -> str:
    return f"""
    <details class="history-item">
      <summary class="history-summary">
        <div class="history-summary-top">
          <time datetime="{html.escape(post.date)}">{html.escape(pretty_date(post.date))}</time>
          <span class="history-tag">{html.escape(mode_label(post.mode))}</span>
        </div>
        <div class="history-preview">{html.escape(post.preview)}</div>
      </summary>
      <div class="history-content">{paragraphize(post.body)}</div>
    </details>
    """.strip()


def render_page(posts: List[Post]) -> str:
    latest = posts[0]
    older = posts[1:]
    history_html = "\n".join(render_history_item(post) for post in older) or (
        '<div class="empty-history">Пока что других записей нет.</div>'
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#09090d">
  <meta name="description" content="Хроники Бегемота — живая московская хроника, обновляющаяся день за днём.">
  <title>Хроники Бегемота</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="page-shell">
    <div class="ambient ambient-a"></div>
    <div class="ambient ambient-b"></div>

    <header class="hero">
      <div class="hero-copy">
        <div class="eyebrow">Архив наблюдений и происшествий</div>
        <h1>Хроники Бегемота</h1>
        <p class="hero-text">Московская жизнь, долги, примусы, достоинство и редкие случаи бытовой метафизики.</p>
      </div>
      <div class="hero-mark">
        <img src="assets/behemoth-quill.svg" alt="Кот Бегемот с писчим пером">
      </div>
    </header>

    <main class="content-grid">
      <section class="latest-section">
        <div class="section-heading">
          <span class="section-kicker">Последняя запись</span>
          <span class="section-date">{html.escape(pretty_date(latest.date))}</span>
        </div>

        <article class="message-card message-card-latest">
          <div class="message-meta">
            <time datetime="{html.escape(latest.date)}">{html.escape(pretty_date(latest.date))}</time>
            <span class="message-mode">{html.escape(mode_label(latest.mode))}</span>
          </div>
          <div class="message-body">{paragraphize(latest.body)}</div>
        </article>
      </section>

      <section class="history-section">
        <div class="section-heading">
          <span class="section-kicker">Что уже случилось</span>
          <span class="section-date">нажмите на запись</span>
        </div>
        <div class="history-list">{history_html}</div>
      </section>
    </main>
  </div>
</body>
</html>
"""


def build() -> None:
    posts = load_posts()
    if not posts:
        raise SystemExit("No chronicle posts found under posts/YYYY/MM/*.md")

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "assets").mkdir(parents=True, exist_ok=True)

    (SITE_DIR / "index.html").write_text(render_page(posts), encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy2(WEB_DIR / "style.css", SITE_DIR / "style.css")
    shutil.copy2(ASSETS_DIR / "behemoth-quill.svg", SITE_DIR / "assets" / "behemoth-quill.svg")
    print(f"Built {len(posts)} posts into {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    build()
