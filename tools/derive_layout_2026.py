"""2026 정규시즌 실제 기용으로 기본 선발 로테이션·마무리·선발 타순을 도출한다.

근거: KBO 2026 수비 기록의 포지션별 선발 출장(START_GAME_CN, 투수는 선발 등판),
KBO 개인 통산 기록의 2026 행(세이브, 타석, 출루율, 장타율, 도루).
대상은 게임 1군 29명(정규시즌 최종 등록 기준)으로 한정한다. 타순은 기록 기반 규칙이며
특정 경기의 실제 라인업을 복제한 것이 아니다.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'work/ratings_review'
OUT=ROOT/'translation/kbo_2026/season_end_layout.json'
POS={'포수':'C','1루수':'1B','2루수':'2B','3루수':'3B','유격수':'SS','좌익수':'LF','중견수':'CF','우익수':'RF','투수':'P'}
def read(p):return json.loads(Path(p).read_text('utf8'))
def num(v):
 try:return float(str(v).replace(',',''))
 except:return 0.
def season(src):
 rows=[dict(zip(t['headers'],r)) for t in src.get('seasons',[]) for r in t['rows'] if r[0]=='2026']
 tot=[r for r in rows if r.get('팀명') in ('합계','통산')]
 if tot:rows=tot
 out={}
 for r in rows:
  for k,v in r.items():
   if k in ('연도','팀명'):continue
   if k=='IP':v=sum(eval(x) if '/' in x else float(x) for x in str(v).split()) if v else 0
   out[k]=out.get(k,0)+num(v)
 if 'AB' in out and len(rows)>1:
  ab=out['AB'];pa=max(out['PA'],1);out['OBP']=(out['H']+out['BB']+out['HBP'])/pa;out['SLG']=out['TB']/max(ab,1)
 return out
def main():
 ident=read(D/'identities.json');opening=read(D/'opening.json');stats=read(D/'stats.json')
 defense=read(D/'defense_2026.json');starts={}
 for r in defense:
  pos=POS.get(r['POS_SC'])
  if pos:starts.setdefault(r['player_id'],{});starts[r['player_id']][pos]=starts[r['player_id']].get(pos,0)+num(r['START_GAME_CN'])
 result={'source':'KBO 2026 정규시즌 수비/개인 기록, 2026-10-03 최종 1군','STARTERS':{},'ROTATIONS':{},'CLOSERS':{},'evidence':{}}
 for code,act in opening.items():
  byid={p['player_id']:p for p in ident[code]}
  ps=[byid[x['player_id']] for x in act if x['category']=='P'];fs=[byid[x['player_id']] for x in act if x['category']!='P']
  sv=lambda p:season(stats[p['player_id']]).get('SV',0)
  hld=lambda p:season(stats[p['player_id']]).get('HLD',0)
  gs=lambda p:starts.get(p['player_id'],{}).get('P',0)
  rot=sorted([p for p in ps if gs(p)>=5],key=lambda p:-gs(p))[:5]
  # 게임 투수진 구조(선발 5 + 중계 최대 7 + 셋업/마무리 3)를 위해 선발을 5명까지 보충:
  # 시즌 선발 등판, 그다음 등판당 이닝이 긴 투수.
  ipg=lambda p:season(stats[p['player_id']]).get('IP',0)/max(1,season(stats[p['player_id']]).get('G',0))
  for p in sorted([p for p in ps if p not in rot],key=lambda p:(-gs(p),-ipg(p))):
   if len(rot)>=5:break
   if sv(p)<5:rot.append(p)
  closer=max([p for p in ps if p not in rot],key=lambda p:(sv(p),hld(p)))
  # 포지션 배정: 해당 포지션 선발 출장이 가장 많은 선수부터, 희소 포지션 우선.
  used=set();lineup={}
  for pos in ('C','SS','2B','CF','3B','1B','RF','LF'):
   cand=[p for p in fs if p['player_id'] not in used and starts.get(p['player_id'],{}).get(pos,0)>0]
   if not cand:cand=[p for p in fs if p['player_id'] not in used and (pos!='C' or p['category']=='C')]
   best=max(cand,key=lambda p:(starts.get(p['player_id'],{}).get(pos,0),season(stats[p['player_id']]).get('PA',0)))
   lineup[pos]=best;used.add(best['player_id'])
  dh=max([p for p in fs if p['player_id'] not in used and p['category']!='C'] or [p for p in fs if p['player_id'] not in used],key=lambda p:season(stats[p['player_id']]).get('PA',0))
  lineup['DH']=dh
  st={pos:season(stats[p['player_id']]) for pos,p in lineup.items()}
  obp=lambda pos:(st[pos].get('OBP',0)*min(1,st[pos].get('PA',0)/150))
  slg=lambda pos:(st[pos].get('SLG',0)*min(1,st[pos].get('PA',0)/150))
  pool=list(lineup)
  first=max([x for x in pool if x!='C'],key=lambda x:obp(x)+st[x].get('SB',0)/150-max(0,slg(x)-.45));pool.remove(first)
  fourth=max(pool,key=lambda x:slg(x)+obp(x)*.5);pool.remove(fourth)
  third=max(pool,key=lambda x:obp(x)+slg(x));pool.remove(third)
  second=max(pool,key=lambda x:obp(x));pool.remove(second)
  fifth=max(pool,key=lambda x:slg(x));pool.remove(fifth)
  rest=sorted(pool,key=lambda x:-(obp(x)+slg(x)))
  order=[first,second,third,fourth,fifth]+rest
  nm=lambda p:''.join(p['name'].split())
  result['STARTERS'][code]=[[nm(lineup[pos]),pos] for pos in order]
  result['ROTATIONS'][code]=[nm(p) for p in rot]
  result['CLOSERS'][code]=nm(closer)
  result['evidence'][code]=dict(rotation_starts={p['name']:gs(p) for p in rot},closer_saves=sv(closer),
    lineup={pos:dict(name=lineup[pos]['name'],starts_at_pos=starts.get(lineup[pos]['player_id'],{}).get(pos,0),PA=st[pos].get('PA',0),OBP=round(st[pos].get('OBP',0),3),SLG=round(st[pos].get('SLG',0),3)) for pos in order})
  print(code,'로테이션',result['ROTATIONS'][code],'마무리',closer['name'],sv(closer),'| 타순',' '.join(f"{lineup[x]['name']}({x})" for x in order))
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n','utf8')
if __name__=='__main__':main()
