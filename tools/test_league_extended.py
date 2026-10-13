import sys,struct,json,random
from pathlib import Path
sys.path.insert(0,'tools')
from unicorn import *
from unicorn.mips_const import *
from league_feats import best,history,triple
from league_titles import lookup
from league_records import patches as rp
u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x8800000,0x1800000)
base=0x8e00000;obj=0x9900000;src=obj+0x20000;rows=0x9a00000;end=0x9ff0000
W=lambda a,*v:u.mem_write(a,struct.pack('<%dI'%len(v),*v))
R=lambda a:struct.unpack('<I',u.mem_read(a,4))[0]
def run(code,args):
 u.mem_write(base,code(base));u.ctl_remove_cache(base,base+0x1000);u.reg_write(UC_MIPS_REG_SP,0x9f00000);u.reg_write(UC_MIPS_REG_RA,end)
 for r,v in zip([UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3],args):u.reg_write(r,v)
 u.emu_start(base,end,count=100000)
random.seed(2026)
for case in range(100):
 vals=[random.randrange(-1,20) for _ in range(2)];counts=[random.randrange(0,8) for _ in range(2)];ps=[]
 for side,adr in enumerate([obj,src]):
  pointers=[]
  for i in range(3):
   row=rows+side*0x1000+i*0x100;pointers.append(row);u.mem_write(row+8,struct.pack('<f',float(vals[side])))
  W(adr,counts[side],*pointers);ps.append(pointers)
 run(best,[obj,src,1,8]);active=[i for i,c in enumerate(counts) if c];m=max([vals[i] for i in active],default=0);winning=[i for i in active if vals[i]==m];expected=[p for i in winning for p in ps[i][:min(3,counts[i])]][:3];assert R(obj)==sum(counts[i] for i in winning)
 assert [R(obj+4+i*4) for i in range(len(expected))]==expected
for case in range(100):
 allrows=[];counts=[]
 for side,adr in enumerate([obj,src]):
  cnt=random.randrange(0,8);counts.append(cnt);vals=sorted([random.randrange(0,255) for _ in range(3)],reverse=True);pointers=[]
  for i,v in enumerate(vals):
   row=rows+side*0x1000+i*0x100;pointers.append(row);u.mem_write(row+12,bytes([v]));
   if i<cnt:allrows.append((v,row))
  W(adr,cnt,*pointers)
 run(history,[obj,src,1]);expected=sorted(allrows,key=lambda r:r[0],reverse=True)[:3];assert R(obj)==sum(counts);assert [R(obj+4+i*4) for i in range(len(expected))]==[p for _,p in expected]
# Title lookup must handle swapped leagues and rearranged teams.
u.mem_write(base,lookup());u.ctl_remove_cache(base,base+0x1000) # lookup has local branches only
for swap in [False,True]:
 orders=[[0,5,2,1,4,3],[6,8,10,11,9,7]]
 if swap:orders.reverse()
 W(obj+0x1b2fc,0x9980000,0x9990000)
 for lg,ids in zip([0x9980000,0x9990000],orders):
  for i,t in enumerate(ids):W(lg+0x57ac+i*4,rows+t*0x20000);W(rows+t*0x20000+0xec30,t)
 for team in range(10):
  sp=0x9f00000;W(sp+0x20,obj);W(sp+0x10,team);u.reg_write(UC_MIPS_REG_SP,sp);u.reg_write(UC_MIPS_REG_RA,end);u.emu_start(base,end,count=1000);assert u.reg_read(UC_MIPS_REG_V0)==rows+team*0x20000
# Career filters keep original qualification thresholds.
for _,v,b,_ in rp():u.mem_write(v,b)
for selected in list(range(12))+[12]:
 for category in [0,1,7,9]:
  u.mem_write(obj,bytes(0x30000));W(obj+0xa0,0);W(obj+0x64,selected);W(obj+0x2ecd0,36);expect=[]
  for i in range(36):
   team=i//3;row=obj+0xb0+i*0xe0;W(row+8,team);W(row+0x14,3999+i%3);u.mem_write(row+0x38,struct.pack('<f',5999.+i%3))
   if team<10 and ((selected<12 and team==selected) or (selected==12 and (category!=0 or i%3>=1) and (category not in [7,9] or i%3>=1))):expect.append(row)
  u.reg_write(UC_MIPS_REG_A0,obj);u.reg_write(UC_MIPS_REG_A1,category);u.reg_write(UC_MIPS_REG_RA,end);u.emu_start(0x8cfc23c,end,count=10000);assert R(obj+0x2ecd4)==len(expect);assert [R(obj+0x2dfb0+i*4) for i in range(len(expect))]==expect
# Execute the original fielding filter with the patched instructions.
raw=next(Path('work/iso').rglob('com_pena.elf')).read_bytes();ph=struct.unpack_from('<I',raw,28)[0];off,va,_,size=struct.unpack_from('<4I',raw,ph+4);u.mem_write(va,raw[off:off+size])
for _,v,b,_ in rp():u.mem_write(v,b)
u.ctl_remove_cache(va,va+size)
for selected in [12,0,6,9]:
 for category in [0,5]:
  u.mem_write(obj,bytes(0x10000));W(obj+0x98,0);W(obj+0x60,selected);W(obj+0xfa0c,36);expect=[]
  for i in range(36):
   team=i//3;row=obj+0xac+i*0x48;W(row+4,team//6);W(row+8,team);u.mem_write(row+0x10,bytes([int(i%3==2),int(i%3==0)]))
   if (selected<12 and team==selected and i%3!=2) or (selected==12 and team<10 and i%3!=2 and (category!=5 or i%3==0)):expect.append(row)
  u.reg_write(UC_MIPS_REG_A0,obj);u.reg_write(UC_MIPS_REG_A1,category);u.reg_write(UC_MIPS_REG_RA,end);u.emu_start(0x8d182d0,end,count=10000);assert R(obj+0xfa10)==len(expect),(selected,category,R(obj+0xfa10),len(expect));assert [R(obj+0xecec+i*4) for i in range(len(expect))]==expect
Path('build/league_extended_cpu_test.json').write_text(json.dumps(dict(passed=True,best_merge_cases=100,history_merge_cases=100,title_lookup_cases=20,career_cases=52,fielding_cases=8),indent=2),'utf8');print('최고 기록 100 / 과거 기록 100 / 타이틀 팀 조회20 / 통산 필터52 통과')
