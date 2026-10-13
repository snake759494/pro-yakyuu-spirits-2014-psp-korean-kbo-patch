"""구단 ID와 자원 이름은 0부터 시작한다. 한 글자 표기는 별도 필드."""
TEAMS=[('LG','G','L'),('SS','D','삼'),('HT','C','기'),('WO','YS','키'),('KT','DB','K'),('LT','T','롯'),('HH','E','한'),('OB','F','두'),('SK','L','S'),('NC','BS','N')]
SHORT={code:short for code,asset,short in TEAMS}
ASSET_CODE={asset:code for code,asset,short in TEAMS}
ASSET_CODE['EL']='HH'
def texture_short(file):
 if not file.startswith('TEAM'):return None
 key=file[4:].split('_')[0]
 return SHORT.get(ASSET_CODE.get(key))
