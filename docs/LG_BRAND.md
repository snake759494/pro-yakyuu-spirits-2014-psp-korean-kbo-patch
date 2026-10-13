# LG 트윈스 구단 표시 패치

서울·LG 트윈스·잠실 명칭과 공식 구단 BI를 사용한다. 홈은 흰색 줄무늬, 원정은 검정 상의이며 모자·헬멧·소매·선택 화면을 함께 처리한다. 기존 LG 선수 데이터와 영문 등 이름·번호는 유지한다.

구단 선택·메뉴·경기 UI·큰 엠블럼·히어로 배경·응원 깃발의 로고를 교체했다. 팀별 유니폼 자원 번호가 0부터 시작한다는 점을 반영하여 LG `N00G`가 누락되고 다른 팀이 한 칸씩 밀리던 연결도 수정했다.

LG 홈구장 및 72개 홈경기 일정은 개방형 CHIBA 슬롯7을 사용한다. 낮·밤 모델의 광고판을 서울 잠실야구장/LG 트윈스 표기로 바꿨다. 투명 외야 광고는 각 문구 영역과 투명도를 보존해 검은 사각형을 방지한다. 실제 잠실을 새로 만든 모델은 아니며 원 모델의 형상·충돌·치수(좌우99.5m, 중앙122m)를 유지한다. 선택 미리보기의 사진과 일본 지도·도시 배경 전체는 재제작하지 않았다.

한 글자 약칭은 텍스트 필드와 팀별 비트맵 양쪽에 적용한다: 한화 **한**, LG **L**, 삼성 **삼**, 키움 **키**, KT **K**, KIA **기**, 롯데 **롯**, 두산 **두**, NC **N**, SSG **S**.

## 재현과 검증

```powershell
python -X utf8 tools/build.py --league-trial
python -X utf8 tools/verify.py
python -X utf8 tools/verify_lg_brand.py
```

설치 데이터는 재생성하지 않는다. 최종 해시는 `SHA256SUMS.txt`, 정적 결과는 `build/lg_brand/static_validation.json`, 실제 실행 범위·스크린샷 해시는 `build/runtime_validation.json`에 기록한다. 중간 후보 화면은 최종 실행 증거로 사용하지 않는다.

반복 적용 규칙은 [KBO_TEAM_PATCH_RULES.md](KBO_TEAM_PATCH_RULES.md)를 따른다. 선수 데이터의 기존 추정값 및 외형 제한은 [LG_DETAILS.md](LG_DETAILS.md)를 참고한다.

## 공식 참고 자료

- LG BI: https://www.lgtwins.com/twins/about/bi
- LG 잠실 홈구장: https://www.lgtwins.com/twins/about/homeGround?ground=seoul
- LG 공식 유니폼: https://twinslockerdium.co.kr/product/list.html?cate_no=236
