"""공식 신체 정보와 사진으로 외형 편집 명세를 만든다."""
import json,re,struct,cv2,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from hanwha_roster import ROOT,load
D=ROOT/'translation/hanwha_visual'
def body(h,w):
 bmi=w/(h/100)**2
 if bmi>=32:return 15 if h>=182 else 12
 if bmi>=28:return 14 if h>=185 else 12 if h<177 else 10
 if bmi>=25:return 9 if h>=190 else 10 if h>=180 else 6
 return 2 if h>=189 else 0 if h>=178 else 1
def main():
 rows=json.loads((D/'official_profiles.json').read_text('utf8'));roster={p['index']:p for p in load()['records']}
 old=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();face=cv2.FaceDetectorYN.create('onnx',np.frombuffer((ROOT/'tools/bin/face_detection_yunet_2023mar.onnx').read_bytes(),np.uint8),np.array([],np.uint8),(320,320),0.7)
 canvas=Image.new('RGB',(1000,((len(rows)+7)//8)*150),'#333333');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),13)
 for num,r in enumerate(rows):
  p=roster[r['index']];im=Image.open(ROOT/r.get('face_photo',r['photo'])).convert('RGBA');rgb=np.array(im.convert('RGB'));gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
  face.setInputSize(im.size);_,found=face.detect(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR));found=[] if found is None else [b for b in found if b[1]<im.height*.55]
  box=max(found,key=lambda b:b[2]*b[3]) if len(found) else (int(im.width*.30),int(im.height*.18),int(im.width*.38),int(im.width*.38))
  x,y,w,h=map(int,box[:4]);r['face_box']=[x,y,w,h];r['face_detection']='yunet' if len(found) else 'fallback_review'
  if len(found):r['landmarks']=[list(map(float,box[i:i+2])) for i in range(4,14,2)]
  # 유니폼 이름 필드는 NUL 포함 12바이트. 공식 영문 성과 이름 이니셜을 표기.
  tokens=re.findall('[A-Z]+',r['english'].upper());surname=tokens[0]
  overrides={'화이트':'WHITE','에르난데스':'HERNANDEZ','페라자':'PERAZA','왕옌청':'WANG Y.C.','주현상':'JOO H.S.','류현진':'RYU H.J.','하주석':'HA J.S.','손아섭':'SON A.S.'}
  latin=overrides.get(r['name'],surname+' '+'.'.join(t[0] for t in tokens[1:])+('.' if len(tokens)>1 else ''))
  if len(latin)>11:latin=surname
  assert len(latin)<=11 and latin
  r['back_name']=latin;r['body_type']=body(r['height'],r['weight'])
  o=5120+r['index']*192;r['face_id']=struct.unpack_from('<H',old,o+86)[0];r['original_body_type']=struct.unpack_from('<I',old,o+156)[0]>>27
  r['face_file']=f"F{r['face_id']}.CHK"
  view=im.crop((max(0,x-w*.2),max(0,y-h*.4),min(im.width,x+w*1.2),min(im.height,y+h*1.2)));view.thumbnail((120,120));cx=(num%8)*125;cy=(num//8)*150;canvas.paste(view,(cx,cy),view);draw.text((cx,cy+120),f"{r['index']} {r['name']}",font=font,fill='white')
 (D/'appearance.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8');canvas.save(ROOT/'build/hanwha_official_faces.jpg')
 print('외형 명세',len(rows),'검토 필요',[(r['name'],r['face_box']) for r in rows if r['face_detection']=='fallback_review'])
if __name__=='__main__':main()
