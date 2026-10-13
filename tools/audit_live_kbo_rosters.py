"""PPSSPP 새 페넌트 편성의 실제 24바이트 선수/8바이트 스태프 연결을 감사한다.

읽기 전용. 상태저장 또는 메모리 패치를 수행하지 않는다.
"""
import json,struct,hashlib,sys
from pathlib import Path
from ppsspp_rpc import Debugger,readmem
from kbo_team_layout import ROOT,layouts
BASE=0x08800000
d=Debugger()
try:
 status=d.call('cpu.status');d.call('cpu.stepping')
 ram=readmem(d,BASE,0x1800000)
finally:
 if not status.get('stepping'):d.call('cpu.resume')
 d.close()
cm={r['hangul']:bytes.fromhex(r['code']) for r in json.loads((ROOT/'build/charmap.json').read_text('utf8')) if 'hangul' in r}
def enc(s):return b''.join(cm[c] if c in cm else c.encode('cp932') for c in s)
def record(ptr):
 assert BASE<=ptr<BASE+len(ram)-192,hex(ptr)
 return ram[ptr-BASE:ptr-BASE+192]
teams=[]
# 기본 편성과 새 페넌트 편성을 모두 검사한다. 옛 복사본을 무시하지 않는다.
roots=[];at=0;lg=layouts()['LG']
needle=struct.pack('<IIH',0,len(lg['players']),lg['active'][0]['index'])
while (at:=ram.find(needle,at))>=0:
 if all(at+t['team_id']*0x28e8+8<len(ram) and struct.unpack_from('<II',ram,at+t['team_id']*0x28e8)==(t['team_id'],len(t['players'])) for t in layouts().values()):roots.append(at)
 at+=1
assert roots,('KBO 10구단 편성 루트 없음',roots)
for code,t in layouts().items():
 if len(sys.argv)>1 and code not in sys.argv[1:]:continue
 n=len(t['players']);needle=struct.pack('<IIH',t['team_id'],n,t['active'][0]['index'])
 at=0;found=[];expected={p['index']:p for p in t['players']}
 while (at:=ram.find(needle,at))>=0:
  if at not in [root+t['team_id']*0x28e8 for root in roots]:at+=1;continue
  ids=[struct.unpack_from('<H',ram,at+8+i*24)[0] for i in range(n)]
  if set(ids)==set(expected) and len(ids)==len(set(ids)):found.append(at)
  at+=1
 assert len(found)==len(roots),(code,'일부 편성 복사본에서 명단 불일치',found,roots)
 results=[]
 for at in found:
  players=[]
  for i in range(n):
   entry=at+8+i*24;idx=struct.unpack_from('<H',ram,entry)[0];p=expected[idx]
   ptr=struct.unpack_from('<I',ram,entry+16)[0];r=record(ptr)
   name=r[110:152].split(b'\0')[0];assert name==enc(p['name']),(code,p['name'],name.hex())
   primary=(r[168]&0x78)>>3
   cached_primary=(ram[entry+4]&0x78)>>3
   assert cached_primary==primary,(code,p['name'],'저장 편성 캐시 포지션',cached_primary,primary)
   assert primary in {'P':{0},'C':{1},'IF':{2,3,4,5},'OF':{6,7,8}}[p['category']],(code,p['name'],primary)
   flags=struct.unpack_from('<H',ram,entry+10)[0]
   selector=(flags>>11)&7
   assert selector<6,(code,p['name'],'등록명 선택자 범위 오류')
   from kbo_ratings_review import manifest
   from player_fields import get,POSITIONS,PITCHES
   rating=next(q for q in manifest()['teams'][code]['players'] if q['index']==idx)
   for key,value in rating['abilities'].items():assert get(r,key)==value,(code,p['name'],key,get(r,key),value)
   for key in POSITIONS:assert get(r,key)==rating['fielding'].get(key,0),(code,p['name'],key)
   assert get(r,'velocity_raw')+80==rating['velocity']
   kinds=[struct.unpack_from('<H',r,58+j*2)[0]&127 for j in range(12)]
   assert sorted(k for k in kinds if k!=37)==sorted(PITCHES[q['name']][0] for q in rating['pitches']),(code,p['name'],'구종')
   players.append(dict(abilities={k:get(r,k) for k in rating['abilities']},pitch_kinds=kinds,index=idx,name=p['name'],category=p['category'],primary=primary,cached_primary=cached_primary,registration_selector=selector,active=(flags>>14)==1,record_address=hex(ptr)))
  staff=[]
  for i,p in enumerate(t['coaches']):
   idx=struct.unpack_from('<H',ram,at+0x698+i*8)[0]
   ptr=struct.unpack_from('<I',ram,at+0x69c+i*8)[0]
   assert idx==p['index'],(code,'코치 순서',idx,p['index'])
   assert record(ptr)[110:152].split(b'\0')[0]==enc(p['name']),(code,'코치 이름',p['name'])
   assert idx not in expected,(code,'선수와 스태프 중복')
   staff.append(dict(index=idx,name=p['name'],role=p.get('role')))
  active=[p for p in players if p['active']]
  assert len(active)==len(t['active']) and sum(p['category']=='P' for p in active)==len(t['pitchers']),(code,'1군 분류',len(active),[(p['name'],p['category']) for p in active])
  assert {p['index'] for p in active}=={p['index'] for p in t['active']},(code,'1군 인원은 맞으나 선수 연결이 다름')
  results.append(dict(team_address=hex(BASE+at),players=players,staff=staff))
 teams.append(dict(code=code,copies=results))
iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
with iso.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report=dict(iso_sha256=digest,method='기본/새 페넌트 전체 팀 편성 RAM: 선수/스태프 포인터, 이름, 본체·캐시 주 포지션, 등록명 선택자, 1군 상태 전수 대조',roots=[hex(BASE+r) for r in roots],memory_write=False,teams=teams,players=sum(len(layouts()[t['code']]['players']) for t in teams),staff=len(teams)*5,passed=True)
path=ROOT/('build/identity_audit/live_'+('_'.join(sys.argv[1:]) or 'all')+'.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({k:v for k,v in report.items() if k!='teams'},ensure_ascii=False))
