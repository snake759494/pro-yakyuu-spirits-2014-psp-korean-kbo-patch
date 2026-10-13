"""구단별 시각 자원: 원 UV, 글자 아틀라스와 파일 크기를 보존한다."""
import json,re,struct,hashlib
from functools import lru_cache
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT
from analyze import chunks
from hanwha_visual import decode,encode
BLACK=(24,24,27);RED=(194,0,49);WHITE=(238,238,234)
def configs():return json.loads((ROOT/'translation/club_brand.json').read_text('utf8'))
def find(file):
 for code,c in configs().items():
  if c['uniform']+'_' in file or file=='TMSELUNI'+c.get('select_asset',c['asset'])+'.CHK':return code
 return None
def files():return {'TMSELUNI'+c.get('select_asset',c['asset'])+'.CHK' for c in configs().values()}
def mark(name='logo04'):
 path=ROOT/C['asset_dir']/('home_word.png' if name=='logo04' else 'away_word.png') if name.startswith('logo') else ROOT/'translation/kbo_logos'/(C['code']+'.png')
 im=Image.open(path).convert('RGBA');return im.crop(im.getbbox())
def paste(im,art,box):
 x,y,w,h=box
 if w<1 or h<1:return
 art=art.copy();art.thumbnail((w,h),Image.Resampling.LANCZOS);im.alpha_composite(art,(x+(w-art.width)//2,y+(h-art.height)//2))
def initial():
 im=Image.open(ROOT/C['asset_dir']/'cap.png').convert('RGBA');return im.crop(im.getbbox())
def recolor_fabric(a,target,mask):
 if not mask.any():return a
 lum=a[:,:,:3].mean(2);shade=np.clip(lum/max(float(np.quantile(lum[mask],.75)),1),.65,1.1)
 a[:,:,:3][mask]=np.clip(shade[:,:,None]*np.array(target),0,255).astype('uint8')[mask]
 return a

@lru_cache(maxsize=1)
def plain_fabric():
 # 동일 재단의 무지 원단에서 주름만 가져온다. 핀스트라이프/옆선/목 뒤 원 구단 표장 잔류 방지.
 from inventory import ISO
 es=json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd'];e=next(e for e in es if e['name']=='N01D_H1D.CHK')
 with ISO.open('rb') as f:f.seek(e['offset']);cs={n:b for n,o,b in chunks(f.read(e['size']))}
 pal=np.frombuffer(cs['00000002'][16:],np.uint8).reshape(-1,4)
 return np.array(Image.fromarray(pal[decode(cs['00000000'])]).rotate(-90))
def shirt(im,variant):
 size=im.size;a=np.array(im.resize((256,256),Image.Resampling.BILINEAR).rotate(-90));yy,xx=np.indices(a.shape[:2]);fabric=yy>=88
 if C.get('plain_template'):a[:,:,:3]=plain_fabric()[:,:,:3]
 # 프런트의 양 끝 UV와 소매에 남은 원 일본 팀 표장을 지운다.
 old=np.zeros((256,256),np.uint8)
 for x0,y0,x1,y1 in [(0,148,58,206),(198,148,256,206),(52,88,87,124),(172,88,213,124),(114,126,137,141)]:old[y0:y1,x0:x1]=255
 a[:,:,:3]=cv2.inpaint(a[:,:,:3],old,3,cv2.INPAINT_TELEA)
 home=variant=='H1';a=recolor_fabric(a,tuple(C['home_color']) if home else tuple(C['away_color']) if variant=='V1' else tuple(C['alternate_color']),fabric)
 if home and C['pinstripe']:a[:,:,:3][fabric&((xx%12)==0)]=C['cap_color']
 if C.get('side_color'):
  side=fabric&(((xx>65)&(xx<90)&(yy>155))|((xx>165)&(xx<190)&(yy>155)))
  a[:,:,:3][side]=C['side_color']
 # 원 주황색 파이핑과 검정 내복은 LG 검정/붉은색 계열로 통일.
 orange=(a[:,:,0].astype(float)>a[:,:,1]*1.3)&(a[:,:,1]>30)&~fabric;a[:,:,:3][orange]=BLACK
 im=Image.fromarray(a);art=mark('logo04' if home else 'logo06');art.thumbnail((92,29),Image.Resampling.LANCZOS)
 half=art.width//2
 # 단추 여밈의 실제 UV 경계는 0/256이 아니라 11/245이다.
 im.alpha_composite(art.crop((0,0,half,art.height)),(245-half,165))
 im.alpha_composite(art.crop((half,0,art.width,art.height)),(11,165))
 sleeve=mark('emblem01').rotate(180)
 paste(im,sleeve,(57,96,23,18));paste(im,sleeve,(179,96,23,18))
 return im.rotate(90).resize(size,Image.Resampling.LANCZOS)
def image_for(im,n,variant):
 if n in (0,1):return shirt(im,variant)
 a=np.array(im);rgb=a[:,:,:3].astype(float)
 if n in (10,12,14,16):
  active=a[:,:,3]>0;a[:,:,:3][active]=C['cap_color'];im=Image.fromarray(a)
  # 서로 다른 모자/헬멧 UV를 구분.
  box=(round(im.width*56/128),round(im.height*41/64),round(im.width*15/128),round(im.height*18/64)) if n in (10,12) else (round(im.width*40/64),round(im.height*21/64),round(im.width*12/64),round(im.height*15/64))
  paste(im,initial(),box);return im
 if n in (18,20):
  # 이름/번호 글자 아틀라스에 로고를 덧씌우지 않는다.
  ink=a[:,:,3]>0
  a[:,:,:3][ink]=C.get('home_letter_color',C['cap_color']) if variant=='H1' else C.get('away_letter_color',WHITE)
  return Image.fromarray(a)
 if n in (3,5):
  # 3/5는 바지가 아니라 팔 안쪽 긴소매다. 밝은 부분만 흰색으로 바꾸면 얼룩이 생긴다.
  fabric=(a[:,:,3]>0)&(rgb.max(2)>20)
  a=recolor_fabric(a,tuple(C.get('undershirt_color',C['cap_color'])),fabric);return Image.fromarray(a)
 # 7/8/9는 바지·양말·신발 아틀라스. 흰 바지는 보존하고 원 구단의 유색 원단만 교체한다.
 colored=(rgb.max(2)-rgb.min(2)>25)&(a[:,:,3]>0)
 a=recolor_fabric(a,tuple(C['cap_color']),colored)
 return Image.fromarray(a)
def uniform(file,data,preview=False,code=None):
 global C
 if file=='TMSEL.CHK' and code is None:
  reports=[]
  for code in configs():data,r=uniform(file,data,preview,code);reports+=r
  return data,reports
 code=code or find(file)
 if code is None:return data,[]
 C=dict(configs()[code],code=code)

 cs={n:(o,b) for n,o,b in chunks(data)};out=bytearray(data);groups={};select=file.startswith('TMSEL')
 if select:groups={n.replace('TA','PA',1):[n] for n in cs if n.startswith(f"TA{C['team_id']:02}")}
 elif file.startswith('CT_'):groups={f'{int(n)+1:08}':[n] for n,(o,b) in cs.items() if n.isdigit() and b[:4]==b'PTXI' and f'{int(n)+1:08}' in cs}
 else:
  groups={'00000002':['00000000','00000001','00000007','00000008','00000009']}
  groups.update({f'{i+1:08}':[f'{i:08}'] for i in (3,5,10,12,14,16,18,20,23)})
 match=re.search(r'_([HVC][1-9])',file);variant=match.group(1) if match else 'H1';regions=[]
 for pn,names in groups.items():
  if pn not in cs:continue
  po,pb=cs[pn];pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4).copy();modified=[]
  for name in names:
   if name not in cs:continue
   o,b=cs[name];a=decode(b);im=Image.fromarray(pal[a]);n=int(name) if name.isdigit() else 0
   if select:
    v=('H1','V1','H2','H3','H4','H5')[int(name[-1])];ar=np.array(im);rgb=ar[:,:,:3].astype(float);yy,xx=np.indices(ar.shape[:2]);torso=(yy<42)&(ar[:,:,3]>0)
    orange=(rgb[:,:,0]>rgb[:,:,1]*1.25)&(rgb[:,:,1]>30)&(rgb[:,:,0]>rgb[:,:,2]*1.3);ar[:,:,:3][orange]=BLACK
    ar=recolor_fabric(ar,tuple(C['home_color']) if v=='H1' else tuple(C['away_color']) if v=='V1' else tuple(C['alternate_color']),torso)
    # 작은 선택 그림은 원본 줄무늬와 목/소매 표장이 남지 않게 알파 실루엣 안에서 재구성한다.
    ar[:,:,:3][torso]=C['home_color'] if v=='H1' else C['away_color'] if v=='V1' else C['alternate_color']
    if v=='H1' and C['pinstripe']:ar[:,:,:3][torso&((xx%6)==0)]=C['cap_color']
    # 기존 가슴 글자 면과 모자 로고를 가린 후 해당 UV 안에 새 표장을 배치.
    ar[12:29,36:87,:3]=tuple(C['home_color']) if v=='H1' else tuple(C['away_color']) if v=='V1' else tuple(C['alternate_color'])
    ar[:,:,:3][(yy>=42)&(xx<40)&(ar[:,:,3]>0)]=C['cap_color']
    im=Image.fromarray(ar);paste(im,mark('logo04' if v=='H1' else 'logo06'),(36,14,51,20));paste(im,initial(),(13,49,12,12))
   elif file.startswith('CT_'):im=shirt(im,variant)
   else:im=image_for(im,n,variant)
   modified.append((name,np.array(im),b))
  if not modified:continue
  count=min(len(pal),16 if any(b[12]==4 for _,_,b in modified) else 256)
  flat=np.concatenate([a.reshape(-1,4) for _,a,_ in modified]);q=Image.fromarray(flat.reshape(1,-1,4),'RGBA').quantize(colors=count,method=Image.Quantize.FASTOCTREE);ix=np.array(q).reshape(-1);rgba=np.array(q.convert('RGBA')).reshape(-1,4)
  for i in range(count):
   k=np.flatnonzero(ix==i)
   if len(k):pal[i]=rgba[k[0]]
  cur=0
  for name,a,b in modified:
   h,w=a.shape[:2];indices=ix[cur:cur+h*w].reshape(h,w);cur+=h*w;o=cs[name][0];packed=encode(indices,b);out[o+16:o+len(b)]=packed;regions.append((o+16,len(packed)))
   if preview:Image.fromarray(pal[indices]).save(ROOT/'build/club_brand'/f'{file}_{name}.png')
  out[po+16:po+len(pb)]=pal.tobytes();regions.append((po+16,len(pb)-16))
 assert len(out)==len(data)
 return out,[dict(file=file,offset=o,size=n,original=data[o:o+n].hex(),patched=out[o:o+n].hex(),reason=C['code']+' 구단별 홈/원정/모자/소매 및 글자 UV 보존') for o,n in regions if data[o:o+n]!=out[o:o+n]]
