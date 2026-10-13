"""PSP 원본 2014 구단별 감독/코치 레코드 ID."""

# Each tuple is (manager index, four coach indices in the game's displayed role order).
# These are verified against the Japanese names already stored at those IDs in PDN.
STAFF_SLOTS = {
    'LG': (99, (594, 3, 180, 35)),       # Hara; Kawaguchi, Murata, Suguro, Onishi
    'SS': (13, (6, 28, 368, 20)),        # Tanishige; Tomori, Haru, Tsuji, Ueda
    'HT': (10, (40, 181, 133, 12)),     # Nomura; Yamauchi, Arai, Ko, Ishii
    'WO': (179, (17, 24, 37, 31)),      # Ogawa; Takatsu, Manaka, Shiroishi, Fukuchi
    'KT': (672, (50, 74, 750, 16)),     # Nakahata; Kawamura, Koike, Horai, Baba
    'LT': (4, (205, 18, 113, 371)),     # Wada; Nakanishi, Sekikawa, Takashiro, Yamawaki
    'HH': (107, (108, 134, 98, 137)),   # Hoshino; Sato, Tashiro, Suzuki, Yonemura
    'OB': (670, (33, 836, 139, 15)),    # Kuriyama; Atsuzawa, Kashiwabara, Shirai, Otsuka
    'SK': (116, (129, 370, 11, 19)),    # Ihara; Kiyokawa, Tanabe, Kawada, Narahara
    'NC': (122, (369, 128, 117, 52)),   # Moriwaki; Takayama, Osanai, Makishi, Satake
}

# 게임의 네 코치 역할: 투수, 타격, 내야수비, 외야수비/주루.
# 공식 명단의 첫 네 명을 쓰면 수석/컨디셔닝 코치가 잘못 배치된다.
KBO_ROLE_COACHES = {
 'LG': ('김광삼','모창민','김일경','정수성'),
 'SS': ('최일언','무라카미','손주인','이종욱'),
 'HT': ('이동걸','김주찬','박기남','김연훈'),
 'WO': ('노병오','김태완','문찬종','김준완'),
 'KT': ('제춘모','유한준','박기혁','박경수'),
 'LT': ('카네무라','이병규','문규현','이현곤'),
 'HH': ('양상문','김민호','김우석','추승우'),
 'OB': ('정재훈','이진영','손지환','임재현'),
 'SK': ('경헌호','임훈','조동찬','윤재국'),
 'NC': ('김경태','조영훈','진종길','김종호'),
}

