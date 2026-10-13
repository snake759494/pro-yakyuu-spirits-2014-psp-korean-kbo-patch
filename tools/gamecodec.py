"""標準 CP932 밖의 게임 전용 상표 기호를 명시적으로 보존한다."""
SPECIAL={b'\xfc\x57':'<TM>',b'\xfc\x59':'<REG>'}
def decode(data):
 for raw,tag in SPECIAL.items():data=data.replace(raw,tag.encode('ascii'))
 return data.decode('cp932')
def encode(text):
 out=text.encode('cp932')
 for raw,tag in SPECIAL.items():out=out.replace(tag.encode('ascii'),raw)
 return out
