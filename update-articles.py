#!/usr/bin/env python3
"""
Batch-update article HTML files to use shared article-base.css
and correct category colors.

Usage: python3 update-articles.py
       python3 update-articles.py --dry-run   (preview without changes)

Place in the same directory as your article HTML files.
"""

import os
import re
import sys
from pathlib import Path

# === CONFIGURATION ===
SCRIPT_DIR = Path(__file__).parent
CSS_FILE = "article-base.css"

# Map tag text -> data-category value
CATEGORY_MAP = {
    "personal story": "personal-story",
    "science": "science",
    "app guide": "app-guide",
    "self-care": "self-care",
    "self care": "self-care",
    "narrative therapy": "narrative-therapy",
    "tips": "tips",
    "triggers": "triggers",
    "understanding": "understanding",
}

# Article files to process (auto-detect or list manually)
# Files that are NOT articles (skip these)
SKIP_FILES = {
    "index.html", "blog.html", "faq.html", "collaborate.html",
    "contact.html", "disclaimer.html", "meet-mi.html",
}

DRY_RUN = "--dry-run" in sys.argv


def detect_category(html):
    """Detect category from .article-tag content."""
    match = re.search(
        r'class="article-tag"[^>]*>\s*([^<]+?)\s*<',
        html, re.IGNORECASE
    )
    if match:
        tag_text = match.group(1).strip().lower()
        # Remove emoji if present
        tag_text = re.sub(r'[^\w\s-]', '', tag_text).strip()
        for key, value in CATEGORY_MAP.items():
            if key in tag_text:
                return value
    return None


def add_data_category(html, category):
    """Add data-category to <body> tag."""
    # Remove existing data-category
    html = re.sub(r'(<body[^>]*)\s+data-category="[^"]*"', r'\1', html)
    # Add new one
    html = re.sub(r'<body([^>]*?)>', f'<body\\1 data-category="{category}">', html, count=1)
    return html


def replace_inline_styles(html):
    """Remove the inline <style> block and add link to shared CSS."""
    css_link = f'    <link rel="stylesheet" href="{CSS_FILE}">\n'
    
    # Check if already linked
    if CSS_FILE in html:
        # Already has the link, just remove inline styles
        html = re.sub(
            r'\s*<style>.*?</style>\s*',
            '\n',
            html,
            flags=re.DOTALL
        )
        return html
    
    # Remove inline <style>...</style>
    html = re.sub(
        r'\s*<style>.*?</style>\s*',
        f'\n{css_link}',
        html,
        count=1,
        flags=re.DOTALL
    )
    return html


def fix_inline_style_colors(html):
    """Fix any remaining inline style colors for known patterns."""
    # Fix article-meta div with inline styles (some articles have this)
    # These should use classes, not inline styles
    
    # Fix medical disclaimer box inline styles
    html = re.sub(
        r'<div id="medical-disclaimer" style="[^"]*">',
        '<div id="medical-disclaimer" class="medical-disclaimer-box">',
        html
    )
    
    # Fix author transparency inline styles
    html = re.sub(
        r'<p style="margin-top:8px;font-size:0.8rem;color:var\(--text-dark\);">\s*<em>Transparency',
        '<p class="author-transparency"><em>Transparency',
        html
    )
    
    # Fix author contact inline styles
    html = re.sub(
        r'<p style="margin-top:8px;font-size:0.8rem;color:var\(--text-dark\);">.*?Contact:',
        '<p class="author-contact">📧 Contact:',
        html
    )
    
    return html


def ensure_font_links(html):
    """Make sure Google Fonts links are present."""
    fonts_needed = [
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800",
        "Cormorant+Garamond"
    ]
    
    has_inter = "Inter" in html and "googleapis" in html
    has_cormorant = "Cormorant" in html and "googleapis" in html
    
    if not has_inter or not has_cormorant:
        font_link = '    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">\n'
        # Insert before </head>
        html = html.replace('</head>', f'{font_link}</head>')
    
    return html


def process_file(filepath):
    """Process a single article HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    html = original
    
    # 1. Detect category
    category = detect_category(html)
    if not category:
        print(f"  ⚠️  Could not detect category: {filepath.name}")
        return False
    
    # 2. Add data-category to body
    html = add_data_category(html, category)
    
    # 3. Replace inline styles with shared CSS link
    html = replace_inline_styles(html)
    
    # 4. Fix inline style colors
    html = fix_inline_style_colors(html)
    
    # 5. Ensure font links
    html = ensure_font_links(html)
    
    # Check if anything changed
    if html == original:
        print(f"  ✓  No changes needed: {filepath.name} [{category}]")
        return False
    
    if DRY_RUN:
        print(f"  🔍 Would update: {filepath.name} [{category}]")
        return True
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"  ✅ Updated: {filepath.name} [{category}]")
    return True


def find_article_files():
    """Find all article HTML files."""
    articles = []
    for f in SCRIPT_DIR.glob("*.html"):
        if f.name in SKIP_FILES:
            continue
        # Check if it looks like an article (has article-tag or article-hero)
        content = f.read_text(encoding='utf-8', errors='ignore')
        if 'article-tag' in content or 'article-hero' in content:
            articles.append(f)
    return sorted(articles)


def main():
    print("=" * 60)
    print("  Migraine Companion — Article Style Updater")
    print("=" * 60)
    
    if DRY_RUN:
        print("  MODE: DRY RUN (no files will be changed)\n")
    else:
        print("  MODE: LIVE (files will be updated)\n")
    
    # Check CSS file exists
    css_path = SCRIPT_DIR / CSS_FILE
    if not css_path.exists():
        print(f"  ❌ ERROR: {CSS_FILE} not found in {SCRIPT_DIR}")
        print(f"     Please create {CSS_FILE} first.")
        sys.exit(1)
    
    # Find articles
    articles = find_article_files()
    print(f"  Found {len(articles)} article files.\n")
    
    if not articles:
        print("  No article files found. Make sure you're running")
        print("  this script in the same directory as your HTML files.")
        sys.exit(1)
    
    updated = 0
    for filepath in articles:
        try:
            if process_file(filepath):
                updated += 1
        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}")
    
    print(f"\n  {'Would update' if DRY_RUN else 'Updated'}: {updated}/{len(articles)} files")
    
    if DRY_RUN and updated > 0:
        print("\n  Run without --dry-run to apply changes.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
