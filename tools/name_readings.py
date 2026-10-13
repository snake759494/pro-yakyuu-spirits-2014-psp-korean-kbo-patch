"""게임 내 영문 성 표기의 읽기를 한글로 옮기는 로컬 표기 규칙.

실존 선수 이름은 이 규칙으로 추정하지 않는다. 가상 선수의 명시된
영문 성만 사용하며, 이름(名)은 직접 작성한 사전을 통해 적용한다.
"""
import re
ROWS={
 '':'아이우에오','k':'카키쿠케코','g':'가기구게고','s':'사시스세소',
 'z':'자지즈제조','t':'타티쓰테토','d':'다디즈데도','n':'나니누네노',
 'h':'하히후헤호','b':'바비부베보','p':'파피푸페포','m':'마미무메모',
 'r':'라리루레로','w':'와위우웨워',
}
MAP={c+v:h for c,row in ROWS.items() for v,h in zip('aiueo',row)}
MAP.update(dict(zip(['ya','yu','yo','shi','chi','tsu','fu','ji','sha','shu','sho','cha','chu','cho','ja','ju','jo','jya','jyu','jyo'],['야','유','요','시','치','쓰','후','지','샤','슈','쇼','차','추','초','자','주','조','자','주','조'])))
for root,k in [('ky','캬큐쿄'),('gy','갸규교'),('ny','냐뉴뇨'),('hy','햐휴효'),('by','뱌뷰뵤'),('py','퍄퓨표'),('my','먀뮤묘'),('ry','랴류료')]:
 MAP.update({root+v:h for v,h in zip('auo',k)})
def surname(latin):
 s=latin.lower();s=re.sub(r'([aeou])h',r'\1',s);s=s.replace("'",'');out='';i=0
 while i<len(s):
  if i+1<len(s) and s[i]==s[i+1] and s[i] not in 'aeioun':
   if not out:raise ValueError(latin)
   n=ord(out[-1])-0xac00
   if not 0<=n<11172 or n%28:raise ValueError(latin)
   out=out[:-1]+chr(ord(out[-1])+19);i+=1;continue
  if s[i]=='n' and (i+1==len(s) or s[i+1] not in 'aiueoy'):
   n=ord(out[-1])-0xac00 if out else -1
   if n<0 or n%28:raise ValueError(latin)
   out=out[:-1]+chr(ord(out[-1])+4);i+=1;continue
  match=next((s[i:i+n] for n in (3,2,1) if s[i:i+n] in MAP),None)
  if not match:raise ValueError((latin,s[i:]))
  c=MAP[match]
  if not out:
   c={'카':'가','키':'기','쿠':'구','케':'게','코':'고','캬':'갸','큐':'규','쿄':'교','타':'다','테':'데','토':'도','차':'자','치':'지','추':'주','초':'조'}.get(c,c)
  out+=c;i+=len(match)
 return out
