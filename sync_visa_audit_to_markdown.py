import csv,json,re
from pathlib import Path
csv_path=Path("docs/data/visa-audit.csv")
folder=Path("docs/.vitepress/content/destinations")
with csv_path.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
by_name={r["destination"].strip():r for r in rows if r.get("destination")}
updated=0
unmatched=[]
fields=("verification_status","visa_note","visa_checked_at","visa_source_url")
for path in folder.glob("*.md"):
    text=path.read_text(encoding="utf-8")
    m=re.search(r"^name: (.+)$",text,re.M)
    if not m: continue
    try: name=json.loads(m.group(1))
    except Exception: name=m.group(1).strip().strip('"')
    row=by_name.pop(str(name).strip(),None)
    if not row: continue
    for field in fields:
        value=row.get(field,"").strip()
        line=field+": "+json.dumps(value,ensure_ascii=False)
        pattern=r"^"+re.escape(field)+r":.*$"
        if re.search(pattern,text,re.M): text=re.sub(pattern,lambda _:line,text,flags=re.M)
        else: text=text.replace("\n---\n", "\n"+line+"\n---\n", 1)
    path.write_text(text,encoding="utf-8")
    updated+=1
unmatched=sorted(by_name)
print("Обновлено Markdown-файлов:",updated)
print("Не сопоставлено:",len(unmatched))
for name in unmatched: print("-",name)
