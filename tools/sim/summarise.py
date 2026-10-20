import json, sys, statistics as st
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
ok = [r for r in rows if not r['error']]
bad = [r for r in rows if r['error']]
S = [f'DL-{i:02d}' for i in range(1, 12)]
def split(m):
    keys = S + ['end']
    d = {k: (m[keys[i + 1]] - m[k]) if k in m and keys[i + 1] in m else float('nan') for i, k in enumerate(S)}
    d['opening'] = m['play'] - m['opening']; d['total'] = m['end'] - m['play']; d['with opening'] = m['end'] - m['opening']
    return d
f = lambda s: (lambda r: f"{r // 60}:{r % 60:02d}")(int(round(s))) if s >= 0 else '-'
cols = ['opening'] + S + ['total', 'with opening']
print('runs', len(rows), 'completed', len(ok), 'failed', len(bad))
for r in bad: print('  FAIL', r['seed'], r['error'])
sp = [split(r['marks']) for r in ok]
print('%-13s %7s %7s %7s %7s %7s' % ('', 'mean', 'median', 'min', 'max', 'sd'))
for c in cols:
    v = [d[c] for d in sp]
    print('%-13s %7s %7s %7s %7s %6.0fs' % (c, f(st.mean(v)), f(st.median(v)), f(min(v)), f(max(v)), st.pstdev(v)))
if any('deaths' in r for r in ok): print('deaths per run: mean %.1f, max %d' % (sum(r.get('deaths', 0) for r in ok) / len(ok), max(r.get('deaths', 0) for r in ok)))
if any('found' in r for r in ok): print('curiosities found per run: mean %.1f' % (sum(r.get('found', 0) for r in ok) / len(ok)))
print()
for r, d in zip(ok, sp):
    print(r['seed'], r['player'], ' '.join(f"{c}={f(d[c])}" for c in S + ['total']))
