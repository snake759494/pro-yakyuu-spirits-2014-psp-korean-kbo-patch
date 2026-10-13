"""경기 로딩 완료 화면에서 실행: 순위표 생성 후 연출 화면을 연속 보존한다."""
import time
from pathlib import Path
from ppsspp_rpc import Debugger

d=Debugger();address=0x8da8360
try:
 d.call('cpu.breakpoint.add',address=address)
 d.call('input.buttons.press',button='cross',duration=12)
 deadline=time.monotonic()+55
 while time.monotonic()<deadline:
  status=d.call('cpu.status')
  if status.get('stepping') and status['pc']==address:break
  time.sleep(.1)
 else:raise RuntimeError('순위표 장면이 이번 연출에서 호출되지 않았음')
 d.call('cpu.breakpoint.remove',address=address);d.call('cpu.resume')
 directory=Path('build/alpha4_rank_sequence');directory.mkdir(exist_ok=True)
 for i in range(12):
  time.sleep(.15);d.frame(str(directory/f'{i:02}.png'))
 print('순위표 연출 12개 프레임 보존')
finally:
 d.call('cpu.breakpoint.remove',address=address)
 if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
 d.close()
