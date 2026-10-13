from pathlib import Path
import json,sys,re
q=Path(sys.argv[1]); a=json.loads(q.read_text('utf8')); b=Path(sys.argv[2]).read_text('utf-8-sig').splitlines();assert len(a)==len(b),(len(a),len(b))
p=Path('translation/new_ui.json');ui=json.loads(p.read_text('utf8'))
for j,k in zip(a,b):
 assert re.findall(r'<[^>]+>',j)==re.findall(r'<[^>]+>',k),(j,k)
 ui[j]=k
p.write_text(json.dumps(ui,ensure_ascii=False,indent=2),'utf8');print('직접 번역',len(b))
