"""공유 팔레트를 보존하며 한화의 메뉴용 얼굴과 모자/상의 합성판을 변경한다."""
import struct
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from analyze import chunks
from inventory import ROOT

def portrait_targets(data,pal,decode):
 """원본 메뉴 초상화의 볼 LAB 중앙값을 원래 선수 피부 유형별로 모은다(원 PDTPLIST 순번)."""
 cs={n:b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())};pd=cs['PDN']
 order=struct.unpack('<2535H',cs['INIPLIST']);idmap={struct.unpack_from('<H',pd,i*192+84)[0]:i for i in range(len(pd)//192)};g={}
 for pos,gid in enumerate(order):
  if gid not in idmap or (pos+1)*6144>len(data):continue
  r=pd[idmap[gid]*192:idmap[gid]*192+192]
  if (r[168]&7)==4:continue
  a=pal[decode(data[pos*6144:pos*6144+4112])];
  if a[28:35,13:24,3].min()<200:continue
  lab=cv2.cvtColor(a[28:35,13:24,:3],cv2.COLOR_RGB2LAB).reshape(-1,3)
  g.setdefault((struct.unpack_from('<I',r,152)[0]>>23)&7,[]).append(np.median(lab,axis=0))
 base=np.median(np.array([x for v in g.values() for x in v]),axis=0)
 # 초상화 순번과 선수 대응은 구단별 시작표를 거쳐 정확하지 않으므로, 전체 초상화 중앙값(대부분 일본 선수=유형0)에
 # 원본 3D 얼굴 텍스처에서 측정한 유형별 LAB 차이를 더한다.
 from hanwha_visual import skin_targets
 ft=skin_targets()
 return {k:base+(v-ft[0]) for k,v in ft.items()}
def match_portrait(im,target):
 a=np.array(im)
 for _ in range(8):
  lab=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)
  delta=target-np.median(lab[28:35,13:24].reshape(-1,3),axis=0);delta[1:]=np.clip(delta[1:],-12,12)
  if abs(delta[0])<2:break
  w=np.clip((lab[:,:,0]-15)/40,.5,1)*(a[:,:,3]>0)
  a[:,:,:3]=cv2.cvtColor(np.clip(lab+w[:,:,None]*delta,0,255).astype(np.uint8),cv2.COLOR_LAB2RGB)
 return Image.fromarray(a)
def apply(data,preview=False):
 from hanwha_visual import spec,decode,encode,recolor,logo,NAVY
 cs={n:b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())}
 order=list(struct.unpack('<2535H',cs['INIPLIST']))
 menu={n:b for n,o,b in chunks((ROOT/'work/assets/MENU2D.CHK').read_bytes())}
 pal=np.frombuffer(menu['COMFACEP'][16:],np.uint8).reshape(-1,4)
 from kbo_team_layout import layouts
 portrait_order={p['index']:t['start']+i for t in layouts().values() for i,p in enumerate(t['rows'])}
 # 실제 loader 08a622c8은 PDTPLIST의 구단 내 순번에 별도 표 08a96878의
 # 시작 위치를 더한다. kbo_identity_code가 그 표도 함께 동기화한다.
 from club_brand import configs
 clubs={2452+c['team_id']:dict(c,code=code) for code,c in configs().items()}
 entries=[(portrait_order[p['index']],p) for p in spec()]+[(2458,None),(2452,None)]+[(i,None) for i in clubs]
 targets=portrait_targets(data,pal,decode)
 out=bytearray(data);report=[];gallery=Image.new('RGBA',(8*96,((len(entries)+7)//8)*96));draw=ImageDraw.Draw(gallery)
 assert len({i for i,p in entries})==len(entries)
 colors=pal.astype(float);colors[:,:3]*=colors[:,3:4]/255
 for j,(i,p) in enumerate(entries):
  start=i*6144;b=data[start:start+4112];a=decode(b);im=Image.fromarray(pal[a])
  if p:
   source=np.array(Image.open(ROOT/p.get('face_photo',p['photo'])).convert('RGB'))
   lm=np.array(p['landmarks'],np.float32);eyes=lm[:2][np.argsort(lm[:2,0])]
   matrix=cv2.getAffineTransform(np.array([eyes[0],eyes[1],lm[3:5].mean(0)],np.float32),np.array([[12.5,24],[24,24],[18.5,37]],np.float32))
   warped=cv2.warpAffine(source,matrix,(64,64),borderMode=cv2.BORDER_REFLECT_101)
   from face_blend import blend
   im=match_portrait(im,targets.get(p.get('skin_type',0),targets[0]))
   base=blend(np.array(im),warped,(18.5,31),(15,20),(slice(28,35),slice(13,24)))
   # 원본 같은 피부 유형 초상화의 볼 톤에 맞춘다(사진 조명·기존 슬롯 얼굴의 어두움 제거).
   im=match_portrait(Image.fromarray(base),targets.get(p.get('skin_type',0),targets[0]))
  else:
   base=np.array(im);yy,xx=np.indices(base.shape[:2]);im=recolor(im,NAVY,yy<30)
   # 기존 cap의 흰 E 잔재를 덮고 공식 한화 E를 넣는다.
   base=np.array(im);mask=(yy<30)&(base[:,:,3]>0);base[:,:,:3][mask]=NAVY;im=Image.fromarray(base)
   if i in clubs:
    c=clubs[i];a=np.array(im);a[:,:,:3][(yy<30)&(a[:,:,3]>0)]=c['cap_color'];im=Image.fromarray(a)
    from lg_brand import paste
    cap=Image.open(ROOT/c['asset_dir']/'cap.png').convert('RGBA');paste(im,cap.crop(cap.getbbox()),(13,5,11,12))
   elif i==2452:
    from lg_brand import initial,paste
    paste(im,initial(),(13,5,11,12))
   else:logo(im,'ci_initial_orange.png',(13,5,11,12))
   base=np.array(im);red=(base[:,:,0].astype(float)>base[:,:,1]*1.2)&(base[:,:,0].astype(float)>base[:,:,2]*1.15)&(yy>=30)
   im=recolor(im,NAVY,red)
  rgba=np.array(im).astype(float);rgba[:,:,:3]*=rgba[:,:,3:4]/255;indices=np.empty((64,64),np.uint8)
  for y in range(64):indices[y]=((rgba[y,:,None,:]-colors[None,:,:])**2).sum(2).argmin(1)
  raw=encode(indices,b);out[start+16:start+4112]=raw
  report.append(dict(file='COMFACE.BIN',offset=start+16,size=4096,original=b[16:].hex(),patched=raw.hex(),reason=(p['name']+' 공식 사진 기반 메뉴 초상화') if p else ('LG' if i==2452 else '한화')+' 메뉴 모자/상의 합성판'))
  if preview:
   result=Image.fromarray(pal[indices]);gallery.paste(result.resize((80,80)),((j%8)*96,(j//8)*96));draw.text(((j%8)*96,(j//8)*96+80),str(i),fill='white')
 if preview:gallery.save(ROOT/'build/hanwha_visual/portraits.png')
 assert len(out)==len(data)
 return out,report
