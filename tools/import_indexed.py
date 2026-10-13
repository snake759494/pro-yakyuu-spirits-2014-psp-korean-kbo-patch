from pathlib import Path
import json,sys,re
q=json.loads(Path(sys.argv[1]).read_text('utf8'));p=Path(sys.argv[3] if len(sys.argv)>3 else 'translation/new_ui.json');a=json.loads(p.read_text('utf8')) if p.exists() else {};n=0
for line in Path(sys.argv[2]).read_text('utf-8-sig').splitlines():
 if '|' not in line:continue
 i,k=line.split('|',1);j=q[int(i)];k=k.replace('\\n','\n').replace('\\r','\r').replace('\\t','\t')
 assert re.findall('<[^>]+>',j)==re.findall('<[^>]+>',k),(i,j,k)
 assert re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',j)==re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',k),(i,j,k)
 a[j]=k;n+=1
p.write_text(json.dumps(a,ensure_ascii=False,indent=2),'utf8');print('직접 번역',n)
