# 한화 2026 선수 외형 및 유니폼

한화 62명 선수와 5명 코칭 슬롯에 영문 등 이름, 공식 키와 몸무게를 참고한 체형, 공식 사진 기반 얼굴 텍스처를 적용한다. 개막 명단·등번호·능력치는 기존 한화 빌드를 유지한다. 선수 ID, 음성 키, 투구 모션, 얼굴 모델의 정점과 레코드 크기는 보존한다.

## 재현 범위

- 등 이름: 원 게임의 NUL 포함 12바이트 필드에 영문 성과 이름 이니셜을 넣는다. 외국인은 HERNANDEZ, WHITE, PERAZA 등을 사용한다. 실제 KBO 유니폼의 한글 등 이름과는 다른 영문 표기이다.
- 키: 공식 프로필의 cm 수치를 사용한다. 몸무게를 kg 그대로 표현하는 게임 필드는 확인되지 않아 키와 BMI 구간을 기존 체형 모델에 대응시켰다. 실제 체형과의 근사치이다.
- 얼굴: 공식 사진의 눈·입 위치를 기존 64×64 얼굴 UV에 맞춘다. 기존 3D 얼굴 골격·머리카락·몸의 피부 재질을 유지하므로 정밀한 실제 얼굴 조형은 아니다. 코치와 일부 선수는 정면 사진 대신 구단 프로필 사진을 사용한다.
- 유니폼: 한화 공식 CI와 2026 공식 상품 목록을 참고해 홈 흰색·원정 회색·대체 주황·대체 남색, 모자와 헬멧의 E, 영문 등 이름 및 등번호 색상을 넣는다. 게임의 기존 재단·UV에 맞춘 재현이며 모든 스폰서 패치와 자수·봉제선을 실물과 똑같이 복제하지는 않는다.
- 67개 얼굴 CHK와 26개 유니폼/선택 화면 CHK를 ISO 안에서 수정한다. 외부 에뮬레이터 텍스처 팩은 사용하지 않는다.
- 선수 목록의 작은 초상화는 `COMFACE.BIN`의 별도 자산이다. PDN 번호가 아니라 INIPLIST의 첫 선수 ID 위치에 대응하는 425–491번 67개 초상화와 한화 모자/상의 합성판 2458번을 수정한다. 공유 COMFACEP 팔레트와 다른 구단의 초상화는 보존한다. 사진을 저해상도 공유 팔레트에 맞추므로 색과 윤곽이 단순화된다.
- 공식 프로필은 조사 시점의 공개 자료이다. 개막 당일 신체 측정치를 따로 제공하지 않는 경우 현재 공개 수치를 사용한다. 이적 선수의 현재 소속 표시는 얼굴만 잘라 사용하며 기존 개막 명단 소속·등번호를 유지한다.

## 소스와 재빌드

`translation/hanwha_visual/official_profiles.json`에는 개별 공식 URL·사진 경로·해시를, `appearance.json`에는 등 이름·키·몸무게·체형·얼굴 ID·사진 좌표를 보존한다. 공식 자료 갱신은 `tools/research_hanwha_visual.py`, 명세 생성은 `tools/prepare_hanwha_visual.py`, ISO 삽입은 `tools/hanwha_visual.py`와 `tools/hanwha_roster.py`가 담당한다.

`tools/hanwha_portraits.py`는 메뉴 초상화를 담당한다. 기존 빌드의 외형만 반복 검토할 때는 `tools/rebuild_hanwha_visual.py`로 허용 영역을 다시 만들 수 있다. 설치 데이터는 기본적으로 유지하고 동기화하지 않는다. `--with-install-data`를 명시한 경우에만 설치 블록/MAC를 함께 갱신한다. 전체 재현의 기준은 `tools/build.py --league-trial`이다. 두 경로 모두 `tools/verify.py`로 원본 대비 변경 범위를 검증한다. 설치 생략 빌드는 설치 영역 보존을, 설치 포함 빌드는 직접 읽기 데이터와의 일치를 검사한다.

사진의 얼굴 위치 검출에는 OpenCV Zoo YuNet을 사용한다. 이는 번역 서비스가 아니며 사진의 눈·입 좌표만 로컬에서 검출한다. 모델 출처: https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet . 모델과 라이선스는 `tools/bin`에 보존한다.

```powershell
python -X utf8 tools/test_hanwha_visual.py
python -X utf8 tools/build.py --league-trial
python -X utf8 tools/verify.py
```

검사는 텍스처 디코드/인코드 왕복, 모델 및 헤더 보존, 파일 크기와 변경 범위, 기존 능력·ID 보존, 원 게임 MIPS 체형 getter를 포함한다. 실제 화면의 확인 범위는 최신 ISO 해시가 적힌 `build/runtime_validation.json`을 기준으로 한다.

기존 페넌트 및 시스템 저장 데이터에는 이전 선수 정보가 남을 수 있다. 기존 저장을 백업·분리하고 새 시스템/새 페넌트로 확인한다. 상태 저장은 사용하지 않는다. 검증 후 에뮬레이터를 종료한다.

## 공식 출처

- [한화 선수단과 개별 프로필](https://www.hanwhaeagles.co.kr/PL/PC/PLPC01.do)
- [한화 공식 CI](https://www.hanwhaeagles.co.kr/MN/CL/MNCLSY01.do)
- [한화 공식 상품 목록](https://www.hanwhaeagles.co.kr/SH/PCSH01.do)
- [KBO 선수 검색](https://www.koreabaseball.com/Player/Search.aspx)
