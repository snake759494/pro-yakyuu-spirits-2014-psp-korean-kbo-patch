"""팀 선택 화면에서 관찰된 경로만 조작한다. 상태 저장/메모리 변경 없음."""
import sys,time
from pathlib import Path
from ppsspp_rpc import Debugger
def press(d,button,n=1):
 for _ in range(n):
  d.call('input.buttons.send',buttons={button:True});time.sleep(.15)
  d.call('input.buttons.send',buttons={button:False});time.sleep(.85)

GRID={'HH':(0,0),'SK':(0,1),'NC':(0,4),'OB':(0,5),
      'LG':(1,0),'LT':(1,1),'HT':(1,2),'SS':(1,3),'KT':(1,4),'WO':(1,5),
      'M':(0,2),'H':(0,3)}
home,away=sys.argv[1:3];night='--night' in sys.argv
def option(key,default):return sys.argv[sys.argv.index(key)+1] if key in sys.argv else default
def move(d,target,current):
 r,c=GRID[target];pr,pc=GRID[current]
 if r!=pr:press(d,'down' if r>pr else 'up')
 press(d,'right' if c>pc else 'left',abs(c-pc))
out=Path('build/club_brand/final');out.mkdir(exist_ok=True,parents=True)
d=Debugger()
try:
 if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
 if '--settings' not in sys.argv:
  move(d,home,option('--from-home','HH'))
  d.call('input.buttons.send',buttons={'rtrigger':True});press(d,'cross')
  move(d,away,option('--from-away','LG'))
  press(d,'cross');d.call('input.buttons.send',buttons={'rtrigger':False})
 press(d,'down');press(d,'right');press(d,'down')
 # 대전 기본값은 상대 슬롯과 저장 설정에 영향을 받는다. 필요 시 명시적 토글.
 toggle=away in ('LG','SS','HT','WO','KT','LT')
 if '--toggle-dh' in sys.argv:toggle=True
 if '--keep-dh' in sys.argv:toggle=False
 if toggle:press(d,'right')
 press(d,'up',2);press(d,'cross');time.sleep(1)
 d.frame(out/f'{home}_uniform_select.png')
 press(d,'cross',2);time.sleep(1)
 if night:press(d,'down',2);press(d,'right');press(d,'up',2)
 d.frame(out/f'{home}_stadium_select.png')
 # 구장, 경기 설정, 1P 오더, COM 오더, 오더 확인.
 for _ in range(5):press(d,'cross');time.sleep(2)
 time.sleep(6);d.frame(out/f'{home}_loading.png',resume_after=False)
finally:
 try:d.call('input.buttons.send',buttons={'rtrigger':False})
 finally:d.close()
