from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "posts"
OUT = ROOT / "_site"
STYLE = ROOT / "web" / "style.css"

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


def parse_post(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8").strip()
    meta: dict[str, str] = {}
    body = raw

    if raw.startswith("---\n"):
        _, front, body = raw.split("---", 2)
        for line in front.splitlines():
            if ":" not in line or line.startswith(" "):
                continue
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()

    iso = meta.get("date", path.stem)
    return {
        "date": iso,
        "mode": meta.get("mode", "ordinary-life"),
        "body": body.strip(),
        "source": path.as_posix(),
    }


def pretty_date(iso: str) -> str:
    try:
        y, m, d = (int(part) for part in iso.split("-"))
        return f"{d} {MONTHS[m]} {y}"
    except Exception:
        return iso


def paragraphs(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]


def render_body(text: str) -> str:
    rendered = []
    for para in paragraphs(text):
        safe = html.escape(para).replace("\n", "<br>")
        rendered.append(f"<p>{safe}</p>")
    return "\n".join(rendered)


def excerpt(text: str, limit: int = 230) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    cut = compact[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode, mode.replace("-", " ").title())


def build() -> None:
    posts = [parse_post(p) for p in POSTS.glob("*/*/*.md")]
    posts.sort(key=lambda p: p["date"], reverse=True)
    if not posts:
        raise SystemExit("No chronicle posts found under posts/YYYY/MM/*.md")

    latest = posts[0]
    archive = posts[1:]
    css = STYLE.read_text(encoding="utf-8")

    archive_html = []
    for post in archive:
        search_blob = html.escape((post["date"] + " " + post["body"]).lower(), quote=True)
        archive_html.append(f'''\n<article class="archive-card reveal" data-search="{search_blob}">
  <div class="archive-card__top">
    <time datetime="{html.escape(post['date'])}">{html.escape(pretty_date(post['date']))}</time>
    <span class="mode">{html.escape(mode_label(post['mode']))}</span>
  </div>
  <p class="excerpt">{html.escape(excerpt(post['body']))}</p>
  <details>
    <summary>Открыть запись <span aria-hidden="true">↘</span></summary>
    <div class="post-body">{render_body(post['body'])}</div>
  </details>
</article>''')

    archive_markup = "\n".join(archive_html) if archive_html else '<p class="empty">Архив пока пуст.</p>'
    latest_date = pretty_date(latest["date"])

    page = f'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#09070d">
  <meta name="description" content="Хроники Бегемота — московская мистическая хроника, продолжающаяся день за днём.">
  <title>Хроники Бегемота</title>
  <style>{css}</style>
</head>
<body>
  <div class="ambient ambient--one"></div>
  <div class="ambient ambient--two"></div>
  <div class="grain"></div>

  <header class="hero shell">
    <nav class="nav" aria-label="Основная навигация">
      <a class="sigil" href="#top" aria-label="К началу страницы">
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <path d="M43 10c-13 2-23 13-23 26 0 8 4 15 10 19C17 53 8 43 8 30 8 17 19 6 32 6c4 0 8 1 11 4Z"/>
          <circle cx="44" cy="22" r="2"/>
          <circle cx="49" cy="34" r="1.5"/>
        </svg>
      </a>
      <div class="nav__wordmark">Бегемот <span>·</span> Москва</div>
      <a class="nav__link" href="#archive">Архив</a>
    </nav>

    <div id="top" class="hero__grid">
      <div class="hero__copy">
        <p class="eyebrow">Хроника продолжается</p>
        <h1>Тёмные дела.<br><em>Обычные дни.</em></h1>
        <p class="lede">Записки Бегемота о московском быте, долгах, примусах, достоинстве и прочих обстоятельствах, которые почему-то всегда оказываются важнее положенного.</p>
        <a class="ghost-button" href="#latest">Читать последнюю запись <span>↓</span></a>
      </div>

      <div class="moon-card" aria-hidden="true">
        <div class="moon-orbit"></div>
        <svg class="cat-mark" viewBox="0 0 320 360">
          <path class="moon" d="M246 45c-77 17-126 91-109 168 15 67 76 114 143 111-31 24-70 36-111 31C78 344 13 261 24 170 35 79 118 14 209 25c13 2 25 5 37 10Z"/>
          <path class="cat" d="M160 133c17-27 37-41 62-42l14-31 18 35c19 9 32 27 36 50 5 28-6 55-28 70-8 6-16 10-25 13l-4 68h-17l-8-58c-8 2-16 3-25 2l-9 56h-17l-4-65c-25-10-40-30-42-55-2-19 5-34 20-43 8-5 18-5 29 0Z"/>
          <circle class="eye" cx="225" cy="140" r="4"/>
        </svg>
        <span class="orbit-label">примерно год спустя</span>
      </div>
    </div>
  </header>

  <main>
    <section id="latest" class="latest shell">
      <div class="section-kicker"><span>01</span><i></i><b>Последняя запись</b></div>
      <article class="latest-card reveal">
        <div class="latest-card__meta">
          <div>
            <p class="meta-label">Сегодня в хронике</p>
            <time datetime="{html.escape(latest['date'])}">{html.escape(latest_date)}</time>
          </div>
          <span class="mode mode--large">{html.escape(mode_label(latest['mode']))}</span>
        </div>
        <div class="post-body post-body--latest">{render_body(latest['body'])}</div>
      </article>
    </section>

    <section id="archive" class="archive shell">
      <div class="archive__heading">
        <div>
          <div class="section-kicker"><span>02</span><i></i><b>Архив</b></div>
          <h2>Что уже случилось</h2>
        </div>
        <label class="search">
          <span aria-hidden="true">⌕</span>
          <input id="search" type="search" placeholder="Поиск по хронике" autocomplete="off">
        </label>
      </div>
      <div id="archive-list" class="archive-list">
        {archive_markup}
      </div>
      <p id="no-results" class="empty" hidden>Ничего не найдено. Даже подозрительно.</p>
    </section>
  </main>

  <footer class="footer shell">
    <div class="footer__mark">
      <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M43 10c-13 2-23 13-23 26 0 8 4 15 10 19C17 53 8 43 8 30 8 17 19 6 32 6c4 0 8 1 11 4Z"/></svg>
      <span>Хроники Бегемота</span>
    </div>
    <p>Собрано из дневниковых записей репозитория. Никаких гарантий насчёт рассказчика.</p>
  </footer>

  <script>
    const search = document.querySelector('#search');
    const cards = [...document.querySelectorAll('.archive-card')];
    const empty = document.querySelector('#no-results');

    search?.addEventListener('input', () => {{
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      cards.forEach(card => {{
        const match = !query || card.dataset.search.includes(query);
        card.hidden = !match;
        visible += match ? 1 : 0;
      }});
      empty.hidden = visible !== 0;
    }});

    const observer = new IntersectionObserver(entries => {{
      entries.forEach(entry => {{
        if (entry.isIntersecting) {{
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.08 }});
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
  </script>
</body>
</html>'''

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(posts)} posts into {OUT / 'index.html'}")


if __name__ == "__main__":
    build()
