"""프로젝트 번역 소스와 원본 문자열로부터 글꼴의 미사용 슬롯을 재검사한다."""
import json
from inventory import ROOT,WORK

def linear(code):
 a=int.from_bytes(code,'little')
 if a&0x8000:a=(a-256)&65535
 if a&255>=224:a=(a-64)&65535
 a=(a-16513)&65535
 return (a>>8)+(a&255)*188

def inverse(n):
 a=((n%188)<<8)|(n//188);a=(a+16513)&65535
 if a&255>=160:a=(a+64)&65535
 if a>=32512:a=(a+256)&65535
 return a.to_bytes(2,'little')

def main():
 rows=json.loads((WORK/'strings.json').read_text(encoding='utf8'));ps=json.loads((ROOT/'translation/players.json').read_text(encoding='utf8'))
 # select.elf의 3712자 전각 문자표는 전체 폰트의 코드 목록이다.
 # 실제 대사 사용으로 간주하면 미사용 슬롯이 0개가 된다.
 # 문자표에서는 재배정한 코드가 해당 한글 글리프로 표시된다.
 display=[r for r in rows if not (r['file']=='select.elf' and r['offset']==412096 and len(r['ja'])==3712)]
 used=set(''.join(r['ja'] for r in display)+''.join(''.join(p['ja']) for p in ps));slots=[]
 for i in range(2965):
  code=inverse(linear(b'\x88\x9f')+i);ch=code.decode('cp932')
  if ch not in used:slots.append(dict(original=ch,code=code.hex(),index=611+i,split_index=376+i))
 (WORK/'font_slots.json').write_text(json.dumps(slots,ensure_ascii=False,indent=2),encoding='utf8');print(len(slots))
if __name__=='__main__':main()
