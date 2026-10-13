"""공식 2025 수비 포지션/이닝/실책. 잘못 닫힌 조건 주석 때문에 hidden은 정규식으로 읽는다."""
import requests,re,json,time,sys
SEASON=sys.argv[1] if len(sys.argv)>1 else '2025'
from bs4 import BeautifulSoup
from research_ratings_review import D,save
URL='https://www.koreabaseball.com/Record/Player/Defense/Basic.aspx'
PREFIX='ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$'
def form(h):
 f={k:v for k,v in re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"',h,re.I)}
 soup=BeautifulSoup(h,'html.parser')
 for x in soup.select('select[name]'):
  f[x['name']]=(x.select_one('option[selected]') or x.select_one('option'))['value']
 return f
def main():
 s=requests.Session();r=s.get(URL,timeout=30);r.encoding='utf8';h=r.text;out=[]
 for page in range(1,45):
  f=form(h);f[PREFIX+'ddlSeason$ddlSeason']=SEASON
  event='ddlSeason$ddlSeason' if page==1 else 'ucPager$btnNext' if page%5==1 else 'ucPager$btnNo'+str((page-1)%5+1)
  f['__EVENTTARGET']=PREFIX+event;f['__EVENTARGUMENT']=''
  r=s.post(URL,data=f,headers={'Referer':URL,'Origin':'https://www.koreabaseball.com'},timeout=30);r.encoding='utf8';h=r.text
  assert 'Error.html' not in r.url,(page,r.url)
  b=BeautifulSoup(h,'html.parser');assert b.select_one('select option[selected]').get('value')==SEASON
  rows=[]
  for tr in b.select('table tbody tr'):
   a=tr.select_one('a[href*="playerId="]')
   if not a:continue
   row={x.get('data-id'):x.get_text(' ',strip=True) for x in tr.select('td[data-id]')}
   row.update(player_id=re.search(r'playerId=(\d+)',a['href'])[1],name=a.get_text(strip=True),year=int(SEASON))
   rows.append(row)
  if not rows or all(x in out for x in rows):break
  out.extend(x for x in rows if x not in out);save(D/f'defense_{SEASON}.json',out)
  (D/f'defense{SEASON}').mkdir(exist_ok=True);(D/f'defense{SEASON}'/f'{page:02}.html').write_text(h,'utf8')
  print(page,len(rows),len(out),flush=True)
  if len(rows)<30:break
  time.sleep(.25)
if __name__=='__main__':main()
