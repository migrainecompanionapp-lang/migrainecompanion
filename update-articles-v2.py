#!/usr/bin/env python3
"""
SAFE article updater — does NOT remove inline styles.
Only adds:
  1. data-category="..." on <body>
  2. <link rel="stylesheet" href="article-category-colors.css"> before </head>
  3. Fixes category tag text to match blog.html

Usage: python3 update-articles-v2.py --dry-run
       python3 update-articles-v2.py
"""

import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSS_FILE = "article-category-colors.css"
DRY_RUN = "--dry-run" in sys.argv

# Article files to skip
SKIP_FILES = {
    "index.html", "blog.html", "faq.html", "collaborate.html",
    "contact.html", "disclaimer.html",
}

# Map article filename -> correct category (from blog.html)
# This is the AUTHORITATIVE mapping
FILE_CATEGORY_MAP = {
    "article-30-years.html": "personal-story",
    "article-narrative-therapy.html": "narrative-therapy",
    "article-478-breathing.html": "self-care",
    "article-understanding-triggers.html": "tips",
    "article-prediction.html": "science",
    "meet-mi.html": "app-guide",
    "article-weekend-migraines.html": "science",
    "article-caffeine.html": "triggers",
    "article-postdrome.html": "understanding",
    "article-moh.html": "triggers",
    "article-not-my-migraine.html": "narrative-therapy",
    "the-exercise-paradox.html": "science",
    "article-invisible-pain.html": "personal-story",
    "article-aura.html": "understanding",
    "article-relationships.html": "personal-story",
    "the-second-brain.html": "science",
    "weather-migraine-myth.html": "science",
    "alcohol-migraine-24-hour-rule.html": "triggers",
    "article-migraine-vs-tension.html": "understanding",
    "screen-migraine-science.html": "triggers",
    "magnesium-riboflavin-coq10-migraine.html": "science",
    "the-goldilocks-problem-sleep-migraine.html": "triggers",
    "article-body-calendar.html": "science",
    "article-migraine-aphasia.html": "understanding",
    "article-osmophobia.html": "understanding",
    "article-emergency-kit.html": "tips",
    "article-migraine-friendly-lighting.html": "self-care",
    "article-pediatric-migraine.html": "understanding",
    "food-detective.html": "tips",
    "article-traveling-with-migraine.html": "tips",
    "article-conference-room-confession.html": "personal-story",
    "article-cgrp-revolution.html": "science",
    "article-botox-chronic-migraine.html": "science",
    "article-vagus-nerve-migraine.html": "self-care",
    "article-dehydration-equation.html": "triggers",
    "article-neck-connection.html": "understanding",
    "article-migraine-pregnancy.html": "understanding",
    "article-hyperexcitable-brain.html": "science",
}

# Category display names for tag text
CATEGORY_DISPLAY = {
    "personal-story": "Personal Story",
    "science": "Science",
    "app-guide": "App Guide",
    "self-care": "Self-Care",
    "narrative-therapy": "Narrative Therapy",
    "tips": "Tips",
    "triggers": "Triggers",
    "understanding": "Understanding",
}


def add_data_category(html, category):
    """Add or replace data-category on <body>."""
    html = re.sub(r'(<body[^>]*)\s+data-category="[^"]*"', r'\1', html)
    html = re.sub(r'<body([^>]*?)>', f'<body\\1 data-category="{category}">', html, count=1)
    return html


def add_css_link(html):
    """Add link to overlay CSS before </head> if not already present."""
    if CSS_FILE in html:
        return html
    link_tag = f'    <link rel="stylesheet" href="{CSS_FILE}">\n'
    html = html.replace('</head>', f'{link_tag}</head>')
    return html


def fix_tag_text(html, category):
    """Fix article-tag text to match blog category name."""
    display_name = CATEGORY_DISPLAY.get(category, "")
    if not display_name:
        return html
    # Replace whatever is inside .article-tag span
    html = re.sub(
        r'(<span\s+class="article-tag"[^>]*>)\s*[^<]+?\s*(</span>)',
        f'\\1{display_name}\\2',
        html,
        count=1
    )
    return html


def process_file(filepath, category):
    """Process a single file — SAFE, no style removal."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    html = original

    # 1. Add data-category to body
    html = add_data_category(html, category)

    # 2. Add CSS link (does NOT remove inline styles)
    html = add_css_link(html)

    # 3. Fix tag text
    html = fix_tag_text(html, category)

    if html == original:
        print(f"  ✓  No changes needed: {filepath.name} [{category}]")
        return False

    if DRY_RUN:
        print(f"  🔍 Would update: {filepath.name} [{category}]")
        return True

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✅ Updated: {filepath.name} [{category}]")
    return True


def main():
    print("=" * 60)
    print("  Migraine Companion — SAFE Article Color Updater v2")
    print("  Does NOT remove inline styles")
    print("=" * 60)

    if DRY_RUN:
        print("  MODE: DRY RUN (no files will be changed)\n")
    else:
        print("  MODE: LIVE (files will be updated)\n")

    css_path = SCRIPT_DIR / CSS_FILE
    if not css_path.exists():
        print(f"  ❌ ERROR: {CSS_FILE} not found!")
        sys.exit(1)

    updated = 0
    total = 0

    for filename, category in sorted(FILE_CATEGORY_MAP.items()):
        filepath = SCRIPT_DIR / filename
        if not filepath.exists():
            print(f"  ⚠️  File not found: {filename}")
            continue
        total += 1
        try:
            if process_file(filepath, category):
                updated += 1
        except Exception as e:
            print(f"  ❌ Error: {filename}: {e}")

    print(f"\n  {'Would update' if DRY_RUN else 'Updated'}: {updated}/{total} files")
    if DRY_RUN and updated > 0:
        print("  Run without --dry-run to apply changes.")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

---

**Теперь пошагово:**

**Шаг 1** — Сохрани оба файла на GitHub через браузер (чтобы не мучиться с токенами):

1. Иди на **https://github.com/migrainecompanionapp-lang/migrainecompanion**
2. Нажми **Add file → Create new file**
3. Имя: `article-category-colors.css`
4. Вставь содержимое первого файла
5. Нажми **Commit changes**
6. Повтори для `update-articles-v2.py`

**Шаг 2** — В терминале:
```
cd ~/Desktop/migrainecompanion && git pull
```

**Шаг 3** — Тестовый прогон:
```
python3 update-articles-v2.py --dry-run
