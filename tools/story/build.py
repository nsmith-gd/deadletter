import json, re
# The story and the puzzles after the school come from the director's plan (docs/full_game_plan.md, revision 0.3):
# section 6 for the prologue's story direction, section 7 per level after it, section 5 for the ladder and the
# permanent rules, section 4 for each chapter's turn. The gameplay of the levels already built (DL-01 to DL-17) comes
# from docs/gameplay_breakdown.md, and scenes.json keeps what the built game shows.
PLAN = open('../../docs/full_game_plan.md', encoding='utf-8').read()
scenes = {s['n']: s for s in json.load(open('scenes.json'))}
BUILT = 17


def read_gameplay(path='../../docs/gameplay_breakdown.md'):
    """The puzzle-by-puzzle breakdown: each level's fields (the ladder and chapter summaries are now the plan's)."""
    levels, lv, field = {}, None, None
    for line in open(path, encoding='utf-8').read().split('\n'):
        if line.startswith('## '):
            lv = None
            continue
        m = re.match(r'^### (DL-\d\d) (.+)$', line)
        if m:
            lv = levels[m.group(1)] = dict(type='', builds='', new='', steps=[], wrong='', aha='', carries='')
            field = None
            continue
        if lv is None: continue
        m = re.match(r'^\*(.+)\*$', line.strip())
        if m and not lv['type']:
            lv['type'] = m.group(1)
            continue
        m = re.match(r'^- \*\*(Builds on|New|Play|Wrong first try|The aha|Carries forward):\*\*\s*(.*)$', line)
        if m:
            field = {'Builds on': 'builds', 'New': 'new', 'Play': 'steps', 'Wrong first try': 'wrong', 'The aha': 'aha', 'Carries forward': 'carries'}[m.group(1)]
            if field != 'steps': lv[field] = m.group(2).strip()
            continue
        m = re.match(r'^\s+\d+\. (.+)$', line)
        if m and field == 'steps': lv['steps'].append(m.group(1).strip())
    return levels


def plan_section(head):
    return next(b for b in re.split(r'^## ', PLAN, flags=re.M) if b.startswith(head))


def plan_levels(head):
    """'DL-nn' -> (name, [[field, text], ...]) for each ### DL-nn block under a ## heading of the plan."""
    out = {}
    for blk in re.split(r'^### ', plan_section(head), flags=re.M)[1:]:
        m = re.match(r'(DL-\d\d) (.+)', blk)
        fields, cur = [], None
        for line in blk.splitlines()[1:]:
            f = re.match(r'- \*\*([^*]+):\*\*\s*(.*)', line)
            if f: cur = [f.group(1), f.group(2).strip()]; fields.append(cur)
            elif cur and re.match(r'\s+\d+\.\s', line): cur[1] += (' ' if cur[1] else '') + line.strip()
        out[m.group(1)] = (m.group(2).strip(), fields)
    return out


def table(head, sub):
    """The body rows of the first Markdown table after '### sub' in the plan's '## head' section."""
    rows = []
    for l in plan_section(head).split('### ' + sub, 1)[1].splitlines():
        if l.startswith('|'): rows.append([c.strip() for c in l.strip().strip('|').split('|')])
        elif rows: break
    return rows[2:]


cap = lambda t: t[0].upper() + t[1:] if t else t
# Ranges and pairs written as DL-27–31 or DL-44/47 become 'DL-27 to DL-31' and 'DL-44 and DL-47', so every
# level is a link on the board and the ladder can highlight the open level inside a range.
dlrefs = lambda t: re.sub(r'DL-(\d\d)/(\d\d)', r'DL-\1 and DL-\2', re.sub(r'DL-(\d\d)[–-](\d\d)', r'DL-\1 to DL-\2', t))

GAMEPLAY = read_gameplay()
PLAN_LEVELS = plan_levels('7. Full post-prologue plan')
DIRECTION = {m.group(1): m.group(3).strip() for m in re.finditer(r'^\| (DL-\d\d) ([^|]+)\| ([^|]+)\| ([^|]+)\|$', PLAN, re.M)}
# Each chapter's turn from section 4: (changed belief, emotional movement).
TURNS = [[c.strip() for c in l.strip('|').split('|')][1:3] for l in plan_section('4. Save the Cat').splitlines() if re.match(r'^\| [A-Z][^|]*, DL-', l)]
# (first, last, part, eras, where, its idea, changed belief, emotional movement)
PARTS = [(1, 11, 'Prologue', ['order', 'failure'], 'The lower rings', 'You are an allocation'),
         (12, 17, 'Ch 1 Attendance', ['protocols', 'order'], 'The school', 'You are our future, so you must be kept'),
         (18, 25, 'Ch 2 Someone Home', ['commons', 'purpose'], 'The Commons', 'We can make a life together'),
         (26, 33, 'Ch 3 The Work Above', ['purpose', 'thinning'], 'The Works', 'What future are we working for?'),
         (34, 41, 'Ch 4 Protective Custody', ['survey', 'thinning'], 'The ward', 'Protection can outlive understanding'),
         (42, 46, 'Ch 5 Recipient Found', ['now'], 'The workshop', 'Someone particular is here'),
         (47, 51, 'Ch 6 First Delivery', ['now'], 'The surface', 'Life continues beyond our ownership')]
PARTS = [p + tuple(TURNS[i]) for i, p in enumerate(PARTS)]
# What the built game shows where it differs from scenes.json.
GAME = {
 15: 'D-17 takes the place of the child he is following. Three seats kept ready in a class built for forty; the third is Mara’s, her tree carved in the lid, her chair pulled out as if she got up in a hurry. Under the sick bay balcony, her hiding place.',
 16: 'The dismissal procession goes where the PLAYGROUND arrow points: into a storage rack of folded figures, dozens of them. D-17 steps aside for them as if they were children.',
 17: 'The school’s workshop, the most lived-in room: pupils’ growing experiments with names on them, a volunteer’s bench. Mara’s crooked tree has become an irrigation drawing, and the drawer holds her placement at the Works.',
}
PUZZLE = {'Disposition', 'Builds on', 'Goal / evidence', 'Goal / play', 'Obvious wrong solution', 'Apparent wrong approach', 'Apparent wrong approach / play', 'Play', 'Recovery / forward'}
STORY = {'Aha / story': 'Story', 'Insight / story': 'Insight and story'}

levels = []
for n in range(1, 52):
    lid = 'DL-%02d' % n
    p = next(p for p in PARTS if p[0] <= n <= p[1])
    s, bd = scenes[n], GAMEPLAY.get(lid)
    rows, disp, game = [], 'Preserve', None
    if bd and n <= BUILT:  # as built: the breakdown's panel
        none = re.match(r'none\b', bd['new'], re.I)
        game = dict(type=bd['type'], builds=bd['builds'], box=['Nothing new' if none else 'New here', cap(bd['new']), bool(none)],
                    steps=bd['steps'], pairs=[['Wrong first try', cap(bd['wrong'])], ['The aha', cap(bd['aha'])], ['Carries forward', bd['carries']]])
    if n <= 11:
        name = s['name']
        rows = [['Story direction', cap(DIRECTION[lid])], ['What it says', s['evidence']], ['Player comes to see', s['understanding']]]
    else:
        name, fields = PLAN_LEVELS[lid]
        f = {k: dlrefs(cap(v)) for k, v in fields}
        disp, aha = f['Disposition'], ''
        for k, _ in fields:
            if k in PUZZLE: continue
            v = f[k]
            if k == 'Aha / story':  # its first sentence is the puzzle's aha; the rest is the story
                aha, _, v = v.partition('. ')
                aha, v = aha + '.', cap(v)
            if v: rows.append([STORY.get(k, k), v])
        if n <= BUILT: rows.append(['In the game now', GAME.get(n, s['evidence'])])
        wrong = f.get('Obvious wrong solution') or f.get('Apparent wrong approach') or f.get('Apparent wrong approach / play', '')
        steps = [cap(x.strip().rstrip('.')) + '.' for x in f.get('Play', '').split('; ') if x.strip()]
        plan = dict(type='Planned · ' + disp, builds=f.get('Builds on', ''), box=['Goal', f.get('Goal / evidence') or f.get('Goal / play', ''), False],
                    steps=steps, pairs=[x for x in [['Wrong first try, and play' if 'Apparent wrong approach / play' in f else 'Wrong first try', wrong],
                                                    ['The aha', aha], ['Recovery and forward', f.get('Recovery / forward', '')]] if x[1] and x[1] != '.'])
        if game: game['proposal'] = plan  # a built school level: the plan's refinement beside what is built
        else: game = plan
    levels.append(dict(id=lid, n=n, name=name, part=p[2], eras=p[3], depth=p[4], idea=p[5], built=n <= BUILT, disp=disp,
                       arc=f'{p[6]}. {p[7]}.', rows=[[k, v] for k, v in rows if v], game=game))

# The ladder: the plan's learning ladder, and its permanent rules.
LADDER = [[r[0]] + [dlrefs(c) for c in r[1:]] for r in table('5. Puzzle architecture', 'Learning ladder')]
RULES = [[r[0]] + [dlrefs(c) for c in r[1:]] for r in table('5. Puzzle architecture', 'Permanent rules')]
CHAPTERS = [dict(name=f'{p[2]} (DL-{p[0]:02d} to DL-{p[1]:02d})',
                 notes=[f'**{p[4]}:** {p[5]}' + ('' if p[5].endswith('?') else '.'), f'**The player comes to believe:** {p[6]}.', f'**Feeling:** {p[7]}.']) for p in PARTS]
CHAPTERS.append(dict(name='Prototype chains', notes=[f'**{dlrefs(m.group(1))}:** {m.group(2)}' for m in
                     re.finditer(r'^\d\. \*\*(.+?):\*\* (.+)$', plan_section('10. Duration'), re.M)]))
CHAPTERS.append(dict(name='Puzzle rules', notes=[
    '**Fair misdirection:** a plausible wrong solution applies a true earlier rule too broadly; the feedback shows the missing distinction. A clever player who sees it at once can solve at once. Failure is never a mandatory unlock.',
    '**Quiet rooms stay quiet:** major puzzles need a central inference and a clear causal model; quiet interactions need no trick. If every chair is a gotcha the world becomes dishonest.',
    '**No dishonest exceptions:** accept any solution that satisfies the established physical rules. No load sensor secretly reads intent to force one choreography.',
    '**Recovery:** checkpoint before danger and after permanent solutions; keep braked platforms, transfers, routes and inserted parts. A wrong guess teaches in seconds. No escort health or abandonment timer.',
    '**Care is never the cost:** no patient loses air to grow a tree; no wrong input destroys an irreplaceable plant. Safeguards show a limit, then the player finds a better distribution.']))

TIMELINE = [
 ['268', 'Order', 'The refuge is sealed over capacity in a shaft beneath a terraced industrial valley, one refuge in a network. Grades assign access, rations, air, space and birth licences. Lower rings hold labour, distribution and crowded housing; upper rings hold schools, administration, medicine and surface access.', 'The prologue: graded doors, queues, sealed stairs.'],
 ['268–308', 'Order', 'Everything allocated. Some measures sustain life while distributing protection cruelly. ORDER ABOVE ALL.', 'The prologue: the depot, the ration hall, the relocation lobby.'],
 ['302', 'The last childhoods', 'Mara is born. Births dwindle across the shelter network; a small final cohort (Mara, Abel, Orme) grows up under intensifying protection.', 'Ch 1: extended sleeves, padded corners, three desks, false windows, escorted lifts.'],
 ['309–311', 'The Failure', 'Systems fail and grade-based triage abandons the lower rings. Mara, nine, is relocated up in 311; her parent’s birthday parcel (little outdoor boots) stays below.', 'The prologue, all of it.'],
 ['311–328', 'The Commons', 'Survivors remove grades, share services, improvise homes, argue and help each other.', 'Ch 2: names over numbers, kitchen rotas, mixed repair styles.'],
 ['316', 'The Commons', 'Mara, fourteen, enters irrigation work at the Works. She asked for the placement; Vance helped arrange it.', 'DL-17: the placement drawer.'],
 ['319 (proposed)', 'The failed survey', 'Young adults attempt an unauthorised surface survey. A damaged seal contaminates a local ward; people are injured and die, and the participants also try to rescue them. A local tragedy, not the end of humanity.', 'Ch 4: breach tools, rescue rope, sealing repairs. Mara’s part is suggested by recurring marks only.'],
 ['320s on', 'Change of purpose', 'Recovering the population becomes implausible. The community keeps caring for its living while turning abandoned expansion capacity into surface restoration. Shelter replies dwindle; planting dates continue.', 'Ch 2 and Ch 3: nursery pipes in cancelled housing routes, trays on the ration track.'],
 ['adulthood', 'Change of purpose', 'Mara shares a home and work with Rowan, a propagation worker. Rowan dies; Mara keeps some things, alters others, and adapts shared tools for solo work.', 'Ch 2: two coats, repaired bowls, the withdrawn second chair, the jig adapted for one.'],
 ['to 378', 'The final thinning', 'Work rotas shrink. The last other resident dies in P.A. 378. Mara has lived alone for nine years.', 'Ch 4: a final shared rota, then Mara’s single mark.'],
 ['387', 'Now', 'Mara’s rerouting wakes D-17. She is about 85, the last human alive (inferred from long silence, not certainty). Recovery is visible but incomplete.', 'The opening relay pulse; the living workshop; the final bypass.'],
]
BIBLE = """Theme: a future is worth caring for even when it will not belong to us. Its intimate form: another person's life matters beyond a task or a useful function. Humanity makes a place for other life; a parent makes a gift for a child's imagined future; Mara makes a place beside her for a machine whose job is done.

The story: a little courier wakes beneath the last human refuge with a birthday parcel seventy-six years overdue. It follows a girl through the places where she learned, loved, worked and grew old, and finds that the last of humanity, unable to secure a future for themselves, spent their remaining lives repairing the living world above them. It finds Mara, an elderly irrigation technician still tending that inheritance. Helping each other, they finish one modest part of her work and step outside. The parcel holds the little outdoor boots her parent hoped she would someday need. She cannot wear them; she can finally stand where they were meant to take her. She sits beneath a crooked tree. The delivery completes. The robot sits beside her because it wants to remain.

What the player wants, in order: complete a delivery; discover whether the child survived; understand the life she built; understand why people kept the Works running; reach the person above; accept help when D-17 cannot go on alone; help Mara experience the world she helped restore; stay after the job is finished.

The world: the surface suffered a long, fictional mix of contamination and ecosystem collapse. Long-running filtration, watershed treatment, soil work, propagation and planting have slowly improved the region. No single valve cleanses a planet and no tree grows instantly. The forest at the end has grown over decades; some managed propagation beds still need irrigation. D-17 helps finish a local regulator and access bypass, not a biosphere. The ascent travels through increasingly recent occupation; direct Works access is damaged or sealed, so the residential route is necessary.

Humanity's disappearance is a tragedy. Not a deserved punishment; recovery is not absolution. No one contaminant, teenager's mistake or infertile person ended it. The failed survey is a local tragedy within a long decline. The Commons did not turn off patients' air to water trees: people argued over surplus, kept essential care, and compromised (one more communal room against nursery expansion; a revised plan gets smaller versions of both). Order's survivors could be capable, privately kind and implicated in terrible decisions; the Commons generous, stubborn and inefficient; a protective machine could trap a pupil and later catch a falling courier.

The gradient, low to high: the lower rings (you are an allocation: graded bodies, impossible queues, refusal loops; severe darkness, water, metal); the school (you are our future, so you must be kept: repaired coats, false windows, hidden friendship; institutional green, mechanical lesson music); the Commons (we can make a life together: shared kitchens, different mugs, domestic arguments; imperfect amber warmth); the Works (what future are we working for?: converted expansion, generations of labour, continuing planting; mineral light, immense water, first green); the ward (protection can outlive understanding: private comforts, rescue repairs, obsolete limits); the workshop (someone particular is here: shortened handles, worn grips, a cup cleaned today); the surface (life continues beyond our ownership: wind, insects, leaf litter, distant water). Mass death gives way to cared-for individuals, then empty places, then one maintained daily routine. Loss becomes more personal as the world becomes more beautiful.

Protected decisions: preserve the prologue's puzzles and solutions, its live voice and lit window (a living person is hinted early). Mara appears in person late. D-17 has no hidden human soul. The parcel holds boots, not seeds or a power source. Mara is alive at the end: no death reveal, sacrificial outing or fade on a final breath. No last-second survivor tease."""
t = open('template.html').read()
for k, v in [('LEVELS', levels), ('TIMELINE', TIMELINE), ('LADDER', LADDER), ('RULES', RULES), ('CHAPTERS', CHAPTERS)]:
    assert f'/*{k}*/[]' in t, k
    t = t.replace(f'/*{k}*/[]', json.dumps(v, ensure_ascii=False))
t = t.replace('/*BIBLE*/""', json.dumps(BIBLE, ensure_ascii=False))
open('/home/user/deadletter/docs/story_board.html', 'w').write(t)
print(len(t), len(levels))
