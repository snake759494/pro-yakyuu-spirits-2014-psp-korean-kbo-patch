"""KBO 기록 환산값을 원본 게임 1군 척도의 상단에 맞추는 최종 척도화(V3).

배경: 원본 PSP 척도는 일본 개막 1군도 컨택 중앙값 44·파워 52 수준으로 낮다. KBO를 주인공 리그로
보고 기록 순위는 유지하면서, KBO 1군의 분위 p를 원본 1군 분포의 분위 p**0.6에 대응시킨다
(KBO 중위 → 원본 1군 상위 약 34%, KBO 최상위 → 원본 최상위). 2군은 같은 단조 함수로 옮긴다.
이전 환산에서 전원 같은 값이던 어깨·포구·송구·회복은 2026/2025 수비·출장 기록으로 개인차를 만든다.
구속은 실측 km/h이므로 바꾸지 않는다. 공식 게임 등급이 아닌 추정치다.
"""
import json,struct,copy
from pathlib import Path
from functools import lru_cache
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
VERSION='KBO_TOP_SCALE_V3_2026B'
GAMMA=.6
FAST=('포심','투심')

@lru_cache(None)
def npb_active():
 """원본 BOOT 개막 1군 표(0x8a94a10)로 고른 일본 1군 선수의 능력 분포."""
 from analyze import chunks
 from player_fields import get,POSITIONS
 cs={n:b for n,a,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())};pd=cs['PDN']
 boot=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();off=lambda a:a-0x8804000+0x1018
 order=struct.unpack('<2535H',cs['PDTPLIST']);idmap={struct.unpack_from('<H',pd,i*192+84)[0]:i for i in range(len(pd)//192)}
 H={};P={};pitch={'break':[],'stuff':[],'control':[],'stuff_fast':[],'control_fast':[]}
 for tid in range(12):
  start,first,_=struct.unpack_from('<HHI',boot,off(0x8a94a10)+tid*8)
  for gid in order[start:start+first]:
   r=pd[idmap[gid]*192:idmap[gid]*192+192];pos=(r[168]&0x78)>>3
   if pos==0:
    for k in ('stamina','recovery','arm','catching','throwing','P'):P.setdefault(k,[]).append(get(r,k))
    for v in struct.unpack_from('<12H',r,58):
     if v&127==37:continue
     fast=v&127 in (0,2);sfx='_fast' if fast else ''
     if not fast:pitch['break'].append((v>>7)&7)
     pitch['stuff'+sfx].append((v>>10)&7);pitch['control'+sfx].append((v>>13)&7)
   else:
    for k in ('contact_r','contact_l','power','speed','arm','catching','throwing','recovery'):H.setdefault(k,[]).append(get(r,k))
    H.setdefault('field',[]).append(max(get(r,q) for q in POSITIONS if q!='P'))
 return H,P,pitch

def mapper(kbo_active,target,lo,hi):
 """KBO 1군 값의 분위 p → 원본 1군 분위 p**GAMMA. 범위 밖은 기울기 1로 연장."""
 x=np.asarray(kbo_active,float);t=np.asarray(target,float)
 ps=np.linspace(0,1,41);xs=np.quantile(x,ps);ys=np.quantile(t,ps**GAMMA)
 xs,idx=np.unique(xs,return_index=True);ys=np.maximum.accumulate(ys[idx])
 def f(v):
  if v<xs[0]:y=ys[0]-(xs[0]-v)
  elif v>xs[-1]:y=ys[-1]+(v-xs[-1])
  else:y=np.interp(v,xs,ys)
  return int(max(lo,min(hi,round(float(y)))))
 return f

def num(v):
 try:return float(str(v).replace(',',''))
 except:return 0.

def games(stats,pid):
 g={}
 for t in stats.get(pid,{}).get('seasons',[]):
  for row in t['rows']:
   r=dict(zip(t['headers'],row))
   if r['연도'] in ('2026','2025') and r.get('팀명') not in ('합계','통산'):g[r['연도']]=g.get(r['연도'],0)+num(r.get('G'))
 return g.get('2026',0)+.5*g.get('2025',0)

def rescale(data):
 if data.get('scale_version')==VERSION:return data
 data=copy.deepcopy(data)
 from prepare_ratings_review import defense_rows,innings,POS
 stats=json.loads((ROOT/'work/ratings_review/stats.json').read_text('utf8'))
 dfn={}
 for r in defense_rows():dfn.setdefault(r['player_id'],[]).append(r)
 H,P,pitch=npb_active()
 allp=[(code,p,p['index'] in set(t['opening_indices'])) for code,t in data['teams'].items() for p in t['players']]
 hit=[x for x in allp if x[1]['category']!='P'];pit=[x for x in allp if x[1]['category']=='P']
 # 개인차 원값: 포지션 기본 어깨, 외야 보살률, 포수 도루저지율, 수비 적성, 출장 수.
 ARMBASE={'C':4,'SS':6,'3B':5,'RF':6,'CF':5,'2B':3,'LF':3,'1B':1}
 raw={}
 for code,p,act in hit:
  pid=p['player_id'];rows=[r for r in dfn.get(pid,[]) if POS.get(r['POS_SC']) not in (None,'P')]
  main=max(rows,key=lambda r:innings(r['DEFEN_INN2_CN'])) if rows else None
  pos=POS[main['POS_SC']] if main else ['C','1B','2B','3B','SS','LF','CF','RF'][p['primary_position']-1]
  inn=innings(main['DEFEN_INN2_CN']) if main else 0
  arm=ARMBASE.get(pos,3)*6
  if main and pos in ('LF','CF','RF'):arm+=min(12,num(main['ASS_CN'])/max(inn,100)*9*40)
  if main and pos=='C' and main.get('CS_RT') not in (None,'-'):arm+=(num(main['CS_RT'])-25)*.5
  fld=max(p['fielding'].values())
  raw[pid]=dict(arm=arm+fld*.3,catching=fld+p['abilities']['catching']*.3,throwing=fld*.6+arm*.6,recovery=games(stats,pid)+fld*.05)
 for code,p,act in pit:
  f=p['fielding'].get('P',45);raw[p['player_id']]=dict(catching=f,throwing=f+p['velocity']*.05)
 def remap(group,key,target,lo,hi,value):
  f=mapper([value(p) for c,p,a in group if a],target,lo,hi)
  return {p['player_id']:f(value(p)) for c,p,a in group}
 # 타자
 new={}
 for k in ('contact_r','contact_l','power','speed'):new[k]=remap(hit,k,H[k],25,99,lambda p,k=k:p['abilities'][k])
 for k in ('arm','catching','throwing','recovery'):new[k]=remap(hit,k,H[k],30,99,lambda p,k=k:raw[p['player_id']][k])
 ff=mapper([max(p['fielding'].values()) for c,p,a in hit if a],H['field'],25,99)
 for code,p,act in hit:
  pid=p['player_id'];a=p['abilities']
  for k in new:a[k]=new[k][pid]
  a['trajectory']=4 if a['power']>=75 else 3 if a['power']>=55 else 2
  p['fielding']={pos:ff(v) for pos,v in p['fielding'].items()}
 # 투수
 for k,lo in (('stamina',30),('recovery',30),('arm',40)):
  m=remap(pit,k,P[k],lo,99,lambda p,k=k:p['abilities'][k])
  for c,p,a in pit:p['abilities'][k]=m[p['player_id']]
 for k in ('catching','throwing'):
  m=remap(pit,k,P[k],30,99,lambda p,k=k:raw[p['player_id']][k])
  for c,p,a in pit:p['abilities'][k]=m[p['player_id']]
 pf=mapper([p['fielding'].get('P',45) for c,p,a in pit if a],P['P'],25,99)
 for c,p,a in pit:p['fielding']={'P':pf(p['fielding'].get('P',45))}
 # 구종 등급: 직구/변화구를 따로, 정수 등급에 사용률로 동순위를 나눈 뒤 원본 1군 등급 분포에 대응.
 for key,fast in (('break',False),('stuff',False),('control',False),('stuff',True),('control',True)):
  items=[(q[key]+q.get('usage_pct',30)/1000,q,a) for c,p,a in pit for q in p['pitches'] if (q['name'] in FAST)==fast]
  f=mapper([v for v,q,a in items if a],pitch[key+('_fast' if fast else '')],1,7)
  for v,q,a in items:
   y=f(v);u=q.get('usage_pct',100)
   if key!='control' and u<3:y=min(y,3)
   elif key!='control' and u<10:y=min(y,4)
   q[key]=y
 data['scale_version']=VERSION
 data['method']+=' / V3: KBO 1군 분위 p → 원본 개막 1군 분위 p^0.6(순위 보존), 어깨·포구·송구·회복은 수비/출장 기록으로 개인차, 구속 실측 유지.'
 return data
