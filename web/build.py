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


def render_history_item(post: Post, is_latest: bool = False) -> str:
    return f"""
    <button class="history-item{' is-active' if is_latest else ''}" type="button"
            data-post-id="post-{html.escape(post.date)}" aria-pressed="{'true' if is_latest else 'false'}">
      <span class="history-summary">
        <div class="history-summary-top">
          <time datetime="{html.escape(post.date)}">{html.escape(pretty_date(post.date))}</time>
          <span class="history-tag">{html.escape(mode_label(post.mode))}</span>
        </div>
        {'<span class="history-today">Сегодня</span>' if is_latest else ''}
        <div class="history-preview">{html.escape(post.preview)}</div>
      </span>
    </button>
    """.strip()


def render_post_template(post: Post, is_latest: bool = False) -> str:
    return f"""
    <template id="post-{html.escape(post.date)}">
      <div class="message-meta">
        {'<span class="today-badge">Сегодня</span>' if is_latest else ''}
        <time datetime="{html.escape(post.date)}">{html.escape(pretty_date(post.date))}</time>
        <span class="reading-time"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>≈ 5 мин чтения</span>
      </div>
      <div class="message-body">{paragraphize(post.body)}</div>
    </template>
    """.strip()


def render_page(posts: List[Post]) -> str:
    latest = posts[0]
    history_html = "\n".join(render_history_item(post, index == 0) for index, post in enumerate(posts)) or (
        '<div class="empty-history">Пока что других записей нет.</div>'
    )
    post_templates = "\n".join(render_post_template(post, index == 0) for index, post in enumerate(posts))

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
    <header class="hero">
      <div class="hero-copy">
        <h1>Хроники Бегемота</h1>
        <div class="eyebrow">Архив наблюдений и происшествий</div>
        <p class="hero-text">Московская жизнь, долги, примусы, достоинство и редкие случаи бытовой метафизики.</p>
      </div>
    </header>

    <main class="content-grid">
      <section class="latest-section" aria-label="Последняя запись">
        <article class="message-card-latest" id="active-post" aria-live="polite">
          <div class="message-meta">
            <span class="today-badge">Сегодня</span>
            <time datetime="{html.escape(latest.date)}">{html.escape(pretty_date(latest.date))}</time>
            <span class="reading-time"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>≈ 5 мин чтения</span>
          </div>
          <div class="message-body">{paragraphize(latest.body)}</div>
          <footer class="article-footer">
            <div class="tag-list"><span class="tag">домоуправление</span><span class="tag">быт</span></div>
            <div class="article-actions" aria-label="Действия с записью">
              <button type="button" aria-label="Сохранить"><svg viewBox="0 0 24 24"><path d="M6 4h12v16l-6-4-6 4Z"/></svg></button>
              <button type="button" aria-label="Поделиться"><svg viewBox="0 0 24 24"><path d="M14 5l5 5-5 5v-3c-5 0-8 2-10 6 1-6 4-10 10-10Z"/></svg></button>
            </div>
          </footer>
        </article>
      </section>

      <section class="history-section" id="history">
        <div class="history-heading"><span>Выберите день</span><svg viewBox="0 0 24 24"><rect x="4" y="6" width="16" height="14" rx="2"/><path d="M8 3v6M16 3v6M4 10h16M9 14h2"/></svg></div>
        <div class="history-list">{history_html}</div>
        <button class="history-more" type="button">Показать ещё <span>⌄</span></button>
      </section>
      {post_templates}
    </main>
    <footer class="site-footer">
      <div class="quote"><span class="quote-mark" aria-hidden="true">“</span><span>Рукописи не горят. Зато отлично пылятся.<br><b>— М. А. Б.</b></span></div>
      <div class="copyright">© Хроники Бегемота, 2026<br>Сделано с чёрным юмором и вниманием к деталям.</div>
    </footer>
  </div>
  <script src="script.js"></script>
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

    (SITE_DIR / "index.html").write_text(render_page(posts), encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy2(WEB_DIR / "style.css", SITE_DIR / "style.css")
    shutil.copy2(WEB_DIR / "script.js", SITE_DIR / "script.js")
    shutil.copytree(WEB_DIR / "assets", SITE_DIR / "assets")
    print(f"Built {len(posts)} posts into {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    build()
