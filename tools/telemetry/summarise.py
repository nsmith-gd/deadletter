"""Summarise Dead Letter play telemetry.

Reads collector batches (data/*.jsonl) and/or play logs saved from the pause card (dead-letter-playlog-*.json), and
prints, per chapter scene: how many sessions reached it, median time spent, deaths by cause, players idle 25 s or
more, button prompts shown, and where sessions ended without finishing; plus the end-to-end time, puzzle signals
(weigh-in readings, lift buzzes, cage dips) and frame rate by device.

    python summarise.py data/*.jsonl ~/Downloads/dead-letter-playlog-*.json
"""
import collections
import json
import statistics as st
import sys


def load(paths):
    sessions = collections.defaultdict(lambda: {'events': [], 'device': None})
    for p in paths:
        text = open(p).read().strip()
        batches = [json.loads(text)] if p.endswith('.json') else [json.loads(l) for l in text.splitlines() if l.strip()]
        for b in batches:
            s = sessions[b['sid']]
            s['device'] = s['device'] or b.get('device')
            s['events'].extend(b['events'])
    for s in sessions.values():
        seen = set()
        s['events'] = sorted((e for e in s['events'] if not (e['i'] in seen or seen.add(e['i']))), key=lambda e: e['i'])
        for e in s['events']:
            if e['type'] == 'session' and not s['device']:
                s['device'] = e.get('device')
    return sessions


def fmt(sec):
    return '-' if sec is None else f'{int(sec // 60)}:{int(sec % 60):02d}'


def main(paths):
    S = load(paths)
    scenes = [f'DL-{i:02d}' for i in range(1, 12)]
    reach, time_in, deaths, idle, prompts, quit_at = (collections.Counter() for _ in range(6))
    dwell = collections.defaultdict(list)
    causes = collections.defaultdict(collections.Counter)
    totals, perf = [], collections.defaultdict(list)
    signals = collections.Counter()
    for sid, s in S.items():
        ev = s['events']
        cur, since, got = None, None, set()
        finished = any(e['type'] == 'end' for e in ev)
        for e in ev:
            sc = (e.get('name') or '')[:5] if e['type'] == 'scene' else e.get('scene', '')[:5]
            if e['type'] == 'scene':
                if cur and since is not None:
                    dwell[cur].append(e['t'] - since)
                cur, since = sc, e['t']
                if sc not in got:
                    got.add(sc)
                    reach[sc] += 1
            elif e['type'] == 'death':
                deaths[sc] += 1
                causes[sc][e.get('how')] += 1
            elif e['type'] == 'idle':
                idle[sc] += 1
            elif e['type'] == 'prompt':
                prompts[sc] += 1
            elif e['type'] == 'end':
                totals.append(e.get('time'))
            elif e['type'] == 'perf':
                dev = s['device'] or {}
                key = ('mobile' if dev.get('mobile') else 'desktop') + ' / ' + (dev.get('gpu') or '?')[:40]
                perf[key].append((e['fps'], e['worstMs'], e['long']))
            elif e['type'] in ('weigh', 'liftBuzz', 'cageDip', 'whiteWarn', 'reloadCheckpoint', 'skipIntro', 'startAt'):
                signals[e['type'] + (':' + e['reading'] if e['type'] == 'weigh' else '')] += 1
        if not finished and cur:
            quit_at[cur] += 1
    n = len(S)
    print(f'sessions {n}, finished {len(totals)}; full-chapter time median {fmt(st.median(totals)) if totals else "-"}')
    print(f'{"scene":7} {"reached":>8} {"median":>7} {"deaths":>7} {"idle":>5} {"prompts":>8} {"quit here":>10}  causes')
    for sc in scenes:
        d = dwell.get(sc, [])
        print(f'{sc:7} {reach[sc]:>8} {fmt(st.median(d)) if d else "-":>7} {deaths[sc]:>7} {idle[sc]:>5} {prompts[sc]:>8} {quit_at[sc]:>10}  {dict(causes[sc])}')
    print('\npuzzle and flow signals:', dict(signals))
    print('\nframe rate by device (median fps, median worst frame ms, long frames per 10 s):')
    for k, v in sorted(perf.items(), key=lambda kv: -len(kv[1])):
        print(f'  {k}: {st.median(x[0] for x in v):.0f} fps, {st.median(x[1] for x in v):.0f} ms, {st.mean(x[2] for x in v):.1f}  ({len(v)} samples)')


if __name__ == '__main__':
    main(sys.argv[1:])
