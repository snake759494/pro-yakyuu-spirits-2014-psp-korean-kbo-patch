"""PSP v2.00 PDN(192), PDW(84)의 확인된 비트 필드.

BOOT.BIN getters: 수비 088ec5b0, 파워 088ec6f4, 컨택 088ec7fc,
주력 088ec9ac, 어깨 088ecaa8, 송구 088ecba0, 포구 088ecc9c,
피로회복 088ecd98, 구속 088ecfc0, 구종 088ed5f8,
변화량 08900488, 구위 088ed3e8, 제구 088ed3a0.
ID 84:90, 구단 90:92, 이름 110:152, 생일 104 하위16bit.
"""
import struct
FIELDS={
 'trajectory':(12,11,3),
 'contact_r':(24,7,7),'contact_l':(24,14,7),'stamina':(24,21,7),
 'starter':(24,29,3),'reliever':(28,0,3),'closer':(28,3,3),
 'recovery':(28,6,7),'speed':(28,13,7),'arm':(28,20,7),
 'power':(32,0,7),'throwing':(32,14,7),'catching':(32,21,7),
 'velocity_raw':(36,0,7),'height':(152,0,8),
 'throw_hand':(152,12,2),'bat_hand':(152,14,2),
 'jersey':(160,0,11),
}
POSITIONS={'P':(24,0,7),'C':(12,22,7),'1B':(16,0,7),'2B':(16,7,7),
 '3B':(16,14,7),'SS':(16,21,7),'LF':(20,0,7),'CF':(20,7,7),'RF':(20,14,7)}
def get(r,field):
 o,s,n=(FIELDS|POSITIONS)[field];return (int.from_bytes(r[o:o+4],'little')>>s)&((1<<n)-1)
def put(r,field,value):
 o,s,n=(FIELDS|POSITIONS)[field];assert 0<=value<1<<n,(field,value)
 v=int.from_bytes(r[o:o+4],'little');mask=((1<<n)-1)<<s
 r[o:o+4]=((v&~mask)|(value<<s)).to_bytes(4,'little')
def jersey_code(number):
 return sum(int(c)*11**i for i,c in enumerate(str(number)[::-1]))
def pitch(kind,breaking,stuff,control):
 assert 0<=kind<=37 and all(0<=x<=7 for x in (breaking,stuff,control))
 return struct.pack('<H',kind|(breaking<<7)|(stuff<<10)|(control<<13))
PITCHES={'포심':(0,5),'투심':(2,5),'슬라이더':(4,0),'커터':(6,0),'커브':(8,1),
 '너클커브':(13,1),'포크':(14,2),'체인지업':(18,2),'스플리터':(19,2),
 '싱커':(23,3),'서클체인지':(31,3),'슈트':(33,4)}
def apply_abilities(old,p):
 r=bytearray(old);a=p['abilities']
 # 원 일본 선수의 특수능력은 넘겨받지 않는다. 확인된 기본 능력을 별도로 기록.
 r[:84]=bytes(84)
 for k,v in a.items():
  if k in FIELDS:put(r,k,v)
 for pos,v in p['fielding'].items():put(r,pos,v)
 put(r,'velocity_raw',p.get('velocity',120)-80)
 r[58:82]=pitch(37,0,0,0)*12
 used=set()
 for q in p.get('pitches',[]):
  kind,slot=PITCHES[q['name']]
  if slot in used:slot+=6
  assert slot not in used,(p['name'],q);used.add(slot)
  r[58+slot*2:60+slot*2]=pitch(kind,q['break'],q['stuff'],q['control'])
 return r
