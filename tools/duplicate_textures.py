"""원본 인덱스 텍스처가 동일한 사본에 번역을 복제하고 팔레트 연결을 보존한다."""
import json,hashlib,collections
from inventory import ROOT,WORK,ISO
from analyze import chunks
from sprites import bindings

def main():
 p=ROOT/'translation/textures.json';specs=json.loads(p.read_text('utf8'));group=collections.defaultdict(list)
 for s in specs:group[(s['file'],s['chunk'])].append(s)
 inv=json.loads((WORK/'inventory.json').read_text('utf8'));catalog=collections.defaultdict(list);palettes={}
 with ISO.open('rb') as f:
  for e in inv['fbd']:
   if not e['name'].endswith('.CHK'):continue
   f.seek(e['offset']);data=f.read(e['size']);cs={n:b for n,o,b in chunks(data)};ls=bindings(data)
   for n,b in cs.items():
    if b[:4]!=b'PTXI' or b[12] not in (4,5):continue
    pn=ls.get(n,[n.replace('TTEX','TPAL').replace('TEX','PAL')])[0]
    if pn in cs:palettes[(e['name'],n)]=(e['name'],pn)
    k=hashlib.sha256(b).hexdigest();catalog[k].append((e['name'],n))
 added=[];conflicts=[]
 for items in catalog.values():
  sources=[key for key in items if key in group]
  if not sources:continue
  source=max(sources,key=lambda k:len(group[k]));defs=group[source]
  for dest in items:
   if dest in group:continue
   for s in defs:
    new=dict(s,file=dest[0],chunk=dest[1])
    if dest not in palettes:
     if 'palette_file' in s:new.update(palette_file=s['palette_file'],palette_chunk=s['palette_chunk'])
     else:new.update(palette_file=palettes[source][0],palette_chunk=palettes[source][1])
    specs.append(new)
   added.append(dict(source=source,destination=dest,labels=len(defs)))
 p.write_text(json.dumps(specs,ensure_ascii=False,indent=2),'utf8')
 report=ROOT/'build/duplicate_textures.json';previous=json.loads(report.read_text('utf8')) if report.exists() else [];report.write_text(json.dumps(previous+added,ensure_ascii=False,indent=2),'utf8')
 print('사본 텍스처',len(added),'추가 문구',sum(r['labels'] for r in added))
 for r in added:print(r)
if __name__=='__main__':main()
