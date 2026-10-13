"""한화 개막 선수단을 기존 팀 6 슬롯에 고정 크기로 삽입한다."""
from pathlib import Path
import json,struct,hashlib
from analyze import chunks
from player_fields import put,get,jersey_code,apply_abilities
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'translation/hanwha_2026.json'
def load():return json.loads(SPEC.read_text('utf8'))
def filter_rows(rows):
 selected={r['index'] for r in load()['records'] if r['kind']=='player'}
 def retained(r):
  if r['file']!='PLAYERDATA.CHK':return True
  o=r['offset']
  for base,stride in ((5120,192),(486816,84)):
   i,within=divmod(o-base,stride)
   if i in selected and 0<=within<84:return False
  return True
 return [r for r in rows if retained(r)]
def override_names(players):
 spec=load();target={r['index']:r for r in spec['records']};out=[];seen=set()
 for p in players:
  if p['chunk']=='PDN' and p['index'] in target:
   p=dict(p,ko=[target[p['index']]['name'],'']);seen.add(p['index'])
  out.append(p)
 for i in target.keys()-seen:
  out.append(dict(chunk='PDN',index=i,offset=5120+i*192+110,ja=[],ko=[target[i]['name'],'']))
 return out
def apply(original,translated):
 spec=load();out=bytearray(translated);cs={n:(o,b) for n,o,b in chunks(original)};pd=cs['PDN'][0];wd=cs['PDW'][0];regions=[]
 appearance_path=ROOT/'translation/hanwha_visual/appearance.json'
 appearance={p['index']:p for p in json.loads(appearance_path.read_text('utf8'))} if appearance_path.exists() else {}
 def replace(off,new,label):
  old=original[off:off+len(new)];assert out[off:off+len(new)]==old,label
  out[off:off+len(new)]=new
  if old!=new:regions.append(dict(file='PLAYERDATA.CHK',offset=off,size=len(new),original=old.hex(),patched=bytes(new).hex(),reason=label))
 for p in spec['records']:
  i=p['index'];base=pd+i*192;old=original[base:base+192];r=bytearray(old)
  assert get(old,'jersey')<2048 and old[90]&63==6
  if p['kind']=='player':
   r=apply_abilities(old,p)
   replace(base,r[:84],p['name']+' 기본 능력/수비/구종')
   replace(wd+i*84,r[:84],p['name']+' 대체 능력 데이터 동기화')
  y,m,d=map(int,p['birth'].split('-'));assert 1900<=y<=2027
  struct.pack_into('<H',r,104,(y-1900)|(m<<7)|(d<<11))
  put(r,'height',p['height']);put(r,'throw_hand',p['throw_hand']);put(r,'bat_hand',p['bat_hand']);put(r,'jersey',jersey_code(p['number']))
  # 등록명 선택: word 0xa0 bits 13..15. 銀次 슬롯의 given-name(3) 등을
  # 첫 문자열(0)에 저장한 한국어 전체 이름으로 통일한다.
  r[161]&=0x1f
  if p['kind']=='player':
   # 0x98 bit31: 외국인. 원 일본 외국인 슬롯 여부를 새 신원에 맞춘다.
   r[155]=(r[155]&0x7f)|(0x80 if p['foreign'] else 0)
  if i in appearance:
   visual=appearance[i];latin=visual['back_name'].encode('ascii');assert len(latin)<=11
   if 'skin_type' in visual:
    skin=struct.unpack_from('<I',r,152)[0]
    struct.pack_into('<I',r,152,(skin&~0x03800000)|(visual['skin_type']<<23))
   r[92:104]=latin.ljust(12,b'\0');put(r,'height',visual['height'])
   body=struct.unpack_from('<I',r,156)[0];struct.pack_into('<I',r,156,(body&0x07ffffff)|(visual['body_type']<<27))
   replace(base+92,r[92:104],p['name']+' 영문 등 이름')
   replace(base+156,r[156:160],p['name']+' 공식 키/몸무게에 맞춘 체형 모델')
  replace(base+104,r[104:106],p['name']+' 생년월일')
  replace(base+152,r[152:156],p['name']+' 키/투타/외국인')
  replace(base+160,r[160:162],p['name']+' 등번호/등록명 선택')
  assert r[84:92]==old[84:92],'선수 ID·음성 키·구단 보존'
 assert len(out)==len(original)
 return out,dict(cutoff=spec['cutoff'],players=sum(r['kind']=='player' for r in spec['records']),coaches=sum(r['kind']=='coach' for r in spec['records']),opening_members=29,
  positions={k:sum(r.get('category')==k for r in spec['records']) for k in ('PC','CC','IF','OF')},
  spec_sha256=hashlib.sha256(SPEC.read_bytes()).hexdigest(),regions=regions,limitations=spec['limitations'])
