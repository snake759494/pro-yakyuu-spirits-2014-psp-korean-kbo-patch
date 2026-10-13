"""한화 외형/유니폼: 원 CHK 크기·모델 구조·팔레트 용량을 보존한다."""
import json,struct,re,hashlib
import numpy as np,cv2
from PIL import Image,ImageDraw
from analyze import chunks
from inventory import ROOT
D=ROOT/'translation/hanwha_visual'
def spec():
 rows=json.loads((D/'appearance.json').read_text('utf8'))
 lg=ROOT/'translation/lg_2026/details.json'
 if lg.exists():rows.extend(json.loads(lg.read_text('utf8')))
 full=ROOT/'translation/kbo_2026/appearance.json'
 if full.exists():
  merged={r['index']:r for r in rows}
  for r in json.loads(full.read_text('utf8')):
   merged[r['index']]=dict(merged.get(r['index'],{}),**r)
  rows=list(merged.values())
 return rows
def files():
 from club_brand import files as club_files
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']
 return {r['face_file'] for r in spec() if r.get('dedicated_face',True)}|{e['name'] for e in inv if re.match(r'(?:AS_)?N0[0-9][A-Z]_',e['name']) or re.match(r'CT_N0[0-9][A-Z]_',e['name'])}|{'TMSELUNIE.CHK','TMSELUNIG.CHK','TMSEL.CHK','COMFACE.BIN'}|club_files()
def decode(b):
 fmt=b[12];assert fmt in (4,5)
 h=1<<b[9];stride=struct.unpack_from('<H',b,10)[0];bw=stride if fmt==5 else stride//2
 raw=np.frombuffer(b[16:],np.uint8).copy();assert len(raw)==h*bw
 if b[14]:raw=raw.reshape(h//8,bw//16,8,16).transpose(0,2,1,3).reshape(h,bw)
 else:raw=raw.reshape(h,bw)
 if fmt==5:return raw
 a=np.empty((h,stride),np.uint8);a[:,::2]=raw&15;a[:,1::2]=raw>>4;return a
def encode(a,b):
 if b[12]==4:a=a[:,::2]|(a[:,1::2]<<4)
 h,w=a.shape
 return a.reshape(h//8,8,w//16,16).transpose(0,2,1,3).tobytes() if b[14] else a.tobytes()
def recolor(im,target,mask=None):
 a=np.array(im).copy();rgb=a[:,:,:3].astype(float);lum=rgb.mean(2);shade=np.clip(lum/np.maximum(np.quantile(lum,.8),1),.35,1.15)
 out=np.clip(shade[:,:,None]*np.array(target),0,255).astype('uint8')
 if mask is None:a[:,:,:3]=out
 else:a[:,:,:3][mask]=out[mask]
 return Image.fromarray(a)
def logo(im,name,box):
 mark=Image.open(D/name).convert('RGBA');mark=mark.crop(mark.getbbox());x,y,w,h=box;mark.thumbnail((w,h),Image.Resampling.LANCZOS);im.alpha_composite(mark,(x+(w-mark.width)//2,y+(h-mark.height)//2))
def clean_red(im):
 a=np.array(im);r,g,b=[a[:,:,i].astype(float) for i in range(3)];mask=((r>g*1.20)&(r>b*1.15)&(r>40))|((r>100)&(g>75)&(b<g*.7))
 mask=cv2.dilate(mask.astype('uint8')*255,np.ones((3,3),np.uint8))
 a[:,:,:3]=cv2.inpaint(a[:,:,:3],mask,3,cv2.INPAINT_TELEA);return Image.fromarray(a)
NAVY=(24,29,42);ORANGE=(245,92,18)
def shirt(im,variant):
 size=im.size;im=im.resize((256,256),Image.Resampling.BILINEAR).rotate(-90)
 # 색 원단 전체를 inpaint하면 밑단 검정이 넓게 번진다. 구 로고만 지운다.
 a=np.array(im);marks=np.zeros((256,256),np.uint8)
 for x0,y0,x1,y1 in ((0,157,49,201),(208,157,256,201),(54,91,84,120),(175,91,211,120)):
  marks[y0:y1,x0:x1]=255
 a[:,:,:3]=cv2.inpaint(a[:,:,:3],marks,3,cv2.INPAINT_TELEA)
 yy,xx=np.indices(a.shape[:2]);torso=yy>=88
 color={'H1':(238,239,241),'H2':ORANGE,'H3':NAVY,'V1':(177,182,189)}[variant]
 rgb=a[:,:,:3].astype(float);lum=rgb.mean(2);reference=max(float(np.median(lum[140:235,85:170])),1)
 shade=np.clip(lum/reference,.68,1.15)
 a[:,:,:3][torso]=np.clip(shade[:,:,None]*np.array(color),0,255).astype(np.uint8)[torso]
 im=Image.fromarray(a)
 red=(rgb[:,:,0]>rgb[:,:,1]*1.2)&(rgb[:,:,0]>rgb[:,:,2]*1.15)&~torso
 im=recolor(im,NAVY,red)
 # 프런트 UV가 텍스처 양 끝으로 갈라져 있다. 로고도 정확히 같은 경계로 분할.
 word='home' if variant in ('H1','H2') else 'away';ink='white' if variant in ('H2','H3') else 'orange'
 mark=Image.open(D/f'ci_wordmark_{word}_{ink}.png').convert('RGBA');mark=mark.crop(mark.getbbox());mark.thumbnail((84,32),Image.Resampling.LANCZOS)
 layer=Image.new('RGBA',(256,256));x=256-mark.width//2;y=164
 layer.alpha_composite(mark,(x,y));layer.alpha_composite(mark,(x-256,y));im=Image.alpha_composite(im,layer)
 # 기존 라쿠텐 소매 표기를 지운 영역은 한화의 오렌지 E로 표시.
 logo(im,'ci_initial_orange.png',(52,92,20,15));logo(im,'ci_initial_orange.png',(184,92,20,15))
 return im.rotate(90).resize(size,Image.Resampling.LANCZOS)
def cap(im,idx):
 size=im.size;im=im.resize((128,64) if idx==10 else (64,64),Image.Resampling.BILINEAR)
 im=recolor(im,NAVY);im=clean_red(im)
 # old cream emblem also disappears under the navy fabric repaint.
 a=np.array(im);bright=(a[:,:,:3].mean(2)>28);a[:,:,:3][bright]=NAVY;im=Image.fromarray(a)
 box=(45,36,24,22) if idx==10 else (17,18,30,31)
 logo(im,'ci_initial_orange.png',box);return im.resize(size,Image.Resampling.LANCZOS)
def uniform_image(im,idx,variant):
 if idx in (0,1):return shirt(im,variant)
 if idx in (10,12,14,16):return cap(im,10 if idx in (10,12) else 14)
 a=np.array(im);rgb=a[:,:,:3].astype(float);red=(rgb[:,:,0]>rgb[:,:,1]*1.2)&(rgb[:,:,0]>rgb[:,:,2]*1.15)
 if idx in (18,20):
  # 등 이름/등번호의 원 글자 모양을 보존하며 한화 색상으로 바꾼다.
  bright=rgb.mean(2)>70;target=(255,255,255) if variant in ('H2','H3') else ORANGE
  a[:,:,:3][bright]=target;a[:,:,:3][~bright]=NAVY;return Image.fromarray(a)
 if red.any():return recolor(im,NAVY,red)
 return im
_TONE=None
def skin_targets():
 """원본 얼굴 텍스처(F*.CHK)의 볼 LAB 중앙값을 원래 주인의 피부 유형별로 모은 목표 톤."""
 global _TONE
 if _TONE is not None:return _TONE
 from ui_textures import original_chunks
 pd=next(b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes()) if n=='PDN')
 inv={e['name'] for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']};groups={}
 for i in range(len(pd)//192):
  r=pd[i*192:(i+1)*192];fid=struct.unpack_from('<H',r,86)[0];name=f'F{fid}.CHK'
  if name not in inv:continue
  try:
   cs=original_chunks(name);pal=np.frombuffer(cs['00000004'][16:],np.uint8).reshape(-1,4);a=pal[decode(cs['00000003'])][:,:,:3]
  except Exception:continue
  h,w=a.shape[:2];lab=cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[int(h*.40):int(h*.60),int(w*.30):int(w*.70)].reshape(-1,3)
  groups.setdefault((struct.unpack_from('<I',r,152)[0]>>23)&7,[]).append(np.median(lab,axis=0))
 _TONE={k:np.median(np.array(v),axis=0) for k,v in groups.items()}
 return _TONE
def match_tone(im,row):
 """합성 후 얼굴 피부(볼 영역) 톤을 원본 같은 피부 유형 얼굴의 톤에 맞춘다. 머리카락·눈썹 등 어두운 부분은 약하게."""
 t=skin_targets().get(row.get('skin_type',0),skin_targets()[0])
 a=np.array(im);h,w=a.shape[:2]
 # 어두운 픽셀은 가중치가 낮아 한 번에 목표에 닿지 않으므로 볼 중앙값이 목표에 가까워질 때까지 반복.
 for _ in range(8):
  lab=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)
  delta=t-np.median(lab[int(h*.40):int(h*.60),int(w*.30):int(w*.70)].reshape(-1,3),axis=0);delta[1:]=np.clip(delta[1:],-12,12)
  if abs(delta[0])<2:break
  weight=np.clip((lab[:,:,0]-15)/40,.5,1)
  a[:,:,:3]=cv2.cvtColor(np.clip(lab+weight[:,:,None]*delta,0,255).astype(np.uint8),cv2.COLOR_LAB2RGB)
 return Image.fromarray(a)
def face_image(im,row):
 # 머리 모델 음영 기준(skin_base)은 얼굴을 어둡게 만들어 쓰지 않는다. 최종 톤은 match_tone.
 # 슬롯의 원래 얼굴(예: 피부가 짙은 원 선수)이 사진 바깥 가장자리에 남지 않도록 바탕부터 목표 톤으로 맞춘다.
 im=match_tone(im,row)
 photo=Image.open(ROOT/row.get('face_photo',row['photo'])).convert('RGB');src=np.array(photo)
 lm=np.array(row['landmarks'],np.float32);eyes=lm[:2][np.argsort(lm[:2,0])];mouth=lm[3:5].mean(0)
 m=cv2.getAffineTransform(np.array([eyes[0],eyes[1],mouth],np.float32),np.array([[21,14],[41,14],[32,39]],np.float32))
 warped=cv2.warpAffine(src,m,(64,64),flags=cv2.INTER_AREA,borderMode=cv2.BORDER_REFLECT_101)
 from face_blend import blend
 base=blend(np.array(im.resize((64,64))),warped,(32,29),(22,26),(slice(22,35),slice(23,41)))
 return match_tone(Image.fromarray(base).resize(im.size,Image.Resampling.LANCZOS),row)

def skin_base(im,row,portrait=False):
 """얼굴 외곽·귀·목을 선택한 몸 피부 팔레트와 같은 색 계열로 맞춘다."""
 if 'skin_reference_head' not in row:return im
 from ui_textures import original_chunks
 cs=original_chunks('GMCOMMON.CHK');n=row['skin_reference_head']
 pal=np.frombuffer(cs[f'HEAD{n}PM'][16:],np.uint8).reshape(-1,4)
 ref=np.array(Image.fromarray(pal[decode(cs[f'HEAD{n}TM'])]).resize(im.size,Image.Resampling.BILINEAR))
 a=np.array(im);lab=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)
 target=cv2.cvtColor(ref[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)
 sample=lab[29:36,13:24] if portrait else lab[22:35,10:19]
 delta=np.median(target[22:35,10:19].reshape(-1,3),axis=0)-np.median(sample.reshape(-1,3),axis=0)
 rgb=a[:,:,:3].astype(float)
 weight=np.clip((lab[:,:,0]-30)/45,0,1)*np.clip((rgb[:,:,0]-rgb[:,:,2]-8)/20,0,1)
 corrected=np.clip(lab+weight[:,:,None]*delta,0,255).astype(np.uint8)
 a[:,:,:3]=cv2.cvtColor(corrected,cv2.COLOR_LAB2RGB)
 return Image.fromarray(a)
def apply(file,data,preview=False):
 from club_brand import find as club_find,uniform as club_uniform
 if club_find(file):return club_uniform(file,data,preview)
 if 'N00G_' in file or file=='TMSELUNIG.CHK':
  from lg_brand import uniform
  return uniform(file,data,preview)
 if file=='TMSEL.CHK':
  from lg_brand import uniform
  data,lg_report=uniform(file,data,preview)
  data,club_report=club_uniform(file,data,preview);lg_report+=club_report
 else:lg_report=[]
 if file=='COMFACE.BIN':
  from hanwha_portraits import apply as portraits
  return portraits(data,preview)
 if ('N06E_' not in file) and (re.match(r'(?:AS_)?N0[0-9][A-Z]_',file) or re.match(r'CT_N0[0-9][A-Z]_',file)):
  return apply_kbo_uniform(file,data,preview)
 rows={r['face_file']:r for r in spec()};cs={n:(o,b) for n,o,b in chunks(data)};out=bytearray(data);regions=[];groups={}
 face=file in rows
 if file in ('TMSELUNIE.CHK','TMSEL.CHK'):
  for n,(o,b) in cs.items():
   if n.startswith('TA06'):groups.setdefault('PA'+n[2:],[]).append(n)
 elif face:groups={'00000004':['00000003']}
 elif file.startswith('CT_'):
  for n,(o,b) in cs.items():
   if b[:4]==b'PTXI':groups.setdefault(f'{int(n)+1:08}',[]).append(n)
 else:
  groups={'00000002':['00000000','00000001','00000007','00000008','00000009']}
  for i in (3,5,10,12,14,16,18,20,23):groups[f'{i+1:08}']=[f'{i:08}']
 variant=next((k for k in ('H1','H2','H3','V1') if k in file),'H1')
 for palname,names in groups.items():
  po,pb=cs[palname];pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4);modified=[]
  for name in names:
   o,b=cs[name];a=decode(b);im=Image.fromarray(pal[a]);idx=int(name) if name.isdigit() else 0
   if face:im=face_image(im,rows[file])
   elif file in ('TMSELUNIE.CHK','TMSEL.CHK'):
    vv=('H1','V1','H2','H3')[int(name[-1])];im=clean_red(im);color={'H1':(238,239,241),'H2':ORANGE,'H3':NAVY,'V1':(177,182,189)}[vv];im=recolor(im,color)
    a=np.array(im);mask=np.zeros(a.shape[:2],np.uint8);mask[12:29,36:87]=255;a[:,:,:3]=cv2.inpaint(a[:,:,:3],mask,3,cv2.INPAINT_TELEA);im=Image.fromarray(a)
    yy,xx=np.indices(a.shape[:2]);im=recolor(im,NAVY,(yy>=43)&(xx<40))
    logo(im,f"ci_wordmark_{'home' if vv in ('H1','H2') else 'away'}_{'white' if vv in ('H2','H3') else 'orange'}.png",(36,14,51,21))
   elif file.startswith('CT_'):
    im=recolor(im,NAVY);logo(im,'ci_initial_orange.png',(im.width//3,im.height//3,max(8,im.width//3),max(8,im.height//3)))
   else:im=uniform_image(im,idx,variant)
   modified.append((name,np.array(im),b))
  count=min(len(pal),16 if any(b[12]==4 for _,_,b in modified) else 256)
  flat=np.concatenate([im.reshape(-1,4) for _,im,_ in modified]);q=Image.fromarray(flat.reshape(1,-1,4),'RGBA').quantize(colors=count,method=Image.Quantize.FASTOCTREE)
  qi=np.array(q).reshape(-1);qp=np.array(q.convert('RGBA')).reshape(-1,4);newpal=pal.copy()
  for i in range(count):
   where=np.flatnonzero(qi==i)
   if len(where):newpal[i]=qp[where[0]]
  cursor=0
  for name,im,b in modified:
   h,w=im.shape[:2];indices=qi[cursor:cursor+h*w].reshape(h,w);cursor+=h*w;o=cs[name][0]
   packed=encode(indices,b);assert len(packed)==len(b)-16
   out[o+16:o+len(b)]=packed;regions.append((o+16,len(packed)))
   if preview and (face or name in ('00000000','00000010') or file in ('TMSELUNIE.CHK','TMSEL.CHK')):
    pd=ROOT/'build/hanwha_visual';pd.mkdir(exist_ok=True);Image.fromarray(newpal[indices]).save(pd/f'{file}_{name}.png')
  out[po+16:po+len(pb)]=newpal.tobytes();regions.append((po+16,len(pb)-16))
 assert len(out)==len(data)
 report=[dict(file=file,offset=o,size=n,original=data[o:o+n].hex(),patched=out[o:o+n].hex(),reason='공식 한화 사진 기반 얼굴 텍스처' if face else '한화 유니폼/모자/등 글자 색상') for o,n in regions if data[o:o+n]!=out[o:o+n]]
 return out,lg_report+report

def apply_kbo_uniform(file,data,preview=False):
 """10개 참가 슬롯의 NPB 원단을 대응 KBO 구단 색상·공식 엠블럼으로 교체."""
 from kbo_logos import CODES
 teams=[('LG',(185,25,45)),('SS',(0,58,140)),('HT',(195,25,45)),('WO',(20,38,80)),('KT',(0,34,70)),('LT',(0,49,116)),('HH',ORANGE),('OB',(0,35,86)),('SK',(200,20,35)),('NC',(25,75,150))]
 idx=int(re.search(r'N(\d\d)',file).group(1));code,color=teams[idx]
 cs={n:(o,b) for n,o,b in chunks(data)};out=bytearray(data);regions=[]
 is_select=file in ('TMSELUNIE.CHK','TMSEL.CHK')
 groups={}
 if is_select:
  # Only selected team's TAxx texture set is rewritten.
  prefix=f'TA{idx+1:02d}';groups={n[2:] for n in cs if n.startswith(prefix) and n.endswith('T')}
  groups={f'P{g}':[f'T{g}'] for g in groups if f'P{g}' in cs}
 elif file.startswith('CT_'):
  groups={f'{int(n)+1:08}':[n] for n,(o,b) in cs.items() if n.isdigit() and b[:4]==b'PTXI' and f'{int(n)+1:08}' in cs}
 else:
  groups={'00000002':['00000000','00000001','00000007','00000008','00000009']}
  for i in (3,5,10,12,14,16,18,20,23):groups[f'{i+1:08}']=[f'{i:08}']
 for pn,names in groups.items():
  if pn not in cs:continue
  po,pb=cs[pn];pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4).copy();modified=[]
  for name in names:
   if name not in cs:continue
   o,b=cs[name];a=decode(b);im=Image.fromarray(pal[a]);n=int(name) if name.isdigit() else 0
   if is_select:
    variant=('H1','V1','H2','H3')[n%4];im=clean_red(im);im=recolor(im,color);yy,xx=np.indices((im.height,im.width));arr=np.array(im);mask=np.zeros(arr.shape[:2],np.uint8);mask[12:29,36:87]=255;arr[:,:,:3]=cv2.inpaint(arr[:,:,:3],mask,3,cv2.INPAINT_TELEA);im=Image.fromarray(arr)
    logo(im,f"../kbo_logos/{code}.png",(36,14,51,21))
   elif file.startswith('CT_'):
    im=recolor(im,color)
   else:
    im=clean_red(im);arr=np.array(im);red=(arr[:,:,0]>arr[:,:,1]*1.2)&(arr[:,:,0]>arr[:,:,2]*1.15);im=recolor(im,color,red)
    if n in (0,1):
     yy,xx=np.indices((im.height,im.width));fabric=yy>=88;arr=np.array(im);rgb=arr[:,:,:3].astype(float);lum=rgb.mean(2);shade=np.clip(lum/max(float(np.quantile(lum,.8)),1),.35,1.15);arr[:,:,:3][fabric]=np.clip(shade[:,:,None]*np.array(color),0,255).astype('uint8')[fabric];im=Image.fromarray(arr)
    if n in (0,1,3,5,10,12,14,16,18,20,23):logo(im,f'../kbo_logos/{code}.png',(im.width//3,im.height//3,max(8,im.width//3),max(8,im.height//3)))
   modified.append((name,np.array(im),b))
  if not modified:continue
  q=Image.fromarray(np.concatenate([x[1].reshape(-1,4) for x in modified]).reshape(1,-1,4),'RGBA').quantize(colors=min(len(pal),256),method=Image.Quantize.FASTOCTREE);ix=np.array(q).reshape(-1);qp=np.array(q.convert('RGBA')).reshape(-1,4);newpal=pal.copy()
  for j in range(min(len(pal),256)):
   pos=np.flatnonzero(ix==j)
   if len(pos):newpal[j]=qp[pos[0]]
  cursor=0
  for name,im,b in modified:
   h,w=im.shape[:2];packed=encode(ix[cursor:cursor+h*w].reshape(h,w),b);cursor+=h*w;o=cs[name][0];out[o+16:o+len(b)]=packed;regions.append((o+16,len(packed)))
  out[po+16:po+len(pb)]=newpal.tobytes();regions.append((po+16,len(pb)-16))
 report=[dict(file=file,offset=o,size=n,original=data[o:o+n].hex(),patched=out[o:o+n].hex(),reason=f'{code} KBO 유니폼 색상·공식 로고') for o,n in regions if out[o:o+n]!=data[o:o+n]]
 return out,report


