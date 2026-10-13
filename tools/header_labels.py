from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1];p=r/'translation/new_ui.json';direct=json.loads(p.read_text('utf8'));ui=json.loads((r/'translation/reference_matches.json').read_text('utf8'))
for l in (r/'translation/new_ui.txt').read_text('utf-8-sig').splitlines():
 if '|' in l:j,k=l.split('|',1);ui[j]=k
ui.update(direct);n=0
for row in json.loads((r/'work/strings.json').read_text('utf8')):
 j=row['ja']
 if '<RIGHT>' not in j or j in ui:continue
 parts=re.split('(<[^>]+>)',j)
 if any(s and not s.startswith('<') and s not in ui for s in parts):continue
 direct[j]=''.join(s if not s or s.startswith('<') else ui[s] for s in parts);n+=1
p.write_text(json.dumps(direct,ensure_ascii=False,indent=2),'utf8');print('조작 안내 조합',n)
