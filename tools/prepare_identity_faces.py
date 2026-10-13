"""공식 고유 ID와 게임 슬롯을 명시적으로 연결한 전 선수 외형 명세."""
import json, re, struct, hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from analyze import chunks
from prepare_hanwha_visual import body

ROOT=Path(__file__).resolve().parents[1]

def main():
    read=lambda p:json.loads((ROOT/p).read_text('utf8'))
    officials=read('work/identity_audit/official_profiles.json')['players']
    ratings=read('translation/kbo_2026/ratings_review.json')
    old=read('translation/hanwha_visual/appearance.json')+read('translation/lg_2026/details.json')
    prior={p['index']:p for p in old}
    pd=next(b for n,o,b in chunks((ROOT/'work/assets/PLAYERDATA.CHK').read_bytes()) if n=='PDN')
    inv={p['name'] for p in read('work/inventory.json')['fbd']}
    detector=cv2.FaceDetectorYN.create('onnx',np.frombuffer((ROOT/'tools/bin/face_detection_yunet_2023mar.onnx').read_bytes(),np.uint8),np.array([],np.uint8),(320,320),.6)
    skins=read('translation/kbo_2026/skin_types.json')['foreign']
    rows=[];review=[]
    for p in officials:
        idx=p['index'];prev=prior.get(idx,{})
        current=next(q for q in ratings['teams'][p['team']]['players'] if q['index']==idx)
        photo=p.get('photo') or prev.get('face_photo',prev.get('photo'))
        assert photo,(p['team'],p['expected_name'],'사진 없음')
        im=Image.open(ROOT/photo).convert('RGB');rgb=np.array(im)
        detector.setInputSize(im.size);_,found=detector.detect(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR))
        if found is None:
            # 기존에 검토한 같은 선수 사진을 사용하고, 감지 실패는 별도 기록.
            if prev:
                photo=prev.get('face_photo',prev.get('photo'));lm=prev['landmarks'];box=prev['face_box']
            else:raise ValueError((p['team'],p['expected_name'],'얼굴 검출 실패'))
            review.append(dict(name=p['expected_name'],index=idx,reason='기존 검토 사진 유지'))
        else:
            f=max(found,key=lambda b:b[2]*b[3]);lm=[list(map(float,f[k:k+2])) for k in range(4,14,2)];box=list(map(int,f[:4]))
        fid=struct.unpack_from('<H',pd,idx*192+86)[0]
        h,w=map(int,re.findall(r'\d+',p['body']))
        row=dict(index=idx,name=current['name'],team=p['team'],player_id=p['player_id'],photo=photo,photo_sha256=hashlib.sha256((ROOT/photo).read_bytes()).hexdigest(),profile_source=p['source'],photo_source=p.get('photo_source',prev.get('photo_source')),landmarks=lm,face_box=box,face_id=fid,face_file=f'F{fid}.CHK',dedicated_face=f'F{fid}.CHK' in inv,height=h,weight=w,body_type=prev.get('body_type',body(h,w)))
        if 'skin_type' in prev:
            row.update(skin_type=prev['skin_type'],skin_reference_head=prev.get('skin_reference_head',prev['skin_type']+1))
        else:
            # 피부색은 사진의 양 볼 밝기와 원 게임 톤 범위로 근사한다.
            x,y,bw,bh=box;patch=rgb[max(0,int(y+bh*.45)):int(y+bh*.75),max(0,int(x+bw*.25)):int(x+bw*.75)]
            light=float(np.median(cv2.cvtColor(patch,cv2.COLOR_RGB2LAB)[:,:,0]))
            skin=2 if light<120 else 1 if light<165 else 0
            row.update(skin_type=skin,skin_reference_head=skin+1)
        # 피부 팔레트는 밝기 순서가 비단조(2>0>4>1>5>3)이므로 검토된 지정표로 정한다.
        st=skins.get(p['player_id'],{}).get('skin_type',0)
        row.update(skin_type=st,skin_reference_head=st+1)
        rows.append(row)
    assert len(rows)==619 and len({p['index'] for p in rows})==619
    out=ROOT/'translation/kbo_2026/appearance.json'
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n','utf8')
    (ROOT/'build/identity_audit/face_preparation.json').write_text(json.dumps(dict(players=len(rows),dedicated=sum(p['dedicated_face'] for p in rows),fallback_review=review,generic_models=[dict(name=p['name'],team=p['team'],index=p['index']) for p in rows if not p['dedicated_face']]),ensure_ascii=False,indent=2),'utf8')
    print('얼굴',len(rows),'전용 모델',sum(p['dedicated_face'] for p in rows),'사진 대체',review)

if __name__=='__main__':main()
