"""공개 구단 프로필 및 KBO 연도별 기록 수집. 2026 성적은 평가 입력에서 제외."""
from pathlib import Path
import requests,json,re,concurrent.futures
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/hanwha_research'
def get_player(item):
 category,p=item
 url=f'https://www.hanwhaeagles.co.kr/PL/{category}/PL{category}02.do?id={p["ID"]}&pcode={p.get("PCODE","")}'
 r=requests.get(url,timeout=40);r.raise_for_status();profile=r.json().get('result',{})
 result=dict(category=category,listing=p,profile=profile,source=url)
 if p.get('PCODE'):
  kind='PitcherDetail' if category=='PC' else 'HitterDetail'
  ku=f'https://www.koreabaseball.com/Record/Player/{kind}/Total.aspx?playerId={p["PCODE"]}'
  r=requests.get(ku,timeout=40);r.raise_for_status();r.encoding='utf8';b=BeautifulSoup(r.text,'html.parser')
  tables=[]
  for t in b.select('table'):
   head=[x.get_text(' ',strip=True) for x in t.select('thead th')]
   rows=[]
   for row in t.select('tbody tr'):
    cells=[x.get_text(' ',strip=True) for x in row.select('td')]
    if cells and re.fullmatch(r'20\d\d',cells[0]) and int(cells[0])<=2025:rows.append(cells)
   if rows:tables.append(dict(headers=head,rows=rows))
  result['kbo_source']=ku;result['through_2025']=tables
 return result
def main():
 items=[]
 for cat in ('PC','CC','IF','OF'):
  file='PL_PC_PLPC01.do.txt' if cat=='PC' else cat+'.txt'
  for p in json.loads((OUT/file).read_text('utf8'))['result']:items.append((cat,p))
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
  rows=list(ex.map(get_player,items))
 (OUT/'official_profiles.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8')
 print('공식 프로필',len(rows),'연도별 기록',sum(bool(x.get('through_2025')) for x in rows))
if __name__=='__main__':main()
