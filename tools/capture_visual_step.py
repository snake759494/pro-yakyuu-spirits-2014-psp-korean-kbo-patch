"""독립 PPSSPP를 잠깐 진행하고 화면을 저장한 뒤 CPU를 정지한다."""
import sys,time
from pathlib import Path
from ppsspp_rpc import Debugger

def main():
 path=Path(sys.argv[1]);seconds=float(sys.argv[2]);button=sys.argv[3] if len(sys.argv)>3 else None
 d=Debugger()
 try:
  if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
  if button:d.call('input.buttons.press',button=button,duration=2)
  time.sleep(seconds)
  print(d.frame(path,resume_after=False))
 finally:d.close()
if __name__=='__main__':main()
