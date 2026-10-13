"""슬롯 1의 독립 복사본에만 적용하는 원인 확인용 실험. 최종 검증 대체 불가."""
import base64,json,struct
from pathlib import Path
from ppsspp_rpc import Debugger,readmem
from kbo_team_layout import apply_playerdata,layouts,patches,ROOT
from analyze import chunks
d=Debugger()
def write(a,b):d.call('memory.write',address=a,base64=base64.b64encode(b).decode())
try:
 d.call('cpu.stepping')
 entry=next(e for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd'] if e['name']=='PLAYERDATA.CHK')
 with (ROOT/'Pro Yakyuu Spirits 2014 (Japan) (v2.00) (Korean DEV).iso').open('rb') as f:
  f.seek(entry['offset']);raw=apply_playerdata(f.read(entry['size']))
 write(0x9369620,raw)
 tpl=next(b for n,o,b in chunks(raw) if n=='PDTPLIST')
 write(0x8ad4d74,tpl)
 for t in layouts().values():
  seq=[p['index'] for p in t['rows']]
  write(0x9468710+t['team_id']*150,struct.pack('<75H',*(seq+[0]*(75-len(seq)))))
 for file,a,b,reason in patches():write(a,b)
 d.call('memory.breakpoint.remove',address=0x9468710,size=2)
 d.call('cpu.resume')
 print('슬롯 1 복사본에 구조 수정 실험 적용')
finally:d.close()
