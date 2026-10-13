"""KBO 영문 공식 선수 페이지: 공식 영문명(등 이름 근거), 등번호, 2026 시즌 요약을 수집한다."""
import json,re,sys,time,concurrent.futures,hashlib
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'work/kbo_roster_research/eng';D.mkdir(parents=True,exist_ok=True)
TEAMS=['LG','SS','HT','WO','KT','LT','HH','OB','SK','NC']
def text(h):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',h)).replace('&nbsp;',' ')
def fetch(pid,pitcher):
 kind='PlayerInfoPitcher' if pitcher else 'PlayerInfoHitter'
 path=D/f'{pid}.html'
 if not path.exists():
  for a in range(3):
   try:
    r=requests.get(f'https://eng.koreabaseball.com/Teams/{kind}/Summary.aspx?pcode={pid}',timeout=30);r.raise_for_status();break
   except Exception:
    if a==2:raise
    time.sleep(2)
  path.write_text(r.text,'utf8');time.sleep(.1)
 h=path.read_text('utf8');t=text(h)
 m=re.search(r'Name : ?(.*?) ?Position : ?(.*?) ?No : ?(\S*?) ?Salary : ?(\S*?) ?(?:[\d,]+ )?Born : ?(\S*) .*?HT/WT : ?(\S*)',t)
 if not m:return pid,dict(error='parse')
 out=dict(english=m[1].strip(),position=m[2].strip(),number=m[3],salary_currency=m[4],foreign=m[4]=='$',born=m[5],body=m[6],sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 # 2026 season row: header list then team row.
 s=re.search(r'2026 Season Stats (.*?)(?:Recent|Career|$)',t)
 if s:
  seg=s[1]
  if pitcher:
   g=re.search(r'TEAM ERA G CG SHO W L SV HLD WPCT PA NP IP H 2B 3B HR \S+ ([\d.\-]+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) \S+ (\d+) (\d+) ([\d /]+?) (\d+) ',seg)
   if g:out['season2026']=dict(ERA=g[1],G=int(g[2]),W=int(g[5]),L=int(g[6]),SV=int(g[7]),HLD=int(g[8]),TBF=int(g[9]),IP=g[11].strip())
  else:
   g=re.search(r'TEAM AVG G PA AB R H 2B 3R HR TB RBI SB CS SAC SF \S+ ([\d.\-]+) (\d+) (\d+) (\d+)',seg)
   if g:out['season2026']=dict(AVG=g[1],G=int(g[2]),PA=int(g[3]),AB=int(g[4]))
 return pid,out
def main():
 jobs={}
 for t in TEAMS:
  for p in json.loads((ROOT/f'work/kbo_roster_research/current/{t}.json').read_text('utf8'))['players']:jobs[p['player_id']]=p['position']=='투수'
 for p in json.loads((ROOT/'translation/kbo_2026/appearance.json').read_text('utf8')):
  jobs.setdefault(p['player_id'],None)
 res={}
 with concurrent.futures.ThreadPoolExecutor(6) as ex:
  fs={ex.submit(fetch,pid,True if v is None else v):pid for pid,v in jobs.items()}
  for i,f in enumerate(concurrent.futures.as_completed(fs),1):
   try:k,v=f.result();res[k]=v
   except Exception as e:res[fs[f]]=dict(error=str(e))
   if i%100==0:print(i,len(jobs),flush=True)
 (ROOT/'work/kbo_roster_research/english.json').write_text(json.dumps(res,ensure_ascii=False,indent=1),'utf8')
 print('완료',len(res),'오류',sum('error' in v for v in res.values()))
if __name__=='__main__':main()
