"""KBO 선수 ID별 공식 프로필/사진을 새로 수집하여 기존 명세와 독립 대조."""
import concurrent.futures, hashlib, json, re, io
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'work/identity_audit'

def fetch(item):
    code,p=item;pid=p['player_id'];url=f'https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx?playerId={pid}'
    path=D/'profiles'/f'{pid}.html'
    if not path.exists():
        r=requests.get(url,timeout=35);r.raise_for_status();path.write_text(r.text,encoding='utf-8')
    s=BeautifulSoup(path.read_text('utf8'),'html.parser')
    def field(k):
        x=s.select_one('[id$="lbl'+k+'"]');return x.get_text(' ',strip=True) if x else None
    name=field('Name');pos=field('Position')
    assert name and pos,(code,p['name'],url)
    photo=s.select_one('img[id$="imgPlayer"]')
    if photo is None:photo=next((im for im in s.select('img') if f'/{pid}.' in im.get('src','')),None)
    photo_url=photo.get('src') if photo else None
    result=dict(team=code,index=p['index'],player_id=pid,expected_name=p['name'],official_name=name,position=pos,birth=field('Birthday'),body=field('HeightWeight'),source=url,profile_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if photo_url:
        photo_url=requests.compat.urljoin(url,photo_url)
        dest=D/'photos'/f'{pid}.png'
        try:
            if not dest.exists():
                r=requests.get(photo_url,timeout=30);r.raise_for_status();im=Image.open(io.BytesIO(r.content)).convert('RGB');im.save(dest)
            result.update(photo=dest.relative_to(ROOT).as_posix(),photo_source=photo_url,photo_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
        except Exception as e:result['photo_error']=str(e)
    return result

def main():
    for n in ('profiles','photos'):(D/n).mkdir(parents=True,exist_ok=True)
    m=json.loads((ROOT/'translation/kbo_2026/ratings_review.json').read_text('utf8'))
    todo=[(c,p) for c,t in m['teams'].items() for p in t['players']];rows=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        fs={pool.submit(fetch,p):p for p in todo}
        for f in concurrent.futures.as_completed(fs):
            try:rows.append(f.result())
            except Exception as e:errors.append(dict(team=fs[f][0],name=fs[f][1]['name'],error=str(e)))
            if (len(rows)+len(errors))%50==0:print('조사',len(rows),'오류',len(errors),flush=True)
    rows.sort(key=lambda p:(p['team'],p['index']))
    (D/'official_profiles.json').write_text(json.dumps(dict(players=rows,errors=errors),ensure_ascii=False,indent=2),'utf8')
    print('완료',len(rows),'사진',sum('photo' in p for p in rows),'오류',errors,flush=True)

if __name__=='__main__':main()
