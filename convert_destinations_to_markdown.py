import json,re
from pathlib import Path
src=Path("docs/data/destinations.json")
out=Path("docs/.vitepress/content/destinations")
data=json.loads(src.read_text(encoding="utf-8"))
items=data.get("destinations",data) if isinstance(data,dict) else data
out.mkdir(parents=True,exist_ok=True)
created=0
for x in items:
    slug=re.sub(r"[^a-zA-Z0-9_-]+","-",str(x.get("id") or x.get("name") or "")).strip("-").lower()
    if not slug: continue
    f=out/(slug+".md")
    if f.exists(): continue
    front="\n".join(k+": "+json.dumps(v,ensure_ascii=False) for k,v in x.items())
    name=str(x.get("name") or "Направление")
    f.write_text("---\n"+front+"\n---\n\n## "+name+"\n\nДобавьте здесь описание направления.\n",encoding="utf-8")
    created+=1
print("Создано Markdown-файлов:",created)
print("Папка:",out)
