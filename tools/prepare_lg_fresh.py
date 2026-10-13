"""기존 LG 매핑/능력치 JSON을 읽지 않고 공식 원문과 원본 게임으로 재작성."""
import json,struct,re
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
from analyze import chunks
from prepare_kbo_teams import records
from player_fields import get
ROOT=Path(__file__).resolve().parents[1]
STARTERS=[('홍창기','RF'),('신민재','2B'),('오스틴','1B'),('문보경','DH'),('박동원','C'),('문성주','LF'),('오지환','SS'),('구본혁','3B'),('박해민','CF')]
ROTATION=['치리노스','톨허스트','임찬규','웰스','이정용']
RELIEF=['함덕주','우강훈','이우찬','배재준','김영우']
SETUP=['김진성','장현식']
CLOSER='유영찬'
STAFF=[(99,'염경엽','감독'),(594,'김광삼','투수코치'),(3,'모창민','타격코치'),(180,'김일경','수비코치'),(35,'송지만','주루/외야수비코치')]
POS={'P':0,'C':1,'1B':2,'2B':3,'3B':4,'SS':5,'LF':6,'CF':7,'RF':8}
# 공식 그룹에서 세부 수비를 확정하지 못한 예비 선수는 그룹 기본 위치로 표시한다.
DETAIL={'문보경':'3B','구본혁':'SS','문정빈':'1B','김성진':'1B','신민재':'2B','오스틴':'1B','오지환':'SS','이영빈':'SS','천성호':'3B','문성주':'LF','홍창기':'RF','박해민':'CF','이재원':'LF','송찬의':'RF','최원영':'CF'}
def main():
 rows=list(load_workbook(ROOT/'work/lg_rebuild/official_roster.xlsx',data_only=True)['L-한'].iter_rows(values_only=True))
 assert rows[0][3]=='LG 트윈스'
 end=next(i for i,r in enumerate(rows) if r[3]=='한화 이글스')
 source=[]
 for col,initial in [(3,None),(6,'P')]:
  category=initial
  for r in rows[2:end]:
   if r[col] in ('투수','포수','내야수','외야수'):category={'투수':'P','포수':'C','내야수':'IF','외야수':'OF'}[r[col]]
   if category and isinstance(r[col+1],str):source.append(dict(name=r[col+1].strip(),category=category,note=r[col+2] or ''))
 assert Counter(p['category'] for p in source)=={'P':36,'C':4,'IF':12,'OF':11}
 assert len({p['name'] for p in source})==63
 opening=records('LG');identity={p['name']:p for p in opening}
 identity['웰스']=dict(player_id='55348',birth='1997-02-27',height=185,weight=83,hands='좌투좌타',profile='https://www.koreabaseball.com/Record/Player/PitcherDetail/Basic.aspx?playerId=55348')
 pd={n:b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())}['PDN']
 staff_indices={x[0] for x in STAFF}
 available=[i for i in range(len(pd)//192) if pd[i*192+90]&63==0 and i not in staff_indices and pd[i*192+110]!=0]
 assert len(available)==63,len(available)
 original_lg=set(available)
 used=set()
 for path in (ROOT/'translation/kbo_2026').glob('*.json'):
  if path.stem!='LG':used.update(p['index'] for p in json.loads(path.read_text('utf8')).get('records',[]))
 used.update(p['index'] for p in json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))['records'])
 spare_pitchers=[]
 for i in range(len(pd)//192):
  r=pd[i*192:(i+1)*192]
  if i not in used and r[90]&63==31 and r[110] and r[168]&0x78==0 and 30<=get(r,'stamina')<=70 and 140<=get(r,'velocity_raw')+80<=155:
   spare_pitchers.append(i)
 # Prefer original role-compatible slots. No index is obtained from old LG JSON.
 def origpos(i):return (pd[i*192+168]&0x78)>>3
 activepitch=ROTATION+RELIEF+SETUP+[CLOSER]
 activebat=[p['name'] for p in opening if p['kind']=='player' and p['category']!='P']
 assert len(activepitch)==13 and len(activebat)==15
 priorities=activepitch+[n for n,pos in STARTERS]+activebat
 source.sort(key=lambda p:(priorities.index(p['name']) if p['name'] in priorities else 100, p['category'],p['name']))
 result=[]
 for p in source:
  group=p['category'];allowed={'P':{0},'C':{1},'IF':{2,3,4,5},'OF':{6,7,8}}[group]
  primary=POS.get(DETAIL.get(p['name']),{'P':0,'C':1,'IF':2,'OF':6}[group])
  compatible=[i for i in available if origpos(i) in allowed]
  borrowed=group=='P' and not compatible
  index=spare_pitchers.pop(0) if borrowed else next((i for i in compatible if origpos(i)==primary),compatible[0] if compatible else available[0])
  if not borrowed:available.remove(index)
  q=dict(index=index,name=p['name'],kind='player',category=group,primary_position=primary,foreign=p['note'] in ('외국인','아시아쿼터'),source_note=p['note'],source='KBO 2026-02-10 공식 명단 직접 재파싱',opening_entry=p['name'] in activepitch+activebat)
  if borrowed:q['borrowed']=True
  q.update({k:v for k,v in identity.get(p['name'],{}).items() if k in ('player_id','birth','height','weight','hands','number','profile')})
  # 원본 능력값을 보존하되 투타 적성만 독립적으로 정리한다.
  result.append(q)
 for index,name,role in STAFF:
  q=dict(index=index,name=name,kind='coach',role='감독' if role=='감독' else '코치',assignment=role,source='2026 LG 코칭스태프 보직 발표')
  q.update({k:v for k,v in identity[name].items() if k in ('player_id','birth','height','weight','hands','number','profile')})
  result.append(q)
 spec=dict(team_id=0,code='LG',name='LG 트윈스',cutoff='2026-03-28',rebuild='LG_FRESH_20261011',records=result,assigned_players=63,assigned_staff=5,registered_players=63,vacated_indices=[],borrowed_indices=[],fresh_layout=dict(rotation=ROTATION,relief=RELIEF,setup=SETUP,closer=CLOSER,batting=STARTERS,active_batters=activebat),limitations=['기존 LG 매핑/타순/능력치 JSON을 입력으로 쓰지 않았다. 원본 게임 레코드와 새 공식 명단으로 재작성했다.','원본 게임 능력값을 보존하므로 실제 2026 능력치 전체 재현은 아니다. 투수/야수 적성·주 포지션·보직은 별도로 정리한다.','1군 28명 한도에 맞춰 투수13/야수15. 외국인4명 모두 1군. 개막일 등록명단에서 박시원·백승현을 2군으로 두고 웰스를 추가했다.'])
 spec['borrowed_indices']=[p['index'] for p in result if p.get('borrowed')]
 spec['vacated_indices']=sorted(original_lg-{p['index'] for p in result})
 spec['limitations'].append('원본 LG의 투수 슬롯 부족분은 다른 KBO 팀이 사용하지 않는 원본 투수 슬롯을 사용했다. 이들의 원본 투수 능력·구종·ID는 보존하고, 비게 된 LG 야수 슬롯은 자유선수 풀로 이동했다.')
 (ROOT/'translation/kbo_2026/LG.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n','utf8')
 print('LG 새 매핑: 선수63, 스태프5, 1군 투수13/야수15, 외국인4')
if __name__=='__main__':main()
