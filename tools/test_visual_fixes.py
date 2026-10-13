"""빈 등록명·피부 비트·스윙 판정 UV의 회귀 검사."""
import unittest,struct
from test_hanwha_roster import RosterTests
from hanwha_visual_code import patches
from hanwha_visual import spec
from hanwha_roster import apply,ROOT
from ui_textures import definitions,original_chunks

class VisualFixTests(RosterTests):
 def test_empty_given_name_uses_full_name_without_duplicate_initial(self):
  _,address,code,_=patches()[-1];old=bytes(self.u.mem_read(address,len(code)));self.u.mem_write(address,code)
  try:
   r=bytearray(192);r[110:152]=b'CHAE\0\0'.ljust(42,b'\0')
   for mode in (0,1,2,3,4,6):
    r[161]=0x60
    self.run_getter(0x88f1e04,r,0x09f01000,mode)
    self.assertEqual(bytes(self.u.mem_read(0x09f01000,42)).split(b'\0')[0],b'CHAE',mode)
   r[110:152]=b'FAMILY\0GIVEN\0ALIAS\0'.ljust(42,b'\0')
   for mode,expected in [(0,b'FAMILY'),(1,b'FAMILYGI'),(3,b'GIVEN'),(4,b'FAMILYGI'),(5,b'ALIAS')]:
    self.run_getter(0x88f1e04,r,0x09f01000,mode)
    self.assertEqual(bytes(self.u.mem_read(0x09f01000,42)).split(b'\0')[0],expected,mode)
   r[110:152]=b'CHAE\0\0'.ljust(42,b'\0');r[161]=0x60
   self.run_getter(0x88f1f38,r,0x09f01000,3)
   self.assertEqual(bytes(self.u.mem_read(0x09f01000,42)).split(b'\0')[0],b'CHAE')
  finally:self.u.mem_write(address,old)
 def test_registered_name_caller_mask(self):
  hits=[]
  for file in (ROOT/'work/iso').rglob('*'):
   if file.suffix!='.elf' and file.name!='BOOT.BIN':continue
   data=file.read_bytes();ph=struct.unpack_from('<I',data,28)[0];sz,n=struct.unpack_from('<HH',data,42)
   for i in range(n):
    typ,o,v,_,length,_,_,_=struct.unpack_from('<8I',data,ph+i*sz)
    if typ!=1:continue
    for off in range(o,o+length-3,4):
     w=struct.unpack_from('<I',data,off)[0];ra=v+off-o+8
     if w==0x0e23c696 and ra&0xc1d7==0xd4:hits.append((file.name,ra))
  self.assertEqual(hits,[('BOOT.BIN',0x88f1efc),('BOOT.BIN',0x88f20d4)])
 def test_skin_change_is_exactly_three_bit_field(self):
  data=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();out,_=apply(data,data)
  baseline=(ROOT/'build/baseline_before_visual_fixes/PLAYERDATA.CHK').read_bytes()
  for p in spec():
   o=5120+p['index']*192+152;old=struct.unpack_from('<I',baseline,o)[0];new=struct.unpack_from('<I',out,o)[0]
   if 'skin_type' in p:
    self.assertEqual(new&~0x03800000,old&~0x03800000)
    self.assertEqual((new>>23)&7,p['skin_type'])
   else:self.assertEqual(new,old)
 def test_timing_texts_fit_original_sprite_uv(self):
  rows=[r for r in definitions() if r['file']=='GAME2D.CHK' and r['chunk']=='TEX48']
  self.assertEqual({tuple(r['rect']) for r in rows},{(0,0,75,28),(0,29,75,57),(0,58,53,86),(1,86,63,104)})
  b=original_chunks('GAME2D.CHK')['TCP60'];start=struct.unpack_from('<I',b,20)[0]
  self.assertEqual(struct.unpack_from('<4H',b,start+5*60+36),(0,0,75,28))

if __name__=='__main__':unittest.main()
