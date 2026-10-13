"""실제 편성 초기화 경로: PDTPLIST, 주 포지션, 투수진, DH/비DH 타순.

슬롯 1 추적: 088fced0 <- 088f04dc; 선수 수 08a94a10;
주 포지션은 PDN+168의 0x78. 수비 능력치와 별개다.
INIPLIST는 얼굴 리소스 순서이므로 절대로 재배열하지 않는다.
"""
import json, struct
from pathlib import Path
from functools import lru_cache
from analyze import chunks
from prepare_kbo_teams import records, TEAM_IDS

ROOT=Path(__file__).resolve().parents[1]
POS={'P':0,'C':1,'1B':2,'2B':3,'3B':4,'SS':5,'LF':6,'CF':7,'RF':8,'DH':9}
ROTATIONS={
 'LG':('치리노스','톨허스트','임찬규','이정용','웰스'),
 'SS':('후라도','오러클린','최원태','이승현(좌)'),
 'HT':('네일','올러','이의리'),
 'WO':('와일스','알칸타라','하영민','배동현'),
 'KT':('보쉴리','사우어','소형준','고영표','오원석'),
 'LT':('박세웅','비슬리','로드리게스'),
 'HH':('류현진','문동주','에르난데스','왕옌청','화이트'),
 'OB':('플렉센','잭로그','곽빈','최민석','최준호'),
 'SK':('화이트','베니지아노','김건우','김광현'),
 'NC':('테일러','구창모','토다'),
}
CLOSERS=dict(zip(TEAM_IDS,('유영찬','김재윤','정해영','김재웅','박영현','김원중','김서현','김택연','조병현','김영규')))
# 개막 등록 선수 중 기본 선발 배치. 좌/우 투수 모두 같은 명단을 사용한다.
STARTERS={
 'LG': [('홍창기','RF'),('신민재','2B'),('오스틴','1B'),('문보경','DH'),('박동원','C'),('문성주','LF'),('오지환','SS'),('구본혁','3B'),('박해민','CF')],
 'SS': [('김지찬','CF'),('류지혁','2B'),('구자욱','LF'),('디아즈','1B'),('최형우','DH'),('강민호','C'),('김영웅','3B'),('이재현','SS'),('김성윤','RF')],
 'HT': [('박재현','LF'),('김선빈','2B'),('김도영','3B'),('나성범','DH'),('카스트로','RF'),('오선우','1B'),('한준수','C'),('데일','SS'),('김호령','CF')],
 'WO': [('이주형','CF'),('김태진','2B'),('브룩스','RF'),('최주환','1B'),('안치홍','DH'),('임지열','LF'),('김건희','C'),('오선진','3B'),('어준서','SS')],
 'KT': [('최원준','CF'),('김상수','SS'),('김현수','DH'),('힐리어드','1B'),('안현민','RF'),('허경민','3B'),('장성우','C'),('오윤석','2B'),('장진혁','LF')],
 'LT': [('황성빈','CF'),('전민재','SS'),('레이예스','RF'),('전준우','DH'),('손호영','LF'),('김민성','1B'),('유강남','C'),('한태양','2B'),('노진혁','3B')],
 'HH': [('문현빈','LF'),('페라자','RF'),('노시환','3B'),('강백호','DH'),('채은성','1B'),('김태연','CF'),('최재훈','C'),('하주석','2B'),('심우준','SS')],
 'OB': [('정수빈','CF'),('박찬호','SS'),('카메론','RF'),('양의지','C'),('양석환','1B'),('김민석','LF'),('강승호','3B'),('박준순','2B'),('오명진','DH')],
 'SK': [('최지훈','CF'),('정준재','2B'),('최정','3B'),('에레디아','LF'),('김재환','DH'),('고명준','1B'),('박성한','SS'),('이지영','C'),('김성욱','RF')],
 'NC': [('박민우','2B'),('서호철','3B'),('박건우','RF'),('데이비슨','1B'),('권희동','LF'),('김휘집','DH'),('김주원','SS'),('김형준','C'),('한석현','CF')],
}

# 2026 정규시즌 종료 기준 기용(tools/derive_layout_2026.py)이 있으면 위 개막 기준값을 대체한다.
_SEASON=ROOT/'translation/kbo_2026/season_end_layout.json'
if _SEASON.exists():
 _s=json.loads(_SEASON.read_text('utf8'))
 ROTATIONS={k:tuple(v) for k,v in _s['ROTATIONS'].items()}
 CLOSERS=dict(_s['CLOSERS'])
 STARTERS={k:[tuple(x) for x in v] for k,v in _s['STARTERS'].items()}

def category(p):
 return {'PC':'P','CT':'C','CC':'C','IF':'IF','OF':'OF'}.get(p.get('category'),p.get('category'))

@lru_cache(None)
def layouts():
 raw=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes()
 cs={n:b for n,_,b in chunks(raw)};pd=cs['PDN']
 boot=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
 off=lambda a:a-0x8804000+0x1018
 original_order=struct.unpack('<2535H',cs['PDTPLIST'])
 idmap={struct.unpack_from('<H',pd,i*192+84)[0]:i for i in range(len(pd)//192)}
 result={};cursor=0
 for code,tid in TEAM_IDS.items():
  path='translation/hanwha_2026.json' if code=='HH' else f'translation/kbo_2026/{code}.json'
  spec=json.loads((ROOT/path).read_text('utf8'));players=[dict(p,category=category(p)) for p in spec['records'] if p['kind']=='player']
  from kbo_ratings_review import manifest
  review=manifest()['teams'][code];ratings={p['index']:p for p in review['players']}
  for p in players:
   p['primary_position']=ratings[p['index']]['primary_position']
   p['player_id']=ratings[p['index']]['player_id']
  staff=[p for p in spec['records'] if p['kind']=='coach'];byname={''.join(p['name'].split()):p for p in players}
  assert len(byname)==len(players),(code,'구단 내 표시 이름 중복')
  byindex={p['index']:p for p in players}
  ordered=[byindex[i] for i in review['opening_indices']]
  batting=[(byname[n],POS[pos]) for n,pos in STARTERS[code]]
  assert all(p['category']!='P' and p in ordered for p,pos in batting)
  rotation=[byname[n] for n in ROTATIONS[code] if n in byname and byname[n] in ordered]
  closer=byname[CLOSERS[code]]
  assert closer in ordered and closer not in rotation
  ps=rotation+[p for p in ordered if p['category']=='P' and p not in rotation and p is not closer]+[closer]
  assert all(p['category']=='P' for p in ps) and len({p['index'] for p in ps})==len(ps)
  bs=[p for p,pos in batting]
  bs += [p for p in ordered if p['category']!='P' and p not in bs]
  assert len(ps)+len(bs)==29
  active=ps+bs;rest=[p for p in players if p not in active]
  start,first,flags=struct.unpack_from('<HHI',boot,off(0x8a94a10)+tid*8)
  total=first+(flags&0xfff);coach_ids=original_order[start+total:start+total+5]
  staffmap={p['index']:p for p in staff}
  coaches=[staffmap[idmap[x]] for x in coach_ids]
  assert len({p['index'] for p in coaches})==5
  rows=active+rest+coaches
  for p in rows:p['game_id']=struct.unpack_from('<H',pd,p['index']*192+84)[0]
  result[code]=dict(team_id=tid,start=cursor,players=players,active=active,pitchers=ps,rotation=rotation,batting=batting,bench=[p for p in bs if p not in [x for x,_ in batting]],rows=rows,coaches=coaches)
  cursor+=len(rows)
 assert cursor<=struct.unpack_from('<H',boot,off(0x8a94a10)+10*8)[0]
 return result

def apply_playerdata(data):
 out=bytearray(data);cs={n:(o,b) for n,o,b in chunks(data)};pd=cs['PDN'][0];tpl=cs['PDTPLIST'][0]
 for code,t in layouts().items():
  ids=[p['game_id'] for p in t['rows']]
  out[tpl+t['start']*2:tpl+(t['start']+len(ids))*2]=struct.pack('<%dH'%len(ids),*ids)
  selected={p['index']:pos for p,pos in t['batting'] if pos!=9}
  for p in t['players']:
   pos=p.get('primary_position',selected.get(p['index'],{'P':0,'C':1,'IF':2,'OF':6}[p['category']]))
   at=pd+p['index']*192+168
   out[at]=(out[at]&0x80)|(pos<<3)|3
  # 谷繁 was a player-manager. Park Jin-man must be staff only.
  for p in t['coaches']:
   at=pd+p['index']*192+168
   if p.get('role')=='감독':out[at]=(out[at]&0xf8)|4
 assert cs['INIPLIST'][1]==next(b for n,o,b in chunks(out) if n=='INIPLIST')
 return out

def patches():
 # 원 생성자는 공식 명단 인원을 읽은 뒤 28명으로 잘랐다. 선수 배열은 전체
 # 70개 슬롯을 공유하므로 배열 확장 없이 등록 플래그의 상한만 29로 바꾼다.
 out=[('BOOT.BIN',0x88fce54,struct.pack('<I',0x2a64001e),'개막 1군 인원 29명 허용 비교'),
      ('BOOT.BIN',0x88fce5c,struct.pack('<I',0x3413001d),'개막 등록 인원 상한 29명'),
      ('com_sel.elf',0x8ccc12c,struct.pack('<I',0x2863001d),'팀 등록 정규화: 투수 처리 중 총원 29명'),
      ('com_sel.elf',0x8ccc160,struct.pack('<I',0x2863001d),'팀 등록 정규화: 야수 처리 중 총원 29명'),
      ('com_sel.elf',0x8ccdbe8,struct.pack('<I',0x28c6001d),'시즌 선수 객체 정규화: 투수 처리 중 총원 29명'),
      ('com_sel.elf',0x8ccdc18,struct.pack('<I',0x28c6001d),'시즌 선수 객체 정규화: 야수 처리 중 총원 29명')]
 for code,t in layouts().items():
  tid=t['team_id'];n=len(t['players'])
  out.append(('BOOT.BIN',0x8a94a10+tid*8,struct.pack('<HHI',t['start'],len(t['active']),(5<<12)|(n-len(t['active']))),f'{code} 실제 1군/2군/스태프 인원'))
  ns=len(t['rotation']);middle=len(t['pitchers'])-ns-3
  assert 0<=middle<=7 and ns<=5,(code,ns,middle)
  pitchers=[(p['game_id'],3 if j<ns else 9 if j<ns+middle else 7 if j<len(t['pitchers'])-1 else 12) for j,p in enumerate(t['pitchers'])]
  rotation=[(0,0)]*17
  for slot,pair in zip(list(range(ns))+list(range(7,7+middle))+[14,15,16],pitchers):rotation[slot]=pair
  out.append(('BOOT.BIN',0x8a936d8+tid*136,b''.join(struct.pack('<II',*p) for p in rotation),f'{code} 선발/중계/셋업/마무리 선수 ID'))
  dh=[(pos,p['game_id']) for p,pos in t['batting']]
  nodh=[x for x in dh if x[0]!=9]
  bench=[(12,p['game_id']) for p in t['bench'][:2]]
  assert len(bench)==2
  block=b''.join(struct.pack('<II',*p) for p in nodh+bench+dh+bench)
  assert len(block)==168
  out.append(('com_sel.elf',0x8c692e8+tid*336,block*2,f'{code} 좌/우 투수별 DH/비DH 타순'))
 return out
