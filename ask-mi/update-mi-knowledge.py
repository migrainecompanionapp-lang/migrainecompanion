#!/usr/bin/env python3
"""
MI KNOWLEDGE BASE UPDATER
==========================
Run this script after adding a new article to the blog.
It helps you create the knowledge base entry and updates all files.

Usage:
    python3 update-mi-knowledge.py article-filename.html

What it does:
1. Reads the HTML article
2. Extracts title, category, key text
3. Asks YOU to fill in key_facts, connections, etc. (or auto-suggests)
4. Adds entry to mi-knowledge-base.json
5. Regenerates mi-knowledge-compact.txt
6. Shows you what to paste into Cloudflare Worker

You still need to:
- Re-deploy the Cloudflare Worker with updated knowledge base
"""

import json
import re
import sys
import os
from html.parser import HTMLParser

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tag = None
        self.title = ''
        self.category = ''
        self.description = ''
        self.key_takeaways = []
        self.in_key_takeaways = False
        self.all_text = []
        self.current_text = ''
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'h1':
            self.in_tag = 'h1'
        elif tag == 'meta' and attrs_dict.get('name') == 'description':
            self.description = attrs_dict.get('content', '')
        elif 'class' in attrs_dict:
            cls = attrs_dict['class']
            if 'article-tag' in cls:
                self.in_tag = 'tag'
                
    def handle_endtag(self, tag):
        if tag == 'h1' and self.in_tag == 'h1':
            self.in_tag = None
        elif self.in_tag == 'tag':
            self.in_tag = None
            
    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self.in_tag == 'h1' and not self.title:
            self.title = text
        elif self.in_tag == 'tag' and not self.category:
            self.category = text
        
        # Collect key takeaways
        if 'Key Takeaway' in text:
            self.in_key_takeaways = True
        elif self.in_key_takeaways and text.startswith('•'):
            self.key_takeaways.append(text.lstrip('• ').strip())
            if len(self.key_takeaways) >= 6:
                self.in_key_takeaways = False
                
        self.all_text.append(text)


def extract_article_info(html_path):
    """Extract basic info from article HTML."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = ArticleParser()
    parser.feed(content)
    
    # Get filename without extension for URL
    filename = os.path.basename(html_path)
    slug = os.path.splitext(filename)[0]
    
    return {
        'filename': filename,
        'slug': slug,
        'title': parser.title,
        'category': parser.category,
        'description': parser.description,
        'key_takeaways': parser.key_takeaways[:6],
        'full_text': ' '.join(parser.all_text)[:500]  # First 500 chars for context
    }


def create_knowledge_entry(info):
    """Create a knowledge base entry from extracted info."""
    
    print("\n" + "="*60)
    print(f"NEW ARTICLE: {info['title']}")
    print(f"Category: {info['category']}")
    print(f"File: {info['filename']}")
    print("="*60)
    
    # Auto-fill what we can
    entry = {
        'id': info['slug'],
        'title': info['title'],
        'category': info['category'],
        'url': info['filename'],
    }
    
    # Summary
    if info['description']:
        print(f"\nMeta description found: {info['description'][:100]}...")
        summary = input(f"\nSummary (press Enter to use meta description, or type new):\n> ").strip()
        if not summary:
            summary = info['description']
    else:
        summary = input("\nSummary (2-3 sentences about the article):\n> ").strip()
    entry['summary'] = summary
    
    # Key facts
    if info['key_takeaways']:
        print(f"\nFound {len(info['key_takeaways'])} key takeaways:")
        for i, kt in enumerate(info['key_takeaways']):
            print(f"  {i+1}. {kt[:80]}...")
        use_auto = input("\nUse these as key_facts? (y/n): ").strip().lower()
        if use_auto == 'y':
            entry['key_facts'] = info['key_takeaways']
        else:
            entry['key_facts'] = []
            print("Enter key facts (one per line, empty line to finish):")
            while True:
                fact = input("> ").strip()
                if not fact:
                    break
                entry['key_facts'].append(fact)
    else:
        entry['key_facts'] = []
        print("\nEnter key facts (one per line, empty line to finish):")
        while True:
            fact = input("> ").strip()
            if not fact:
                break
            entry['key_facts'].append(fact)
    
    # Connections
    print("\nEnter connected article IDs (comma-separated):")
    print("  Examples: caffeine, morning-migraine, tmj-bruxism-migraine, anxious-brain")
    connects = input("> ").strip()
    entry['connects_to'] = [c.strip() for c in connects.split(',') if c.strip()]
    
    # Topics
    print("\nEnter topics/keywords (comma-separated):")
    topics = input("> ").strip()
    entry['topics'] = [t.strip() for t in topics.split(',') if t.strip()]
    
    # Solutions
    print("\nEnter solutions discussed (comma-separated):")
    solutions = input("> ").strip()
    entry['solutions'] = [s.strip() for s in solutions.split(',') if s.strip()]
    
    return entry


def update_json(entry, json_path='mi-knowledge-base.json'):
    """Add entry to the JSON knowledge base."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check for duplicate
    existing_ids = [a['id'] for a in data['articles']]
    if entry['id'] in existing_ids:
        print(f"\n⚠️  Article '{entry['id']}' already exists in the knowledge base!")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite == 'y':
            data['articles'] = [a for a in data['articles'] if a['id'] != entry['id']]
        else:
            return False
    
    data['articles'].append(entry)
    data['total_articles'] = len(data['articles'])
    data['last_updated'] = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Added to {json_path} (now {data['total_articles']} articles)")
    return True


def regenerate_compact(json_path='mi-knowledge-base.json', compact_path='mi-knowledge-compact.txt'):
    """Regenerate the compact text file from JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lines = []
    lines.append(f"MIGRAINE COMPANION KNOWLEDGE BASE — {data['total_articles']} articles, {data.get('total_citations', '600+')} peer-reviewed citations")
    lines.append(f"Website: https://mi-companion.com | Author: Rustam Iuldashov (30 years lived experience)")
    lines.append("")
    
    for a in data['articles']:
        lines.append("---")
        lines.append(f"ARTICLE: {a['title']}")
        lines.append(f"Category: {a['category']} | URL: https://mi-companion.com/{a['url']}")
        lines.append(f"Summary: {a['summary']}")
        lines.append(f"Key facts: {' | '.join(a['key_facts'])}")
        lines.append(f"Connects to: {', '.join(a['connects_to'])}")
        lines.append(f"Topics: {', '.join(a['topics'])}")
        lines.append(f"Solutions: {', '.join(a['solutions'])}")
        lines.append("")
    
    text = '\n'.join(lines)
    
    with open(compact_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    tokens = len(text) // 4
    print(f"✓ Regenerated {compact_path} ({data['total_articles']} articles, ~{tokens:,} tokens)")
    return text


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 update-mi-knowledge.py <article-filename.html>")
        print("")
        print("Or run without arguments to add manually:")
        
        # Manual mode
        print("\n--- MANUAL ENTRY MODE ---")
        entry = {
            'id': input("Article ID (slug, e.g. 'my-new-article'): ").strip(),
            'title': input("Title: ").strip(),
            'category': input("Category (Science/Tips/Triggers/Understanding/Self-Care/Personal Story/Narrative Therapy/App Guide): ").strip(),
            'url': input("Filename (e.g. 'my-new-article.html'): ").strip(),
            'summary': input("Summary (2-3 sentences): ").strip(),
        }
        
        entry['key_facts'] = []
        print("Key facts (one per line, empty to finish):")
        while True:
            f = input("> ").strip()
            if not f: break
            entry['key_facts'].append(f)
        
        connects = input("Connected article IDs (comma-separated): ").strip()
        entry['connects_to'] = [c.strip() for c in connects.split(',') if c.strip()]
        
        topics = input("Topics (comma-separated): ").strip()
        entry['topics'] = [t.strip() for t in topics.split(',') if t.strip()]
        
        solutions = input("Solutions (comma-separated): ").strip()
        entry['solutions'] = [s.strip() for s in solutions.split(',') if s.strip()]
        
    else:
        html_path = sys.argv[1]
        if not os.path.exists(html_path):
            print(f"Error: File not found: {html_path}")
            sys.exit(1)
        
        info = extract_article_info(html_path)
        entry = create_knowledge_entry(info)
    
    # Update files
    print("\n--- UPDATING FILES ---")
    
    if update_json(entry):
        compact_text = regenerate_compact()
        
        print("\n" + "="*60)
        print("✅ DONE! Knowledge base updated.")
        print("="*60)
        print("")
        print("NEXT STEPS:")
        print("1. Open your Cloudflare Worker")
        print("2. Replace the content between <articles> and </articles>")
        print("   with the new contents of mi-knowledge-compact.txt")
        print("3. Click Deploy")
        print("")
        print(f"Mi now knows about: \"{entry['title']}\"")
        print(f"Total articles: {json.load(open('mi-knowledge-base.json'))['total_articles']}")


if __name__ == '__main__':
    main()
