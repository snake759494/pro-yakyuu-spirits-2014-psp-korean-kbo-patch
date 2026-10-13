import sys,struct,json
from pathlib import Path
sys.path.insert(0,'tools')
from unicorn import *
from unicorn.mips_const import *
from league_team_records import patches
from league_arrange import patches as arrpatch
u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x8800000,0x1800000)
for _,va,b,_ in patches()+arrpatch():u.mem_write(va,b)
obj=0x9900000;sp=0x9f00000;end=0x9ff0000;l1=0x9980000;l2=0x9990000
cases=0
for kind,helper,resume,objreg,idreg,idxreg in [('field',0x8d9bfa0,0x8d9c18c,UC_MIPS_REG_S0,UC_MIPS_REG_S2,UC_MIPS_REG_S5),('bat',0x8d9a024,0x8d9a230,UC_MIPS_REG_S6,UC_MIPS_REG_S7,UC_MIPS_REG_S2),('pit',0x8d9d73c,0x8d9d948,UC_MIPS_REG_S6,UC_MIPS_REG_S7,UC_MIPS_REG_S2)]:
 for swap in [False,True]:
  orders=[[0,5,2,1,4,3],[6,8,10,11,9,7]]
  if swap:orders.reverse()
  u.mem_write(obj+0x44,struct.pack('<II',l1,l2))
  for lg,ids in zip([l1,l2],orders):
   for i,team in enumerate(ids):
    roster=0x9a00000+team*0x20000;u.mem_write(lg+0x57ac+i*4,struct.pack('<I',roster));u.mem_write(roster+0xec30,struct.pack('<I',team))
  for team in range(10):
   u.reg_write(objreg,obj);u.reg_write(idreg,team);u.reg_write(UC_MIPS_REG_SP,sp);u.emu_start(helper,resume,count=2000)
   assert u.reg_read(UC_MIPS_REG_V0)==0x9a00000+team*0x20000+0x11f20,(kind,team)
   i=next(i for ids in orders for i,t in enumerate(ids) if t==team);assert u.reg_read(idxreg)==i;cases+=1
for begin,stop,ptr in [(0x8d9bec8,0x8d9c068,0x290),(0x8d99f4c,0x8d9a0ec,0x740),(0x8d9d664,0x8d9d804,0x678)]:
 u.reg_write(UC_MIPS_REG_S1,obj);u.reg_write(UC_MIPS_REG_S3,0)
 for i in range(10):
  row=obj+0x1000+i*32;u.mem_write(obj+ptr+i*4,struct.pack('<I',row));u.mem_write(row+12,struct.pack('<f',float(i//2)))
 u.emu_start(begin,stop,count=2000)
 assert [struct.unpack('<I',u.mem_read(obj+0x1000+i*32,4))[0] for i in range(10)]==[0,0,2,2,4,4,6,6,8,8]
for slot in range(15):
 u.reg_write(UC_MIPS_REG_A0,slot);u.reg_write(UC_MIPS_REG_RA,end);u.emu_start(0x8b35164,end,count=100)
 expected=slot//8*5+slot%8 if slot%8<5 else 31;assert u.reg_read(UC_MIPS_REG_V0)==expected
for begin,stop,left in [(0x8b373e0,0x8b374cc,True),(0x8b37410,0x8b374cc,False)]:
 for row in range(2):
  for col in range(5):
   u.reg_write(UC_MIPS_REG_S3,col);u.reg_write(UC_MIPS_REG_S5,row);u.emu_start(begin,stop,count=100)
   assert u.reg_read(UC_MIPS_REG_S4)==(col+(-1 if left else 1))%5;assert u.reg_read(UC_MIPS_REG_A0)==row*8
Path('build/league_team_cpu_test.json').write_text(json.dumps(dict(passed=True,roster_lookup_cases=cases,tied_rank_tables=3,arrangement_slots=15,cursor_cases=20),indent=2),'utf8');print('팀 조회 60개, 동률 순위 3개, 편성 슬롯15개·방향키20개 통과')
