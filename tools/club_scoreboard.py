"""구장 전광판의 반복 팀 표장 아틀라스. 전체 이미지에 한 로고를 덮지 않는다."""
from analyze import chunks
from kbo_logos import patch_atlas,CODES

def apply(file,data,original=None):
 original=data if original is None else original
 cs={n:(o,b) for n,o,b in chunks(data)};report=[]
 cells=list(range(10))+list(range(14,24))
 rects=[(i%5*25,i//5*16,25,16) for i in cells]
 for tex in ('T_TMMK1','T_TMMK2'):
  if tex not in cs:continue
  pal=tex.replace('T_','P_')
  data,regions=patch_atlas(data,tex,rects,(8,12,24,255),codes=CODES+CODES,palette=pal)
  for at,size in regions:
   report.append(dict(file=file,offset=at,size=size,original=original[at:at+size].hex(),patched=data[at:at+size].hex(),reason='전광판 공용 팀 로고: 10구단 2회 반복 배열 및 마지막 텍스처 포함'))
 return bytearray(data),report
