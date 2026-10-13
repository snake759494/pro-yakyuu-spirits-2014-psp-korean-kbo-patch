"""한글의 실제 잉크 영역을 셀에 맞춰 확대한다. 코드 배정과 셀 폭은 유지한다."""
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from inventory import ROOT

@lru_cache(maxsize=8192)
def glyph(text, w, h):
    if not text.strip():
        return Image.new('L', (w, h))
    font = ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'), 96)
    box = font.getbbox(text)
    ink = Image.new('L', (box[2]-box[0]+4, box[3]-box[1]+4))
    ImageDraw.Draw(ink).text((2-box[0], 2-box[1]), text, font=font, fill=255)
    ink = ink.crop(ink.getbbox())
    # 오른쪽과 아래 한 픽셀만 남겨 인접 글리프가 붙지 않게 한다.
    ink = ink.resize((w-1, h-1), Image.Resampling.LANCZOS)
    out = Image.new('L', (w, h))
    out.paste(ink, (0, 0))
    return out

def render(row, w, h):
    if 'phrase' not in row:
        return glyph(row.get('hangul', row.get('display_alias')), w, h).copy()
    text = row['phrase']
    wide = Image.new('L', (w*len(text), h))
    for col, char in enumerate(text):
        wide.paste(glyph(char, w, h), (col*w, 0))
    wide = wide.resize((w*row['cells'], h), Image.Resampling.LANCZOS)
    return wide.crop((row['cell']*w, 0, (row['cell']+1)*w, h))
