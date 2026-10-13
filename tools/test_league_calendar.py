import sys,struct,json
from pathlib import Path
sys.path.insert(0,'tools')
from unicorn import *
from unicorn.mips_const import *
from league_calendar import patches,BASE
u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x8800000,0x1800000)
for name in ['BOOT.BIN','com_sel.elf']:
 b=next(Path('work/iso').rglob(name)).read_bytes();ph=struct.unpack_from('<I',b,28)[0];off,va,_,size=struct.unpack_from('<4I',b,ph+4);u.mem_write(va,b[off:off+size])
for _,va,b,_ in patches():u.mem_write(va,b)
u.reg_write(UC_MIPS_REG_CP0_STATUS,u.reg_read(UC_MIPS_REG_CP0_STATUS)|0x20000000)
obj=0x9900000;sp=0x99f0000;end=0x9ff0000;p1=0x9980000;p2=p1+0x1000;cases=[]
for mode in ['descending','ascending','ties']:
 u.mem_write(obj,bytes(0xc00));u.mem_write(sp+0x3c,struct.pack('<II',p1,p2)) # second pointer actually +44
 u.mem_write(sp+0x44,struct.pack('<I',p2))
 for team in range(12):
  r=bytearray(28);r[8]=10-team if mode=='descending' and team<10 else (team if mode=='ascending' else 5);r[9]=max(0,10-r[8]);struct.pack_into('<I',r,24,team);u.mem_write((p1 if team<6 else p2)+(team%6)*28,bytes(r))
 u.reg_write(UC_MIPS_REG_A0,obj);u.reg_write(UC_MIPS_REG_SP,sp);u.reg_write(UC_MIPS_REG_RA,end);u.emu_start(BASE,end,count=500000)
 rows=[struct.unpack('<IIf',u.mem_read(obj+(0xa4 if i<5 else 0x104)+(i%5)*16,12)) for i in range(10)]
 assert sorted(r[1] for r in rows)==list(range(10)),rows
 expected=list(range(10)) if mode!='ascending' else list(range(9,-1,-1));assert [r[1] for r in rows]==expected,rows
 assert [r[0] for r in rows]==([0]*10 if mode=='ties' else list(range(10))),rows
 assert u.reg_read(UC_MIPS_REG_SP)==sp;cases.append(dict(mode=mode,rows=rows))
Path('build/league_calendar_cpu_test.json').write_text(json.dumps(dict(passed=True,cases=cases),indent=2),'utf8');print('달력 순위 3개 경우 통과')

