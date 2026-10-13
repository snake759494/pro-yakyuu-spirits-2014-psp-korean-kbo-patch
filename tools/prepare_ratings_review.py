"""2026 개막 기준 전 선수 완전 능력치 명세. 공식 게임 수치가 아닌 공개 기록 기반 추정이다.

선수 ID로만 기록을 결합한다. 소표본은 리그 평균으로 수축하며, 미확인 자료는
확인된 것으로 포장하지 않고 estimated_fields에 남긴다. 원 일본 능력치는 사용하지 않는다.
"""
import json,re,math,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from player_fields import PITCHES
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'work/ratings_review'
OUT=ROOT/'translation/kbo_2026/ratings_review.json'
def read(p):return json.loads(p.read_text('utf8'))
def norm(s):return re.sub(r'\([^)]*\)|\s','',s)
def clamp(v,lo=25,hi=92):return max(lo,min(hi,round(v)))
def num(v):
 try:return float(str(v).replace(',',''))
 except:return 0.
def innings(v):
 return sum(float(t.split('/')[0])/float(t.split('/')[1]) if '/' in t else num(t) for t in str(v).split())
POS={'투수':'P','포수':'C','1루수':'1B','2루수':'2B','3루수':'3B','유격수':'SS','좌익수':'LF','중견수':'CF','우익수':'RF'}
PORDER=['P','C','1B','2B','3B','SS','LF','CF','RF']
# 국제 리그의 싱커는 빠른 투심 계열. PSP의 느린 싱커와 구분한다.
PMAP={'직구':'포심','스위퍼':'슬라이더','싱커':'투심','포크':'포크','너클볼':'커브','스크루볼':'싱커'}
def aggregate(source):
 tables=source.get('seasons',source['through_2025'])
 if not tables:return {},None
 rows=[dict(zip(tables[0]['headers'],r)) for r in tables[0]['rows']]
 years=sorted({int(r['연도']) for r in rows},reverse=True)[:3];out=defaultdict(float)
 for year,w in zip(years,(1,.6,.35)):
  rs=[r for r in rows if int(r['연도'])==year]
  totals=[r for r in rs if r.get('팀명') in ('합계','통산')]
  for row in (totals or rs):
   for k,v in row.items():
    if k not in ('연도','팀명'):out[k]+=(innings(v) if k=='IP' else num(v))*w
 return dict(out),years[0]

# 입단 전 스카우팅 자료에 명시된 구종과 구속. 등급(구위/변화량/제구)은 게임용 추정.
SCOUT={
 'WO:와일스':(154,'포심 커터 체인지업 슬라이더',4,5,'와일스'),
 'SS:오러클린':(153,'포심 슬라이더 커브 체인지업',4,3,'오러클린'),
 'SS:매닝':(156,'포심 슬라이더 커브 커터 스플리터',5,3,'매닝'),
 'KT:보쉴리':(152,'포심 투심 커터 슬라이더 체인지업 커브',4,5,'보쉴리'),
 'KT:사우어':(156,'포심 커터 투심 슬라이더 커브 스플리터',5,4,'사우어'),
 'LT:로드리게스':(157,'포심 커터 커브 슬라이더 체인지업',5,4,'로드리게스'),
 'LT:비슬리':(158,'포심 투심 커터 슬라이더 스플리터',5,4,'비슬리'),
 'HH:화이트':(155,'포심 투심 슬라이더 커터 체인지업 커브',5,3,'화이트'),
 'HH:에르난데스':(156,'투심 슬라이더 체인지업',5,4,'에르난데스'),
 'SK:베니지아노':(156,'포심 투심 슬라이더 체인지업',5,3,'베네지아노'),
 'NC:테일러':(156,'포심 투심 슬라이더 체인지업 커터',5,4,'테일러'),
}
EXTERNAL={
 'SS:장찬희':(148,'포심 슬라이더 체인지업 포크 커브',4,3,'https://v.daum.net/v/20251217125458725'),
 'LT:박정민':(152,'포심 슬라이더 커브 체인지업',4,3,'https://m.mk.co.kr/amp/11423062'),
 'NC:원종해':(144,'포심 체인지업 커브',3,4,'https://www.mk.co.kr/news/sports/11244227'),
 'OB:플렉센':(152,'포심 커브 커터',5,4,'https://member.newspim.com/news/view/20251218000650'),
 'LT:쿄야마':(155,'포심 스플리터',4,4,'https://v.daum.net/v/20251212152713924'),
 'KT:박지훈':(154,'포심 슬라이더 체인지업',4,3,'https://sports.donga.com/sports/article/all/20260130/133265220/1'),
 'SS:미야지':(158,'포심 스플리터 슬라이더 커브',5,3,'https://www.koreabaseball.com/MediaNews/News/KboPhoto/View.aspx?bdSe=515360'),
 'KT:스기모토':(154,'포심 슬라이더 커터 커브 포크',4,4,'https://note.com/tokushima_indigo/n/n4714eaf8c496'),
 'NC:토다':(150,'포심 투심 포크 슬라이더 커브 커터',4,5,'https://view.asiae.co.kr/article/2025121109473315323'),
 'HH:왕옌청':(154,'포심 슬라이더 체인지업 커브 스플리터',4,4,'https://v.daum.net/v/YbTUmefzGx'),
 'WO:유토':(150,'포심 포크 슬라이더',4,4,'https://cb.yna.co.kr/gate/big5/cn.yna.co.kr/view/AKR20251123020400007'),
 'OB:타무라':(150,'포심 포크 커브 커터',4,4,'https://siri.or.kr/2025/12/두산-새-아시아쿼터로-npb-베테랑-우완-타무라-이치로/'),
}
# 신규 외국인 타자: 2025 AAA 성적/스카우팅을 국내 게임 척도로 보수적으로 환산.
BATTERS={
 'WO:브룩스':(64,58,72,55,62,'브룩스'),
 'KT:힐리어드':(64,49,85,78,81,'힐리어드'),
 'HT:카스트로':(72,66,75,58,64,'카스트로'),
 'OB:카메론':(60,69,83,74,78,'카메론'),
}
def arsenal_table():
 # 2026 정규시즌 구종 집계를 우선하고, 없을 때만 2025 집계를 쓴다(선수당 1건).
 a25=read(D/'arsenals.json');a26=read(D/'arsenals_2026.json') if (D/'arsenals_2026.json').exists() else {}
 have={(norm(x['name']),x['birth']) for x in a26.values()}
 out={'2026:'+k:v for k,v in a26.items()}
 out.update({'2025:'+k:v for k,v in a25.items() if (norm(v['name']),v['birth']) not in have})
 return out
def defense_rows():
 # 선수별로 2026 수비 기록이 있으면 2026만, 없으면 2025를 사용한다.
 d25=read(D/'defense_2025.json');d26=read(D/'defense_2026.json') if (D/'defense_2026.json').exists() else []
 ids={r['player_id'] for r in d26}
 return d26+[r for r in d25 if r['player_id'] not in ids]
def has2026(source):
 return any(r[0]=='2026' for t in source.get('seasons',[]) for r in t['rows'])
def main():
 identities=read(D/'identities.json');stats=read(D/'stats.json');arsenals=arsenal_table()
 older=read(D/'older_arsenals.json') if (D/'older_arsenals.json').exists() else {}
 opening=read(D/'opening.json');defense=defense_rows();bydef=defaultdict(list)
 for row in defense:bydef[row['player_id']].append(row)
 from kbo_team_layout import STARTERS,ROTATIONS,CLOSERS
 result={'schema':1,'cutoff':'2026-10-03 정규시즌 종료 1군 등록','stats_cutoff':2026,
 'method':'2026 정규시즌 포함 최근 3시즌 가중(1/.6/.35), 타격 120타수/투구 25이닝 사전분포. 구종별 2026 구사율·헛스윙률·구속(없으면 2025). 수비 2026 포지션별 이닝·실책(없으면 2025). 수치는 게임용 추정이며 공식 KBO 능력치가 아님.',
 'opening_source':'https://www.koreabaseball.com/Player/Register.aspx','teams':{}}
 seen=set()
 for code,players in identities.items():
  rows=[];openids={p['player_id'] for p in opening[code]};indices={p['player_id']:p['index'] for p in players}
  assert len(openids)==29 and openids<=indices.keys(),code
  for p in players:
   pid=p['player_id'];assert pid not in seen,(code,p['name'],pid);seen.add(pid)
   st,year=aggregate(stats[pid]);key=code+':'+p['name'];cat=p['category'];estimated=[]
   a=dict(trajectory=0,contact_r=15,contact_l=15,power=20,speed=45,arm=60,catching=55,throwing=55,recovery=60,stamina=0,starter=0,reliever=0,closer=0)
   src=[stats[pid]['stats_url']];pitchlist=[];vel=120;pitchbasis='야수';df=bydef[pid]
   realdef=[r for r in df if POS.get(r['POS_SC']) in {'P':{'P'},'C':{'C'},'IF':{'1B','2B','3B','SS'},'OF':{'LF','CF','RF'}}[cat]]
   if cat=='P':
    ip=st.get('IP',0);g=st.get('G',0);k9=9*(st.get('SO',0)+21)/(ip+25);bb9=9*(st.get('BB',0)+9)/(ip+25)
    starter=ip/max(1,g)>=2.8 or p['name'] in ROTATIONS[code]
    a.update(starter=7 if starter else 1,reliever=4 if starter else 7,closer=7 if p['name']==CLOSERS[code] else 3 if st.get('SV',0)>=5 else 0,
       stamina=clamp(57+ip/max(g,1)*5,65,88) if starter else clamp(34+ip/max(g,1)*8,40,62),
       recovery=clamp(57+min(140,g)*.24,57,88),arm=68)
    stuff=clamp(2+k9*.35,2,6);control=clamp(7-bb9*.65,2,6)
    matches=[x for x in arsenals.values() if norm(x['name'])==norm(p['name']) and x['birth']==p.get('birth')]
    if not matches and older.get(pid,{}).get('available'):
     previous=older[pid];profile=previous['profile'];mix={q['pitch_type']:q for q in profile['mix']}
     aq=[]
     for q in profile['usageVelo']:
      m=mix.get(q['pitch_type'],{})
      aq.append(dict(name=q['pitch_type'],n=q['pct'],pct=q['pct'],avg_spd=q['avg_speed'],whiff=m.get('whiff_pct',0),max_speed=m.get('max_speed',0)))
     if aq:matches=[dict(source=previous['source'],arsenal=aq,year=previous['year'])]
    if len(matches)==1:
     ar=matches[0];src.append(ar['source']);pitchbasis=str(ar['year'])+' 구종 집계'
     qlist=sorted(ar['arsenal'],key=lambda x:-x['n']);used=Counter();names=set()
     fast=[q['avg_spd'] for q in qlist if q['name'] in ('포심','직구','투심','싱커') and q['avg_spd']]
     vel=clamp((max(fast) if fast else max(q['avg_spd'] for q in qlist))+5,130,163)
     measured=[q.get('max_speed',0) or 0 for q in qlist if q['name'] in ('직구','포심','투심','싱커')]
     if measured and max(measured)>125:vel=clamp(max(measured),130,163)
     else:estimated.append('최고구속: '+str(ar['year'])+' 패스트볼 평균+5km/h 환산')
     for q in qlist:
      name=PMAP.get(q['name'],q['name'])
      if name=='기타':continue
      if name not in PITCHES:raise ValueError(name)
      if name in names or used[PITCHES[name][1]]>=2:continue
      if q['pct']<1 and len(pitchlist)>=3:continue
      names.add(name);used[PITCHES[name][1]]+=1
      if q['name'] in ('너클볼','스크루볼'):estimated.append('희귀 구종을 PSP 유사 구종으로 대응: '+q['name'])
      pitchlist.append(dict(name=name,**{'break':0 if name in ('포심','투심') else clamp(2+num(q.get('whiff'))/12,2,6),
        'stuff':clamp(stuff*.6+(2+num(q.get('whiff'))/11)*.4,2,6),'control':control},usage_pct=q['pct']))
    elif key in SCOUT or key in EXTERNAL:
     vel,names,stuff,control,ref=(SCOUT|EXTERNAL)[key]
     if key in SCOUT:ref=(D/'scout'/f'{ref}.txt').read_text('utf8').splitlines()[0]
     src.append(ref);pitchbasis='입단 전 영입/스카우팅 자료'
     pitchlist=[dict(name=n,**{'break':0 if n in ('포심','투심') else 4,'stuff':stuff,'control':control}) for n in names.split()]
     if key in SCOUT:a.update(starter=7,reliever=4,stamina=76,recovery=72)
     elif key in ('HH:왕옌청','NC:토다'):a.update(starter=7,reliever=5,stamina=72,recovery=70)
    else:
     # 공개 구종이 확보되지 않은 선수는 명시적 추정. 일본 슬롯/빈 구종의 상속은 금지.
     prior=p.get('pitches') or p.get('ratings',{}).get('pitches')
     priorv=p.get('velocity',p.get('ratings',{}).get('velocity',0))
     if prior and priorv>125:
      pitchlist=[dict(q) for q in prior];vel=priorv;pitchbasis='기존 선수별 추정 명세(구종 미확인)'
     else:
      vel=145;pitchlist=[dict(name='포심',**{'break':0,'stuff':stuff,'control':control}),dict(name='슬라이더',**{'break':3,'stuff':stuff,'control':control})]
      pitchbasis='자료 미확보: 임시 게임용 구종'
     estimated.extend(['구종 구성 미확인','구속 미확인'])
    a['arm']=clamp(55+(vel-135)*1.4,50,90)
    fielding={'P':clamp(55+min(ip,180)*.06,55,70)}
   else:
    ab=st.get('AB',0);h=st.get('H',0);tb=st.get('TB',0);g=st.get('G',0)
    avg=(h+31.2)/(ab+120);iso=(tb-h+15.6)/(ab+120);hrr=(st.get('HR',0)+2.4)/(ab+120)
    contact=clamp(60+(avg-.260)*430,32,92);power=clamp(32+iso*170+hrr*350,32,94)
    speed=clamp(46+math.sqrt(st.get('SB',0)/max(g,35))*67+st.get('3B',0)/max(g,35)*80,38,88)
    a.update(contact_r=contact,contact_l=contact,power=power,speed=speed,arm=63,catching=60,throwing=60,
      recovery=clamp(56+min(g,150)*.19,56,87),trajectory=4 if power>=72 else 3 if power>=53 else 2)
    estimated.append('대좌/대우 컨택: 통합 타율 기준(상대 손별 기록 미확보)')
    if not st:estimated.append('타격 기록 없음: 신인/미출장 선수 중립 사전분포')
    if key in BATTERS and not has2026(stats[pid]):
     cr,cl,powr,spd,arm,ref=BATTERS[key];a.update(contact_r=cr,contact_l=cl,power=powr,speed=spd,arm=arm,trajectory=4,recovery=76)
     src.append((D/'scout'/f'{ref}.txt').read_text('utf8').splitlines()[0]);estimated.append('신규 외국인: 해외 성적과 스카우팅의 게임용 환산')
    fielding={}
    if realdef:
     for r in realdef:
      pos=POS[r['POS_SC']];ip=innings(r['DEFEN_INN2_CN']);ch=num(r['PO_CN'])+num(r['ASS_CN'])+num(r['ERR_CN']);err=num(r['ERR_CN'])
      # 포구율은 범위와 다르므로 실책 영향은 +-6으로 제한한다.
      expected={'C':.008,'1B':.006,'2B':.016,'3B':.030,'SS':.025,'LF':.015,'CF':.012,'RF':.015}.get(pos,.02)
      sure=clamp((expected-(err+expected*80)/(ch+80))*300,-6,6)
      rate=clamp(52+min(ip,1150)/1150*23+sure+(speed-55)*.12,45,90)
      fielding[pos]=max(fielding.get(pos,0),rate)
     main=max(realdef,key=lambda r:innings(r['DEFEN_INN2_CN']))
     mainpos=POS[main['POS_SC']];ch=num(main['PO_CN'])+num(main['ASS_CN'])+num(main['ERR_CN']);err=num(main['ERR_CN'])
     expected={'C':.008,'1B':.006,'2B':.016,'3B':.030,'SS':.025,'LF':.015,'CF':.012,'RF':.015}[mainpos]
     sure=clamp((expected-(err+expected*80)/(ch+80))*300,-6,6)
     ip=innings(main['DEFEN_INN2_CN']);a['catching']=clamp(55+min(ip,1000)*.015+sure,48,85);a['throwing']=clamp(55+min(ip,1000)*.014,52,80)
     if cat=='C':a['arm']=clamp(60+(num(main['CS_RT'])-25)*.6,50,85)
     src.append('https://www.koreabaseball.com/Record/Player/Defense/Basic.aspx [%s]'%max(r['year'] for r in realdef))
    else:
     old=p.get('fielding',{});fielding={k:v for k,v in old.items() if v>0 and k!='P'}
     if not fielding:fielding={'C':{'C':55},'IF':{'1B':52,'2B':48,'3B':48,'SS':45},'OF':{'LF':55,'CF':50,'RF':55}}[cat]
     estimated.append('2025·2026 수비 출장 없음: 기존 개별 포지션 또는 그룹 추정')
    # 2026 시즌 종료 기준 기본 선발 포지션에 대한 적성은 반드시 있어야 한다.
    for name,pos in STARTERS[code]:
     if norm(name)==norm(p['name']) and pos!='DH':fielding[pos]=max(fielding.get(pos,0),60)
   estimated.append('게임용 능력 등급 환산; 실측 공식 능력치 아님')
   group={'P':['P'],'C':['C'],'IF':['1B','2B','3B','SS'],'OF':['LF','CF','RF']}[cat]
   # 주 포지션은 KBO 등록 포지션군 안에서 정한다. 다른 군 수비 적성은 그대로 유지.
   if not any(k in group for k in fielding):
    fielding[group[0]]=40;estimated.append('등록 포지션군 수비 기록 없음: 최소 적성 부여')
   defaultpos=max([k for k in fielding if k in group],key=fielding.get)
   primary=PORDER.index(defaultpos)
   # 등록 카테고리와 주 수비 위치 일치 보장.
   assert primary in {'P':{0},'C':{1},'IF':{2,3,4,5},'OF':{6,7,8}}[cat],(code,p['name'],primary)
   rows.append(dict(index=p['index'],name=p['name'],player_id=pid,birth=p.get('birth'),category=cat,primary_position=primary,
      opening_entry=pid in openids,abilities=a,fielding=fielding,velocity=vel,pitches=pitchlist,
      last_stat_year=year,pitch_basis=pitchbasis,sources=src,estimated_fields=estimated,
      official_stats_sha256=stats[pid]['sha256']))
  result['teams'][code]={'players':rows,'opening_indices':[indices[p['player_id']] for p in opening[code]],'opening_player_ids':[p['player_id'] for p in opening[code]]}
 assert len(seen)==619
 # 원본 PSP의 비선형 구종 평가 및 팀 전력 척도에 맞춘 최종 환산.
 from recalibrate_team_strength import recalibrate
 result=recalibrate(result)
 # KBO 1군을 원본 1군 척도 상단에 맞춘다(V3).
 from realism_scale_2026 import rescale
 result=rescale(result)
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
 print('완전 명세',len(seen),'개막 등록',sum(len(t['opening_indices']) for t in result['teams'].values()))
 print('구종 근거',dict(Counter(p['pitch_basis'] for t in result['teams'].values() for p in t['players'] if p['category']=='P')))
if __name__=='__main__':main()
