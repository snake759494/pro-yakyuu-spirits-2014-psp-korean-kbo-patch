"""SINF 재질 연결과 PGOX 삼각형 스트립으로 광고판의 실제 UV 범위를 추출한다."""
import struct, math
import numpy as np

def panels(cs,targets):
    info=cs['000'];count=struct.unpack_from('<I',info,12)[0]
    # 헤더 뒤의 12바이트 그룹 목록 길이. 24번 값은 오프셋이 아니며
    # 히로시마에서는 우연히 기존 계산과 일치했지만 치바/진구에는 맞지 않는다.
    start=36+struct.unpack_from('<I',info,8)[0]*12;materials=start+count*84
    result={n:[] for n in targets}
    for i in range(count):
        at=start+i*84;mesh=struct.unpack_from('<I',info,at+28)[0]
        slots=struct.unpack_from('<4H',info,at+32)
        b=cs[f'{mesh:03}'];assert b[:4]==b'PGOX'
        o=96;uv=None;texture=None
        while o+16<=len(b):
            tag=b[o:o+4];size=struct.unpack_from('<I',b,o+4)[0]
            if tag.startswith(b'MAT'):
                slot=int(chr(tag[3]));mat=slots[slot]
                texture=f'{struct.unpack_from("<I",info,materials+mat*8+4)[0]:03}'
            elif tag.startswith(b'VTX') and texture in result:
                n=struct.unpack_from('<I',b,o+8)[0]
                fmt=struct.unpack_from('<I',b,16)[0]&0xf000
                dtype,stride,scale={0x1000:('u1',10,128),0x2000:('<u2',12,32768),0x4000:('<f4',16,1)}[fmt]
                assert size>=16+n*stride,(mesh,texture,tag,size,n,fmt)
                uv=np.ndarray((n,2),dtype=dtype,buffer=b,offset=o+16,strides=(stride,np.dtype(dtype).itemsize)).astype(float)/scale
            elif tag==b'STRP' and texture in result and uv is not None:
                n=struct.unpack_from('<I',b,o+8)[0];idx=struct.unpack_from(f'<{n}H',b,o+12)
                parents=list(range(len(uv)))
                def root(x):
                    while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
                    return x
                used=set()
                for a,c,d in zip(idx,idx[1:],idx[2:]):
                    if len({a,c,d})<3:continue
                    assert max(a,c,d)<len(uv)
                    for v in (c,d):parents[root(v)]=root(a)
                    used.update((a,c,d))
                groups={}
                for v in used:groups.setdefault(root(v),[]).append(v)
                tb=cs[texture];w=struct.unpack_from('<H',tb,10)[0];h=1<<tb[9]
                for vertices in groups.values():
                    lo=uv[vertices].min(0);hi=uv[vertices].max(0)
                    bounds=[]
                    for a,z,scale in zip(lo,hi,(w,h)):
                        if z-a>=.97:a,z=0.,1.
                        else:
                            shift=math.floor(float(a)+.02);a-=shift;z-=shift
                        bounds.append((max(0,round(float(a)*scale)),min(scale,round(float(z)*scale))))
                    (x0,x1),(y0,y1)=bounds
                    if x1-x0>=5 and y1-y0>=5:result[texture].append((x0,y0,x1,y1))
                uv=None
            if size<16 or o+size>len(b):break
            o+=size
    return {n:sorted(set(rects)) for n,rects in result.items()}

if __name__=='__main__':
    import json
    from inventory import ROOT
    from ui_textures import original_chunks
    from hanwha_stadium import ADS
    result=panels(original_chunks('DHIROSHIMA.CHK'),ADS)
    (ROOT/'build/visual_fixes/stadium_uv.json').write_text(json.dumps(result,indent=2),'utf8')
    print(json.dumps(result))

