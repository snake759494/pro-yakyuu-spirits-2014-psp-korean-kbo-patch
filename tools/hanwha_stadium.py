"""한화 전용 12번 구장 슬롯: 마쓰다 모델 복제와 대전 표기.

외야 충돌 데이터도 함께 복제한다. 다른 팀의 원래 마쓰다 자원은 보존한다.
"""
import hashlib,json,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from inventory import ROOT,ISO
from analyze import chunks
from hanwha_visual import decode,encode,logo,NAVY,ORANGE

MODEL_FILES={'CMIYAGI.CHK','DMIYAGI.CHK','NMIYAGI.CHK','DMIYAGIM.CHK','NMIYAGIM.CHK'}
FILES=MODEL_FILES|{'STSEL.CHK'}
ADS={'060','077','086','088','090','093','095','097','100','102','107','128','140','143','145','147','167','169','172','175','177','206','208','212','229','242','244','251','253','255','280','303','330'}

def originals():
    es={e['name']:e for e in json.loads((ROOT/'work/inventory.json').read_text('utf8'))['fbd']}
    result={}
    with ISO.open('rb') as f:
        for n in MODEL_FILES|{n.replace('MIYAGI','HIROSHIMA') for n in MODEL_FILES}:
            e=es[n];f.seek(e['offset']);result[n]=f.read(e['size'])
    return result

def sign(size,number=0,rects=None):
    if rects is not None:
        w,h=size;im=Image.new('RGBA',size,NAVY+(255,))
        for j,(x0,y0,x1,y1) in enumerate(rects):
            width,height=x1-x0,y1-y0
            tile=Image.new('RGBA',(width*4,height*4),NAVY+(255,))
            if width<height:
                logo(tile,'ci_initial_orange.png',(width//2,height//2,width*3,height*3))
            else:
                text=('대전 한화생명 볼파크' if width>=120 and height>=24 else '한화 이글스') if j%2==0 else '대전 볼파크'
                if height<10:text='HANWHA EAGLES'
                font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),64)
                box=font.getbbox(text);mask=Image.new('L',(box[2]-box[0],box[3]-box[1]))
                ImageDraw.Draw(mask).text((-box[0],-box[1]),text,font=font,fill=255)
                mask.thumbnail((max(4,width*4-16),max(4,height*4-10)),Image.Resampling.LANCZOS)
                tile.paste((255,255,255,255),((tile.width-mask.width)//2,(tile.height-mask.height)//2),mask)
            im.alpha_composite(tile.resize((width,height),Image.Resampling.LANCZOS),(x0,y0))
        return im
    w,h=size;im=Image.new('RGBA',(max(w,128)*3,max(h,32)*3),NAVY+(255,))
    W,H=im.size;d=ImageDraw.Draw(im)
    d.rectangle((0,0,W-1,max(1,H//16)),fill=ORANGE+(255,))
    if number%3==0:
        logo(im,'ci_wordmark_home_orange.png',(W//12,H//5,W*5//6,H*3//5))
    else:
        text='대전 한화생명 볼파크' if number%3==1 else '한화 이글스'
        font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),64)
        box=font.getbbox(text);mask=Image.new('L',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(mask).text((-box[0],-box[1]),text,font=font,fill=255)
        mask.thumbnail((W*9//10,H*3//5),Image.Resampling.LANCZOS)
        im.paste((255,255,255,255),((W-mask.width)//2,(H-mask.height)//2),mask)
    return im.resize((w,h),Image.Resampling.LANCZOS)

def replace_texture(out,cs,tn,pn,im):
    to,tb=cs[tn];po,pb=cs[pn];count=(len(pb)-16)//4
    a=decode(tb);assert im.size==(a.shape[1],a.shape[0])
    q=im.quantize(colors=min(count,16 if tb[12]==4 else 256),method=Image.Quantize.FASTOCTREE)
    indices=np.array(q);rgba=np.array(q.convert('RGBA'));pal=np.zeros((count,4),np.uint8)
    for i in np.unique(indices):pal[i]=rgba[indices==i][0]
    out[to+16:to+len(tb)]=encode(indices,tb);out[po+16:po+len(pb)]=pal.tobytes()

def apply(sources,patched,preview=False):
    original=originals();day={n:b for n,o,b in chunks(original['DHIROSHIMA.CHK'])}
    from stadium_uv import panels
    uv_panels=panels(day,ADS)
    uv_panels['303']=[(0,0,44,32),(44,0,64,32),(0,33,64,64)]
    uv_panels['330']=[(0,0,64,16)]
    # 빌딩 외벽 전체에 하나의 간판을 확대하지 않고 광고 부분만 덮는다.
    uv_panels['128']=[(0,16,48,32),(0,48,48,64),(0,72,48,88)]
    uv_panels['147']=[(0,0,128,31),(0,32,128,64)]
    ad_hashes={hashlib.sha256(day[n]).hexdigest():int(n) for n in ADS}
    report=[];details=[]
    for name in sorted(MODEL_FILES):
        donor=name.replace('MIYAGI','HIROSHIMA')
        if name.endswith('M.CHK'):
            # 기존 팔레트 용량과 치수를 유지하고 새 구장의 조명을 옮긴다.
            out=bytearray(sources[name]);cs={n:(o,b) for n,o,b in chunks(out)};ds={n:b for n,o,b in chunks(original[donor])}
            for n in ('LIGHTS','M_ITA'):
                if n in cs:
                    o,b=cs[n];assert len(b)==len(ds[n]);out[o:o+len(b)]=ds[n]
            for j in (1,2):
                tn=f'T_TMMK{j}';pn=f'P_TMMK{j}';a=decode(cs[tn][1]);im=sign((a.shape[1],a.shape[0]),0)
                replace_texture(out,cs,tn,pn,im)
        else:
            out=bytearray(original[donor]);cs={n:(o,b) for n,o,b in chunks(out)}
            if name[0] in 'DN':
                sequence=list(cs)
                for i,n in enumerate(sequence):
                    b=cs[n][1];key=hashlib.sha256(b).hexdigest()
                    if key not in ad_hashes:continue
                    pn=sequence[i+1];assert cs[pn][1][:4]==b'PPAL'
                    a=decode(b);source=f'{ad_hashes[key]:03}'
                    im=sign((a.shape[1],a.shape[0]),ad_hashes[key],uv_panels[source])
                    if source=='128':
                        pb=cs[pn][1];pal=np.frombuffer(pb[16:],np.uint8).reshape(-1,4)
                        facade=Image.fromarray(pal[a]);painted=im
                        for rect in uv_panels[source]:facade.paste(painted.crop(rect),rect[:2])
                        im=facade
                    replace_texture(out,cs,n,pn,im);details.append(dict(file=name,chunk=n,source_chunk=ad_hashes[key]))
            assert len(out)<=len(sources[name]),(name,len(out),len(sources[name]))
            out.extend(bytes(len(sources[name])-len(out)))
        assert len(out)==len(sources[name]);patched[name]=out
        report.append(dict(file=name,offset=0,size=len(out),original=sources[name].hex(),patched=out.hex(),reason='한화 전용 대전 구장 모델/충돌/조명/간판'))
    # 구장 ID와 리소스/명칭 포인터는 유지하고 치수·잔디·외야 곡선·카메라를 같은 모델에 맞춘다.
    donor=0x2cd2f8+16;target=0x2cdcc4+16;size=228-16
    old=sources['BOOT.BIN'][target:target+size];new=sources['BOOT.BIN'][donor:donor+size]
    assert struct.unpack_from('<f',old,16)[0]>122 and struct.unpack_from('<f',new,16)[0]==122
    patched['BOOT.BIN'][target:target+size]=new
    report.append(dict(file='BOOT.BIN',offset=target,size=size,original=old.hex(),patched=new.hex(),reason='복제 구장과 잔디/치수/외야/카메라 정보 일치'))
    name='STSEL.CHK';cs={n:(o,b) for n,o,b in chunks(sources[name])}
    out=bytearray(patched[name]);patched[name]=out
    for target,donor in [('STA012','STA001'),('TPAL12','TPAL01'),('STA112','STA101'),('TPA112','TPA101')]:
        o,b=cs[target];db=cs[donor][1];assert len(b)==len(db)
        out[o:o+len(b)]=db
        report.append(dict(file=name,offset=o,size=len(b),original=b.hex(),patched=db.hex(),reason='대전 구장 선택 미리보기 모델 일치'))
    if preview:
        (ROOT/'build/face_stadium/boards.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),'utf8')
        (ROOT/'build/visual_fixes/stadium_uv.json').write_text(json.dumps(uv_panels,indent=2),'utf8')
    return report

def index_patch(inv):
    archive=next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
    e=next(e for e in inv['fbd'] if e['name']=='CMIYAGI.CHK')
    assert e['size']==111168 and e['capacity']==112640
    return dict(offset=archive['offset']+22+e['index']*268+260,original=struct.pack('<I',e['size']).hex(),patched=struct.pack('<I',e['capacity']).hex(),size=4)
