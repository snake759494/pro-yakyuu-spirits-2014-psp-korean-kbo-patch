"""10팀 통합 대진 실험. 순위/포스트시즌 엔진의 단일 리그화와 구분한다."""
from collections import Counter
from datetime import date, timedelta
from analyze import chunks

VERSION = 'KBO-2026-format-schedule-alpha1'
TEAMS = tuple(range(10))
STADIUMS = (7, 3, 1, 0, 3, 5, 12, 11, 8, 6)
from club_brand import configs
STADIUMS = tuple(next((c['stadium_slot'] for c in configs().values() if c['team_id']==i),s) for i,s in enumerate(STADIUMS))
EMPTY = bytes((33, 33, 19, 0, 0))

def apply(data):
    out = bytearray(data)
    parts = list(chunks(data))
    assert len(parts) == 1 and parts[0][0] == 'OFFICIAL'
    _, offset, original = parts[0]
    assert len(original) == 241 * 60
    ring = list(TEAMS)
    rounds = []
    for r in range(9):
        pairs = []
        for i in range(5):
            a, b = ring[i], ring[9-i]
            if a is not None and b is not None:
                pairs.append((a, b) if (r+i) % 2 == 0 else (b, a))
        rounds.append(pairs)
        ring = [ring[0], ring[-1]] + ring[1:-1]
    # 각 상대와 2연전 8회. 홈/원정 각 8경기, 팀당 144경기.
    blocks = []
    for cycle in range(8):
        for pairs in rounds:
            games = [(b,a) if cycle % 2 else (a,b) for a,b in pairs]
            blocks.extend([games, games])
    start = date(2014, 3, 28)
    days = []
    for day in range(241):
        current = start + timedelta(days=day)
        # 월요일 휴식. 원본 달력의 올스타 기간은 비워 둔다.
        if current.weekday() != 0 and not date(2014,7,17) <= current <= date(2014,7,21):
            days.append(day)
    games_log = []
    for day in range(241):
        base = offset + day * 60
        out[base:base+30] = EMPTY * 6
    for day, games in zip(days, blocks):
        for slot, (home, away) in enumerate(games):
            base = offset + day * 60 + slot * 5
            out[base:base+5] = bytes((home, away, STADIUMS[home], 0, 15))
            games_log.append(dict(day=day,date=str(start+timedelta(days=day)),slot=slot,home=home,away=away))
    assert len(out) == len(data)
    report = audit(bytes(out), data)
    report.update(version=VERSION, games=games_log, first_date=games_log[0]['date'], last_date=games_log[-1]['date'],
                  unified_standings=False, single_league_postseason=False, kbo_rosters=False,
                  status='10팀 통합 대진 시험판; 순위와 포스트시즌은 기존 2리그 로직')
    return bytes(out), report

def audit(patched, original):
    _, off, schedule = next(chunks(patched))
    assert len(schedule) == 241*60
    totals, home_counts, pairs = Counter(), Counter(), Counter()
    for day in range(241):
        used = set()
        for slot in range(6):
            record = schedule[day*60+slot*5:day*60+slot*5+5]
            if record == EMPTY:
                continue
            home, away, stadium, variant, flags = record
            assert home in TEAMS and away in TEAMS and home != away
            assert home not in used and away not in used
            assert stadium == STADIUMS[home] and variant == 0 and flags == 15
            used.update((home,away))
            totals.update((home,away));home_counts[home] += 1
            pairs[tuple(sorted((home,away)))] += 1
        a = off + day*60 + 30
        assert patched[a:a+30] == original[a:a+30], '2군 일정 변경'
    assert set(totals) == set(TEAMS) and set(totals.values()) == {144}
    assert set(home_counts.values()) == {72}
    assert len(pairs) == 45 and set(pairs.values()) == {16}
    assert patched[:off] == original[:off]
    assert patched[off+len(schedule):] == original[off+len(schedule):]
    return dict(active_team_ids=list(TEAMS), total_games=sum(totals.values())//2,
                games_per_team=dict(totals), home_games_per_team=dict(home_counts),
                games_per_pair=16, farm_schedule_preserved=True, record_size_preserved=True,
                offset=off, size=len(schedule))

def apply_built_iso():
    """검증된 한글 ISO의 일정만 갱신한다. 다른 번역/그래픽 변경은 보존한다."""
    import json, hashlib
    from inventory import ROOT, WORK, ISO
    from build import OUT, sha
    from install import update_install
    inv = json.loads((WORK/'inventory.json').read_text('utf8'))
    report_path = ROOT/'build/build_report.json'
    report = json.loads(report_path.read_text('utf8'))
    old_hash = sha(OUT)
    assert old_hash == report['sha256'], 'ISO와 빌드 보고서 불일치: 동시 빌드 종료 후 재검사 필요'
    entry = next(e for e in inv['fbd'] if e['name']=='SCHEDULE.CHK')
    archive = next(e for e in inv['iso'] if e['name']=='/PSP_GAME/USRDIR/CDVDROOT/BASEBALL.FBD')
    install = next(e for e in inv['iso'] if e['name']=='/PSP_GAME/INSDIR/BASEBALL.FBD')
    with ISO.open('rb') as f:
        f.seek(entry['offset']); original = f.read(entry['size'])
    expected, league = apply(original)
    with OUT.open('r+b') as f:
        f.seek(entry['offset']); before = f.read(entry['size'])
        assert before in (original, expected), '예상하지 않은 일정 변경 감지'
        install_report = update_install(f,f,install,archive,[(entry['offset']-archive['offset'],before,expected)])
        f.seek(entry['offset']);f.write(expected);f.flush()
        f.seek(entry['offset']);assert f.read(entry['size']) == expected
    report['sha256'] = sha(OUT)
    report['league_trial'] = {k:v for k,v in league.items() if k!='games'}
    report['league_incremental_build'] = dict(base_sha256=old_hash,installation_validation=install_report)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    (ROOT/'build/league_trial.json').write_text(json.dumps(league,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps(dict(sha256=report['sha256'],league=report['league_trial']),ensure_ascii=False,indent=2))

if __name__ == '__main__':
    import sys
    assert sys.argv[1:] == ['--apply-built-iso']
    apply_built_iso()
