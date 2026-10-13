"""고정 크기 저장 아이콘 PNG의 하단 모드 이름만 한글로 교체한다."""
import io
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT
LABELS={'ADHOC':'애드혹 대전','GP':'그랑프리','MUSIC':'응원곡','NEW':'새 데이터','PENNANT':'페넌트 레이스','SPI_RANK':'스피리츠 랭킹','SPIRITS':'스피리츠','STPL':'스타 플레이어','SYSTEM':'시스템'}
FILES={'ICON0_SAVE_'+k+'.PNG':v for k,v in LABELS.items()}
def apply(name,data,preview=False):
 im=Image.open(io.BytesIO(data)).convert('RGBA');old=im.copy();y=60
 for yy in range(y,80):
  color=im.getpixel((1,yy))
  for x in range(144):im.putpixel((x,yy),color)
 d=ImageDraw.Draw(im);font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),12);text=FILES[name];box=d.textbbox((0,0),text,font=font);x=(144-(box[2]-box[0]))//2;ty=y+(20-(box[3]-box[1]))//2-box[1]
 d.text((x,ty),text,font=font,fill='white' if 'NEW' in name else 'black')
 assert im.crop((0,0,144,y)).tobytes()==old.crop((0,0,144,y)).tobytes()
 b=io.BytesIO();encoded=im.convert('RGB') if im.getextrema()[3]==(255,255) else im;encoded.save(b,format='PNG',optimize=True,compress_level=9);raw=b.getvalue();assert len(raw)<=len(data),(name,len(raw),len(data))
 if preview:im.save(ROOT/'build/textures'/name)
 return raw.ljust(len(data),b'\0')
