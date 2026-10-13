"""추가 구단의 원본 구장 UV/물리 정보를 보존한 표장 교체."""
import hashlib,struct,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT
from analyze import chunks
from hanwha_visual import decode
from hanwha_stadium import replace_texture
from lg_brand import paste
from club_brand import configs
C={};BLACK=(20,25,30)
def selected():return {k:v for k,v in configs().items() if k!='SS'}
def files():
 import json
 available={e['name'] for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']}
 result={'STSEL.CHK'}
 for c in selected().values():
  mapping=resources(c)
  result.update(mapping);result.update(mapping.values())
  result.update(c.get('aux_light_sources',{}).values())
 return result

def resources(c):
 if c.get('resource_map'):return c['resource_map']
 available={e['name'] for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']}
 names={p+c['stadium_model']+suffix+'.CHK' for p in ('C','D','N') for suffix in ('','M') if p+c['stadium_model']+suffix+'.CHK' in available}
 return {n:n for n in names}
def mark(name):
 im=Image.open(ROOT/'translation/kbo_logos'/(C['code']+'.png')).convert('RGBA');return im.crop(im.getbbox())

def sign(size,rects,number,transparent=False):
 bg=(0,0,0,0) if transparent else BLACK+(255,)
 im=Image.new('RGBA',size,bg)
 for j,(x0,y0,x1,y1) in enumerate(rects or [(0,0,*size)]):
  w,h=x1-x0,y1-y0
  if w<1 or h<1:continue
  tile=Image.new('RGBA',(w*4,h*4),bg);dr=ImageDraw.Draw(tile)
  if w<h or w/h<2:paste(tile,mark('emblem03'),(2,2,w*4-4,h*4-4))
  else:
   text=(C['stadium_name'],C['name'],C['stadium_english'])[(number+j)%3] if h>=16 else C['stadium_english']
   font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),64);box=font.getbbox(text);mask=Image.new('L',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(mask).text((-box[0],-box[1]),text,font=font,fill=255);mask.thumbnail((max(1,w*4-12),max(1,h*4-8)),Image.Resampling.LANCZOS);tile.paste('white',((w*4-mask.width)//2,(h*4-mask.height)//2),mask)
  im.alpha_composite(tile.resize((w,h),Image.Resampling.LANCZOS),(x0,y0))
 return im
def apply_one(sources,patched,preview=False):
 from stadium_uv import panels
 model=C['stadium_model'];day={n:b for n,o,b in chunks(sources['D'+model+'.CHK'])};targets=set(C['ads'])&day.keys();uv=panels(day,targets);uv.update(C.get('uv_overrides',{}));hashes={hashlib.sha256(day[n]).hexdigest():n for n in targets};report=[];boards=[]
 for file,donor in sorted(resources(C).items()):
  data=sources[donor];out=bytearray(data if donor!=file else patched[file])
  if donor.startswith('C'):
   if donor!=file:
    assert len(out)<=len(sources[file]),(file,donor)
    out.extend(bytes(len(sources[file])-len(out)));patched[file]=out
    report.append(dict(file=file,offset=0,size=len(out),original=sources[file].hex(),patched=out.hex(),reason=C['code']+' 복제 구장 충돌'))
   continue
  cs={n:(o,b) for n,o,b in chunks(data)};names=list(cs)
  if file.endswith('M.CHK'):
   from club_scoreboard import apply as scoreboard
   out,rr=scoreboard(file,data)
   if file in C.get('aux_light_sources',{}):
    light_source={n:b for n,o,b in chunks(sources[C['aux_light_sources'][file]])}
    at,raw=cs['LIGHTS'];new=light_source['LIGHTS'];assert len(raw)==len(new)
    out[at:at+len(raw)]=new
   if donor==file:report+=rr
   names=[]
  for i,n in enumerate(names[:-1]):
   o,b=cs[n];key=hashlib.sha256(b).hexdigest()
   if file.endswith('M.CHK'):
    if not n.startswith('T_TMMK'):continue
    pn=n.replace('T_','P_',1);rects=[];num=0
   else:
    if key not in hashes:continue
    src=hashes[key];pn=names[i+1];rects=uv[src];num=int(src)
   if pn not in cs or cs[pn][1][:4]!=b'PPAL':continue
   a=decode(b);pal=np.frombuffer(cs[pn][1][16:],np.uint8).reshape(-1,4);transparent=bool((pal[a][:,:,3]<50).mean()>.35)
   im=sign((a.shape[1],a.shape[0]),rects,num,transparent)
   if not file.endswith('M.CHK') and src in C.get('preserve_facade',[]):
    facade=Image.fromarray(pal[a]);
    for rect in rects:facade.paste(im.crop(tuple(rect)),tuple(rect[:2]))
    im=facade
   replace_texture(out,cs,n,pn,im);boards.append(dict(file=file,chunk=n,rects=rects,transparent=transparent))
   for q in (() if donor!=file else (n,pn)):
    at,raw=cs[q];report.append(dict(file=file,offset=at,size=len(raw),original=data[at:at+len(raw)].hex(),patched=out[at:at+len(raw)].hex(),reason=C['code']+' 구장 간판: UV 조각별 맞춤'))
  if donor!=file:
   assert len(out)<=len(sources[file]),(file,donor,len(out),len(sources[file]))
   out.extend(bytes(len(sources[file])-len(out)))
   report.append(dict(file=file,offset=0,size=len(out),original=sources[file].hex(),patched=out.hex(),reason=C['code']+' 독립 구장 모델/간판 복제'))
  patched[file]=out
 # 구단별 홈구장 포인터와 일정은 같은 슬롯을 사용한다.
 boot=sources['BOOT.BIN'];target=0x2846a0+C['team_id']*4;new=struct.pack('<I',C['stadium_slot'])
 patched['BOOT.BIN'][target:target+4]=new
 report.append(dict(file='BOOT.BIN',offset=target,size=4,original=boot[target:target+4].hex(),patched=new.hex(),reason=C['code']+' 홈구장 연결'))
 if 'donor_slot' in C:
  slot=C['stadium_slot'];donor_slot=C['donor_slot']
  at=0x2cd214+slot*228+16;src=0x2cd214+donor_slot*228+16;new=boot[src:src+212]
  patched['BOOT.BIN'][at:at+212]=new
  report.append(dict(file='BOOT.BIN',offset=at,size=212,original=boot[at:at+212].hex(),patched=new.hex(),reason=C['code']+' 모델과 치수/잔디/카메라 일치'))
  if C.get('resource_labels'):
   ptrs=[]
   for name in C['resource_labels']:
    pos=boot.index(name.encode()+b'\0');ptrs.append(pos+0x8804000-0x1018)
   at=0x3130b8+slot*16;new=struct.pack('<4I',*(ptrs*2))
   patched['BOOT.BIN'][at:at+16]=new
   report.append(dict(file='BOOT.BIN',offset=at,size=16,original=boot[at:at+16].hex(),patched=new.hex(),reason=C['code']+' 낮/밤 구장 리소스 연결'))
  cs={n:(o,b) for n,o,b in chunks(sources['STSEL.CHK'])}
  for pref in ('STA0','TPAL','STA1','TPA1'):
   target=pref+f'{slot:02}';source=pref+f'{donor_slot:02}'
   # 원래 돔 슬롯에는 별도 밤 미리보기가 없다. 낮 사진은 복제하고 실제 밤 모델은 별도 포인터로 연결한다.
   if target not in cs:continue
   o,b=cs[target];db=cs[source][1];assert len(b)==len(db)
   patched['STSEL.CHK'][o:o+len(b)]=db
   report.append(dict(file='STSEL.CHK',offset=o,size=len(b),original=b.hex(),patched=db.hex(),reason=C['code']+' 실제 복제 모델과 선택 미리보기 일치'))
 if preview:(ROOT/'build/club_brand'/(C['code']+'_stadium_boards.json')).write_text(json.dumps(boards,ensure_ascii=False,indent=2),'utf8')
 return report

def apply(sources,patched,preview=False):
 global C,BLACK
 report=[]
 for code,c in selected().items():
  C=dict(c,code=code);BLACK=tuple(c['cap_color']);report+=apply_one(sources,patched,preview)
 return report
