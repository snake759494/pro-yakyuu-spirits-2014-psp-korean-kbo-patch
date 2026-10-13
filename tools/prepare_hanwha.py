"""공식 자료와 개막 전 평가를 게임용 선수 명세로 변환한다. 외부 번역 없음."""
from pathlib import Path
import json,re,requests,struct,sys
from bs4 import BeautifulSoup
from analyze import chunks
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'work/hanwha_research'
def bounded(x,lo,hi):return max(lo,min(hi,round(x)))
def innings(s):
 return sum(float(a.split('/')[0])/float(a.split('/')[1]) if '/' in a else float(a) for a in s.split())
def stats(p):
 tables=p.get('through_2025',[])
 if not tables:return {},'프로 성적 부족: 보수적 기본값'
 t=tables[0];rs=[dict(zip(t['headers'],r)) for r in t['rows']]
 latest=max(int(r['연도']) for r in rs);selected=[r for r in rs if int(r['연도'])==latest]
 r=next((r for r in selected if r['팀명']=='합계'),selected[-1])
 return r,f'KBO {latest} 정규시즌; 소표본은 기본값으로 수축'
def hitter(p):
 s,note=stats(p);ab=float(s.get('AB',0));h=float(s.get('H',0));hr=float(s.get('HR',0));tb=float(s.get('TB',0));g=float(s.get('G',0));sb=float(s.get('SB',0))
 avg=(h+52)/(ab+200);iso=(tb-h+22)/(ab+200);hrr=(hr+4)/(ab+200)
 return dict(contact_r=bounded(55+400*(avg-.260),30,88),contact_l=bounded(55+400*(avg-.260),30,88),
  power=bounded(28+550*hrr+120*iso,30,88),speed=bounded(48+160*sb/max(g,40),35,82),
  arm=58,catching=55,throwing=55,recovery=bounded(50+g*.23,50,84),stamina=0,starter=0,reliever=0,closer=0),s,note
def pitcher(p,sp=False):
 s,note=stats(p);ip=innings(s.get('IP','0'));bb=float(s.get('BB',0));k=float(s.get('SO',0))
 bb9=9*(bb+12)/(ip+30);k9=9*(k+24)/(ip+30)
 control=bounded(7-bb9*.75,2,6);stuff=bounded(1+k9*.45,2,6)
 a=dict(contact_r=12,contact_l=12,power=18,speed=40,arm=60,catching=45,throwing=48,
  recovery=65,stamina=bounded(52+ip*.12,55,78) if sp else bounded(35+ip*.08,35,47),starter=7 if sp else 0,reliever=4 if sp else 7,closer=0)
 return a,s,note,control,stuff
def main():
 profiles=json.loads((D/'official_profiles.json').read_text('utf8'));by={p['listing']['NAME']:p for p in profiles}
 extras=json.loads((D/'extra_sources.json').read_text('utf8'))
 h=extras[0]['data']['result'];by['에르난데스']=dict(category='PC',listing=h,profile=h,source=extras[0]['url'])
 # 개막 이후 이적 선수는 현재 KBO 소속·등번호를 쓰지 않는다.
 opening=BeautifulSoup((D/'opening_register.html').read_text('utf8'),'html.parser');entry={}
 for tr in opening.select('table tbody tr'):
  tds=tr.select('td');a=tr.select_one('a[href*="playerId="]')
  if len(tds)>=5 and a:
   name=a.get_text(strip=True);entry[name]=dict(name=name,pcode=re.search('playerId=(\\d+)',a['href']).group(1),hand=tds[2].get_text(strip=True),birth=tds[3].get_text(strip=True),body=tds[4].get_text(strip=True))
 for name,number in [('손아섭',31),('하주석',16)]:
  e=entry[name];url='https://www.koreabaseball.com/Record/Player/HitterDetail/Total.aspx?playerId='+e['pcode'];r=requests.get(url,timeout=40);r.encoding='utf8';b=BeautifulSoup(r.text,'html.parser');tables=[]
  for t in b.select('table'):
   rows=[[x.get_text(' ',strip=True) for x in tr.select('td')] for tr in t.select('tbody tr')];rows=[r for r in rows if r and re.fullmatch('20\\d\\d',r[0]) and int(r[0])<=2025]
   if rows:tables.append(dict(headers=[x.get_text(' ',strip=True) for x in t.select('thead th')],rows=rows))
  by[name]=dict(category='OF' if name=='손아섭' else 'IF',listing={'NAME':name,'PCODE':e['pcode']},profile=dict(NAME=name,BACK_NUM=str(number),BIRTH=e['birth'],PITCH_HIT=e['hand'],HEIGHT=int(e['body'].split('cm')[0])),source=url,kbo_source=url,through_2025=tables)
 # 기존 62개 선수 ID를 그대로 유지하며 포지션별 인원은 새 명단으로 재구성한다.
 active={699:'에르난데스',584:'화이트',398:'류현진',440:'왕옌청',704:'문동주',507:'엄상백',21:'박상원',385:'조동욱',318:'김종수',258:'정우주',51:'주현상',459:'김서현',
  310:'최재훈',386:'허인서',753:'강백호',32:'심우준',241:'채은성',219:'하주석',462:'노시환',335:'이도윤',136:'황영묵',387:'오재원',658:'페라자',242:'문현빈',660:'이진영',164:'김태연',271:'손아섭',144:'장규현'}
 reserve_names='황준서 김민우 강재민 김도빈 원종혁 윤산흠 박준영 이상규 이민우 정이황 양수호 권민규 배민서 김범준 박재규 한서구 남지민 장유호 강건우 박준영68 이재원 박상언 권현 정민규 최원준 이지성 한지윤 박정현 최유빈 임종찬 권광민 유로결 이원석 최인호'.split()
 by['박준영68']=next(p for p in profiles if p['profile'].get('NAME')=='박준영' and p['profile'].get('BACK_NUM')=='68')
 by['박준영']=next(p for p in profiles if p['profile'].get('NAME')=='박준영' and p['profile'].get('BACK_NUM')=='96')
 d=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();cs={n:(o,b) for n,o,b in chunks(d)};pd=cs['PDN'][1]
 coaches={98:('김우석',822),137:('추승우',112),107:('김경문',862),108:('양상문',884),134:('김민호',923)}
 indices=[i for i in range(len(pd)//192) if pd[i*192+90]&63==6];reserved=[i for i in indices if i not in active and i not in coaches]
 assert len(reserved)==len(reserve_names)==34
 mapping=active|dict(zip(reserved,reserve_names));records=[]
 positions={'최재훈':{'C':74},'허인서':{'C':58},'장규현':{'C':52},'이재원':{'C':62},'박상언':{'C':57},'권현':{'C':43},
  '강백호':{'1B':43,'RF':35},'심우준':{'SS':78,'2B':60},'채은성':{'1B':62,'RF':40},'하주석':{'2B':66,'SS':62},'노시환':{'3B':65,'1B':42},'이도윤':{'2B':66,'SS':65,'3B':50},'황영묵':{'2B':65,'SS':58,'3B':50},
  '정민규':{'3B':47,'1B':45},'최원준':{'SS':48,'2B':45},'이지성':{'2B':48,'SS':43},'한지윤':{'1B':43,'3B':35},'박정현':{'SS':56,'2B':52},'최유빈':{'2B':53,'SS':48},
  '오재원':{'CF':65,'LF':56,'RF':55},'페라자':{'RF':52,'LF':49},'문현빈':{'LF':60,'CF':43,'2B':38},'이진영':{'RF':61,'LF':56,'CF':48},'김태연':{'RF':51,'LF':50,'1B':48,'3B':35},'손아섭':{'RF':46,'LF':44},
  '임종찬':{'RF':58,'LF':54,'CF':50},'권광민':{'RF':52,'LF':48},'유로결':{'CF':58,'RF':55,'LF':54},'이원석':{'CF':71,'RF':60,'LF':60},'최인호':{'LF':63,'RF':59,'CF':46}}
 # 구속은 아래 구단 영입 자료 확인값 외에는 개막 전 투구 유형에 맞춘 게임용 추정값.
 velo={'에르난데스':156,'화이트':155,'왕옌청':154,'양수호':153,'류현진':147,'문동주':160,'엄상백':153,'김서현':158,'정우주':157,'박상원':154,'주현상':151,'김종수':150,'조동욱':148,'황준서':147,'김민우':147,'강재민':145,'윤산흠':146,'김도빈':149,'원종혁':149,'박준영':151,'권민규':145,'남지민':154}
 reper={'류현진':['포심','커터','커브','체인지업'],'문동주':['포심','커브','슬라이더','스플리터'],'에르난데스':['투심','슬라이더','체인지업'],'화이트':['포심','커터','슬라이더','커브','체인지업'],'왕옌청':['포심','슬라이더','체인지업'],
  '엄상백':['포심','슬라이더','체인지업'],'김서현':['포심','슬라이더','체인지업'],'정우주':['포심','슬라이더','커브'],'박상원':['포심','슬라이더','포크'],'주현상':['포심','슬라이더','포크'],'강재민':['포심','슬라이더','체인지업'],'황준서':['포심','커브','스플리터'],'조동욱':['포심','슬라이더','체인지업']}
 sp={'류현진','문동주','에르난데스','화이트','왕옌청','엄상백','황준서','김민우','박준영','남지민'}
 for i,key in mapping.items():
  p=by[key];pr=p['profile'];n=pr['NAME'];is_pitch=p['category']=='PC';s={};pitches=[]
  if is_pitch:
   a,s,note,ctrl,stuff=pitcher(p,key in sp)
   if key in ('에르난데스','화이트','왕옌청'):a.update(stamina=70);ctrl=4;stuff=5;note='구단 공식 영입 발표의 2025 해외 성적과 스카우팅 설명을 반영한 수동 평가'
   if key=='류현진':ctrl=6;stuff=4
   if key=='김서현':a.update(closer=7,reliever=7)
   field={'P':55};v=velo.get(key,147)
   for q in reper.get(key,['포심','슬라이더','체인지업']):
    br=0 if q in ('포심','투심') else 3
    if key=='류현진' and q=='체인지업':br=5
    if key=='왕옌청' and q=='슬라이더':br=4
    if key in ('문동주','김서현','정우주') and q=='포심':stuff=6
    pitches.append(dict(name=q,**{'break':br},stuff=stuff,control=ctrl))
  else:
   a,s,note=hitter(p);field=positions[key];v=120
   if not s:a.update(contact_r=43,contact_l=43,power=38)
   elif float(s.get('AB',0))<40:a.update(contact_r=min(a['contact_r'],46),contact_l=min(a['contact_l'],46),power=min(a['power'],42))
   if key=='페라자':a.update(contact_r=67,contact_l=67,power=75,speed=58);note='구단 공식 발표: 2025 AAA .307/19홈런, 2024 KBO .275/24홈런을 함께 고려한 수동 평가'
   if key=='오재원':a.update(contact_r=48,contact_l=48,power=38,speed=76);note='신인: 1군 실적 없음. 보수적 타격과 중견수·주력 임시 평가'
   if key=='이원석':a['speed']=82
   if key=='심우준':a['speed']=75
   if key=='최재훈':a.update(catching=74,throwing=68,arm=63)
   if key=='노시환':a.update(arm=74,throwing=64)
   if key=='강백호':a.update(arm=75,catching=43,throwing=48)
  a['trajectory']=0 if is_pitch else 5 if key in ('노시환','강백호','페라자') else 4 if key=='채은성' else 3 if a['power']>=50 else 1
  hands=pr.get('PITCH_HIT','우투우타').replace('투','/').replace('타','').split('/')
  throw=1 if hands[0].startswith('좌') else 0;bat=2 if '양' in hands[-1] else 1 if '좌' in hands[-1] else 0
  bd=[int(v) for v in re.findall(r'\d+',pr['BIRTH'])];assert len(bd)==3,(key,bd)
  birth=f'{bd[0]:04}{bd[1]:02}{bd[2]:02}'
  records.append(dict(index=i,name=n,key=key,kind='player',category=p['category'],opening_entry=n in entry and re.sub('[^0-9]','',entry[n]['birth'])==birth,initial_active=i in active,number=pr['BACK_NUM'],birth=f'{birth[:4]}-{birth[4:6]}-{birth[6:]}',height=pr['HEIGHT'],throw_hand=throw,bat_hand=bat,
   foreign=key in ('에르난데스','화이트','왕옌청','페라자'),source=p['source'],stats_source=p.get('kbo_source'),stats=s,rating_basis=note,abilities=a,fielding=field,velocity=v,pitches=pitches,
   estimated_fields=['수비 적성','주력 보정','어깨','포구','송구','구종별 등급','구종 구성(외국인 공식 소개 외)','구속(공식 영입 발표 외)']))
 for i,(name,cid) in coaches.items():
  url=f'https://www.hanwhaeagles.co.kr/PL/CS/PLCS02.do?id={cid}';pr=requests.get(url,timeout=30).json()['result'];birth=re.sub('[^0-9]','',pr['BIRTH']);hands=pr['PITCH_HIT']
  records.append(dict(index=i,name=name,kind='coach',number=pr['BACK_NUM'],birth=f'{birth[:4]}-{birth[4:6]}-{birth[6:]}',height=pr['HEIGHT'],throw_hand=int(hands.startswith('좌')),bat_hand=int('좌타' in hands),source=url,role={98:'수비',137:'1루/외야',107:'감독',108:'투수',134:'타격'}[i]))
 assert len(records)==67 and sum(r['opening_entry'] for r in records if r['kind']=='player')==29
 out=dict(cutoff='2026-03-28',team_id=6,players=62,coaches=5,records=sorted(records,key=lambda r:r['index']),
  primary_sources=[r['url'] for r in json.loads((D/'news_sources.json').read_text('utf8'))],
  opening_source='https://www.koreabaseball.com/Player/Register.aspx',opening_date='20260328',opening_team='HH',
  limitations=['게임의 기존 62명 선수/5명 코칭 슬롯 유지. 전체 육성 선수와 모든 코칭 보직 확장 아님.','1군 기본 엔트리는 게임의 28명 구조. 개막 29명은 전원 선수단에 포함되나 일부는 2군 시작.','공식 능력치가 아닌 공개 기록 기반 자체 게임용 평가. 신인/소표본 및 구종 세부 평가는 추정.','외모, 얼굴 사진, 음성, 고유 모션은 원 게임 자산. 실제 선수 초상 재현 아님.','달력 연도는 기존 2014이며 한화 선수의 나이 계산만 2026 기준으로 보정한다. 생년월일은 실제 값이다.'])
 (ROOT/'translation/hanwha_2026.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8')
 print('확정',len(records),'명; 개막 엔트리 29명 포함')
if __name__=='__main__':main()
