"""검수한 PSP 8bpp 텍스처 글자를 원본 UV 영역과 팔레트 안에서 교체한다."""
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT,WORK,ISO
from functools import lru_cache
from analyze import chunks
from menu_texture import decode_indices,encode_indices
from sprites import bindings

@lru_cache(maxsize=64)
def original_chunks(file):
 e=next(e for e in json.loads((WORK/'inventory.json').read_text('utf8'))['fbd'] if e['name']==file)
 with ISO.open('rb') as f:f.seek(e['offset']);data=f.read(e['size'])
 return {n:b for n,o,b in chunks(data)}

def definitions():return json.loads((ROOT/'translation/textures.json').read_text('utf8'))
def apply(file,data,preview=False,league_trial=False):
 specs=[s for s in definitions() if s['file']==file];out=bytearray(data);reports=[]
 if league_trial:
  from kbo_identity import texture_short
  short=texture_short(file)
  if short:specs=[dict(s,ko=short) if s['chunk']=='UP04T' else s for s in specs]
 if league_trial and file in ('PRETITCEN.CHK','PRETITPAC.CHK','PRETIT_IL.CHK'):
  specs=[dict(s,ko='KBO 공식전') for s in specs]
 cs={n:(o,b) for n,o,b in chunks(data)};links=bindings(data)
 for chunk in dict.fromkeys(s['chunk'] for s in specs):
  off,b=cs[chunk];original=decode_indices(b);spec=next(s for s in specs if s['chunk']==chunk);pn=links.get(chunk,[chunk.replace('TTEX','TPAL').replace('TEX','PAL')])[0]
  palette=original_chunks(spec['palette_file'])[spec['palette_chunk']] if 'palette_file' in spec else cs[pn][1]
  pal=np.frombuffer(palette[16:],np.uint8).reshape(-1,4);im=Image.fromarray(pal[original],'RGBA');allowed=np.zeros(original.shape,bool)
  for s in [s for s in specs if s['chunk']==chunk]:
   x0,y0,x1,y1=s['rect'];w=x1-x0;h=y1-y0;assert 0<=x0<x1<=im.width and 0<=y0<y1<=im.height
   allowed[y0:y1,x0:x1]=True
   bg=s.get('background',[0,0,0,0])
   if isinstance(bg,dict) and bg.get('keep_green'):
    a=np.array(im.crop((x0,y0,x1,y1)));keep=(a[:,:,1].astype(float)>a[:,:,0]*1.1)&(a[:,:,1].astype(float)>a[:,:,2]*1.1);a[~keep]=0;layer=Image.fromarray(a,'RGBA')
   elif isinstance(bg,dict) and 'row_sample' in bg:
    layer=im.crop((bg['row_sample'],y0,bg['row_sample']+1,y1)).resize((w,h),Image.Resampling.NEAREST)
   else:
    if isinstance(bg,dict):bg=im.getpixel(tuple(bg['sample']))
    layer=Image.new('RGBA',(w,h),tuple(bg))
   dr=ImageDraw.Draw(layer);text=s['ko'];size=s.get('size',max(8,h-5));font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),size)
   # 높이는 유지하고 가로 폭만 UV에 맞춘다. 작은 글씨의 과도한 축소를 피한다.
   stroke=s.get('stroke',1);pad=s.get('padding',2)
   box=dr.textbbox((0,0),text,font=font,stroke_width=stroke);tw=box[2]-box[0];th=box[3]-box[1]
   ink=Image.new('RGBA',(tw+2*pad,th+2*pad));idraw=ImageDraw.Draw(ink);color=tuple(s.get('color',[245,245,245,255]));edge=tuple(s.get('edge',[35,35,35,255]))
   idraw.text((pad-box[0],pad-box[1]),text,font=font,fill=color,stroke_width=stroke,stroke_fill=edge)
   if ink.width>w or ink.height>h:ink=ink.resize((min(w,ink.width),min(h,ink.height)),Image.Resampling.LANCZOS)
   layer.alpha_composite(ink,((w-ink.width)//2,(h-ink.height)//2));im.paste(layer,(x0,y0))
  rgba=np.array(im).astype(np.float32);p=pal.astype(np.float32);rgba[:,:,:3]*=rgba[:,:,3:4]/255;p[:,:3]*=p[:,3:4]/255;result=original.copy()
  for y in np.where(allowed.any(axis=1))[0]:
   cols=np.where(allowed[y])[0];cost=((rgba[y,cols,None,:]-p[None,:,:])**2).sum(axis=2);result[y,cols]=cost.argmin(axis=1)
  assert np.array_equal(result[~allowed],original[~allowed]);raw=encode_indices(result,b[12]);out[off+16:off+len(b)]=raw;assert len(raw)==len(b)-16
  if preview:
   folder=ROOT/'build/textures';folder.mkdir(exist_ok=True);Image.fromarray(pal[result],'RGBA').save(folder/(file+'_'+chunk+'.png'))
  reports.append(dict(file=file,chunk=chunk,offset=off+16,size=len(raw),labels=sum(s['chunk']==chunk for s in specs),palette_preserved=True,outside_rectangles_preserved=True))
 return bytes(out),reports
