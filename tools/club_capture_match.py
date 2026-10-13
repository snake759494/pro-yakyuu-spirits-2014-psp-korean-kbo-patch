"""로딩 설명 화면부터 도입과 첫 이닝 필드까지만 관찰 증거를 저장한다."""
import sys,time
from pathlib import Path
from ppsspp_rpc import Debugger
home,away=sys.argv[1:3];out=Path('build/club_brand/final');out.mkdir(exist_ok=True,parents=True)
d=Debugger()
try:
 if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
 d.call('input.buttons.send',buttons={'cross':True});time.sleep(.15);d.call('input.buttons.send',buttons={'cross':False})
 for suffix,wait in [('intro',5),('home',6),('away',8),('field',25)]:
  time.sleep(wait);p=out/f'{away if suffix=="away" else home}_{suffix}.png';d.frame(p);print(p,flush=True)
 d.call('cpu.stepping')
finally:d.close()
