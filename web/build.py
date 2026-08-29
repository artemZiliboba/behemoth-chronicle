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
    year, month, day = post.date.split("-")
    return f"""
    <button class="history-item{' is-active' if is_latest else ''}" type="button"
            data-post-id="post-{html.escape(post.date)}" data-date="{html.escape(pretty_date(post.date))}" data-latest="{str(is_latest).lower()}" aria-pressed="{'true' if is_latest else 'false'}">
      <svg class="history-frame" viewBox="0 0 320 152" preserveAspectRatio="none" aria-hidden="true">
        <path d="M15 1H305V5H312V11H319V59L312 66L319 73V141H312V147H305V151H15V147H8V141H1V73L8 66L1 59V11H8V5H15Z"/>
        <path d="M17 5H303V9H308V15H315V57L307 66L315 75V137H308V143H303V147H17V143H12V137H5V75L13 66L5 57V15H12V9H17Z"/>
      </svg>
      <span class="history-summary">
        <time datetime="{html.escape(post.date)}">
          <span class="history-day">{int(day)}</span>
          <span class="history-date"><b>{MONTHS[int(month)]}</b><span>{year}</span>{'<i>Сегодня.</i>' if is_latest else ''}</span>
        </time>
      </span>
    </button>
    """.strip()


def render_post_template(post: Post, is_latest: bool = False) -> str:
    return f"""
    <template id="post-{html.escape(post.date)}">
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
  <meta name="theme-color" content="#d8c7a5">
  <meta name="description" content="Хроники Бегемота — живая московская хроника, обновляющаяся день за днём.">
  <title>Хроники Бегемота</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&amp;family=Old+Standard+TT:wght@400;700&amp;family=Roboto+Condensed:wght@400;500;600;700&amp;family=Yanone+Kaffeesatz:wght@600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="page-shell">
    <header class="hero">
      <div class="side-stamp">Архив · Москва · 2026</div>
      <div class="masthead">
        <h1>Хроники<br>Бегемота</h1>
        <div class="issue"><b>№ <span>028</span></b><span>Москва</span><span>2026</span></div>
        <nav aria-label="Основная навигация"><a href="#history">Архив</a><a href="#about">О проекте</a></nav>
      </div>
      <div class="eyebrow">Архив наблюдений и происшествий</div>
    </header>

    <main class="content-grid">
      <section class="latest-section" aria-label="Последняя запись">
        <div class="edition-line"><span id="edition-date"><b>Сегодня.</b> {html.escape(pretty_date(latest.date))}</span></div>
        <article class="message-card-latest" id="active-post" aria-live="polite">
          <div class="message-body">{paragraphize(latest.body)}</div>
        </article>
      </section>

      <section class="history-section" id="history">
        <div class="history-heading">Выберите день.</div>
        <div class="history-list">{history_html}</div>
        <button class="history-more" type="button"><span aria-hidden="true">↓</span> Показать ещё.</button>
      </section>
      {post_templates}
    </main>
    <footer class="site-footer" id="about">
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
