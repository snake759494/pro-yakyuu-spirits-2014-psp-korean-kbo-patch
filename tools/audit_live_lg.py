"""PPSSPP 새 페넌트 편성의 실제 24바이트 선수/8바이트 스태프 연결을 감사한다.

읽기 전용. 상태저장 또는 메모리 패치를 수행하지 않는다.
"""
import json,struct,hashlib
from pathlib import Path
from ppsspp_rpc import Debugger,readmem
from kbo_team_layout import ROOT,layouts
from player_fields import get,jersey_code
from kbo_rosters import specs
details={p['index']:p for p in specs()['LG']['records']}
def audit_details(idx,r):
 p=details[idx]
 assert r[92:104].split(b'\0')[0].decode('ascii')==p['back_name'],(p['name'],'등 이름')
 assert get(r,'height')==p['height'],(p['name'],'키')
 assert get(r,'jersey')==jersey_code(p['number']),(p['name'],'등번호')
 assert struct.unpack_from('<I',r,156)[0]>>27==p['body_type'],(p['name'],'체형')
 assert (struct.unpack_from('<I',r,152)[0]>>23)&7==p['skin_type'],(p['name'],'피부톤')
 for k,v in p.get('ratings',{}).items():
  if k not in ('pitches','velocity'):assert get(r,k)==v,(p['name'],'능력',k,get(r,k),v)
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
for code,t in [('LG',layouts()['LG'])]:
 n=len(t['players']);needle=struct.pack('<IIH',t['team_id'],n,t['active'][0]['index'])
 at=0;found=[];expected={p['index']:p for p in t['players']}
 while (at:=ram.find(needle,at))>=0:
  ids=[struct.unpack_from('<H',ram,at+8+i*24)[0] for i in range(n)]
  if set(ids)==set(expected) and len(ids)==len(set(ids)):found.append(at)
  at+=1
 assert found,(code,'초기화된 실제 팀 레코드 없음')
 results=[]
 for at in found:
  players=[]
  for i in range(n):
   entry=at+8+i*24;idx=struct.unpack_from('<H',ram,entry)[0];p=expected[idx]
   ptr=struct.unpack_from('<I',ram,entry+16)[0];r=record(ptr)
   audit_details(idx,r)
   name=r[110:152].split(b'\0')[0];assert name==enc(p['name']),(code,p['name'],name.hex())
   primary=(r[168]&0x78)>>3
   assert primary in {'P':{0},'C':{1},'IF':{2,3,4,5},'OF':{6,7,8}}[p['category']],(code,p['name'],primary)
   cached_primary=(ram[entry+4]&0x78)>>3
   assert cached_primary==primary,(p['name'],'저장 편성의 캐시 포지션 불일치',cached_primary,primary)
   if p['category']=='P':
    assert get(r,'stamina')>0 and get(r,'velocity_raw')>0,(p['name'],'투수 기본값 없음')
    assert any((struct.unpack_from('<H',r,k)[0]&127)!=37 for k in range(58,82,2)),(p['name'],'구종 없음')
   flags=struct.unpack_from('<H',ram,entry+10)[0]
   selector=(flags>>11)&7
   assert selector<6,(code,p['name'],'등록명 선택자 범위 오류')
   players.append(dict(index=idx,name=p['name'],category=p['category'],primary=primary,cached_primary=cached_primary,foreign=bool(r[155]&128),registration_selector=selector,active=(flags>>14)==1,record_address=hex(ptr)))
  staff=[]
  for i,p in enumerate(t['coaches']):
   idx=struct.unpack_from('<H',ram,at+0x698+i*8)[0]
   ptr=struct.unpack_from('<I',ram,at+0x69c+i*8)[0]
   assert idx==p['index'],(code,'코치 순서',idx,p['index'])
   assert record(ptr)[110:152].split(b'\0')[0]==enc(p['name']),(code,'코치 이름',p['name'])
   audit_details(idx,record(ptr))
   assert idx not in expected,(code,'선수와 스태프 중복')
   staff.append(dict(index=idx,name=p['name'],role=p.get('role')))
  active=[p for p in players if p['active']]
  assert len(active)==28 and sum(p['category']=='P' for p in active)==13,(code,'1군 분류')
  assert {p['name'] for p in active}=={p['name'] for p in t['active']},'1군 명단 불일치'
  assert {p['name'] for p in active if p['foreign']}=={'치리노스','톨허스트','웰스','오스틴'},'외국인 1군 불일치'
  rotation=[struct.unpack_from('<II',ram,at+0x6d4+i*8) for i in range(17)]
  expected_rotation=[(0,0)]*17
  for j,(slot,p) in enumerate(zip([0,1,2,3,4,7,8,9,10,11,14,15,16],t['pitchers'])):
   expected_rotation[slot]=(p['game_id'],3 if j<5 else 9 if j<10 else 7 if j<12 else 12)
  assert rotation==expected_rotation,('투수 선발/중계/셋업/마무리',rotation,expected_rotation)
  results.append(dict(team_address=hex(BASE+at),players=players,staff=staff,pitching_slots=rotation))
 teams.append(dict(code=code,copies=results))
iso=ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso'
with iso.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report=dict(iso_sha256=digest,method='사용자 SYSTEM.DAT 복사본으로 새 페넌트 LG 편성의 실제 RAM: 선수/스태프 포인터, 이름, 주 포지션, 등록명 선택자, 1군 상태 전수 대조',memory_write=False,teams=teams,players=63,staff=5,passed=True)
path=ROOT/'build/lg_rebuild/live_roster_audit.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({k:v for k,v in report.items() if k!='teams'},ensure_ascii=False))
