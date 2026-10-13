"""SBIB의 텍스처/팔레트 연결과 60바이트 스프라이트 레코드 해석."""
import struct,collections
from analyze import chunks
def bindings(data):
 result=collections.defaultdict(list)
 for name,off,b in chunks(data):
  if b[:4]!=b'SBIB':continue
  nt,np,ng=b[5:8];to,po,go,do=struct.unpack_from('<4I',b,8)
  tex=[b[to+i*8:to+i*8+8].split(b'\0')[0].decode('ascii') for i in range(nt)]
  pal=[b[po+i*8:po+i*8+8].split(b'\0')[0].decode('ascii') for i in range(np)]
  for i in range(ng):
   flags,unk,t,p,mode,first,count=struct.unpack_from('<7I',b,go+i*28)
   if t>=len(tex) or p>=len(pal):continue
   if pal[p] not in result[tex[t]]:result[tex[t]].append(pal[p])
 return dict(result)
