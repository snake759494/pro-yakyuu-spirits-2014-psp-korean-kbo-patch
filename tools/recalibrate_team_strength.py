"""원본 PSP 평가 척도에 맞춰 기록→능력치 환산의 과대 기본값을 교정한다.

팀 표시 함수/상한은 수정하지 않는다. 선수 ID·보직·사진·구속·구종 구성은 보존.
"""
import json,copy
from pathlib import Path
from prepare_ratings_review import aggregate,clamp,norm,num,innings,POS,PMAP,BATTERS,arsenal_table,defense_rows,has2026
ROOT=Path(__file__).resolve().parents[1]
VERSION='PSP_SCALE_V2_SEASON2026'
def recalibrate(data):
 if data.get('calibration_version')==VERSION:return data
 data=copy.deepcopy(data)
 read=lambda p:json.loads((ROOT/p).read_text('utf8'))
 stats=read('work/ratings_review/stats.json');arsenals=arsenal_table()
 defense=defense_rows()
 from kbo_team_layout import STARTERS
 changes=[]
 for code,t in data['teams'].items():
  for p in t['players']:
   old=copy.deepcopy(p);pid=str(p['player_id']);st,_=aggregate(stats[pid]);a=p['abilities']
   if p['category']=='P':
    ip=st.get('IP',0);k9=9*(st.get('SO',0)+21)/(ip+25);bb9=9*(st.get('BB',0)+9)/(ip+25)
    base_stuff=.5+k9*.33;control=clamp(5.5-bb9*.6,1,6)
    matches=[q for q in arsenals.values() if norm(q['name'])==norm(p['name']) and q['birth']==p.get('birth')]
    bypitch={PMAP.get(q['name'],q['name']):q for q in matches[0]['arsenal']} if len(matches)==1 else {}
    for pitch in p['pitches']:
     q=bypitch.get(pitch['name']);fast=pitch['name'] in ('포심','투심')
     if q:
      n=num(q['n']);whiff=(num(q['whiff'])*n+25*120)/(n+120)
      pitch['stuff']=clamp(base_stuff*.55+(.5+whiff/10)*.45,1,6)
      pitch['control']=control
      pitch['break']=0 if fast else clamp(.5+whiff/10,1,5)
      usage=num(q['pct'])
     elif '구종 집계' in p['pitch_basis']:
      # 이전 시즌 구종도 같은 척도에 맞춘다. 원 기록으로 다시 검증하지 않은
      # 구종별 성능은 등급을 실측이라고 주장하지 않는다.
      pitch['stuff']=clamp(pitch['stuff']-1,1,5);pitch['control']=control
      pitch['break']=0 if fast else clamp(pitch['break']-1,1,5);usage=pitch.get('usage_pct',100)
     else:
      pitch['stuff']=clamp(pitch['stuff']-1,1,5);pitch['control']=clamp(pitch['control']-1,1,5)
      pitch['break']=0 if fast else clamp(pitch['break']-1,1,5);usage=pitch.get('usage_pct',100)
     if usage<3:
      pitch['stuff']=min(pitch['stuff'],2)
      if not fast:pitch['break']=min(pitch['break'],2)
     elif usage<10:
      pitch['stuff']=min(pitch['stuff'],3)
      if not fast:pitch['break']=min(pitch['break'],3)
    a.update(catching=45,throwing=48,arm=clamp(48+(p['velocity']-135)*.85,45,80))
    p['fielding']={'P':clamp(42+min(ip,180)*.05,42,55)}
   else:
    ab=st.get('AB',0);h=st.get('H',0);tb=st.get('TB',0)
    prior_avg=.260 if ab else .220;prior_iso=.130 if ab else .080;prior_hr=.020 if ab else .010
    avg=(h+prior_avg*120)/(ab+120);iso=(tb-h+prior_iso*120)/(ab+120);hrr=(st.get('HR',0)+prior_hr*120)/(ab+120)
    contact=clamp(45+(avg-.260)*430,25,92);power=clamp(25+iso*170+hrr*350,25,94)
    a.update(contact_r=contact,contact_l=contact,power=power,catching=50,throwing=50)
    if code+':'+p['name'] in BATTERS and not has2026(stats[pid]):
     a.update(contact_r=clamp(old['abilities']['contact_r']-10,25,92),contact_l=clamp(old['abilities']['contact_l']-10,25,92),power=clamp(old['abilities']['power']-5,25,94))
    a['trajectory']=4 if a['power']>=72 else 3 if a['power']>=53 else 2
    df=[r for r in defense if str(r['player_id'])==pid and POS.get(r['POS_SC']) in {'C':{'C'},'IF':{'1B','2B','3B','SS'},'OF':{'LF','CF','RF'}}[p['category']]]
    if df:
     field={}
     for r in df:
      pos=POS[r['POS_SC']];ip=innings(r['DEFEN_INN2_CN']);ch=num(r['PO_CN'])+num(r['ASS_CN'])+num(r['ERR_CN']);err=num(r['ERR_CN'])
      expected={'C':.008,'1B':.006,'2B':.016,'3B':.030,'SS':.025,'LF':.015,'CF':.012,'RF':.015}[pos]
      sure=clamp((expected-(err+expected*80)/(ch+80))*300,-6,6)
      field[pos]=max(field.get(pos,0),clamp(42+min(ip,1150)/1150*23+sure+(a['speed']-55)*.12,30,85))
     p['fielding']=field
     main=max(df,key=lambda r:innings(r['DEFEN_INN2_CN']));ip=innings(main['DEFEN_INN2_CN'])
     a['catching']=clamp(old['abilities']['catching']-10,35,80);a['throwing']=clamp(old['abilities']['throwing']-10,35,78)
    else:p['fielding']={k:clamp(v-10,30,80) for k,v in p['fielding'].items()}
    # 기존 검증된 주 포지션과 개막 선발 포지션은 유지하며 평가만 교정.
    primary=['P','C','1B','2B','3B','SS','LF','CF','RF'][p['primary_position']]
    p['fielding'][primary]=max(p['fielding'].get(primary,0),40)
    for name,pos in STARTERS[code]:
     if norm(name)==norm(p['name']) and pos!='DH':p['fielding'][pos]=max(p['fielding'].get(pos,0),50)
   p['estimated_fields'].append('PSP 원본 평가 척도 V2: 환산 기본값·희소 구종 소표본 보정; 공식 등급 아님')
   if p['category']!='P' and not st.get('AB',0):p['estimated_fields'].append('1군 타격 기록 없음: 타율 .220/ISO .080의 보수적 사전분포')
   changes.append(dict(team=code,index=p['index'],name=p['name'],before={k:old[k] for k in ('abilities','fielding','pitches')},after={k:p[k] for k in ('abilities','fielding','pitches')}))
 data['calibration_version']=VERSION
 data['method']+=' / PSP 평가 척도 V2: 컨택 기준 45, 파워 기준 25, 수비 기준 42, 구위 .5+.33*K9와 소표본 보정 헛스윙률, 제구 5.5-.6*BB9. 3% 미만 구종 등급 상한2, 10% 미만 상한3.'
 report=ROOT/'build/team_strength/calibration_changes.json';report.parent.mkdir(exist_ok=True,parents=True)
 report.write_text(json.dumps(changes,ensure_ascii=False,indent=2),'utf8')
 return data
if __name__=='__main__':
 path=ROOT/'translation/kbo_2026/ratings_review.json';data=json.loads(path.read_text('utf8'))
 path.write_text(json.dumps(recalibrate(data),ensure_ascii=False,indent=2)+'\n','utf8')
 print(VERSION)
