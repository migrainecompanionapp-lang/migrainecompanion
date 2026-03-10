#!/usr/bin/env python3
"""
Fix mobile hero category tag clipping in article HTML files.
Problem: On mobile, .article-hero has fixed height (400px) + overflow:hidden + 
         align-items:center, causing the category tag at top to be clipped.
Solution: On mobile, switch to height:auto + min-height + flex-end alignment 
          with padding, so content anchors to bottom and tag stays visible.
          Desktop remains unchanged.
"""

import os
import re
import sys
import shutil
from datetime import datetime

# --- Configuration ---
# Change this to your actual articles directory
ARTICLES_DIR = "/mnt/user-data/uploads"
# Set to True for dry run (no changes written)
DRY_RUN = False
# Backup original files
CREATE_BACKUP = True

def find_article_files(directory):
    """Find all HTML files that contain article-hero class."""
    article_files = []
    if not os.path.isdir(directory):
        print(f"Directory not found: {directory}")
        return article_files
    
    for fname in os.listdir(directory):
        if fname.endswith('.html'):
            filepath = os.path.join(directory, fname)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'article-hero' in content:
                    article_files.append(filepath)
            except Exception as e:
                print(f"  Skipping {fname}: {e}")
    
    return sorted(article_files)


def fix_mobile_hero(content, filepath):
    """
    Fix the mobile hero section. Strategy:
    
    1. Find the @media (max-width: 768px) block
    2. Replace .article-hero { height: 400px; } with the fix
    3. If no mobile hero rule exists, add one
    
    The fix: on mobile, use auto height with min-height and flex-end 
    alignment so the tag doesn't get clipped.
    """
    fname = os.path.basename(filepath)
    changes = []
    
    # Pattern: find .article-hero rule inside @media (max-width: 768px) block
    # We need to be careful to only modify the mobile media query
    
    # First, check if file has the standard mobile media query
    media_pattern = r'(@media\s*\(\s*max-width\s*:\s*768px\s*\)\s*\{)'
    media_match = re.search(media_pattern, content)
    
    if not media_match:
        print(f"  [{fname}] No mobile media query found — skipping")
        return content, False
    
    # Find the complete media query block
    media_start = media_match.start()
    
    # Now find the .article-hero rule within the media query
    # Look for .article-hero { height: 400px; } or similar
    # The media block content is between the opening { and closing }
    
    # Strategy: find ".article-hero" after the media query start
    # and replace its height rule
    
    # Pattern 1: .article-hero { height: 400px; } (common pattern)
    hero_in_media = re.search(
        r'(\.article-hero\s*\{\s*height\s*:\s*\d+px\s*;\s*\})',
        content[media_start:]
    )
    
    if hero_in_media:
        old_rule = hero_in_media.group(1)
        # New rule: auto height, min-height for safety, flex-end + padding
        new_rule = (
            '.article-hero { '
            'height: auto; '
            'min-height: 400px; '
            'align-items: flex-end; '
            'padding-bottom: 40px; '
            '}'
        )
        
        # Replace only within the media query section
        abs_start = media_start + hero_in_media.start()
        abs_end = media_start + hero_in_media.end()
        content = content[:abs_start] + new_rule + content[abs_end:]
        changes.append(f"Replaced '{old_rule}' → mobile hero fix")
    
    elif '.article-hero' in content[media_start:media_start+2000]:
        # There's a .article-hero rule but with different format
        # Try a more flexible pattern
        hero_flex = re.search(
            r'(\.article-hero\s*\{[^}]*\})',
            content[media_start:media_start+2000]
        )
        if hero_flex:
            old_rule = hero_flex.group(1)
            # Check if our fix is already applied
            if 'align-items: flex-end' in old_rule and 'height: auto' in old_rule:
                print(f"  [{fname}] Already fixed — skipping")
                return content, False
            
            new_rule = (
                '.article-hero { '
                'height: auto; '
                'min-height: 400px; '
                'align-items: flex-end; '
                'padding-bottom: 40px; '
                '}'
            )
            abs_start = media_start + hero_flex.start()
            abs_end = media_start + hero_flex.end()
            content = content[:abs_start] + new_rule + content[abs_end:]
            changes.append(f"Replaced complex hero rule → mobile hero fix")
    
    else:
        # No .article-hero in media query — need to add one
        # Insert right after the media query opening brace
        insert_pos = media_match.end()
        insert_rule = (
            '\n            .article-hero { '
            'height: auto; '
            'min-height: 400px; '
            'align-items: flex-end; '
            'padding-bottom: 40px; '
            '}'
        )
        content = content[:insert_pos] + insert_rule + content[insert_pos:]
        changes.append("Added mobile hero fix (no existing rule found)")
    
    if changes:
        for c in changes:
            print(f"  [{fname}] {c}")
        return content, True
    
    return content, False


def main():
    # Allow passing directory as argument
    articles_dir = sys.argv[1] if len(sys.argv) > 1 else ARTICLES_DIR
    
    print(f"{'='*60}")
    print(f"Mobile Hero Tag Fix Script")
    print(f"{'='*60}")
    print(f"Directory: {articles_dir}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"Backup: {'Yes' if CREATE_BACKUP else 'No'}")
    print()
    
    # Find article files
    files = find_article_files(articles_dir)
    print(f"Found {len(files)} article HTML files with .article-hero")
    print()
    
    fixed = 0
    skipped = 0
    errors = 0
    
    for filepath in files:
        fname = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original = f.read()
            
            modified, changed = fix_mobile_hero(original, filepath)
            
            if changed:
                if DRY_RUN:
                    print(f"  [{fname}] Would write changes (dry run)")
                else:
                    if CREATE_BACKUP:
                        backup = filepath + '.bak'
                        shutil.copy2(filepath, backup)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(modified)
                    print(f"  [{fname}] ✓ Fixed and saved")
                fixed += 1
            else:
                skipped += 1
                
        except Exception as e:
            print(f"  [{fname}] ERROR: {e}")
            errors += 1
    
    print()
    print(f"{'='*60}")
    print(f"Results: {fixed} fixed, {skipped} skipped, {errors} errors")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
