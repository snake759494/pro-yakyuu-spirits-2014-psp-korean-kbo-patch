"""2025 미출장 투수의 마지막 2025 이전 공개 구종 집계를 KBO ID로 연결."""
import requests,json,time,concurrent.futures
from research_ratings_review import D,save,norm
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.yagoonara.com'
def request(url,**kw):
 time.sleep(6)
 r=requests.get(url,timeout=30,**kw)
 if r.status_code==429:
  raise RuntimeError('요청 제한: 중단 후 나중에 재개')
 r.raise_for_status();return r
def fetch(task):
 code,p=task;pid=p['player_id'];cache=D/'older_arsenal'/f'{pid}.json';cache.parent.mkdir(exist_ok=True)
 if cache.exists():return pid,json.loads(cache.read_text('utf8'))
 try:
  r=request(BASE+'/api/players',params={'page':1,'limit':20,'search':norm(p['name'])})
  candidates=[x for x in r.json()['data'] if str(x['kbo_id'])==pid]
  if len(candidates)!=1:return pid,{'error':'KBO ID 검색 불일치','name':p['name']}
  who=candidates[0];requested=p.get('last_stat_year') or 2025;url=BASE+f'/api/players/{who["id"]}/pitch-profile?season={requested}'
  r=request(url);profile=r.json().get('data') or {}
  seasons=[y for y in profile.get('seasons',[]) if isinstance(y,int) and y<=2025]
  if not seasons:out=dict(name=p['name'],player_id=pid,source=url,available=False)
  else:
   year=max(seasons)
   if year!=requested:
    url=BASE+f'/api/players/{who["id"]}/pitch-profile?season={year}';r=request(url);profile=r.json()['data']
   assert profile['season']==year
   out=dict(name=p['name'],player_id=pid,source=url,year=year,available=True,profile=profile)
  save(cache,out);return pid,out
 except Exception as e:return pid,dict(name=p['name'],error=str(e))
def main():
 m=json.loads((ROOT/'translation/kbo_2026/ratings_review.json').read_text('utf8'))
 todo=[(c,p) for c,t in m['teams'].items() for p in t['players'] if '미확' in p['pitch_basis'] and p.get('last_stat_year') and p['last_stat_year']>=2016]
 out=json.loads((D/'older_arsenals.json').read_text('utf8')) if (D/'older_arsenals.json').exists() else {}
 for i,task in enumerate(todo,1):
   pid,row=fetch(task)
   out[pid]=row;save(D/'older_arsenals.json',out)
   print(i,len(todo),row['name'],row.get('year',row.get('error','기록 없음')),flush=True)
   if '요청 제한' in row.get('error',''):raise RuntimeError(row['error'])
if __name__=='__main__':main()
