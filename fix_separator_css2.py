import os
import re

NEW_CSS = """.separator { text-align: center; margin: 60px 0; position: relative; height: 20px; display: flex; align-items: center; justify-content: center; }
        .separator::before { content: ''; position: absolute; left: 15%; right: 15%; height: 1px; background: linear-gradient(90deg, transparent 0%, rgba(139,122,168, 0.25) 30%, rgba(139,122,168, 0.40) 50%, rgba(139,122,168, 0.25) 70%, transparent 100%); }
        .separator::after { content: '\\25C6'; position: relative; z-index: 1; color: rgba(139,122,168, 0.35); font-size: 0.55rem; background: var(--bg); padding: 0 16px; }"""

# Ищем ЛЮБОЙ вариант .separator { ... } который не содержит ::before
OLD_PATTERN = re.compile(r'\.separator\s*\{[^}]*?\}(?!\s*\n\s*\.separator::)', re.DOTALL)

fixed = []

for filename in os.listdir('.'):
    if not filename.endswith('.html'):
        continue

    with open(filename, 'r', encoding='utf-8') as f:
        original = f.read()

    # Проверяем есть ли уже правильный CSS
    if '.separator::before' in original:
        continue

    # Заменяем первое вхождение .separator { }
    if '.separator' not in original:
        continue

    content = OLD_PATTERN.sub(NEW_CSS, original, count=1)

    if content != original:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed.append(filename)

print(f'Fixed {len(fixed)} files:')
for f in fixed:
    print(f'  → {f}')
