"""설치용 PGD의 수정 블록·블록 MAC·테이블 MAC·헤더 MAC을 함께 갱신한다."""
import struct,hashlib
from pgd import PGD,Kirk,MacKey,bbmac_update,bbmac_final,DNAS_1A90

def update_install(src,dst,install,archive,replacements):
 base=install['offset'];src.seek(base);header=bytearray(src.read(144));pgd=PGD(header)
 assert pgd.mac_type==1 and pgd.data_size==archive['size']
 count=(pgd.data_size+pgd.block_size-1)//pgd.block_size
 tableoff=base+pgd.data_offset+((pgd.data_size+15)&~15)
 src.seek(tableoff);table=bytearray(src.read(count*16))
 def mac(data,key):
  k=Kirk();m=MacKey(pgd.mac_type);bbmac_update(k,m,data);return bbmac_final(k,m,key)
 assert mac(table,pgd.vkey)==header[0x60:0x70]
 blocks={}
 for relative,old,new in replacements:
  assert len(old)==len(new)
  # 바뀐 바이트마다 Python tuple을 만들면 텍스처 교체에서 메모리가 급증한다.
  # 블록 경계로 분할한 연속 구간만 보관한다.
  i=0
  while i<len(old):
   index,within=divmod(relative+i,pgd.block_size);n=min(pgd.block_size-within,len(old)-i)
   a=old[i:i+n];b=new[i:i+n]
   if a!=b:blocks.setdefault(index,[]).append((within,a,b))
   i+=n
 checks=[]
 for index,edits in sorted(blocks.items()):
  off=base+pgd.data_offset+index*pgd.block_size;src.seek(off);raw=src.read(pgd.block_size)
  assert mac(raw,pgd.vkey)==table[index*16:index*16+16]
  plain=pgd.decrypt_block(index,raw);src.seek(archive['offset']+index*pgd.block_size);assert plain==src.read(len(plain))
  patched=bytearray(raw);expected=bytearray(plain)
  for within,a,b in edits:
   assert plain[within:within+len(a)]==a
   for j,(x,y) in enumerate(zip(a,b)):patched[within+j]^=x^y
   expected[within:within+len(b)]=b
  assert pgd.decrypt_block(index,patched)==expected
  table[index*16:index*16+16]=mac(patched,pgd.vkey);dst.seek(off);dst.write(patched)
  checks.append((off,len(patched),hashlib.sha256(patched).digest()))
 header[0x60:0x70]=mac(table,pgd.vkey);header[0x70:0x80]=mac(header[:0x70],pgd.vkey);header[0x80:0x90]=mac(header[:0x80],DNAS_1A90)
 verified=PGD(header);assert verified.vkey==pgd.vkey and verified.dkey==pgd.dkey
 dst.seek(base);dst.write(header);dst.seek(tableoff);dst.write(table)
 checks.extend([(base,144,hashlib.sha256(header).digest()),(tableoff,len(table),hashlib.sha256(table).digest())])
 for off,size,digest in checks:
  dst.seek(off);assert hashlib.sha256(dst.read(size)).digest()==digest
 return dict(changed_blocks=len(blocks),block_size=pgd.block_size,block_mac_verified=True,table_mac_verified=True,header_mac_verified=True,plaintext_matches_direct_archive=True)
