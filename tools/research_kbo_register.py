"""KBO 공식 선수 등록 페이지를 기준일/구단별로 조회해 원문을 보존한다."""
import concurrent.futures,json,re,sys,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'work/kbo_roster_research'
TEAMS={'KT':'KT','SS':'SS','HT':'HT','LG':'LG','OB':'OB','SK':'SK','LT':'LT','NC':'NC','HH':'HH','WO':'WO'}
BASE='https://www.koreabaseball.com/Player/Register.aspx'
PREFIX='ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$'

def fetch(team,date):
 s=requests.Session();s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=.8,status_forcelist=[429,500,502,503,504],allowed_methods=['GET','POST'])))
 r=s.get(BASE,timeout=45);r.raise_for_status();r.encoding='utf-8';h=r.text
 fields={k:v for k,v in re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"',h,re.I) if k.startswith('__') or 'hfSearch' in k}
 fields[PREFIX+'hfSearchTeam']=team;fields[PREFIX+'hfSearchDate']=date
 fields['__EVENTTARGET']=PREFIX+'btnCalendarSelect';fields['__EVENTARGUMENT']='';fields['__LASTFOCUS']=''
 r=s.post(BASE,data=fields,headers={'Referer':BASE,'Origin':'https://www.koreabaseball.com'},timeout=45);r.raise_for_status();r.encoding='utf-8'
 soup=BeautifulSoup(r.text,'html.parser');tables=[]
 for table in soup.select('table'):
  title=table.find_previous(['h4','h5']);head=[x.get_text(' ',strip=True) for x in table.select('thead th')]
  rows=[]
  for tr in table.select('tbody tr'):
   cells=[x.get_text(' ',strip=True) for x in tr.select('th,td')]
   if cells:rows.append(dict(cells=cells,player_links=[a.get('href') for a in tr.select('a[href]')]))
  if rows:tables.append(dict(section=title.get_text(' ',strip=True) if title else '',headers=head,rows=rows))
 path=OUT/date;path.mkdir(parents=True,exist_ok=True)
 (path/f'{team}.html').write_text(r.text,'utf8')
 return dict(team=team,date=date,tables=tables,source=BASE,raw_html=f'work/kbo_roster_research/{date}/{team}.html',status=r.status_code,html_bytes=len(r.content))

def main():
 date=sys.argv[1] if len(sys.argv)>1 else '20260328';teams=sys.argv[2:] or list(TEAMS)
 OUT.mkdir(parents=True,exist_ok=True)
 for team in teams:
  row=fetch(team,date);out=OUT/date/f'{team}.json';out.write_text(json.dumps(row,ensure_ascii=False,indent=2),'utf8')
  print(team,'tables',[(t['section'],len(t['rows'])) for t in row['tables']])
  time.sleep(.4)
if __name__=='__main__':main()
