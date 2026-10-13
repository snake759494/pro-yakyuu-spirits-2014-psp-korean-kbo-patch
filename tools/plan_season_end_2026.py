"""2026 정규시즌 종료 기준 구단별 게임 슬롯 재배치 계획.

기준: KBO 선수 검색의 현재 소속 선수, 2026 정규시즌 기용량(KBO 영문 공식 시즌 요약),
KBO 날짜별 등록 현황 2026-10-03(정규시즌 최종 1군). 게임 1군 29명은 시즌 대표성을 위해
현재 소속 선수 중 2026 기용량(투수 이닝, 야수 타석) 상위로 정한다. 최종일 등록 명단은
시즌 막판 휴식/조정이 섞여 있으므로 슬롯 보장 대상으로만 쓴다.
게임 슬롯(index)·선수 ID·음성 키·얼굴 파일은 그대로 두고 슬롯에 들어갈 KBO 선수만 바꾼다.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'work/kbo_roster_research'
OUT=ROOT/'work/season_end_2026/plan.json'
TEAMS=['LG','SS','HT','WO','KT','LT','HH','OB','SK','NC']
REGISTER_DATE='20261003'
def read(p):return json.loads(Path(p).read_text('utf8'))
def main():
 base=ROOT/'build/baseline_before_season_end_2026/translation/kbo_2026/appearance.json'
 app=read(base if base.exists() else ROOT/'translation/kbo_2026/appearance.json');eng=read(R/'english.json')
 def games(pid):return (eng.get(pid,{}).get('season2026') or {}).get('G',0)
 def ip(pid):
  v=(eng.get(pid,{}).get('season2026') or {}).get('IP','0');w=v.split()
  return sum(eval(x) if '/' in x else float(x) for x in w) if w else 0
 def load(pid):
  s=eng.get(pid,{}).get('season2026') or {};return ip(pid) if 'IP' in s else s.get('PA',0)
 foreign=lambda pid:eng.get(pid,{}).get('foreign',False)
 plan={}
 for t in TEAMS:
  cur={p['player_id']:p for p in read(R/f'current/{t}.json')['players']}
  reg=read(R/f'{REGISTER_DATE}/{t}.json');act=[];hands={}
  for tb in reg['tables'][2:6]:
   for r in tb['rows']:
    pid=re.search(r'playerId=(\d+)',' '.join(r['player_links']))[1];act.append(pid);hands[pid]=r['cells'][2]
  slots=sorted([p for p in app if p['team']==t],key=lambda p:p['index'])
  held={p['player_id']:p for p in slots}
  free=[p for p in slots if p['player_id'] not in cur]
  # 2026 시즌 대표 1군 29명: 투수 14(이닝), 야수 15(타석, 포수 2 이상), 외국인 최대 4.
  ispitch=lambda pid:cur[pid]['position']=='투수'
  P=sorted([x for x in cur if ispitch(x) and load(x)>0],key=lambda x:(-load(x),x));F=sorted([x for x in cur if not ispitch(x) and load(x)>0],key=lambda x:(-load(x),x))
  fx=[x for x in P+F if foreign(x)];fx=sorted(fx,key=lambda x:-(load(x)*(3 if ispitch(x) else 1)))
  banned=set(fx[4:]);P=[x for x in P if x not in banned];F=[x for x in F if x not in banned]
  C=[x for x in F if cur[x]['position']=='포수']
  active=P[:14]+C[:2]+[x for x in F if x not in C[:2]][:13]
  assert len(active)==29,(t,len(active))
  incoming=[pid for pid in active+[x for x in act if x not in active] if pid not in held]
  keep=[p for p in slots if p['player_id'] in cur]
  evict=sorted([p for p in keep if p['player_id'] not in act and p['player_id'] not in active],key=lambda p:(load(p['player_id']),p['index']))
  free=[p for p in slots if p['player_id'] not in cur]
  while len(free)<len(incoming):free.append(evict.pop(0))
  free.sort(key=lambda p:(not p['dedicated_face'],p['index']))
  rows={p['index']:dict(index=p['index'],player_id=p['player_id'],status='keep',dedicated_face=p['dedicated_face']) for p in slots}
  inplay=set(held)
  for pid,slot in zip(incoming,free):
   rows[slot['index']].update(player_id=pid,status='new',previous=dict(player_id=slot['player_id'],name=slot['name']));inplay.add(pid)
  rest=free[len(incoming):]
  taken={r['player_id'] for r in rows.values()}
  pool=sorted([pid for pid in cur if pid not in taken],key=lambda pid:(-load(pid),pid))
  for slot,pid in zip(rest,pool):
   rows[slot['index']].update(player_id=pid,status='new_reserve',previous=dict(player_id=slot['player_id'],name=slot['name']))
  if len(rest)>len(pool):raise SystemExit((t,'예비 선수 부족'))
  for r in rows.values():
   pid=r['player_id'];c=cur[pid];r.update(name=c['name'],number=c['number'],position=c['position'],birth=c['birth'],body=c['body'],hands=hands.get(pid),games2026=games(pid),load2026=load(pid),foreign=foreign(pid),
     active=pid in active,final_register=pid in act,english=eng.get(pid,{}).get('english',''))
  plan[t]=dict(register_date=REGISTER_DATE,final_register=act,active=active,slots=sorted(rows.values(),key=lambda r:r['index']),
    final_register_not_active=[cur[x]['name'] for x in act if x not in active],active_not_final_register=[cur[x]['name'] for x in active if x not in act])
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(plan,ensure_ascii=False,indent=1),'utf8')
 for t,p in plan.items():
  ch=[r for r in p['slots'] if r['status']!='keep']
  print(t,'변경',len(ch),[ (r['previous']['name'],'→',r['name'],r['status'][4:] or '1군') for r in ch],'| 최종등록 외 1군',p['active_not_final_register'])
if __name__=='__main__':main()
