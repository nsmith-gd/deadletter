import json, sys, statistics as st
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
ok = [r for r in rows if not r['error']]
bad = [r for r in rows if r['error']]
S = ['DL-01', 'DL-02', 'DL-03', 'DL-04', 'DL-05']
def split(m):
    keys = S + ['end']
    d = {k: m[keys[i + 1]] - m[k] for i, k in enumerate(S)}
    d['opening'] = m['play'] - m['opening']; d['total'] = m['end'] - m['play']; d['with opening'] = m['end'] - m['opening']
    return d
f = lambda s: f"{int(s // 60)}:{int(round(s % 60)):02d}" if s >= 0 else '-'
cols = ['opening'] + S + ['total', 'with opening']
print('runs', len(rows), 'completed', len(ok), 'failed', len(bad))
for r in bad: print('  FAIL', r['seed'], r['error'])
sp = [split(r['marks']) for r in ok]
print('%-13s %7s %7s %7s %7s %7s' % ('', 'mean', 'median', 'min', 'max', 'sd'))
for c in cols:
    v = [d[c] for d in sp]
    print('%-13s %7s %7s %7s %7s %6.0fs' % (c, f(st.mean(v)), f(st.median(v)), f(min(v)), f(max(v)), st.pstdev(v)))
deaths = sum(1 for r in ok if 'DL-03 respawn' in r['marks'])
print('carrier deaths in DL-03:', deaths, 'of', len(ok))
print()
for r, d in zip(ok, sp):
    print(r['seed'], r['player'], ' '.join(f"{c}={f(d[c])}" for c in S + ['total']))
