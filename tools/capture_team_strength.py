"""팀 선택 화면의 원본 평가 함수에서 평균 계산 직후 값을 읽는다. 메모리 쓰기 없음."""
import sys,time,json,struct
from pathlib import Path
from ppsspp_rpc import Debugger,readmem,press
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/team_strength';out.mkdir(exist_ok=True)
phase=sys.argv[1] if len(sys.argv)>1 else 'before'
if phase!='before':out=out/phase;out.mkdir(exist_ok=True)
d=Debugger();bp=0x8cd9e40
route=[('HH','left'),('LT','left'),('LG','up'),('SS','right'),('HT','right'),('WO','right'),('KT','right'),('NC','down'),('SK','left'),('OB','left')]
results=[]
try:
 for code,button in route:
  d.call('cpu.breakpoint.add',address=bp)
  press(d,button)
  for _ in range(20):
   status=d.call('cpu.status')
   if status['stepping']:break
   time.sleep(.1)
  assert status['pc']==bp,(code,status)
  regs=d.call('cpu.getAllRegs')['categories']
  g=dict(zip(regs[0]['registerNames'],regs[0]['uintValues']))
  f=dict(zip(regs[1]['registerNames'],regs[1]['floatValues']))
  team=readmem(d,g['s2'],0x1d178)
  (out/f'{code}_team.bin').write_bytes(team)
  r=dict(code=code,address=hex(g['s2']),batting=float(f['f20']),pitching=float(f['f22']),fielding=float(f['f24']),batter_samples=g['s1'],pitcher_samples=g['s3'])
  results.append(r);print(json.dumps(r),flush=True)
  d.call('cpu.breakpoint.remove',address=bp);d.call('cpu.resume');time.sleep(.8)
  d.frame(out/f'{code}_{phase}.png')
finally:
 d.call('cpu.breakpoint.remove',address=bp)
 if d.call('cpu.status')['stepping']:d.call('cpu.resume')
 d.close()
(out/f'{phase}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
