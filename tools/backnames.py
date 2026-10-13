"""KBO 공식 영문명에서 유니폼 등 이름(최대 11자)을 만든다.

규칙: 국내 선수는 'SURNAME X.Y.'(이름 음절 머리글자), 외국인은 성(family name)만.
영문 공식명이 없는 신인은 성 표기표와 음절 첫 자음/모음 머리글자로 만든다.
"""
import re
SURNAME={'김':'KIM','이':'LEE','박':'PARK','최':'CHOI','정':'JUNG','강':'KANG','조':'CHO','윤':'YOON','장':'JANG','임':'LIM','한':'HAN','오':'OH','서':'SEO','신':'SHIN','권':'KWON','황':'HWANG','안':'AHN','송':'SONG','류':'RYU','유':'YOU','홍':'HONG','전':'JEON','고':'KO','문':'MOON','양':'YANG','손':'SON','배':'BAE','백':'BAEK','허':'HUR','남':'NAM','심':'SIM','노':'NOH','하':'HA','곽':'KWAK','성':'SUNG','차':'CHA','주':'JOO','우':'WOO','구':'KOO','민':'MIN','진':'JIN','나':'NA','엄':'UM','원':'WON','채':'CHAE','천':'CHUN','방':'BANG','공':'KONG','현':'HYUN','함':'HAM','변':'BYUN','염':'YEOM','여':'YEO','추':'CHOO','도':'DO','소':'SO','석':'SEOK','선':'SUN','설':'SEOL','마':'MA','길':'GIL','연':'YEON','위':'WI','표':'PYO','명':'MYUNG','기':'KI','반':'BAN','왕':'WANG','금':'KEUM','옥':'OK','육':'YOOK','인':'IN','맹':'MAENG','제':'JE','모':'MO','탁':'TAK','국':'KOOK','어':'EO','은':'EUN','편':'PYUN','용':'YONG','예':'YE','경':'KYUNG','봉':'BONG','부':'BOO','태':'TAE','형':'HYUNG','두':'DOO','동':'DONG','호':'HO','범':'BUM','승':'SEUNG','상':'SANG','지':'JI','라':'RA','명':'MYUNG'}
COMPOUND={'남궁':'NAMGOONG','황보':'HWANGBO','선우':'SUNWOO','제갈':'JEGAL','독고':'DOKGO'}
CHO='KKNDDRMBBSSOJJCKTPH'  # ㅇ은 모음으로 처리
VOW=['A','A','Y','Y','E','E','Y','Y','O','W','W','O','Y','U','W','W','W','Y','E','E','I']
def syllable_initial(ch):
 c=ord(ch)-0xAC00
 if not 0<=c<11172:return ''
 lead,vowel=c//588,(c%588)//28
 return VOW[vowel] if lead==11 else CHO[lead]
def fit(s,n=11):return s if len(s)<=n else s.split(' ')[0][:n]
def back_name(korean,english='',foreign=False):
 korean=re.sub(r'\(.*?\)|\s','',korean);english=(english or '').strip()
 if english:
  toks=english.split()
  sur=[t for t in toks if t.isupper() and re.search('[A-Z]',t)]
  given=[t for t in toks if t not in sur]
  sur=' '.join(sur) or toks[0].upper()
  if foreign:return fit(re.sub(r'[^A-Z ]','',sur.upper()).strip())
  ini=''.join(g[0].upper()+'.' for g in re.split(r'[\s\-]+',' '.join(given)) if g)
  for cand in (f'{sur} {ini}',f'{sur} {ini[:2]}',sur):
   if len(cand)<=11:return cand
  return fit(sur)
 if foreign:raise ValueError(('외국인 영문명 없음',korean))
 for k,v in COMPOUND.items():
  if korean.startswith(k):sur,rest=v,korean[2:];break
 else:sur,rest=SURNAME.get(korean[0]),korean[1:]
 assert sur,('성 표기 없음',korean)
 ini=''.join(syllable_initial(c)+'.' for c in rest)
 return f'{sur} {ini}' if len(f'{sur} {ini}')<=11 else sur
