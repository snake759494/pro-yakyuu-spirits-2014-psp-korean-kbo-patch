"""LG 공식 선수/코치 프로필 원문을 보존. 개막 명단 밖 현재 선수는 채택하지 않는다."""
import requests,json,re,time
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'work/lg_details';D.mkdir(exist_ok=True)
BASE='https://www.lgtwins.com'
def main():
 spec=json.loads((ROOT/'translation/kbo_2026/LG.json').read_text('utf8'));wanted={p['name'] for p in spec['records']}
 profiles={};session=requests.Session()
 for route in ('/team/player-list','/team/coach-list'):
  r=session.get(BASE+route,timeout=30);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
  (D/(route.rsplit('/',1)[-1]+'.html')).write_text(r.text,'utf8')
  links={}
  for a in s.select('a[href*="ttmSeq="]'):
   name=next((n for n in wanted if n in a.get_text(' ',strip=True)),None)
   if name:links[name]=re.sub(r';jsessionid=[^?]+','',a['href'])
  for name,href in links.items():
   path=D/(re.search(r'ttmSeq=(\d+)',href)[1]+'.html')
   if not path.exists():
    r=session.get(BASE+href,timeout=30);r.raise_for_status();path.write_text(r.text,'utf8');time.sleep(.1)
   text=path.read_text('utf8');m=re.search(r'window\.player\s*=\s*(\{.*?\});',text)
   if not m:print('NO PROFILE',name,href,flush=True);continue
   p=json.loads(m[1]);assert p['name']==name
   profiles[name]=dict(profile=p,url=BASE+href,html=path.relative_to(ROOT).as_posix())
   (D/'profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2),'utf8')
   print(name,p.get('playerNo'),p.get('backNumber'),flush=True)
 print('missing',sorted(wanted-profiles.keys()))
if __name__=='__main__':main()

