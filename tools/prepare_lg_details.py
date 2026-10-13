"""LG 개막 명단에 공식 신체/영문 정보와 기록 기반 게임 능력을 결합한다.
구속/수비/구종 등 공식 통계가 없는 항목은 편집 추정치로 명시한다.
"""
import json,re,struct,hashlib,cv2,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from prepare_kbo_teams import rating
from prepare_hanwha_visual import body
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'translation/lg_2026'
# km/h is the game's maximum-speed setting, not a claim of official measured velocity.
PITCH={
'치리노스':(153,'투심 슬라이더 스플리터'),'톨허스트':(155,'포심 슬라이더 커브 체인지업'),
'임찬규':(146,'포심 커브 체인지업'),'웰스':(151,'포심 슬라이더 체인지업'),
'이정용':(153,'포심 슬라이더 포크'),'함덕주':(146,'포심 슬라이더 체인지업'),
'우강훈':(154,'포심 슬라이더 체인지업'),'이우찬':(151,'포심 슬라이더 체인지업'),
'배재준':(149,'포심 슬라이더 커브 포크'),'김영우':(157,'포심 슬라이더 포크'),
'김진성':(150,'포심 슬라이더 포크'),'장현식':(154,'포심 슬라이더 포크'),
'유영찬':(156,'포심 슬라이더 커브 포크'),'권우준':(148,'포심 슬라이더 체인지업'),
'김강률':(151,'포심 슬라이더 포크'),'김대현':(151,'포심 슬라이더 포크'),
'김동현':(148,'포심 슬라이더 커브'),'김유영':(148,'포심 슬라이더 체인지업'),
'김주온':(151,'포심 슬라이더 커브'),'김진수':(150,'포심 슬라이더 포크'),
'박명근':(153,'포심 슬라이더 체인지업'),'박시원':(150,'포심 슬라이더 커브'),
'박준성':(148,'포심 슬라이더 커브'),'백승현':(154,'포심 슬라이더 커브 포크'),
'성동현':(154,'포심 슬라이더 포크'),'손주영':(153,'포심 슬라이더 커브 포크'),
'송승기':(151,'포심 슬라이더 커브 체인지업'),'양우진':(154,'포심 슬라이더 커브'),
'우명현':(152,'포심 슬라이더 커브'),'이민호':(152,'포심 슬라이더 커브 체인지업'),
'이지강':(148,'포심 슬라이더 커브 체인지업'),'장시환':(153,'포심 슬라이더 커브 포크'),
'정우영':(156,'투심 슬라이더 체인지업'),'조건희':(148,'포심 슬라이더 체인지업'),
'조원태':(151,'포심 슬라이더 커브'),'최지명':(149,'포심 슬라이더 커브 체인지업')}
EXTRA={'문보경':{'3B':66,'1B':52},'구본혁':{'SS':77,'3B':75,'2B':72},'신민재':{'2B':78,'CF':48},'오지환':{'SS':82},'박해민':{'CF':88,'LF':75,'RF':72},'홍창기':{'RF':72,'LF':65,'CF':58},'문성주':{'LF':64,'RF':62},'천성호':{'2B':53,'3B':50,'1B':46},'이영빈':{'SS':55,'2B':52,'3B':48},'송찬의':{'RF':46,'LF':44,'1B':42,'2B':35},'손용준':{'SS':50,'2B':50,'3B':44},'김정율':{'2B':49,'SS':46,'3B':42},'추세현':{'3B':48,'SS':42},'김주성':{'LF':48,'RF':46,'3B':40}}
def main():
 s=json.loads((ROOT/'translation/kbo_2026/LG.json').read_text('utf8'));profiles=json.loads((D/'official_profiles.json').read_text('utf8'));stats=json.loads((D/'stats.json').read_text('utf8'))
 old=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();inv={e['name'] for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']}
 detector=cv2.FaceDetectorYN.create('onnx',np.frombuffer((ROOT/'tools/bin/face_detection_yunet_2023mar.onnx').read_bytes(),np.uint8),np.array([],np.uint8),(320,320),.65)
 out=[];gallery=Image.new('RGB',(1000,9*150),'#333333');draw=ImageDraw.Draw(gallery);font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),13)
 for j,p in enumerate(s['records']):
  q=profiles[p['name']]['profile'];birth=q['birthdate'];name=p['name'];r=dict(index=p['index'],name=name,english=q['engName'],number=q['backNumber'],height=int(q['height']),weight=int(q['weight']),birth=f'{birth[:4]}-{birth[4:6]}-{birth[6:]}',hands=q.get('teamMemberSortCodeName',p.get('hands')),player_id=q.get('playerNo',p.get('player_id')),source=profiles[name]['url'])
  r['number']=r['number'].strip()
  if r['number']=='M':r['number']='0';r['number_note']='공식 프로필 군보류(M): 미부여 번호를 게임의 0으로 표시'
  tokens=re.findall('[A-Z]+',r['english'].upper());r['back_name']={'치리노스':'CHIRINOS','웰스':'WELLS','톨허스트':'TOLHURST','오스틴':'DEAN'}.get(name,tokens[0]+' '+'.'.join(t[0] for t in tokens[1:])+'.');assert len(r['back_name'])<=11
  r['body_type']=body(r['height'],r['weight']);r['skin_type']=1 if name=='치리노스' else 0;r['skin_reference_head']=r['skin_type']+1
  r['face_id']=struct.unpack_from('<H',old,5120+p['index']*192+86)[0];r['face_file']=f"F{r['face_id']}.CHK";r['dedicated_face']=r['face_file'] in inv
  photo=D/f"photo_{p['index']}.png";r['photo']=photo.relative_to(ROOT).as_posix();r['photo_sha256']=hashlib.sha256(photo.read_bytes()).hexdigest()
  im=Image.open(photo).convert('RGB');a=np.array(im);detector.setInputSize(im.size);_,found=detector.detect(cv2.cvtColor(a,cv2.COLOR_RGB2BGR));assert found is not None,name
  box=max(found,key=lambda b:b[2]*b[3]);r['landmarks']=[list(map(float,box[k:k+2])) for k in range(4,14,2)];r['face_box']=list(map(int,box[:4]))
  x,y,w,h=r['face_box'];v=im.crop((max(0,x-w*.2),max(0,y-h*.4),min(im.width,x+w*1.2),min(im.height,y+h*1.2)));v.thumbnail((120,120));gallery.paste(v,((j%8)*125,(j//8)*150));draw.text(((j%8)*125,(j//8)*150+120),name,font=font,fill='white')
  if p['kind']=='player':
   st=stats.get(r['player_id'],{});ra=rating(p,st);known=bool(ra)
   if not known:ra=dict(contact_r=35,contact_l=35,power=35,speed=50,arm=55,catching=43,throwing=43,recovery=52,stamina=0,starter=0,reliever=0,closer=0,trajectory=2)
   r['rating_source']=st.get('stats_url');r['rating_year']=ra.pop('rating_year',None);r['rating_basis']='2025 이전 마지막 공식 시즌, 소표본 보정' if known else '1군 기록 없음: 보수적인 신인 추정'
   if p['category']=='P':
    velo,names=PITCH[name];qs=ra.get('pitches',[]);stuff=qs[0]['stuff'] if qs else 3;control=qs[0]['control'] if qs else 3
    starter=name in s['fresh_layout']['rotation'] or name in ('손주영','송승기','이민호','이지강','양우진','조원태');closer=name=='유영찬'
    ra.update(contact_r=12,contact_l=12,power=18,trajectory=0,stamina=max(65,ra.get('stamina',0)) if starter else 45,starter=7 if starter else 0,reliever=3 if starter else 7,closer=7 if closer else 0,velocity=velo,pitches=[dict(name=n,**{'break':0 if n=='포심' else 3 if not known else min(5,stuff),'stuff':stuff,'control':control}) for n in names.split()])
    r['fielding']={'P':55}
   else:
    pos=['P','C','1B','2B','3B','SS','LF','CF','RF'][p['primary_position']];r['fielding']=EXTRA.get(name,{pos:55 if known else 43});ra['trajectory']=4 if ra['power']>=65 else 3 if ra['power']>=45 else 2
    if name=='박해민':ra['speed']=85
    if name=='신민재':ra['speed']=83
   r['ratings']=ra;r['estimated_fields']='구속 상한, 구종, 수비, 어깨, 좌우 타격 차이 및 신인 능력은 게임용 추정; 공식 측정값 아님'
  out.append(r)
 (D/'details.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8');gallery.save(ROOT/'build/lg_rebuild/official_faces.jpg');print('선수/스태프',len(out),'전용 얼굴',sum(r['dedicated_face'] for r in out))
if __name__=='__main__':main()
