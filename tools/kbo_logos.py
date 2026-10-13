"""공식 KBO 엠블럼을 원본 아이콘 영역과 팔레트 용량 안에 삽입한다."""
import json,hashlib
import numpy as np
from PIL import Image
from inventory import ROOT
from analyze import chunks
from menu_texture import decode_indices,encode_indices
CODES=['LG','SS','HT','WO','KT','LT','HH','OB','SK','NC']
RECTS=[(53,19),(68,19),(83,19),(98,19),(113,19),(53,34),(68,34),(83,34),(98,34),(113,34)]
BIG={f'PET_{name}{variant}.CHK':code for name,code in zip(['G','D','C','YS','DB','T','E','F','L','BS'],CODES) for variant in (1,2)}
from kbo_identity import ASSET_CODE
TEAM_ICON_CODES={f'TEAM{a}_{v}.CHK':c for a,c in ASSET_CODE.items() for v in ('H','V')}
TEAM_ICONS=set(TEAM_ICON_CODES)
HERO_CODES={'SOLHBGG.CHK':'LG','SOLHBGE.CHK':'HH','SOLHBGD.CHK':'SS','SOLHBGC.CHK':'HT','SOLHBGYS.CHK':'WO','SOLHBGYB.CHK':'KT','SOLHBGF.CHK':'OB','SOLHBGL.CHK':'SK','SOLHBGBU.CHK':'NC','SOLHBGT.CHK':'LT'}
FILES={'MENU2D.CHK','SELECT.CHK','TMFLAG.CHK','RK_FPLAY.CHK'}|set(HERO_CODES)|set(BIG)|TEAM_ICONS


def patch_atlas(data,tex,rects,background,preview_path=None,codes=CODES,palette=None):
 from hanwha_visual import decode,encode
 cs={n:(o,b) for n,o,b in chunks(data)};off,b=cs[tex];po,pb=cs[palette or tex.replace('TEX','PAL')];indices=decode(b);pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4).copy();original=pal[indices];rgba=original.copy();allowed=np.zeros(indices.shape,bool)
 for code,(x,y,w,h) in zip(codes,rects):
  logo=Image.open(ROOT/'translation/kbo_logos'/f'{code}.png').convert('RGBA');logo=logo.crop(logo.getbbox())
  if w==h==128:
   scale=min(w/logo.width,h/logo.height);logo=logo.resize((round(logo.width*scale),round(logo.height*scale)),Image.Resampling.LANCZOS)
  else:logo.thumbnail((w,h),Image.Resampling.LANCZOS)
  tile=Image.new('RGBA',(w,h),background);tile.alpha_composite(logo,((w-logo.width)//2,(h-logo.height)//2));rgba[y:y+h,x:x+w]=np.array(tile);allowed[y:y+h,x:x+w]=True
 used=set(int(v) for v in indices[~allowed]);free=[i for i in range(len(pal)) if i not in used]
 if free:
  pixels=rgba[allowed].reshape(1,-1,4);q=Image.fromarray(pixels,'RGBA').quantize(colors=len(free),method=Image.Quantize.FASTOCTREE);qp=np.array(q.convert('RGBA'))[0];qi=np.array(q)[0]
  for n,i in enumerate(free):
   where=np.flatnonzero(qi==n)
   if len(where):pal[i]=qp[where[0]]
 # Reuse existing colors as well as new palette entries, preserving all other pixels.
 result=indices.copy();colors=pal.astype(np.float32);colors[:,:3]*=colors[:,3:4]/255
 for y in range(indices.shape[0]):
  if not allowed[y].any():continue
  row=rgba[y].astype(np.float32);row[:,:3]*=row[:,3:4]/255;diff=row[:,None,:]-colors[None,:,:];best=(diff*diff).sum(2).argmin(1);result[y,allowed[y]]=best[allowed[y]]
 assert np.array_equal(pal[result][~allowed],original[~allowed])
 out=bytearray(data);out[off+16:off+len(b)]=encode(result,b);out[po+16:po+len(pb)]=pal.tobytes();assert len(out)==len(data)
 regions=[(off+16,len(b)-16),(po+16,len(pb)-16)]
 if preview_path:Image.fromarray(pal[result],'RGBA').resize((indices.shape[1]*2,indices.shape[0]*2),Image.Resampling.NEAREST).save(preview_path)
 return bytes(out),regions

def apply(file,data,preview=False):
 if file not in FILES:return data,[]
 original=data;regions=[]
 if file in BIG:specs=[('TEX00',[(0,0,128,128)],(0,0,0,0))]
 elif file in TEAM_ICONS:specs=[('UP05T',[(0,0,24,24)],(24,29,42,255)),('TEXH',[(0,0,64,64)],(0,0,0,0))]
 elif file in HERO_CODES:specs=[('001TEX',[(0,0,50,50)],(24,29,42,255))]
 elif file=='RK_FPLAY.CHK':specs=[('TEX00',[(x,y,14,14) for x,y in RECTS],(28,28,32,255))]
 elif file=='MENU2D.CHK':specs=[('TEX27',[(x,y,14,14) for x,y in RECTS],(28,28,32,255))]
 elif file=='TMFLAG.CHK':specs=[('TEX00',[(i%7*72,i//7*48,72,48) for i in range(10)],(255,255,255,255))]
 else:specs=[('TEX03',[(i%7*36,i//7*24,36,24) for i in range(10)],(255,255,255,255)),('TEX02',[(1+i%9*27,1+i//9*27,26,26) for i in range(10)],(28,28,32,255)),('TEX04',[(i%6*76,i//6*38,76,38) for i in range(10)],(0,0,0,0)),('TEX05',[(i%4*60,i//4*60,60,60) for i in range(10)],(0,0,0,0))]
 for tex,rects,bg in specs:
  data,rs=patch_atlas(data,tex,rects,bg,ROOT/'build'/f'kbo_{file}_{tex}.png' if preview else None,codes=[TEAM_ICON_CODES[file]] if file in TEAM_ICONS else [HERO_CODES[file]] if file in HERO_CODES else [BIG[file]] if file in BIG else CODES,palette=('PALH' if tex=='TEXH' else 'UP05P') if file in TEAM_ICONS else '002PAL' if file in HERO_CODES else None);regions+=rs
 report=[]
 for start,size in regions:report.append(dict(file=file,offset=start,size=size,original=original[start:start+size].hex(),patched=data[start:start+size].hex(),reason='공식 KBO 10개 구단 로고; 나머지 픽셀 RGBA 보존'))
 return data,report
