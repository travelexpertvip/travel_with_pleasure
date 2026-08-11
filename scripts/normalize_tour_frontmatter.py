from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOURS = ROOT / 'docs/.vitepress/content/tours'

def quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

def normalize(text: str) -> str:
    if not text.startswith('---\n'):
        return text
    parts = text.split('---', 2)
    if len(parts) < 3:
        return text
    frontmatter, body = parts[1], parts[2]
    frontmatter = re.sub(r'(?m)^(source_channel:)\s*([^\n"].*)$', lambda m: f'{m.group(1)} {quote(m.group(2).strip())}', frontmatter)
    frontmatter = re.sub(r'(?m)^(tour_source_url:)\s*([^\n"].*)$', lambda m: f'{m.group(1)} {quote(m.group(2).strip())}', frontmatter)
    return '---' + frontmatter + '---' + body

changed = 0
for path in TOURS.glob('*.md'):
    original = path.read_text(encoding='utf-8')
    updated = normalize(original)
    if updated != original:
        path.write_text(updated, encoding='utf-8')
        changed += 1
print(f'Normalized {changed} tour files')
