import sys,struct,json
from pathlib import Path
sys.path.insert(0,'tools')
import test_league_code as t
from league_surfaces import home_record,BASE,rank_glyph
from unicorn.mips_const import *
u=t.u;game=0x9800000;buf=0x9b00000;end=0x9ff0000
u.mem_write(game+0x168108,struct.pack('<I',buf))
for league,ids in enumerate([[5,3,1,4,2,0],[11,7,10,8,6,9]]):
 for i,team in enumerate(ids):
  b=bytearray(28);b[8]=10-team if team<10 else 99;b[9]=team;b[14]=team;struct.pack_into('<II',b,20,0,team);u.mem_write(buf+league*336+i*28,bytes(b))
u.mem_write(BASE,home_record())
for team in range(10):
 for reg,v in [(UC_MIPS_REG_A0,game),(UC_MIPS_REG_A1,team),(UC_MIPS_REG_SP,0x9f00000),(UC_MIPS_REG_RA,end)]:u.reg_write(reg,v)
 u.emu_start(BASE,end,count=100000);p=u.reg_read(UC_MIPS_REG_V0);rank=struct.unpack('<I',u.mem_read(p+20,4))[0];assert rank==team,(team,rank,bytes(u.mem_read(p,28)).hex())
print('홈 10팀 순위와 두 리그 내부 순서 변경 검사 통과')

from league_surfaces import common_rank
u.mem_write(0x8c79ae0,common_rank())
for team in range(12):
 for opp in range(12):
  b=bytearray(12)
  if team<10 and opp==(team+1)%10:b[8]=10-team;b[9]=team
  u.mem_write(game+(0x162274 if team<6 else 0x167a1c)+team%6*144+opp*12,bytes(b))
for team in range(12):
 for reg,v in [(UC_MIPS_REG_A0,game),(UC_MIPS_REG_A1,team),(UC_MIPS_REG_SP,0x9f00000),(UC_MIPS_REG_RA,end)]:u.reg_write(reg,v)
 u.emu_start(0x8c79ae0,end,count=100000);assert u.reg_read(UC_MIPS_REG_V0)==(team if team<10 else 12)
# Check sprite coordinates against the independently specified atlas layout.
u.mem_write(0x8d28760,rank_glyph(0x8d28760,0x8d28818));obj=0x99d0000;u.mem_write(obj,struct.pack('<3I',obj+4,0,obj+16));got=[]
def sprite(cpu,addr,size,user):
 got.append(struct.unpack('<4H',cpu.mem_read(cpu.reg_read(UC_MIPS_REG_A1),8)));cpu.reg_write(UC_MIPS_REG_PC,cpu.reg_read(UC_MIPS_REG_RA))
from unicorn import UC_HOOK_CODE
hook=u.hook_add(UC_HOOK_CODE,sprite,begin=0x8945904,end=0x8945904)
for rank in range(10):
 for reg,v in [(UC_MIPS_REG_A0,obj),(UC_MIPS_REG_A1,rank),(UC_MIPS_REG_SP,0x9f00000),(UC_MIPS_REG_RA,end)]:u.reg_write(reg,v)
 u.emu_start(0x8d28760,end,count=1000);x=rank%5*50;y=22+rank//5*22;assert got[-1]==(x,y,x+44,y+20),got[-1]
u.hook_del(hook)
Path('build/league_home_cpu_test.json').write_text(json.dumps(dict(passed=True,home_lookup_teams=10,common_lookup_teams=12,rank_sprite_cases=10),indent=2),'utf8');print('공통 구단 순위 12입력 / 순위 그림 좌표10개 통과')
