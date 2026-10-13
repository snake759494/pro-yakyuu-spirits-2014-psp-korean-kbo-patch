"""첫 이닝 투구 화면에서 경기 중단 후 팀 선택으로 돌아오는 관찰된 경로."""
import sys,time
sys.path.insert(0,'tools')
from ppsspp_rpc import Debugger
def press(d,b,n=1):
 for _ in range(n):
  d.call('input.buttons.send',buttons={b:True});time.sleep(.15)
  d.call('input.buttons.send',buttons={b:False});time.sleep(.85)
d=Debugger()
try:
 if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
 press(d,'start');time.sleep(5);press(d,'right');press(d,'down',6);press(d,'cross');time.sleep(2)
 press(d,'left');press(d,'cross');time.sleep(9);press(d,'cross');time.sleep(3);press(d,'cross');time.sleep(3)
 d.frame('build/league_runtime.png')
finally:d.close()
