from pathlib import Path
import json,re,struct,collections
from inventory import ROOT,WORK,ISO
from elfrefs import references
import gamecodec
import script16
import loading_titles

def chunks(d):
 if d[:4]!=b'CHK ':return
 o=16
 while o+16<=len(d):
  name=d[o:o+8].rstrip(b'\0').decode('ascii');size,used=struct.unpack_from('<2I',d,o+8)
  if name=='CHUNKEND':break
  assert size>=16 and used<=size-16 and o+size<=len(d),(name,o,size,used)
  yield name,o+16,d[o+16:o+16+used-1]
  o+=size
pattern=re.compile(rb'(?:[\x09\x0a\x0d\x20-\x7e\xa1-\xdf]|[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]){2,}\x00')
def strings(d,start=0):
 for m in pattern.finditer(d,start):
  if m.start() and d[m.start()-1]!=0:continue
  try:s=gamecodec.decode(m.group()[:-1])
  except UnicodeDecodeError:continue
  if not re.search('[ぁ-ヿ一-鿿]',s):continue
  if sum(c.isprintable() or c=='\u3000' for c in s)<len(s)*.8:continue
  yield m.start(),s

def main():
 rows=[]; inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'));types=collections.Counter()
 for p in (WORK/'iso').rglob('*'):
  if p.suffix!='.elf' and p.name!='BOOT.BIN':continue
  d=p.read_bytes();shoff=struct.unpack_from('<I',d,32)[0];ss,sn=struct.unpack_from('<HH',d,46)
  regions=[]
  for i in range(sn):
   _,typ,flags,addr,off,size=struct.unpack_from('<6I',d,shoff+i*ss)
   if typ==1 and not flags&4:regions.append((off,size))
  found={}
  for off,size in regions:
   for pos,s in strings(d[off:off+size]):found[off+pos]=s
  for pos in references(d):
   end=d.find(b'\0',pos,min(pos+20000,len(d)))
   if end<0:continue
   try:s=gamecodec.decode(d[pos:end])
   except UnicodeDecodeError:continue
   if len(s)<2 or not re.search('[ぁ-ヿ一-鿿]',s) or any(not c.isprintable() and c not in '\r\n\t\u3000' for c in s):continue
   found[pos]=s
  # PSP 오버레이는 문자열 풀도 실행 속성 섹션에 포함한다.
  # NUL 경계의 완전한 CP932 문자열을 추가 수집해 간접 참조를 놓치지 않는다.
  for pos,s in strings(d):
   if len(re.findall('[ぁ-ヿ一-鿿]',s))<2 or re.search('[\ue000-\uf8ffｦ-ﾟ]',s):continue
   if any(start<=pos<start+len(gamecodec.encode(text)) for start,text in found.items()):continue
   found[pos]=s
  for pos,s in sorted(found.items()):rows.append(dict(file=p.name,offset=pos,ja=s))
 with ISO.open('rb') as f:
  for e in inv['fbd']:
   f.seek(e['offset']);d=f.read(e['size'])
   if d[:4]!=b'CHK ':continue
   for name,off,b in chunks(d):
    if name=='MES' and e['name']=='GLOADM.CHK':
     rows.extend(dict(file=e['name'],chunk=name,offset=off+pos,ja=s,loading_title=True) for pos,s in loading_titles.extract(b))
    if name=='BIN00' and e['name'] in ('SEVENT1.CHK','MVP_SEVENT1.CHK'):
     rows.extend(dict(file=e['name'],chunk=name,offset=off+pos,ja=s,encoding='script16') for pos,s in script16.extract(b))
    types[b[:8].hex()]+=1
    if b.startswith((b'PS2',b'PSP',b'MOT',b'GIM')):continue
    if b.startswith(b'TXCPACK ') or name in ('DATA0','TEXT','MES','NAME','INTR','HELP'):
     for pos,s in strings(b):rows.append(dict(file=e['name'],chunk=name,offset=off+pos,ja=s))
 # PSP 시스템 대화창은 게임 내부 CP932와 별도로 UTF-8을 사용한다.
 d=(WORK/'iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();extra=[]
 for m in re.finditer(rb'[^\x00]{4,}\x00',d):
  if not (0x284700<=m.start()<0x285200 or 0x2a7600<=m.start()<0x2ab820):continue
  try:s=m.group()[:-1].decode('utf8')
  except UnicodeDecodeError:continue
  if re.search('[ぁ-ヿ一-鿿]',s) and all(c.isprintable() or c in '\r\n\t\u3000' for c in s):extra.append(dict(file='BOOT.BIN',offset=m.start(),ja=s,encoding='utf-8'))
 for r in extra:rows=[x for x in rows if x['file']!='BOOT.BIN' or not r['offset']<=x['offset']<r['offset']+len(r['ja'].encode('utf8'))+1]
 rows+=extra
 additional=ROOT/'translation/extra_locations.json'
 if additional.exists():
  extra=json.loads(additional.read_text('utf8'));keys={(r['file'],r['offset']) for r in extra};rows=[r for r in rows if (r['file'],r['offset']) not in keys]+extra
 # UI 색상/좌표 float 두 개의 마지막 6바이트가 문자열로 잡힌 경우.
 # 0.75f와 0.2f의 고정 전치 바이트만 제거하고 실제 문자열 시작을 사용한다.
 clean=[];seen=set()
 for r in rows:
  if r['ja'] in ('@利き腕','@強化中'):
   r=dict(r,offset=r['offset']+1,ja=r['ja'][1:])
  if r['ja']=='@?ＦＡ選手補強、トレード補強、新外国人補強でチームの戦力補強をします。':
   r=dict(r,offset=r['offset']+2,ja=r['ja'][2:])
  if r.get('encoding','cp932')=='cp932' and r['ja'].encode('cp932').startswith(bytes.fromhex('403fcdcc4c3e')):
   r=dict(r,offset=r['offset']+6,ja=r['ja'][6:])
  key=(r['file'],r['offset'])
  if key not in seen:clean.append(r);seen.add(key)
 ranges=[(r['offset'],r['offset']+len(gamecodec.encode(r['ja']))+1) for r in clean if r.get('loading_title')]
 rows=[r for r in clean if r.get('loading_title') or r['file']!='GLOADM.CHK' or not any(r['offset']<hi and r['offset']+len(gamecodec.encode(r['ja']))+1>lo for lo,hi in ranges)]
 (WORK/'strings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 ref={}
 refdir=Path(r'C:\Users\Jay\Downloads\ps2\프로야구스피리츠6\translation')
 for p in refdir.glob('*.json'):
  data=json.loads(p.read_text(encoding='utf-8'))
  if isinstance(data,dict):ref.update({k:v for k,v in data.items() if isinstance(v,str)})
 norm=lambda s:re.sub(r'\s+','',s)
 normalized={norm(k):(k,v) for k,v in ref.items()}
 matched={r['ja']:ref[r['ja']] for r in rows if r['ja'] in ref}
 for r in rows:
  j=r['ja']
  if j not in matched and norm(j) in normalized:
   original,ko=normalized[norm(j)]
   if re.findall('<[^>]*>',j)==re.findall('<[^>]*>',original):matched[j]=ko
 old=ROOT/'translation/reference_matches.json'
 if old.exists():matched.update(json.loads(old.read_text(encoding='utf8')))
 (ROOT/'translation/reference_matches.json').write_text(json.dumps(matched,ensure_ascii=False,indent=2),encoding='utf-8')
 missing=sorted(set(r['ja'] for r in rows)-set(matched))
 (WORK/'untranslated.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Locations',len(rows),'Unique',len(set(r['ja'] for r in rows)),'Reference matches',len(matched),'Untranslated',len(missing));print(collections.Counter(r['file'] for r in rows).most_common(25));print('chunk types',types.most_common(20))
if __name__=='__main__':main()
