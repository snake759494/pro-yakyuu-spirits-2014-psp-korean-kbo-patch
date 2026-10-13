"""공식 구단 프로필·사진을 외형 작업용 소스로 보존한다."""
import concurrent.futures,hashlib,json,re,requests
from pathlib import Path
from bs4 import BeautifulSoup
from hanwha_roster import ROOT,load
D=ROOT/'translation/hanwha_visual';D.mkdir(exist_ok=True)
cache=json.loads((ROOT/'work/hanwha_research/official_profiles.json').read_text('utf8'))
extras=json.loads((ROOT/'work/hanwha_research/extra_sources.json').read_text('utf8'))
def fetch(p):
 def birth(s):
  a=list(map(int,re.findall(r'\d+',s)));return f'{a[0]:04}-{a[1]:02}-{a[2]:02}'
 matches=[r for r in cache if r['profile']['NAME']==p['name'] and birth(r['profile']['BIRTH'])==p['birth']]
 if matches:pr=matches[0]['profile'];source=matches[0]['source']
 elif p['name']=='에르난데스':pr=extras[0]['data']['result'];source=extras[0]['url']
 elif p['kind']=='coach':source=p['source'];pr=requests.get(source,timeout=30).json()['result']
 else:
  source=p['source'];s=BeautifulSoup(requests.get(source,timeout=30).text,'html.parser');pid=source.split('playerId=')[1]
  im=next(x for x in s.select('img') if pid in (x.get('src') or ''))
  wh=re.search(r'(\d+)cm/(\d+)kg',s.select_one('.player_info').get_text())
  pr=dict(NAME=p['name'],HEIGHT=int(wh[1]),WEIGHT=int(wh[2]),EN_NAME={'손아섭':'SON AH SEOP','하주석':'HA JU SEOK'}[p['name']]);photo='https:'+im['src']
 if pr.get('ATTACH_ID'):photo='https://www.hanwhaeagles.co.kr/download/attach.do?id='+str(pr['ATTACH_ID'])
 elif matches and matches[0]['listing'].get('ATTACH_ID'):photo='https://www.hanwhaeagles.co.kr/download/attach.do?id='+str(matches[0]['listing']['ATTACH_ID'])
 dst=D/f"player_{p['index']}.png"
 from PIL import Image
 import io
 if not dst.exists():
  raw=requests.get(photo,timeout=30).content;im=Image.open(io.BytesIO(raw)).convert('RGBA');im.save(dst)
 result=dict(index=p['index'],name=p['name'],height=pr['HEIGHT'],weight=pr['WEIGHT'],english=pr['EN_NAME'],profile_source=source,photo_source=photo,photo=dst.relative_to(ROOT).as_posix(),photo_sha256=hashlib.sha256(dst.read_bytes()).hexdigest())
 kbo=(matches[0].get('kbo_source') or '') if matches else source
 pid='56712' if p['name']=='에르난데스' else kbo.split('playerId=')[-1] if 'playerId=' in kbo else None
 if p['kind']=='player' and pid:
  # 공식 선수 페이지의 정면 증명사진 경로. 활동 사진의 헬멧/마스크가 얼굴에 남지 않도록 사용.
  ku=f'https://6ptotvmi5753.edge.naverncp.com/KBO_IMAGE/person/middle/2026/{pid}.jpg';kd=D/f"face_{p['index']}.png"
  try:
   if not kd.exists():
    response=requests.get(ku,timeout=30);response.raise_for_status();ki=Image.open(io.BytesIO(response.content)).convert('RGBA');ki.save(kd)
   result.update(face_photo=kd.relative_to(ROOT).as_posix(),face_photo_source=ku,face_photo_sha256=hashlib.sha256(kd.read_bytes()).hexdigest())
  except (requests.RequestException,OSError):pass
 return result
def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,load()['records']))
 (D/'official_profiles.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8');print('공식 외형 프로필/사진',len(rows))
if __name__=='__main__':main()
