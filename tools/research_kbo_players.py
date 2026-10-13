"""KBO 공식 선수 검색의 현역 구단별 페이지를 보존한다."""
import json,re,sys,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'work/kbo_roster_research';URL='https://www.koreabaseball.com/Player/Search.aspx'
PREFIX='ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$'
TEAMS=['KT','SS','HT','LG','OB','SK','LT','NC','WO']
def main():
 teams=sys.argv[1:] or TEAMS;outdir=OUT/'search';outdir.mkdir(parents=True,exist_ok=True)
 for team in teams:
  s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=.7,status_forcelist=[429,500,502,503,504])))
  r=s.get(URL,timeout=45);r.raise_for_status();r.encoding='utf8';soup=BeautifulSoup(r.text,'html.parser');data={}
  for x in soup.select('input[name]'):
   if x.get('type') in ('hidden','submit'):data[x['name']]=x.get('value','')
  data[PREFIX+'ddlTeam']=team;data[PREFIX+'ddlPosition']='';data[PREFIX+'txtSearchPlayerName']='';data[PREFIX+'hfPage']='1';data[PREFIX+'btnSearch']='검색'
  r=s.post(URL,data=data,headers={'Referer':URL,'Origin':'https://www.koreabaseball.com'},timeout=45);r.raise_for_status();r.encoding='utf8';p=BeautifulSoup(r.text,'html.parser')
  rows=[]
  for tr in p.select('table tbody tr'):
   cells=[x.get_text(' ',strip=True) for x in tr.select('td')];a=tr.select_one('a[href*="playerId="]')
   if cells:rows.append(dict(cells=cells,profile=a.get('href') if a else None))
  (outdir/f'{team}.html').write_text(r.text,'utf8');result=dict(team=team,date='2026-10-10',source=URL,raw_html=f'work/kbo_roster_research/search/{team}.html',rows=rows)
  (outdir/f'{team}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(team,len(rows),rows[:2]);time.sleep(.4)
if __name__=='__main__':main()
