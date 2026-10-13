"""LG 구단 시각 자원: 원 UV, 글자 아틀라스와 파일 크기를 보존한다."""
import json,re,struct,hashlib
from functools import lru_cache
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT
from analyze import chunks
from hanwha_visual import decode,encode
D=ROOT/'translation/lg_brand';BLACK=(24,24,27);RED=(194,0,49);WHITE=(238,238,234)
def mark(name='logo04'):
 im=Image.open(D/(name+'.png')).convert('RGBA');im=im.crop((2,2,im.width-2,im.height-2));a=np.array(im)
 mask=(a[:,:,:3].min(2)<230) if name.endswith(('01','04')) else (a[:,:,:3].max(2)>65 if name.endswith(('03','06')) else (a[:,:,1]>80))
 a[:,:,3]=mask.astype('uint8')*255;im=Image.fromarray(a);return im.crop(im.getbbox())
def paste(im,art,box):
 x,y,w,h=box
 if w<1 or h<1:return
 art=art.copy();art.thumbnail((w,h),Image.Resampling.LANCZOS);im.alpha_composite(art,(x+(w-art.width)//2,y+(h-art.height)//2))
@lru_cache(maxsize=1)
def initial():
 # 공식 사진의 모자 앞 T를 사용한다. 선수 얼굴 영역은 포함하지 않는다.
 p=next(p for p in json.loads((ROOT/'translation/lg_2026/details.json').read_text('utf8')) if p['name']=='문보경')
 im=Image.open(ROOT/p['photo']).convert('RGBA');a=np.array(im);x,y,w,h=p['face_box'];cx=x+w//2
 crop=a[max(0,y-int(h*.65)):y+5,max(0,cx-int(w*.4)):cx+int(w*.4)]
 rgb=crop[:,:,:3].astype(float);mask=((rgb[:,:,0]>rgb[:,:,1]*1.6)&(rgb[:,:,0]>rgb[:,:,2]*1.35)&(rgb[:,:,0]>70)).astype('uint8')
 n,labels,stats,_=cv2.connectedComponentsWithStats(mask)
 if n<=1:raise AssertionError('공식 모자 T 검출 실패')
 k=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]);mask=(labels==k).astype('uint8');mask=cv2.dilate(mask,np.ones((3,3),np.uint8));crop[:,:,3]=mask*255
 out=Image.fromarray(crop);out=out.crop(out.getbbox())
 # 같은 붉은색의 모자 챙 테두리는 표장 아래에 있으므로 제외한다.
 out=out.crop((0,0,out.width,round(out.height*.70)));return out.crop(out.getbbox())
def recolor_fabric(a,target,mask):
 if not mask.any():return a
 lum=a[:,:,:3].mean(2);shade=np.clip(lum/max(float(np.quantile(lum[mask],.75)),1),.65,1.1)
 a[:,:,:3][mask]=np.clip(shade[:,:,None]*np.array(target),0,255).astype('uint8')[mask]
 return a
def shirt(im,variant):
 size=im.size;a=np.array(im.resize((256,256),Image.Resampling.BILINEAR).rotate(-90));yy,xx=np.indices(a.shape[:2]);fabric=yy>=88
 # 프런트의 양 끝 UV와 소매에 남은 원 일본 팀 표장을 지운다.
 old=np.zeros((256,256),np.uint8)
 for x0,y0,x1,y1 in [(0,148,58,206),(198,148,256,206),(52,88,87,124),(172,88,213,124)]:old[y0:y1,x0:x1]=255
 a[:,:,:3]=cv2.inpaint(a[:,:,:3],old,3,cv2.INPAINT_TELEA)
 home=variant=='H1';a=recolor_fabric(a,WHITE if home else BLACK if variant=='V1' else (178,183,188),fabric)
 if home:a[:,:,:3][fabric&((xx%12)==0)]=(51,51,55)
 # 원 주황색 파이핑과 검정 내복은 LG 검정/붉은색 계열로 통일.
 orange=(a[:,:,0].astype(float)>a[:,:,1]*1.3)&(a[:,:,1]>30)&~fabric;a[:,:,:3][orange]=BLACK
 im=Image.fromarray(a);art=mark('logo04' if home else 'logo06');art.thumbnail((92,29),Image.Resampling.LANCZOS)
 half=art.width//2
 # 단추 여밈의 실제 UV 경계는 0/256이 아니라 11/245이다.
 im.alpha_composite(art.crop((0,0,half,art.height)),(245-half,165))
 im.alpha_composite(art.crop((half,0,art.width,art.height)),(11,165))
 paste(im,mark('emblem01'),(57,96,23,18));paste(im,mark('emblem01'),(179,96,23,18))
 return im.rotate(90).resize(size,Image.Resampling.LANCZOS)
def image_for(im,n,variant):
 if n in (0,1):return shirt(im,variant)
 a=np.array(im);rgb=a[:,:,:3].astype(float)
 if n in (10,12,14,16):
  active=a[:,:,3]>0;a[:,:,:3][active]=BLACK;im=Image.fromarray(a)
  # 서로 다른 모자/헬멧 UV를 구분.
  box=(im.width*35//100,im.height*54//100,im.width*22//100,im.height*34//100) if n in (10,12) else (im.width//4,im.height//4,im.width//2,im.height//2)
  paste(im,initial(),box);return im
 if n in (18,20):
  # 이름/번호 글자 아틀라스에 로고를 덧씌우지 않는다.
  orange=(rgb[:,:,0]>rgb[:,:,1]*1.2)&(rgb[:,:,0]>rgb[:,:,2]*1.2)
  a[:,:,:3][orange]=RED if variant=='H1' else WHITE
  return Image.fromarray(a)
 if n in (3,5):
  bright=rgb.mean(2)>70;a=recolor_fabric(a,WHITE if variant=='H1' else (180,182,186),bright);return Image.fromarray(a)
 orange=(rgb[:,:,0]>rgb[:,:,1]*1.2)&(rgb[:,:,0]>rgb[:,:,2]*1.2);a[:,:,:3][orange]=RED
 return Image.fromarray(a)
def uniform(file,data,preview=False):
 cs={n:(o,b) for n,o,b in chunks(data)};out=bytearray(data);groups={};select=file in ('TMSEL.CHK','TMSELUNIG.CHK')
 if select:groups={n.replace('TA','PA',1):[n] for n in cs if n.startswith('TA00')}
 elif file.startswith('CT_'):groups={f'{int(n)+1:08}':[n] for n,(o,b) in cs.items() if n.isdigit() and b[:4]==b'PTXI' and f'{int(n)+1:08}' in cs}
 else:
  groups={'00000002':['00000000','00000001','00000007','00000008','00000009']}
  groups.update({f'{i+1:08}':[f'{i:08}'] for i in (3,5,10,12,14,16,18,20,23)})
 variant=next((v for v in ('H1','H2','V1') if v in file),'H1');regions=[]
 for pn,names in groups.items():
  if pn not in cs:continue
  po,pb=cs[pn];pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4).copy();modified=[]
  for name in names:
   if name not in cs:continue
   o,b=cs[name];a=decode(b);im=Image.fromarray(pal[a]);n=int(name) if name.isdigit() else 0
   if select:
    v=('H1','V1','H2')[int(name[-1])];ar=np.array(im);rgb=ar[:,:,:3].astype(float);yy,xx=np.indices(ar.shape[:2]);torso=(yy<42)&(ar[:,:,3]>0)
    orange=(rgb[:,:,0]>rgb[:,:,1]*1.25)&(rgb[:,:,1]>30)&(rgb[:,:,0]>rgb[:,:,2]*1.3);ar[:,:,:3][orange]=BLACK
    ar=recolor_fabric(ar,WHITE if v=='H1' else BLACK if v=='V1' else (178,183,188),torso)
    if v=='H1':ar[:,:,:3][torso&((xx%6)==0)]=(70,70,74)
    # 기존 가슴 글자 면과 모자 로고를 가린 후 해당 UV 안에 새 표장을 배치.
    ar[12:29,36:87,:3]=WHITE if v=='H1' else BLACK if v=='V1' else (178,183,188)
    ar[:,:,:3][(yy>=42)&(xx<40)&(ar[:,:,3]>0)]=BLACK
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
   if preview:Image.fromarray(pal[indices]).save(ROOT/'build/lg_brand'/f'{file}_{name}.png')
  out[po+16:po+len(pb)]=pal.tobytes();regions.append((po+16,len(pb)-16))
 assert len(out)==len(data)
 return out,[dict(file=file,offset=o,size=n,original=data[o:o+n].hex(),patched=out[o:o+n].hex(),reason='LG 홈 핀스트라이프/검정 원정 및 공식 로고, 글자 UV 보존') for o,n in regions if data[o:o+n]!=out[o:o+n]]
