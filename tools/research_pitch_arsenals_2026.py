"""공개 2026 투구분석의 구종별 집계(정규시즌)를 보존한다. 형식은 2025 수집본과 같다."""
import json,re,hashlib,concurrent.futures
from bs4 import BeautifulSoup
from research_ratings_review import D,get,save,norm
BASE='https://kbo-analytics-2026.vercel.app/'
def fetch(p):
 name=p['name'];path=D/'arsenal2026'/f'{p["pcode"]}.html';path.parent.mkdir(exist_ok=True)
 url=BASE+f'pitchers/{p["pcode"]}_{name}.html'
 if not path.exists():path.write_text(get(url).text,'utf8')
 raw=path.read_text('utf8');s=BeautifulSoup(raw,'html.parser')
 m=re.search(r'const\s+D\s*=\s*',raw);assert m,(name,'구종 JSON 없음')
 d=json.JSONDecoder().raw_decode(raw[m.end():])[0]
 text=s.get_text(' ',strip=True);birth=re.search(r'\b(19\d{2}|20\d{2})\.\d{2}\.\d{2}\b',text)
 result=dict(name=name,year=2026,team=p['team'],hand=p['hand'],birth=birth[0].replace('.','-') if birth else None,source=url,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),arsenal=d['arsenal'],summary=p)
 for a in result['arsenal']:
  for k in list(a):
   if isinstance(a[k],(list,dict)):del a[k]
 return str(p['pcode']),result
def main():
 raw=(D/'insight2026.html').read_text('utf8');ps=json.JSONDecoder().raw_decode(raw.split('const PS=')[1])[0]
 out={}
 with concurrent.futures.ThreadPoolExecutor(3) as ex:
  for key,p in ex.map(fetch,ps):out[key]=p
 save(D/'arsenals_2026.json',out);print('2026 구종',len(out),sum(bool(p['birth']) for p in out.values()))
if __name__=='__main__':main()
