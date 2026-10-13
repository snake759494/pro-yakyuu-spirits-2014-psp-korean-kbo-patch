"""구단 추가 시 저장 편성 초기화 대상/루프 레지스터 보존 검사."""
import unittest,struct
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn.mips_const import *
from lg_fresh_code import patches
from club_brand import configs

class ClubFreshTests(unittest.TestCase):
 def test_reset_targets_and_volatile_clobber(self):
  u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x08800000,0x1800000)
  _,start,code,_=patches()[0];u.mem_write(start,code);obj=0x09400000;root=0x09600000;sp=0x09f00000
  u.mem_write(obj+0x5c,struct.pack('<I',root));u.reg_write(UC_MIPS_REG_S7,obj);u.reg_write(UC_MIPS_REG_SP,sp);calls=[]
  def hook(uc,addr,size,data):
   if addr in (0x8a388e4,0x8cd91b0,0x88fdff0,0x88fcde8):
    if addr==0x88fcde8:
     calls.append(uc.reg_read(UC_MIPS_REG_A2))
     self.assertEqual(uc.reg_read(UC_MIPS_REG_A0),root)
     self.assertEqual(uc.reg_read(UC_MIPS_REG_A1),root+uc.reg_read(UC_MIPS_REG_A2)*0x28e8)
    for reg in (UC_MIPS_REG_T0,UC_MIPS_REG_T1,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2):uc.reg_write(reg,0xdeadbeef)
    uc.reg_write(UC_MIPS_REG_V0,root);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(start,0x8d20108,count=2000)
  self.assertEqual(calls,sorted(c['team_id'] for c in configs().values())+[0]);self.assertEqual(u.reg_read(UC_MIPS_REG_SP),sp)
if __name__=='__main__':unittest.main()
