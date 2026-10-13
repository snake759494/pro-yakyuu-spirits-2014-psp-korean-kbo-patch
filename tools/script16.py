"""이벤트 VM의 16비트 문자 토큰. 명령 토큰과 인수는 변경하지 않는다."""
import re,struct
def char(word):
 # 0x0034 등의 작은 값은 화자·변수 인수이다. ASCII 문자로 읽지 않는다.
 if not (0x8140<=word<=0x9ffc or 0xe040<=word<=0xfc4b):return None
 try:return word.to_bytes(2,'big').decode('cp932')
 except UnicodeDecodeError:return None
def extract(data):
 start=None;chars=[]
 for pos in range(0,len(data)-1,2):
  c=char(struct.unpack_from('<H',data,pos)[0])
  if c is not None:
   if start is None:start=pos
   chars.append(c)
  else:
   if chars and re.search('[ぁ-ヿ一-鿿]', ''.join(chars)):
    yield start,''.join(chars)
   start=None;chars=[]
def encode(text,encode_char):
 out=bytearray()
 for c in text:
  b=encode_char(c)
  if len(b)==1:out+=b+b'\0'
  elif len(b)==2:out+=b[::-1]
  else:raise ValueError(c)
 return bytes(out)

def encode_text(text,encoder):
 raw=encoder(text);out=bytearray();i=0
 while i<len(raw):
  b=raw[i]
  if 0x81<=b<=0x9f or 0xe0<=b<=0xfc:
   out+=raw[i:i+2][::-1];i+=2
  else:
   c=chr(b);wide='　' if c==' ' else chr(ord(c)+0xfee0) if 0x21<=b<=0x7e else c
   bb=wide.encode('cp932');assert len(bb)==2,(text,b);out+=bb[::-1];i+=1
 return bytes(out)
