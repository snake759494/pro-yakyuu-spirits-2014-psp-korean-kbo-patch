import sys,struct,json
from pathlib import Path
sys.path.insert(0,'tools')
from league_records import patches
from unicorn import *
from unicorn.mips_const import *
u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x8800000,0x1800000)
for _,addr,code,_ in patches():u.mem_write(addr,code)
obj=0x9900000;end=0x9ff0000
cases=[]
for pitch,begin,stop,record,stride,ptr,count,filt,q,ex in [(False,0x8d140d4,end,0x94,0xc4,0x283b4,0x290d4,0x290d8,0x8e,0x15),(True,0x8d1b414,0x8d1b51c,0xac,0xa8,0x227ec,0x2350c,0x23510,0xa6,0x16)]:
 for selected in [12,0,6,9,10,11]:
  for qualified in [0,1]:
   u.mem_write(obj,bytes(0x30000));u.mem_write(obj+count,struct.pack('<I',36));u.mem_write(obj+q,bytes([qualified]));expected=[]
   for i in range(36):
    team=i//3;row=bytearray(stride);struct.pack_into('<3I',row,0,0,team//6,team);row[0x14]=int(i%3==0);row[ex]=int(i%3==2);u.mem_write(obj+record+i*stride,bytes(row))
    if team<10 and ((selected<12 and team==selected) or (selected>=12 and not row[ex] and (not qualified or row[0x14]))):expected.append(obj+record+i*stride)
   for r,v in [(UC_MIPS_REG_A0,selected if pitch else obj),(UC_MIPS_REG_A3,selected),(UC_MIPS_REG_S0,obj),(UC_MIPS_REG_RA,end)]:u.reg_write(r,v)
   u.emu_start(begin,stop,count=10000);n=struct.unpack('<I',u.mem_read(obj+filt,4))[0];got=list(struct.unpack('<%dI'%n,u.mem_read(obj+ptr,n*4))) if n else []
   assert got==expected,(pitch,selected,qualified,n,len(expected));cases.append([pitch,selected,qualified,n])
for begin,stop,array,current,own in [(0x8d12d08,0x8d12dec,0x48,0x80,0x84),(0x8d1a12c,0x8d1a210,0x60,0x98,0x9c)]:
 for team in range(10):
  u.reg_write(UC_MIPS_REG_S0,obj);u.reg_write(UC_MIPS_REG_S1,team);u.emu_start(begin,stop,count=1000)
  assert list(struct.unpack('<11I',u.mem_read(obj+array,44)))==list(range(10))+[12]
  assert struct.unpack('<I',u.mem_read(obj+current,4))[0]==10
  assert struct.unpack('<I',u.mem_read(obj+own,4))[0]==team
Path('build/league_records_cpu_test.json').write_text(json.dumps(dict(passed=True,filter_cases=cases,selection_cases=20),indent=2),'utf8');print('개인 기록 MIPS 필터 24개 조건 / 선택 목록 20개 조건 통과')
