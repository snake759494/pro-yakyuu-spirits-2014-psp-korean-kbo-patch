import struct

def references(d):
 phoff=struct.unpack_from('<I',d,28)[0];ps,pn=struct.unpack_from('<HH',d,42);segments=[]
 for i in range(pn):
  typ,off,va,pa,size,ms,fl,al=struct.unpack_from('<8I',d,phoff+i*ps)
  if typ==1:segments.append((off,va,size))
 result=set()
 def accept(v):
  for off,va,size in segments:
   if va<=v<va+size:result.add(off+v-va)
 for off,va,size in segments:
  for p in range(off,off+size-3,4):
   w=struct.unpack_from('<I',d,p)[0];accept(w)
   if w>>26!=15:continue
   reg=(w>>16)&31;hi=(w&65535)<<16
   if not reg:continue
   for q in range(p+4,min(p+36,off+size-3),4):
    x=struct.unpack_from('<I',d,q)[0];op=x>>26;rs=(x>>21)&31;rt=(x>>16)&31;rd=(x>>11)&31;imm=x&65535
    if rs==reg and op in (9,13):accept(hi+(imm-(65536 if imm&32768 else 0)) if op==9 else hi|imm)
    if (op==0 and rd==reg) or (op in (8,9,10,11,12,13,14,15,32,33,35,36,37) and rt==reg):break
    if op in (2,3):break
 return result
