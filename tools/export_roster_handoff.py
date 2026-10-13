"""현재 빌드 입력을 사람이 읽을 수 있는 통합 JSON으로 보존한다. 입력은 수정하지 않는다."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ratings_path = 'translation/kbo_2026/ratings_review.json'
    ratings = json.loads((ROOT / ratings_path).read_text(encoding='utf-8'))
    result = {
        'schema': 'kbo-roster-handoff-v1',
        '설명': '빌드 입력 통합 보관본. 직접 빌드 입력은 source_files 경로이며, 이 파일만 수정해도 ISO에 자동 반영되지는 않습니다.',
        'cutoff': ratings['cutoff'],
        'stats_cutoff': ratings['stats_cutoff'],
        'source_files': {},
        'teams': {},
    }
    paths = [ratings_path]
    appearance_path='translation/kbo_2026/appearance.json'
    appearance={}
    if (ROOT/appearance_path).exists():
        appearance={p['index']:p for p in json.loads((ROOT/appearance_path).read_text(encoding='utf-8'))}
        paths.append(appearance_path)
    for code, team in ratings['teams'].items():
        path = 'translation/hanwha_2026.json' if code == 'HH' else f'translation/kbo_2026/{code}.json'
        paths.append(path)
        spec = json.loads((ROOT / path).read_text(encoding='utf-8'))
        identities = {p['index']: p for p in spec['records'] if p['kind'] == 'player'}
        assert set(identities) == {p['index'] for p in team['players']}
        active = set(team['opening_indices'])
        players = []
        for player in team['players']:
            players.append({
                'index': player['index'],
                'name': player['name'],
                'squad': '1군' if player['index'] in active else '2군',
                'identity_source_record': identities[player['index']],
                'applied_ratings_record': player,
                'applied_appearance_record': appearance.get(player['index']),
            })
        staff = [p for p in spec['records'] if p['kind'] == 'coach']
        result['teams'][code] = {
            'name': spec.get('name', code),
            'identity_source': path,
            'ratings_source': ratings_path,
            'opening_indices': team['opening_indices'],
            'opening_player_ids': team['opening_player_ids'],
            'counts': {'players': len(players), 'first_team': len(active), 'second_team': len(players)-len(active), 'staff': len(staff)},
            'players': players,
            'staff': staff,
        }
    for path in paths:
        result['source_files'][path] = {'sha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
    result['totals'] = {key: sum(t['counts'][key] for t in result['teams'].values()) for key in ('players', 'first_team', 'second_team', 'staff')}
    assert result['totals'] == dict(players=619, first_team=290, second_team=329, staff=50)
    out = ROOT / 'roster_data/KBO_2026_전체선수_스태프.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assert json.loads(out.read_text(encoding='utf-8')) == result
    print(json.dumps(result['totals'], ensure_ascii=False))


if __name__ == '__main__':
    main()
