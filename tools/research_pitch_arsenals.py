"""공개 2025 투구분석의 구종별 집계를 신원 정보와 함께 보존한다."""
import json,re,hashlib,concurrent.futures
from pathlib import Path
from bs4 import BeautifulSoup
from research_ratings_review import D,get,save,norm
BASE='https://kbo-analytics-2025.vercel.app/'
def fetch(p):
 name=p['name'];path=D/'arsenal'/f'{p["pcode"]}.html';path.parent.mkdir(exist_ok=True)
 url=BASE+f'pitchers/{p["pcode"]}_{name}.html'
 if not path.exists():path.write_text(get(url).text,'utf8')
 raw=path.read_text('utf8');s=BeautifulSoup(raw,'html.parser')
 m=re.search(r'const\s+D\s*=\s*',raw);assert m,(name,'구종 JSON 없음')
 d=json.JSONDecoder().raw_decode(raw[m.end():])[0]
 text=s.get_text(' ',strip=True);birth=re.search(r'\b(19\d{2}|20\d{2})\.\d{2}\.\d{2}\b',text)
 result=dict(name=name,year=2025,team=p['team'],hand=p['hand'],birth=birth[0].replace('.','-') if birth else None,source=url,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),arsenal=d['arsenal'],summary=p)
 # 탄착군/모든 투구 좌표는 평가에 사용하지 않는다. 집계만 재현 가능하게 보존.
 for a in result['arsenal']:
  for k in list(a):
   if isinstance(a[k],(list,dict)):del a[k]
 return str(p['pcode']),result
def main():
 raw=(D/'insight.html').read_text('utf8');ps=json.JSONDecoder().raw_decode(raw.split('const PS=')[1])[0]
 identities=json.loads((D/'identities.json').read_text('utf8'));wanted={norm(p['name']) for rs in identities.values() for p in rs if p['category']=='P'}
 todo=[p for p in ps if norm(p['name']) in wanted];out={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  for i,(key,p) in enumerate(ex.map(fetch,todo),1):
   out[key]=p
   if i%20==0:save(D/'arsenals.json',out);print('2025 구종',i,len(todo),flush=True)
 save(D/'arsenals.json',out);print('완료',len(out),flush=True)
if __name__=='__main__':main()
