"""사진의 조명과 흰 배경을 UV 외곽에 전파하지 않는 피부 합성."""
import cv2
import numpy as np

def blend(base, photo, center, radii, sample):
    out=base.copy()
    yy,xx=np.indices(base.shape[:2],dtype=np.float32)
    cx,cy=center;rx,ry=radii
    radius=np.sqrt(((xx-cx)/rx)**2+((yy-cy)/ry)**2)
    t=np.clip((1-radius)/.38,0,1)
    alpha=t*t*(3-2*t)
    # 흰 배경은 경계 안으로 한 픽셀 확장해 제거한다.
    white=(photo.min(2)>185)&(np.ptp(photo.astype(np.int16),axis=2)<48)
    outer=radius>.65
    reject=cv2.dilate((white&outer).astype(np.uint8),np.ones((3,3),np.uint8))
    alpha*=1-cv2.GaussianBlur(reject.astype(np.float32),(5,5),1)
    alpha*=base[:,:,3]/255
    a=cv2.cvtColor(base[:,:,:3].astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    b=cv2.cvtColor(photo.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    ys,xs=sample
    delta=np.median(a[ys,xs].reshape(-1,3),axis=0)-np.median(b[ys,xs].reshape(-1,3),axis=0)
    b+=delta
    # 눈·코·입의 개인 특징은 유지하면서 사진의 큰 조명 얼룩만 원본에 맞춘다.
    lo_a=cv2.GaussianBlur(a,(0,0),5)
    lo_b=cv2.GaussianBlur(b,(0,0),5)
    # 사진의 측광 그늘(한쪽 볼이 어두운 경우)이 게임 얼굴을 어둡게 만들지 않도록 저주파 조명을 더 강하게 평탄화.
    correction=np.clip(lo_a-lo_b,[-30,-8,-8],[30,8,8])
    b+=correction*.85
    rgb=np.clip(cv2.cvtColor(b,cv2.COLOR_LAB2RGB)*255,0,255)
    out[:,:,:3]=np.rint(rgb*alpha[:,:,None]+base[:,:,:3]*(1-alpha[:,:,None])).astype(np.uint8)
    assert np.array_equal(out[alpha==0],base[alpha==0])
    return out
