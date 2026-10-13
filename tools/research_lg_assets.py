"""공식 LG 프로필, KBO 2025 이전 기록과 사진을 로컬 보존한다."""
import json,re,time,requests
from pathlib import Path
from bs4 import BeautifulSoup
from prepare_kbo_teams import get_stats
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'translation/lg_2026';D.mkdir(exist_ok=True)
def main():
 profiles=json.loads((ROOT/'work/lg_details/profiles.json').read_text('utf8'))
 spec=json.loads((ROOT/'translation/kbo_2026/LG.json').read_text('utf8'))
 for name,seq in [('염경엽',323),('김일경',129),('김광삼',131),('송지만',418),('모창민',290)]:
  s=BeautifulSoup((ROOT/f'work/lg_details/{seq}.html').read_text('utf8'),'html.parser');section=s.select_one('.player_profile');ds=section.select('.profile_right dd');hw=list(map(int,re.findall(r'\d+',ds[1].text)))
  profiles[name]=dict(url=f'https://www.lgtwins.com/team/coach-detail?ttmSeq={seq}',profile=dict(name=name,engName=section.select_one('.name_en').text.strip(),backNumber=section.select_one('.number').text.strip(),height=hw[0],weight=hw[1],birthdate=''.join(re.findall(r'\d+',ds[0].text)),imageFilePath=section.select_one('.profile_center img')['src']))
 for name,eng,no in [('치리노스','YONNY CHIRINOS','46'),('웰스','LACHLAN WELLS','68')]:
  p=next(p for p in spec['records'] if p['name']==name)
  profiles[name]=dict(url='https://lgtwinsfanbook.com/2026/',profile=dict(name=name,engName=eng,backNumber=no,height=p['height'],weight=p['weight'],birthdate=p['birth'].replace('-',''),playerNo=p['player_id'],teamMemberSortCodeName=p['hands']))
 (D/'official_profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2),'utf8')
 path=D/'stats.json';stats=json.loads(path.read_text('utf8')) if path.exists() else {}
 for p in spec['records']:
  q=profiles[p['name']]['profile'];pid=q.get('playerNo') or p.get('player_id');photo=D/f"photo_{p['index']}.png"
  if not photo.exists():
   url=q.get('imageFilePath') or f'https://6ptotvmi5753.edge.naverncp.com/KBO_IMAGE/person/middle/2026/{pid}.jpg'
   r=requests.get(url,timeout=40);r.raise_for_status();photo.write_bytes(r.content)
  if p['kind']=='player' and pid not in stats:
   _,st=get_stats(dict(p,player_id=pid));stats[pid]=st;path.write_text(json.dumps(stats,ensure_ascii=False,indent=2),'utf8');time.sleep(.15)
  print(p['name'],pid,'photo',photo.stat().st_size,'stats',len(stats.get(pid,{}).get('through_2025',[])),flush=True)
if __name__=='__main__':main()
