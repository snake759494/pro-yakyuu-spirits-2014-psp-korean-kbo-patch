"""2026 KBO 개막일 등록 명단과 공개 기록으로 10구단의 1군·코칭 슬롯 명세를 만든다."""
import concurrent.futures, json, re, sys, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from player_fields import get

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'work/kbo_roster_research/20260328'
OUT=ROOT/'translation/kbo_2026'
TEAM_IDS={'LG':0,'SS':1,'HT':2,'WO':3,'KT':4,'LT':5,'HH':6,'OB':7,'SK':8,'NC':9}
TEAM_NAMES={'LG':'LG 트윈스','SS':'삼성 라이온즈','HT':'KIA 타이거즈','WO':'키움 히어로즈','KT':'KT 위즈','LT':'롯데 자이언츠','HH':'한화 이글스','OB':'두산 베어스','SK':'SSG 랜더스','NC':'NC 다이노스'}

def records(code):
    d=json.loads((DATA/f'{code}.json').read_text('utf8')); out=[]
    for table in d['tables']:
        if len(table['headers'])<5: continue
        category=table['headers'][1]
        for row in table['rows']:
            c=row['cells']; href=(row.get('player_links') or [''])[0]
            if len(c)<5 or 'playerId=' not in href or c[1] in ('당일 1군 등록된 선수가 없습니다.','당일 1군 말소된 선수가 없습니다.'): continue
            pid=re.search(r'playerId=(\d+)',href).group(1)
            kind='coach' if category in ('감독','코치') else 'player'
            position={'투수':'P','포수':'C','내야수':'IF','외야수':'OF'}.get(category)
            hand=c[2]
            height,weight=map(int,re.findall(r'\d+',c[4]))
            out.append(dict(name=c[1],kind=kind,role=category,category=position,number=c[0],hands=hand,birth=c[3],height=height,weight=weight,player_id=pid,profile=href))
    return out

def get_stats(p):
    kind='PitcherDetail' if p['category']=='P' else 'HitterDetail'
    url=f"https://www.koreabaseball.com/Record/Player/{kind}/Total.aspx?playerId={p['player_id']}"
    try:
        r=requests.get(url,timeout=45);r.raise_for_status();r.encoding='utf8';s=BeautifulSoup(r.text,'html.parser');tables=[]
        for t in s.select('table'):
            head=[x.get_text(' ',strip=True) for x in t.select('thead th')]
            if not head or head[0]!='연도':continue
            rows=[]
            for tr in t.select('tbody tr'):
                cells=[x.get_text(' ',strip=True) for x in tr.select('td')]
                if cells and re.fullmatch(r'20\d\d',cells[0]) and int(cells[0])<=2025:rows.append(cells)
            if rows:tables.append(dict(headers=head,rows=rows))
        return p['player_id'],dict(stats_url=url,through_2025=tables)
    except Exception as e:return p['player_id'],dict(stats_url=url,through_2025=[],stats_error=str(e))

def rating(p,stats):
    tables=stats.get('through_2025',[])
    if not tables:return {}
    t=next((x for x in tables if x['headers'][0]=='연도'),tables[0]);rows=[dict(zip(t['headers'],r)) for r in t['rows']]
    if not rows:return {}
    year=max(int(x['연도']) for x in rows);latest=[x for x in rows if int(x['연도'])==year]
    s=next((x for x in latest if x.get('팀명')=='합계'),latest[-1])
    def num(k):
        try:return float(s.get(k,'0').replace(',',''))
        except:return 0.
    clamp=lambda x,a,b:max(a,min(b,round(x)))
    if p['category']=='P':
        ip=sum(float(x.split('/')[0])/float(x.split('/')[1]) if '/' in x else float(x) for x in s.get('IP','0').split())
        bb=num('BB');so=num('SO');control=clamp(7-9*(bb+12)/(ip+30)*.75,2,6);stuff=clamp(1+9*(so+24)/(ip+30)*.45,2,6)
        return dict(contact_r=12,contact_l=12,power=18,speed=40,arm=60,catching=45,throwing=48,recovery=65,stamina=clamp(52+ip*.12,55,78),starter=7,reliever=4,closer=0,trajectory=0,velocity=120,pitches=[dict(name='포심',**{'break':0,'stuff':stuff,'control':control}),dict(name='슬라이더',**{'break':3,'stuff':stuff,'control':control})],rating_year=year)
    ab=num('AB');h=num('H');hr=num('HR');tb=num('TB');g=num('G');sb=num('SB')
    avg=(h+52)/(ab+200);iso=(tb-h+22)/(ab+200);hrr=(hr+4)/(ab+200)
    return dict(contact_r=clamp(55+400*(avg-.260),30,88),contact_l=clamp(55+400*(avg-.260),30,88),power=clamp(28+550*hrr+120*iso,30,88),speed=clamp(48+160*sb/max(g,40),35,82),arm=58,catching=55,throwing=55,recovery=clamp(50+g*.23,50,84),stamina=0,starter=0,reliever=0,closer=0,trajectory=3,rating_year=year)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    allrows={t:records(t) for t in TEAM_IDS}
    # Cache official stats by KBO player ID, so same-name and multi-team players remain distinct.
    cachepath=OUT/'official_stats_cache.json';cache=json.loads(cachepath.read_text('utf8')) if cachepath.exists() else {}
    if '--stats' in sys.argv:
        todo={p['player_id']:p for rows in allrows.values() for p in rows if p['kind']=='player' and p['player_id'] not in cache}
        limit=int(sys.argv[sys.argv.index('--stats')+1]) if sys.argv.index('--stats')+1<len(sys.argv) and sys.argv[sys.argv.index('--stats')+1].isdigit() else 20
        # Rate-limit to a single official site request at a time; persist each page promptly.
        for p in list(todo.values())[:limit]:
            pid,result=get_stats(p);cache[pid]=result
            cachepath.write_text(json.dumps(cache,ensure_ascii=False,indent=2),'utf8')
            print('stats',pid,'ok' if result.get('through_2025') else 'empty')
            time.sleep(.25)
    cachepath.write_text(json.dumps(cache,ensure_ascii=False,indent=2),'utf8')
    # Original game record groups are role-sequenced; preserve each player ID and voice key.
    sys.path.insert(0,str(ROOT/'tools'))
    from analyze import chunks
    pd={n:b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())}['PDN']
    for code,teamid in TEAM_IDS.items():
        rows=allrows[code]
        players=[p for p in rows if p['kind']=='player']
        coaches=[p for p in rows if p['kind']=='coach']
        # Select distinct player entries and preserve the original player ID/voice key.
        indices=[i for i in range(len(pd)//192) if pd[i*192+90]&63==teamid]
        assignments=[]
        src=[p for p in players if p['role']=='투수']+[p for p in players if p['role']!='투수']
        for i,p in zip(indices,src):
            stats=cache.get(p['player_id'],{})
            info={**stats,**rating(p,stats)}
            assignments.append(dict(index=i,**p,**info))
        spec=dict(team_id=teamid,code=code,name=TEAM_NAMES[code],cutoff='2026-03-28',source='https://www.koreabaseball.com/Player/Register.aspx',source_file=f'work/kbo_roster_research/20260328/{code}.html',registered_players=len(players),coaches=len(coaches),assigned_players=len(assignments),records=assignments,coaching=coaches,limitations=['KBO 공식 개막일 1군 등록 선수만 선수 레코드에 반영. 등록 2군 외 후보 명단은 포함하지 않음.','선수 능력은 2025년 이전 공식 시즌 기록을 게임용 산식으로 환산하며, 2026 개막 이후 기록은 제외.','게임 슬롯 인원 및 선수 ID·음성 키는 보존. 포지션별 게임 슬롯 수가 1군 인원보다 적으면 뒤 순번은 적용 제외.','외모·얼굴·음성·모션·유니폼의 선수별 성명은 별도 외형 변환 대상.'])
        (OUT/f'{code}.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),'utf8')
        print(code,'player',len(players),'coach',len(coaches),'assigned',len(assignments),'missing_stats',sum(not x.get('through_2025') for x in assignments))

if __name__=='__main__':main()
