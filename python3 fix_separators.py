import os

fixed = []

for filename in os.listdir('.'):
    if not filename.endswith('.html'):
        continue
    
    with open(filename, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original.replace(
        '<div class="separator">* * *</div>',
        '<div class="separator"></div>'
    )
    
    if content != original:
        with open(filename + '.bak', 'w', encoding='utf-8') as f:
            f.write(original)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed.append(filename)

print(f'Fixed {len(fixed)} files:')
for f in fixed:
    print(f'  → {f}')
