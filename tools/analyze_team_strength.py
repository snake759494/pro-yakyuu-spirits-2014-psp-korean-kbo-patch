"""원 게임 평가 함수를 실행하여 KBO 선수와 원본 NPB의 평가 분포를 대조한다."""
import json,struct,statistics,sys
from pathlib import Path
from unicorn import *
from unicorn.mips_const import *
from analyze import chunks
from player_fields import get
ROOT=Path(__file__).resolve().parents[1]
class Evaluator:
 def __init__(self):
  self.u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);self.u.mem_map(0x8800000,0x1800000)
  d=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();ph=struct.unpack_from('<I',d,28)[0];es,n=struct.unpack_from('<HH',d,42)
  for i in range(n):
   typ,o,v,_,s,_,_,_=struct.unpack_from('<8I',d,ph+i*es)
   if typ==1:self.u.mem_write(v,d[o:o+s])
 def call(self,address,r,*args):
  u=self.u;u.mem_write(0x9f00000,bytes(r))
  for reg,val in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_T0),[0x9f00000]+list(args)+[0]*4):u.reg_write(reg,val)
  u.reg_write(UC_MIPS_REG_SP,0x9f10000);u.reg_write(UC_MIPS_REG_RA,0x9e00000)
  u.emu_start(address,0x9e00000,count=5000000)
  assert u.reg_read(UC_MIPS_REG_PC)==0x9e00000,hex(u.reg_read(UC_MIPS_REG_PC))
  return u.reg_read(UC_MIPS_REG_V0)
 def scores(self,r):
  pos=(r[168]>>3)&15
  components={}
  if pos==0:
   signed=lambda x:x if x<0x80000000 else x-0x100000000
   breaking=signed(self.call(0x8902710,r));fastball=signed(self.call(0x8902ab8,r,0));special=signed(self.call(0x8902ca0,r))
   components=dict(breaking_score=breaking,fastball_score=fastball,special_score=special)
   score=int((5*max(breaking,fastball)+4*min(breaking,fastball)+special+50)*.12+.5)
  else:score=0
  return dict(pitching=score,batting=self.call(0x8900898,r,0,2,2),fielding=self.call(0x8900984,r,0,12,0),**components)
def main():
 from kbo_team_layout import layouts
 from kbo_rosters import apply
 ev=Evaluator();original=(ROOT/'work/assets/PLAYERDATA.CHK').read_bytes();orig=dict((n,b) for n,o,b in chunks(original))['PDN']
 inv=json.loads((ROOT/'work/inventory.json').read_text('utf8'));e=next(e for e in inv['fbd'] if e['name']=='PLAYERDATA.CHK')
 with (ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso').open('rb') as f:f.seek(e['offset']);new=dict((n,b) for n,o,b in chunks(f.read(e['size'])))['PDN']
 if '--manifest' in sys.argv:
  from kbo_team_layout import apply_playerdata
  patched,_=apply(original,original);new=dict((n,b) for n,o,b in chunks(apply_playerdata(patched)))['PDN']
 rows=[]
 for code,t in layouts().items():
  for p in t['players']:
   idx=p['index'];r=new[idx*192:(idx+1)*192]
   rows.append(dict(team=code,index=idx,name=p['name'],category=p['category'],active=idx in {q['index'] for q in t['active']},abilities={k:get(r,k) for k in ('contact_r','power','speed','arm','catching','throwing','stamina')},**ev.scores(r)))
  print(code,'완료',flush=True)
 baseline=[];byid={struct.unpack_from('<H',orig,i*192+84)[0]:i for i in range(len(orig)//192)}
 cs=dict((n,b) for n,o,b in chunks(original));boot=(ROOT/'work/iso/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();original_rows=[]
 for tid in range(12):
  start,active,extra=struct.unpack_from('<HHI',boot,0x8a94a10-0x8804000+0x1018+tid*8)
  for j in range(active+(extra&4095)):
   gid=struct.unpack_from('<H',cs['PDTPLIST'],(start+j)*2)[0];original_rows.append((byid[gid],tid,j<active))
 for i,tid,active in original_rows:
  r=orig[i*192:(i+1)*192]
  baseline.append(dict(index=i,team=tid,active=active,category='P' if r[168]&0x78==0 else 'B',abilities={k:get(r,k) for k in ('contact_r','power','speed','arm','catching','throwing','stamina')},**ev.scores(r)))
 result=dict(players=rows,original_players=baseline)
 suffix='_candidate' if '--manifest' in sys.argv else ''
 (ROOT/f'build/team_strength/player_scores{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
 for label,ps in [('KBO',rows),('NPB',baseline)]:
  for cat in ('P','B'):
   subset=[r for r in ps if (r['category']=='P')==(cat=='P')]
   print(label,cat,len(subset),{k:round(statistics.mean(r[k] for r in subset),2) for k in ('pitching','batting','fielding')})
if __name__=='__main__':main()
