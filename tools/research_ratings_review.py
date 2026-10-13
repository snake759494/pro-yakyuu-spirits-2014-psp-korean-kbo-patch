"""개막일 신원과 2025 이전 공식 기록을 다시 수집한다. 번역 서비스 없음."""
import json,re,time,hashlib,concurrent.futures
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from kbo_rosters import specs
import prepare_kbo_teams as reg
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'work/ratings_review';D.mkdir(exist_ok=True)
reg.DATA=D/'register/20260328'
NAMES={'LG':'LG','SS':'삼성','HT':'KIA','WO':'키움','KT':'KT','LT':'롯데','HH':'한화','OB':'두산','SK':'SSG','NC':'NC'}
CAT={'투수':'P','포수':'C','내야수':'IF','외야수':'OF'}
def norm(n):return re.sub(r'\([^)]*\)|\s','',n)
def cat(p):return {'PC':'P','CC':'C'}.get(p['category'],p['category'])
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def get(url,params=None):
 for attempt in range(3):
  try:
   r=requests.get(url,params=params,timeout=35);r.raise_for_status();r.encoding='utf8'
   assert '이용에 불편을 드려' not in r.text
   return r
  except Exception:
   if attempt==2:raise
   time.sleep(2+attempt)
def identity(task):
 code,p=task;p=dict(p);p['category']=cat(p);name=norm(p['name'])
 if p.get('player_id'):return code,p
 for key in ('stats_source','kbo_source','profile'):
  m=re.search(r'playerId=(\d+)',p.get(key) or '')
  if m:p['player_id']=m[1];return code,p
 path=D/'search'/f'{code}_{p["index"]}.html'
 if not path.exists():
  r=get('https://www.koreabaseball.com/Player/Search.aspx',{'searchWord':name});path.parent.mkdir(exist_ok=True);path.write_text(r.text,'utf8');time.sleep(.15)
 soup=BeautifulSoup(path.read_text('utf8'),'html.parser');candidates=[]
 for tr in soup.select('table tbody tr'):
  cells=[x.get_text(' ',strip=True) for x in tr.select('td')];a=tr.select_one('a[href*="playerId="]')
  if not a or len(cells)<6 or CAT.get(cells[3])!=p['category']:continue
  if norm(cells[1])!=name and not (code=='LT' and name=='김상수' and cells[1]=='김태혁'):continue
  if '/Retire/' in a['href']:continue
  candidates.append(dict(player_id=re.search(r'playerId=(\d+)',a['href'])[1],birth=cells[4],current_team=cells[2],profile='https://www.koreabaseball.com'+a['href'],number=cells[0]))
 matches=[q for q in candidates if q['current_team']==NAMES[code]]
 if p.get('birth'):matches=[q for q in candidates if q['birth']==p['birth']]
 if len(matches)!=1 and p.get('birth'):matches=[q for q in candidates if q['birth']==p['birth']]
 if not matches and len(candidates)==1:matches=candidates
 if len(matches)==1:p.update(matches[0]);p['identity_source']=str(path.relative_to(ROOT))
 else:p['identity_candidates']=candidates
 return code,p
def stats(p):
 pid=p['player_id'];kind='PitcherDetail' if p['category']=='P' else 'HitterDetail'
 url=f'https://www.koreabaseball.com/Record/Player/{kind}/Total.aspx?playerId={pid}'
 path=D/'stats'/f'{pid}.html';path.parent.mkdir(exist_ok=True)
 if not path.exists():r=get(url);path.write_text(r.text,'utf8');time.sleep(.15)
 text=path.read_text('utf8');soup=BeautifulSoup(text,'html.parser');tables=[]
 for table in soup.select('table'):
  h=[x.get_text(' ',strip=True) for x in table.select('thead th')]
  if not h or h[0]!='연도':continue
  rows=[]
  for tr in table.select('tbody tr'):
   cells=[x.get_text(' ',strip=True) for x in tr.select('td')]
   if cells and re.fullmatch(r'20\d\d',cells[0]) and int(cells[0])<=2026:rows.append(cells)
  if rows:tables.append(dict(headers=h,rows=rows))
 return pid,dict(stats_url=url,seasons=tables,through_2025=[dict(headers=t['headers'],rows=[r for r in t['rows'] if int(r[0])<=2025]) for t in tables],html=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),fetched_at=__import__('datetime').date.today().isoformat(),name=p['name'])
def main():
 source=specs();source['HH']=json.loads((ROOT/'translation/hanwha_2026.json').read_text('utf8'))
 opening={c:[p for p in reg.records(c) if p['kind']=='player'] for c in source};save(D/'opening.json',opening)
 tasks=[]
 for code,s in source.items():
  for p in s['records']:
   if p['kind']!='player':continue
   p=dict(p);o=[x for x in opening[code] if norm(x['name'])==norm(p['name']) and x['category']==cat(p)]
   if code=='SS' and p['index']==420:
    p={k:v for k,v in p.items() if k in ('index','kind','category','borrowed')};p['name']='홍원표';o=[]
   note=p.get('roster_source_note','');dob=re.search(r'(\d{4})\.\s*(\d+)\.\s*(\d+)',note)
   if dob:p['birth']='%04d-%02d-%02d'%tuple(map(int,dob.groups()))
   if p.get('birth'):o=[x for x in o if x['birth']==p['birth']]
   if '(좌)' in p['name']:o=[x for x in o if x['hands'].startswith('좌')]
   if '(우)' in p['name']:o=[x for x in o if x['hands'].startswith('우')]
   if len(o)==1:p.update({k:v for k,v in o[0].items() if k not in ('index','kind','name')})
   if code=='SS' and p['name']=='이승현(좌)':p['birth']='2002-05-19'
   tasks.append((code,p))
 result={c:[] for c in source}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  for i,(code,p) in enumerate(ex.map(identity,tasks),1):
   result[code].append(p)
   if i%25==0:save(D/'identities.json',result);print('신원',i,len(tasks),flush=True)
 save(D/'identities.json',result)
 missing=[(c,p['name'],p.get('identity_candidates')) for c,rs in result.items() for p in rs if not p.get('player_id')]
 save(D/'identity_unresolved.json',missing);print('신원 미확정',missing,flush=True)
 todo={p['player_id']:p for rs in result.values() for p in rs if p.get('player_id')};cache={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  for i,(pid,r) in enumerate(ex.map(stats,todo.values()),1):
   cache[pid]=r
   if i%20==0:save(D/'stats.json',cache);print('기록',i,len(todo),flush=True)
 save(D/'stats.json',cache);print('수집 완료',len(cache),flush=True)
if __name__=='__main__':main()
