"""삼성 홈구장과 대구 라이온즈파크 광고판을 원본 모델에 적용."""
import hashlib,struct,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT
from analyze import chunks
from hanwha_visual import decode
from hanwha_stadium import replace_texture
from lg_brand import paste
BLACK=(0,38,92)
def mark(name):
 im=Image.open(ROOT/'translation/kbo_logos/SS.png').convert('RGBA');return im.crop(im.getbbox())
FILES={'DYOKOHAMA.CHK','NYOKOHAMA.CHK','DYOKOHAMAM.CHK','NYOKOHAMAM.CHK'}
ADS=set(json.loads((ROOT/'translation/club_brand.json').read_text('utf8'))['SS']['ads'])
def sign(size,rects,number,transparent=False):
 bg=(0,0,0,0) if transparent else BLACK+(255,)
 im=Image.new('RGBA',size,bg)
 for j,(x0,y0,x1,y1) in enumerate(rects or [(0,0,*size)]):
  w,h=x1-x0,y1-y0
  if w<1 or h<1:continue
  tile=Image.new('RGBA',(w*4,h*4),bg);dr=ImageDraw.Draw(tile)
  if w<h or w/h<2:paste(tile,mark('emblem03'),(2,2,w*4-4,h*4-4))
  else:
   text=('대구 삼성라이온즈파크','삼성 라이온즈','DAEGU SAMSUNG')[(number+j)%3] if h>=16 else 'SAMSUNG LIONS'
   font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),64);box=font.getbbox(text);mask=Image.new('L',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(mask).text((-box[0],-box[1]),text,font=font,fill=255);mask.thumbnail((max(1,w*4-12),max(1,h*4-8)),Image.Resampling.LANCZOS);tile.paste('white',((w*4-mask.width)//2,(h*4-mask.height)//2),mask)
  im.alpha_composite(tile.resize((w,h),Image.Resampling.LANCZOS),(x0,y0))
 return im
def apply(sources,patched,preview=False):
 from stadium_uv import panels
 day={n:b for n,o,b in chunks(sources['DYOKOHAMA.CHK'])};targets=ADS&day.keys();uv=panels(day,targets);hashes={hashlib.sha256(day[n]).hexdigest():n for n in targets};report=[];boards=[]
 for file in sorted(FILES-{'STSEL.CHK'}):
  data=sources[file];out=bytearray(patched[file]);cs={n:(o,b) for n,o,b in chunks(data)};names=list(cs)
  if file.endswith('M.CHK'):
   from club_scoreboard import apply as scoreboard
   out,rr=scoreboard(file,data);report+=rr;patched[file]=out;continue
  for i,n in enumerate(names[:-1]):
   o,b=cs[n];key=hashlib.sha256(b).hexdigest()
   if file.endswith('M.CHK'):
    if not n.startswith('T_TMMK'):continue
    pn=n.replace('T_','P_',1);rects=[];num=0
   else:
    if key not in hashes:continue
    src=hashes[key];pn=names[i+1];rects=uv[src];num=int(src)
   if pn not in cs or cs[pn][1][:4]!=b'PPAL':continue
   a=decode(b);pal=np.frombuffer(cs[pn][1][16:],np.uint8).reshape(-1,4);transparent=bool((pal[a][:,:,3]<50).mean()>.35)
   im=sign((a.shape[1],a.shape[0]),rects,num,transparent);replace_texture(out,cs,n,pn,im);boards.append(dict(file=file,chunk=n,rects=rects,transparent=transparent))
   for q in (n,pn):
    at,raw=cs[q];report.append(dict(file=file,offset=at,size=len(raw),original=data[at:at+len(raw)].hex(),patched=out[at:at+len(raw)].hex(),reason='대구 삼성 간판: UV 조각별 맞춤'))
  patched[file]=out
 # 구단 홈구장 표의 첫 항목. 슬롯7의 기존 낮/밤·충돌·미리보기 연결을 그대로 사용.
 boot=sources['BOOT.BIN'];target=0x2846a4;assert struct.unpack_from('<I',boot,target)[0]==4
 new=struct.pack('<I',3);patched['BOOT.BIN'][target:target+4]=new
 report.append(dict(file='BOOT.BIN',offset=target,size=4,original=boot[target:target+4].hex(),patched=new.hex(),reason='삼성 홈구장: 돔4에서 개방형 YOKOHAMA3로 변경'))
 if preview:(ROOT/'build/ss_brand/stadium_boards.json').write_text(json.dumps(boards,ensure_ascii=False,indent=2),'utf8')
 return report
