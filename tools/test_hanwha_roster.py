"""원 게임 MIPS getter 실행으로 비트 필드 및 명단 경계를 검증한다."""
import json,struct,unittest
from pathlib import Path
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import *
from player_fields import *
from hanwha_roster import load,apply,ROOT
from analyze import chunks
class RosterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);cls.u.mem_map(0x08800000,0x01800000)
  d=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();ph=struct.unpack_from('<I',d,28)[0];sz,n=struct.unpack_from('<HH',d,42)
  for i in range(n):
   typ,o,v,_,length,_,_,_=struct.unpack_from('<8I',d,ph+i*sz)
   if typ==1:cls.u.mem_write(v,d[o:o+length])
 def run_getter(self,address,record,*args):
  u=self.u;u.mem_write(0x09f00000,bytes(record))
  for reg,val in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_T0),[0x09f00000]+list(args)+[0]*4):u.reg_write(reg,val)
  u.reg_write(UC_MIPS_REG_SP,0x09f10000);u.reg_write(UC_MIPS_REG_RA,0x09e00000)
  u.emu_start(address,0x09e00000,count=20000);self.assertEqual(u.reg_read(UC_MIPS_REG_PC),0x09e00000)
  return u.reg_read(UC_MIPS_REG_V0)
 def test_scalar_fields_with_original_getters(self):
  r=bytearray(192)
  for key,address in [('power',0x88ec6f4),('contact_r',0x88ec7fc),('speed',0x88ec9ac),('arm',0x88ecaa8),('catching',0x88ecc9c),('throwing',0x88ecba0),('recovery',0x88ecd98)]:
   put(r,key,73);self.assertEqual(self.run_getter(address,r,0,0),73,key)
  put(r,'contact_l',68);self.assertEqual(self.run_getter(0x88ec7fc,r,0,1),68)
  put(r,'velocity_raw',76);self.assertEqual(self.run_getter(0x88ecfc0,r,0),156)
 def test_positions_pitch_grades_and_birthday(self):
  r=bytearray(192)
  for i,key in enumerate(POSITIONS):put(r,key,40+i)
  for i,key in enumerate(POSITIONS):self.assertEqual(self.run_getter(0x88ec5b0,r,i),40+i,key)
  r[58:60]=pitch(4,5,6,3)
  self.assertEqual(self.run_getter(0x88ed108,r,0),5)
  self.assertEqual(self.run_getter(0x88ed3e8,r,0),6)
  self.assertEqual(self.run_getter(0x88ed3a0,r,0),3)
  self.assertEqual(self.run_getter(0x88ed5f8,r,0),4)
  struct.pack_into('<H',r,104,87|(3<<7)|(25<<11))
  self.assertEqual([self.run_getter(0x88f2984,r,i) for i in range(3)],[87,3,25])
 def test_scope_roster_and_identity(self):
  d=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();out,report=apply(d,d);spec=load();cs={n:(o,b) for n,o,b in chunks(d)}
  self.assertEqual(len(out),len(d));self.assertEqual(sum(r.get('opening_entry',False) for r in spec['records']),29)
  # 2026 정규시즌 종료 기준 슬롯 교체(짐머맨/하동준 투수, 정은원 내야) 반영.
  self.assertEqual(report['positions'],{'PC':33,'CC':6,'IF':12,'OF':11})
  selected={r['index'] for r in spec['records']}
  for i in range(2458):
   a=cs['PDN'][0]+i*192;b=cs['PDW'][0]+i*84
   self.assertEqual(d[a+84:a+92],out[a+84:a+92])
   if i not in selected:self.assertEqual(d[a:a+192],out[a:a+192]);self.assertEqual(d[b:b+84],out[b:b+84])
  for p in spec['records']:
   a=cs['PDN'][0]+p['index']*192;r=out[a:a+192]
   if p['kind']=='player':
    self.assertEqual(self.run_getter(0x88ecfc0,r,0),p['velocity'])
    for j,pos in enumerate(POSITIONS):self.assertEqual(self.run_getter(0x88ec5b0,r,j),p['fielding'].get(pos,0))
 def test_age_correction_and_dh_cave(self):
  from hanwha_age import patches
  source=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
  # helper 구간으로 들어오는 다른 직접 jump/call 및 주소 상수가 없어야 한다.
  for file in (ROOT/'work/iso').rglob('*'):
   if file.suffix!='.elf' and file.name!='BOOT.BIN':continue
   data=file.read_bytes()
   for o in range(0,len(data)-3,4):
    w=struct.unpack_from('<I',data,o)[0]
    if w>>26 in (2,3):self.assertFalse(0x8a2dfec<=((w&0x3ffffff)<<2)<0x8a2e010,(file,o))
    self.assertFalse(0x8a2dfec<=w<0x8a2e010,(file,o))
  backups=[]
  for _,a,b,_ in patches()+[('BOOT.BIN',0x8a2dfe4,struct.pack('<II',0x03e00008,0x00001021),'DH')]:
   backups.append((a,bytes(self.u.mem_read(a,len(b)))));self.u.mem_write(a,b)
  try:
   for team in range(12):
    for year in (1958,1987,2003,2007):
     r=bytearray(192);struct.pack_into('<H',r,90,team*65);struct.pack_into('<H',r,104,(year-1900)|(3<<7)|(25<<11))
     self.assertEqual(self.run_getter(0x88f29d8,r,2014),2014+(12 if team==6 else 0)-year)
   self.assertEqual(self.run_getter(0x8a2dfe4,bytearray(192)),0)
  finally:
   for a,b in backups:self.u.mem_write(a,b)
 def test_registered_names_with_original_formatter(self):
  d=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();out,_=apply(d,d)
  for p in load()['records']:
   a=5120+p['index']*192;r=bytearray(out[a:a+192])
   # 실제 표시 함수에 임의의 비어 있지 않은 첫 문자열과 빈 given/alias를 전달.
   expected=('HH'+str(p['index'])).encode();r[110:152]=expected.ljust(42,b'\0')
   self.run_getter(0x88f1e04,r,0x09f01000,6)
   self.assertEqual(bytes(self.u.mem_read(0x09f01000,42)).split(b'\0')[0],expected,p['name'])
   if p['name']=='박준영':
    r[161]|=0x20 # 동명이인 자동 구분: first+given 초기 두 바이트. given이 비면 first만.
    self.run_getter(0x88f1e04,r,0x09f01000,6)
    self.assertEqual(bytes(self.u.mem_read(0x09f01000,42)).split(b'\0')[0],expected)
if __name__=='__main__':unittest.main()
