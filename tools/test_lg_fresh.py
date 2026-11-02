"""LG 초기화 후크와 독립 명단의 회귀 검사."""
import unittest,struct
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn.mips_const import *
from lg_fresh_code import patches
from kbo_team_layout import layouts
from analyze import chunks
from inventory import ROOT
from player_fields import get

class FreshLGTests(unittest.TestCase):
 def test_active_roles(self):
  t=layouts()['LG'];p=t['pitchers'];active=t['active']
  self.assertEqual(len(p),13)
  self.assertEqual(len(active),28)
  self.assertEqual({x['name'] for x in active if x.get('foreign')},{'치리노스','톨허스트','오스틴'})
  self.assertEqual([(x['name'],pos) for x,pos in t['batting']][3],('문보경',9))
  self.assertTrue(all(x['category']=='P' for x in p))
  self.assertTrue(all(x['category']!='P' for x,pos in t['batting']))
  self.assertNotIn('김현수',{x['name'] for x in t['players']})
 def test_all_pitchers_use_original_pitcher_records(self):
  pd={n:b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes())}['PDN']
  for p in layouts()['LG']['players']:
   if p['category']!='P':continue
   r=pd[p['index']*192:(p['index']+1)*192]
   self.assertEqual((r[168]&0x78)>>3,0,p['name'])
   self.assertGreater(get(r,'stamina'),0,p['name'])
   self.assertGreater(get(r,'velocity_raw'),0,p['name'])
   self.assertTrue(any((struct.unpack_from('<H',r,k)[0]&127)!=37 for k in range(58,82,2)),p['name'])
 def test_constructor_preserves_init_and_resets_all_ten_teams(self):
  for existing in (0,0x09600000):
   u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x08800000,0x1800000)
   _,start,code,_=patches()[0];u.mem_write(start,code)
   obj=0x09400000;root=0x09600000
   u.mem_write(obj+0x5c,struct.pack('<I',existing));u.mem_write(obj+0x3a954,b'\xaa'*64)
   u.reg_write(UC_MIPS_REG_S7,obj);u.reg_write(UC_MIPS_REG_SP,0x09f00000)
   calls=[]
   def hook(uc,addr,size,data):
    if addr in (0x8a388e4,0x8cd91b0,0x88fdff0,0x88fcde8):
     calls.append((addr,*[uc.reg_read(r) for r in (UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2)]))
     uc.reg_write(UC_MIPS_REG_V0,root if addr==0x88fdff0 else 0x1234)
     uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
   u.hook_add(UC_HOOK_CODE,hook);u.emu_start(start,0x8d20108,count=1000)
   self.assertEqual(calls[-1],(0x88fcde8,root,root,0))
   self.assertEqual([x[3] for x in calls if x[0]==0x88fcde8],list(range(1,10))+[0])
   self.assertEqual(bytes(u.mem_read(obj+0x3a954,44)),bytes(44))
   self.assertEqual(bytes(u.mem_read(obj+0x3a980,3)),b'\0\0\1')
   self.assertEqual(bytes(u.mem_read(obj+0x3a984,16)),bytes(16))
   self.assertEqual(struct.unpack('<I',u.mem_read(obj+0x5c,4))[0],root)

if __name__=='__main__':unittest.main()
