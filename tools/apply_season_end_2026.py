"""2026 정규시즌 종료 기준 신원·명단을 모든 빌드 입력에 일관되게 반영한다.

입력: work/season_end_2026/plan.json(plan_season_end_2026.py), 공식 프로필, 영문 프로필.
게임 슬롯(index), 선수 게임 ID, 음성 키, 얼굴 파일 번호는 바꾸지 않는다.
"""
import json,re,shutil,datetime
from pathlib import Path
from backnames import back_name
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work/season_end_2026'
def read(p):return json.loads((ROOT/p).read_text('utf8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def norm(s):return re.sub(r'\([^)]*\)|\s','',s)
CAT={'투수':'P','포수':'C','내야수':'IF','외야수':'OF'};HHCAT={'P':'PC','C':'CC','IF':'IF','OF':'OF'}
BACKUP=ROOT/'build/baseline_before_season_end_2026'
FILES=['translation/kbo_2026/LG.json','translation/kbo_2026/SS.json','translation/kbo_2026/HT.json','translation/kbo_2026/WO.json','translation/kbo_2026/KT.json','translation/kbo_2026/LT.json','translation/kbo_2026/OB.json','translation/kbo_2026/SK.json','translation/kbo_2026/NC.json','translation/hanwha_2026.json','work/ratings_review/identities.json','work/ratings_review/opening.json','work/identity_audit/official_profiles.json','translation/lg_2026/details.json','translation/hanwha_visual/appearance.json','translation/kbo_2026/appearance.json','translation/kbo_2026/ratings_review.json','tools/kbo_team_layout.py']
def main():
 if not BACKUP.exists():
  for f in FILES:
   d=BACKUP/f;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,d)
 # 재실행 시 항상 시즌 종료 변경 전 입력에서 다시 시작한다(코드 파일 제외).
 for f in FILES:
  if f.endswith('.json') and 'appearance.json'!=Path(f).name or f.endswith('hanwha_visual/appearance.json'):shutil.copy2(BACKUP/f,ROOT/f)
 plan=json.loads((W/'plan.json').read_text('utf8'));prof={p['index']:p for p in json.loads((W/'official_profiles.json').read_text('utf8'))['players']}
 eng=read('work/kbo_roster_research/english.json')
 ident=read('work/ratings_review/identities.json');opening={}
 lg=read('translation/lg_2026/details.json');hv=read('translation/hanwha_visual/appearance.json')
 lgby={p['index']:p for p in lg};hvby={p['index']:p for p in hv}
 changes=[]
 for code,P in plan.items():
  path='translation/hanwha_2026.json' if code=='HH' else f'translation/kbo_2026/{code}.json'
  spec=read(path);recs={r['index']:r for r in spec['records']};ids={p['index']:p for p in ident[code]}
  # 구단 내 동명이인은 출생연도 두 자리로 구분한다(기존 '(좌)/(우)' 표기는 유지).
  def chosen(s):
   old=recs[s['index']];return old['name'] if s['status']=='keep' and norm(old['name'])==norm(s['name']) else s['name']
  counts={}
  for s in P['slots']:counts[chosen(s)]=counts.get(chosen(s),0)+1
  for s in P['slots']:
   i=s['index'];pr=prof[i];assert pr['player_id']==s['player_id'] and pr['official_name']==s['name'],(code,i)
   m=re.match(r'(.+?)\((.+)\)',pr['position']);role,hands=(m[1],m[2]) if m else (pr['position'],None)
   cat=CAT[role];b=re.findall(r'\d+',pr['birth']);birth='%s-%s-%s'%tuple(b[:3])
   h,w=map(int,re.findall(r'\d+',pr['body'])[:2]);e=eng.get(s['player_id'],{});foreign=bool(e.get('foreign'))
   old=recs[i];name=chosen(s)
   if counts[name]>1:name=f"{s['name']}({birth[2:4]})"
   number=s['number'] if s['number'].isdigit() else None
   info=dict(name=name,player_id=s['player_id'],role=role,hands=hands,birth=birth,height=h,weight=w,number=number,foreign=foreign,
     english=e.get('english',''),back_name=back_name(s['name'],e.get('english',''),foreign),profile=pr['source'],
     opening_entry=s['active'],final_register_20261003=s['final_register'])
   if s['status']!='keep':
    changes.append(dict(team=code,index=i,before=s['previous'],after=dict(player_id=s['player_id'],name=name),kind=s['status']))
    base={k:old[k] for k in ('index','kind','borrowed') if k in old}
    if code=='HH':
     # 능력치 필드는 kbo_ratings_review가 최종 덮어쓴다. 구조 유지를 위한 임시값.
     base.update({k:old[k] for k in ('abilities','fielding','velocity','pitches','estimated_fields') if k in old})
    old.clear();old.update(base,source='KBO 2026 정규시즌 종료 기준(2026-10-03 등록, 현재 소속 조회)',roster_source_note=f"{s['previous']['name']} 슬롯 재사용")
   old.update(info);old['category']=HHCAT[cat] if code=='HH' else cat
   if code=='HH':
    old['key']=name;old['initial_active']=s['active']
    if hands:old['throw_hand']=1 if hands.startswith('좌') else 0;old['bat_hand']=2 if '양타' in hands else 1 if hands.endswith('좌타') else 0
    else:old.setdefault('throw_hand',0);old.setdefault('bat_hand',0)
    old['number']=number or '0'
   idn=ids[i]
   if s['status']!='keep':
    for k in list(idn):
     if k not in ('index','kind','borrowed'):del idn[k]
   idn.update(info,category=cat,current_team=code,identity_source='work/season_end_2026/official_profiles.json')
   # 등 이름/외형 보조 명세(LG, 한화)는 새 신원과 일치시켜 이전 선수 사진이 남지 않게 한다.
   for table in (lgby,hvby):
    if i in table:
     t=table[i]
     if s['status']!='keep':
      for k in ('face_photo','face_photo_source','face_photo_sha256','landmarks','face_box','face_detection','skin_type','skin_reference_head','body_type','original_body_type','ratings','fielding','rating_source','rating_year','rating_basis','estimated_fields','photo','photo_sha256','photo_source','profile_source'):t.pop(k,None)
     t.update(name=name,english=info['english'],back_name=info['back_name'],height=h,weight=w,player_id=s['player_id'],number=number or '',birth=birth,foreign=foreign)
     if hands:t['hands']=hands
     else:t.pop('hands',None)
  spec['cutoff']='2026-10-03';spec['season_end_update']=dict(date=datetime.date.today().isoformat(),register='https://www.koreabaseball.com/Player/Register.aspx (2026-10-03)',current_roster='https://www.koreabaseball.com/Player/Search.aspx',english='https://eng.koreabaseball.com')
  write(path,spec)
  byid={p['player_id']:p for p in ident[code]}
  opening[code]=[dict(name=byid[x]['name'],player_id=x,category=byid[x]['category'],birth=byid[x]['birth'],hands=byid[x]['hands'],number=byid[x]['number']) for x in P['active']]
 write('work/ratings_review/identities.json',ident);write('work/ratings_review/opening.json',opening)
 shutil.copy2(W/'official_profiles.json',ROOT/'work/identity_audit/official_profiles.json')
 write('translation/lg_2026/details.json',lg);write('translation/hanwha_visual/appearance.json',hv)
 write('work/season_end_2026/slot_changes.json',changes);print('슬롯 교체',len(changes))
if __name__=='__main__' and len(__import__('sys').argv)==1:main()
def sync_visual():
 """prepare_identity_faces 이후: 교체 슬롯의 LG/한화 보조 외형 명세를 새 전 선수 명세로 채운다."""
 app={p['index']:p for p in read('translation/kbo_2026/appearance.json')}
 changed={c['index'] for c in read('work/season_end_2026/slot_changes.json')}
 for path in ('translation/lg_2026/details.json','translation/hanwha_visual/appearance.json'):
  rows=read(path)
  for t in rows:
   if t['index'] in app and app[t['index']]['player_id']==t.get('player_id'):
    t.update(skin_type=app[t['index']]['skin_type'],skin_reference_head=app[t['index']]['skin_reference_head'])
   if t['index'] in changed:
    a=app[t['index']];assert a['player_id']==t['player_id'],(path,t['index'])
    t.update({k:a[k] for k in ('photo','photo_sha256','photo_source','landmarks','face_box','face_id','face_file','dedicated_face','height','weight','body_type','skin_type','skin_reference_head')})
  write(path,rows)
 print('보조 외형 동기화',len(changed))
if __name__=='__main__' and len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='sync':sync_visual()
