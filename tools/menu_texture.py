"""PSP PTXI 메뉴 아틀라스를 원본 팔레트·UV 영역 안에서 재작성한다."""
import numpy as np,struct
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT
from analyze import chunks
LABELS=[(0,0,48,25,'대전'),(49,0,177,25,'홈런 경쟁'),(183,0,256,25,'상점'),(0,25,85,50,'스피리츠'),(109,25,240,50,'스타 플레이어'),(0,50,114,75,'페넌트 레이스'),(125,50,217,75,'그랑프리'),(0,75,87,100,'애드혹'),(125,75,239,100,'유틸리티'),(0,100,109,125,'프로스피 입문'),(125,100,233,125,'트레이닝')]
def decode_indices(b):
 w=1<<b[8];h=1<<b[9];fmt=b[12];assert fmt in (4,5)
 # PSP textures can have a wider physical stride than their logical width.
 bw=struct.unpack_from('<H',b,10)[0]*(1 if fmt==5 else 0.5);bw=int(bw)
 assert bw*h==len(b)-16,(w,h,bw,len(b))
 w=bw if fmt==5 else bw*2
 raw=np.frombuffer(b[16:],np.uint8).reshape(h//8,bw//16,8,16).transpose(0,2,1,3).reshape(h,bw).copy()
 if fmt==5:return raw
 out=np.empty((h,w),np.uint8);out[:,::2]=raw&15;out[:,1::2]=raw>>4;return out
def encode_indices(a,fmt=5):
 if fmt==4:
  assert a.max()<16;a=a[:,::2]|(a[:,1::2]<<4)
 h,w=a.shape
 return a.reshape(h//8,8,w//16,16).transpose(0,2,1,3).tobytes()
def apply(data,preview=False):
 cs={n:(o,b) for n,o,b in chunks(data)};off,b=cs['TEX06'];original=decode_indices(b);pal=np.frombuffer(cs['PAL06'][1][16:],np.uint8).reshape(-1,4);im=Image.fromarray(pal[original],'RGBA');allowed=np.zeros(original.shape,bool)
 for x0,y0,x1,y1,text in LABELS:
  allowed[y0:y1,x0:x1]=True;layer=Image.new('RGBA',(x1-x0,y1-y0));font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),18);dr=ImageDraw.Draw(layer)
  while dr.textbbox((0,0),text,font=font,stroke_width=1)[2]>x1-x0-4:font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),font.size-1)
  box=dr.textbbox((0,0),text,font=font);y=(y1-y0-(box[3]-box[1]))//2-box[1];dr.text((3,y+2),text,font=font,fill=(20,14,5,230),stroke_width=1,stroke_fill=(20,14,5,230));dr.text((2,y),text,font=font,fill=(255,246,215,255),stroke_width=0)
  im.paste(layer,(x0,y0))
 rgba=np.array(im).astype(np.float32);p=pal.astype(np.float32);rgba[:,:,:3]*=rgba[:,:,3:4]/255;p[:,:3]*=p[:,3:4]/255
 result=original.copy()
 for y in range(result.shape[0]):
  diff=rgba[y,:,None,:]-p[None,:,:];cost=(diff*diff).sum(axis=2);chosen=cost.argmin(axis=1).astype(np.uint8);result[y,allowed[y]]=chosen[allowed[y]]
 assert np.array_equal(result[~allowed],original[~allowed]);raw=encode_indices(result);assert len(raw)==len(b)-16
 out=bytearray(data);out[off+16:off+len(b)]=raw
 if preview:Image.fromarray(pal[result],'RGBA').save(ROOT/'build/mainmenu_korean_atlas.png')
 assert np.array_equal(decode_indices(bytes(out[off:off+len(b)])),result)
 return bytes(out),dict(file='MAINMENU.CHK',chunk='TEX06',offset=off+16,size=len(raw),labels=len(LABELS),palette_preserved=True,outside_rectangles_preserved=True)
if __name__=='__main__':
 from inventory import WORK
 _,report=apply((WORK/'assets/MAINMENU.CHK').read_bytes(),True);print(report)
