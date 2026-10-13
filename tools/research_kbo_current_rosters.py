"""KBO 공식 선수 검색에서 구단별 현재 소속 선수 전체(1·2군)를 페이지 단위로 수집한다."""
import json,re,sys,time,datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'work/kbo_roster_research/current'
URL='https://www.koreabaseball.com/Player/Search.aspx'
P='ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$'
TEAMS=['LG','SS','HT','WO','KT','LT','HH','OB','SK','NC']
def form(soup):
 d={k:v for k,v in re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"',str(soup))}
 for x in soup.select('input[name]'):
  if x.get('type') not in ('submit','button','image'):d[x['name']]=x.get('value','')
 for s in soup.select('select[name]'):
  o=s.select_one('option[selected]');d[s['name']]=o.get('value','') if o else ''
 return d
def rows(soup):
 out=[]
 for tr in soup.select('table.tEx tbody tr, table tbody tr'):
  td=[x.get_text(' ',strip=True) for x in tr.select('td')];a=tr.select_one('a[href*="playerId="]')
  if len(td)>=7 and a:out.append(dict(number=td[0],name=td[1],team=td[2],position=td[3],birth=td[4],body=td[5],school=td[6],player_id=re.search(r'playerId=(\d+)',a['href']).group(1),profile=a['href']))
 return out
def post(s,soup,target,extra={}):
 d=form(soup);d.update(extra);d['__EVENTTARGET']=target;d['__EVENTARGUMENT']=''
 r=s.post(URL,data=d,headers={'Referer':URL},timeout=45);r.encoding='utf8';return BeautifulSoup(r.text,'html.parser')
def fetch(team):
 s=requests.Session();r=s.get(URL,timeout=45);r.encoding='utf8';soup=BeautifulSoup(r.text,'html.parser')
 soup=post(s,soup,P+'ddlTeam',{P+'ddlTeam':team,P+'ddlPosition':''})
 got={};page=1
 while True:
  for x in rows(soup):got[x['player_id']]=x
  page+=1;btn=P+f'ucPager$btnNo{page}'
  names={a.get('href','') for a in soup.select('a')}
  if not any(f'btnNo{page}' in h for h in names):
   nxt=[h for h in names if 'btnNext' in h]
   if not nxt:break
   soup=post(s,soup,P+'ucPager$btnNext',{P+'hfPage':str(page)})
   before=len(got)
   for x in rows(soup):got[x['player_id']]=x
   if len(got)==before:break
   continue
  soup=post(s,soup,btn,{P+'hfPage':str(page)});time.sleep(.3)
 return list(got.values())
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for t in sys.argv[1:] or TEAMS:
  r=fetch(t);(OUT/f'{t}.json').write_text(json.dumps(dict(team=t,fetched=datetime.datetime.now().isoformat(timespec='seconds'),source=URL,players=r),ensure_ascii=False,indent=1),'utf8')
  print(t,len(r),set(x['team'] for x in r));time.sleep(.4)
if __name__=='__main__':main()
