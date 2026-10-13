"""실행 화면에서 캡처한 10구단 객체를 원 평가 함수로 재생하여 환산을 검증."""
import json,struct,unittest,hashlib
from pathlib import Path
from unicorn import *
from unicorn.mips_const import *
from analyze import chunks
from kbo_rosters import apply
from kbo_team_layout import apply_playerdata
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'build/team_strength'
def evaluate(team,new=None):
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0x8800000,0x1800000);u.mem_write(0x8800000,(D/'select_ram.bin').read_bytes())
 # PPSSPP JIT가 블록 첫 명령에 둔 emuhack만 원 ELF 명령으로 복원한다.
 for path in [ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN',ROOT/'work/iso/PSP_GAME/USRDIR/CDVDROOT/OVERLAYS/com_sel.elf']:
  elf=path.read_bytes();ph=struct.unpack_from('<I',elf,28)[0];size,count=struct.unpack_from('<HH',elf,42)
  for j in range(count):
   typ,off,va,_,length,_,_,_=struct.unpack_from('<8I',elf,ph+j*size)
   if typ!=1:continue
   buf=bytearray(u.mem_read(va,length))
   for x in range(0,length-3,4):
    if buf[x+3]==0x68:buf[x:x+4]=elf[off+x:off+x+4]
   u.mem_write(va,bytes(buf))
 def memset(uc,address,size,data):
  dest=uc.reg_read(UC_MIPS_REG_A0);value=uc.reg_read(UC_MIPS_REG_A1)&255;length=uc.reg_read(UC_MIPS_REG_A2)
  uc.mem_write(dest,bytes([value])*length);uc.reg_write(UC_MIPS_REG_V0,dest);uc.reg_write(UC_MIPS_REG_PC,uc.reg_read(UC_MIPS_REG_RA))
 u.hook_add(UC_HOOK_CODE,memset,begin=0x8a84888,end=0x8a84888)
 addr=0x9935a2c;b=bytearray(team)
 if new:
  for j in range(struct.unpack_from('<I',b,0xe7e0)[0]):
   off=j*0x350+0x18;gid=struct.unpack_from('<H',b,off+84)[0]
   assert gid in new,gid;b[off:off+192]=new[gid]
 u.mem_write(addr,bytes(b));u.reg_write(UC_MIPS_REG_GP,149389936)
 u.reg_write(UC_MIPS_REG_A0,addr-0x5c);u.reg_write(UC_MIPS_REG_A1,0)
 u.reg_write(UC_MIPS_REG_RA,0x9f80000);u.reg_write(UC_MIPS_REG_SP,0x9ff8000)
 stop=u.hook_add(UC_HOOK_CODE,lambda uc,a,s,d:uc.emu_stop(),begin=0x8cd9e40,end=0x8cd9e40)
 u.emu_start(0x8cd9b90,0x9f80000,count=50000000)
 u.hook_del(stop)
 assert u.reg_read(UC_MIPS_REG_PC)==0x8cd9e40,hex(u.reg_read(UC_MIPS_REG_PC))
 floatreg=lambda r:struct.unpack('<f',struct.pack('<I',u.reg_read(r)))[0]
 raw=dict(pitching=floatreg(UC_MIPS_REG_F22),batting=floatreg(UC_MIPS_REG_F20),fielding=floatreg(UC_MIPS_REG_F24))
 raw.update(batter_samples=u.reg_read(UC_MIPS_REG_S1),pitcher_samples=u.reg_read(UC_MIPS_REG_S3))
 u.emu_start(0x8cd9e40,0x9f80000,count=10000)
 raw['bars']={k:struct.unpack('<f',u.mem_read(addr-0x5c+off,4))[0]*100 for k,off in [('pitching',0x3a674),('batting',0x3a66c),('fielding',0x3a67c)]}
 return raw
class TeamStrengthTests(unittest.TestCase):
 def test_calibration_is_idempotent_and_sparse_pitch_is_not_elite(self):
  from recalibrate_team_strength import recalibrate,VERSION
  data=json.loads((ROOT/'translation/kbo_2026/ratings_review.json').read_text('utf8'))
  self.assertEqual(data['calibration_version'],VERSION)
  self.assertEqual(recalibrate(data),data)
  p=next(p for p in data['teams']['LT']['players'] if p['name']=='최준용')
  cutter=next(q for q in p['pitches'] if q['name']=='커터')
  self.assertLessEqual(cutter['stuff'],2);self.assertLessEqual(cutter['break'],2)
 def test_real_screen_replay_and_candidate(self):
  orig=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();p,_=apply(orig,orig);p=apply_playerdata(p)
  pd=dict((n,b) for n,o,b in chunks(p))['PDN'];new={struct.unpack_from('<H',pd,i+84)[0]:pd[i:i+192] for i in range(0,len(pd),192)}
  before=json.loads((D/'before.json').read_text('utf8'));results=[]
  for b in before:
   team=(D/(b['code']+'_team.bin')).read_bytes();old=evaluate(team);candidate=evaluate(team,new)
   for key in ('pitching','batting','fielding'):self.assertAlmostEqual(old[key],b[key],places=4,msg=(b['code'],key))
   for key in ('batter_samples','pitcher_samples'):self.assertEqual(old[key],candidate[key])
   results.append(dict(code=b['code'],before=old,after=candidate))
  self.assertTrue(all(0<=r['after']['bars'][k]<=100.01 for r in results for k in ('pitching','batting','fielding')))
  self.assertGreater(len({round(r['after']['bars']['pitching'],1) for r in results}),5)
  (D/'simulation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
  for r in results:print(r['code'],{k:round(v,1) for k,v in r['after']['bars'].items()})
if __name__=='__main__':unittest.main(verbosity=2)
