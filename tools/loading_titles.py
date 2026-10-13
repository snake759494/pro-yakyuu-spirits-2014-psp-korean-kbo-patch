"""GLOADM MES의 길이 접두어가 있는 두 제목 필드를 추출한다."""
import struct
import gamecodec
def extract(data):
 p=0
 while p+12<=len(data):
  size=struct.unpack_from('<I',data,p)[0]
  if not size:break
  assert size>=12 and p+size<=len(data),(p,size,len(data))
  q=p+10
  for _ in range(2):
   n=data[q];q+=1;raw=data[q:q+n];assert raw[-1:]==b'\0'
   yield q,gamecodec.decode(raw[:-1]);q+=n
  p+=size
