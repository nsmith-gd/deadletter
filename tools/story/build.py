import json, re
# The story and the puzzles after the school come from the director's plan (docs/full_game_plan.md, revision 0.3):
# section 6 for the prologue's story direction, section 7 per level after it, section 5 for the ladder and the
# permanent rules, section 4 for each chapter's turn and the beats. The gameplay of the levels already built (DL-01 to
# DL-17) comes from docs/gameplay_breakdown.md; what the built game shows is on the board's cards.
PLAN = open('../../docs/full_game_plan.md', encoding='utf-8').read()
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
PLAN_LEVELS = plan_levels('7. Full post-prologue plan') | plan_levels('Appendix A')
# Section 6's table: | DL-nn Name | mistaken approach → insight | story direction |
DIRECTION = {m.group(1): m.group(4).strip() for m in re.finditer(r'^\| (DL-\d\d) ([^|]+)\| ([^|]+)\| ([^|]+)\|$', PLAN, re.M)}
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
PUZZLE = {'Disposition', 'Builds on', 'Goal / evidence', 'Goal / play', 'Obvious wrong solution', 'Apparent wrong approach', 'Apparent wrong approach / play', 'Play', 'Recovery / forward'}
STORY = {'Aha / story': 'Story', 'Insight / story': 'Insight and story'}

levels = []
for n in range(1, 52):
    lid = 'DL-%02d' % n
    p = next(p for p in PARTS if p[0] <= n <= p[1])
    name, fields = PLAN_LEVELS[lid]
    bd = GAMEPLAY.get(lid)
    rows, disp, game = [], 'Preserve', None
    if bd and n <= BUILT:  # as built: the breakdown's panel
        none = re.match(r'none\b', bd['new'], re.I)
        game = dict(type=bd['type'], builds=bd['builds'], box=['Nothing new' if none else 'New here', cap(bd['new']), bool(none)],
                    steps=bd['steps'], pairs=[['Wrong first try', cap(bd['wrong'])], ['The aha', cap(bd['aha'])], ['Carries forward', bd['carries']]])
    if n <= 11:
        rows = [['Story direction', cap(DIRECTION[lid])]]
    else:
        f = {k: dlrefs(cap(v)) for k, v in fields}
        disp, aha = f['Disposition'], ''
        for k, _ in fields:
            if k in PUZZLE: continue
            v = f[k]
            if k == 'Aha / story':  # its first sentence is the puzzle's aha; the rest is the story
                aha, _, v = v.partition('. ')
                aha, v = aha + '.', cap(v)
            if v: rows.append([STORY.get(k, k), v])
        wrong = f.get('Obvious wrong solution') or f.get('Apparent wrong approach') or f.get('Apparent wrong approach / play', '')
        steps = [cap(x.strip().rstrip('.')) + '.' for x in f.get('Play', '').split('; ') if x.strip()]
        plan = dict(type='Planned · ' + disp, builds=f.get('Builds on', ''), box=['Goal', f.get('Goal / evidence') or f.get('Goal / play', ''), False],
                    steps=steps, pairs=[x for x in [['Wrong first try, and play' if 'Apparent wrong approach / play' in f else 'Wrong first try', wrong],
                                                    ['The aha', aha], ['Recovery and forward', f.get('Recovery / forward', '')]] if x[1] and x[1] != '.'])
        if game: game['proposal'] = plan  # a built school level: the plan's refinement beside what is built
        else: game = plan
    levels.append(dict(id=lid, n=n, name=name, part=p[2], eras=p[3], depth=p[4], idea=p[5], built=n <= BUILT, disp=disp,
                       arc=f'{p[6]}. {p[7]}.', rows=[[k, v] for k, v in rows if v], game=game))

# The story arc. Tension per scene, 0 calm to 10 most tense: the writer's estimate from the plan's emotional
# sequence (section 4), with the moment that carries it.
ARC = {
 1: (2, 'A tiny courier wakes with one job.'), 2: (2.5, 'A workplace stopped mid-shift; the first letter.'),
 3: (3, 'A substitute can hold the gate for him.'), 4: (3.5, 'He leaves another courier on charge.'),
 5: (5.5, 'The weigh-in wants a person, and the dead are the weight.'), 6: (4.5, 'The address is dead; the procedure carries on.'),
 7: (5, 'He sends the weight where he can’t go.'), 8: (6, 'Something pale moves in the water.'),
 9: (7.5, 'The cage slips toward the dark.'), 10: (6.5, 'The last car went up without them.'),
 11: (8, 'Past the White to an empty room, and a parent’s birthday card.'),
 12: (4, 'Coats without children.'), 13: (3.5, 'The lesson repeats; the friends drew beyond the paper.'),
 14: (3, 'Behind the painted sky, a refuge for three.'), 15: (4.5, 'He sits in her place.'),
 16: (5, 'The pupils are folded into a storage rack.'), 17: (3.5, 'She chose the Works: a life beyond the address.'),
 18: (2.5, 'A cramped room that was hers.'), 19: (3.5, 'Her old repair, two witness taps.'), 20: (2.5, 'Room for two: Rowan.'),
 21: (3.5, 'Two bowls, one evening.'), 22: (4, 'The ration track carries seedlings.'), 23: (6, 'The second place, set for no one.'),
 24: (5, 'The jig adapted for one; the other shelters fall silent.'), 25: (4.5, 'He parks the routine; the keepsake lamp stays lit.'),
 26: (4, 'Water as weight.'), 27: (4.5, 'Nursery first.'), 28: (3.5, 'Other hands built this.'),
 29: (6, 'The water that lifted him runs on into the roots.'), 30: (5.5, 'Roots, daylight, a leaf: work they will never inherit.'),
 31: (6, 'Her labels grow shakier; the branch is under pressure.'), 32: (6.5, 'The repair she could no longer reach.'),
 33: (5.5, 'A ward address, but a fresh scrape and a far light.'), 34: (6.5, 'The attendant catches him.'),
 35: (7, 'Three friends in quarantine, tapping through the pipes.'), 36: (7.5, 'The survey: the soil it brought back, and what it cost.'), 37: (7.5, 'He lets himself be carried.'),
 38: (6, 'The attendant mends its own pad.'), 39: (8, 'Passage and care, in the right order.'),
 40: (8.5, 'The knee gives; the stair is out of reach.'), 41: (8, 'A light under a door: someone is working.'),
 42: (6, 'Mara, her hand out for a spanner.'), 43: (7, 'She repairs him, then reads the label.'),
 44: (8, 'Her knowledge, his reach; three pulses.'), 45: (7.5, 'The air reading, and her choice.'),
 46: (6.5, 'She leaves the work unfinished.'), 47: (7.5, 'Hands in turn.'), 48: (9, 'The last lift, together.'),
 49: (9.5, 'Light on her face. She sits down on the threshold.'), 50: (5, 'The old tree in its field of light; hopscotch on the stones.'), 51: (3, 'The boots. He sits because he wants to.'),
}
for l in levels: l['tension'], l['moment'] = ARC[l['n']]
# Where the director's perspective (the plan's addendum of 23 October) changes a level, it says so on the level.
REVISED = {
 9: 'The hopscotch on the way to C-114 is the game’s signature: whimsy for its own sake. Protect it.',
 11: 'The patched toy is the first repair Mara was given. Repair is how she was loved; “keep drawing your trees” is how she was hoped for.',
 16: 'D-17 stepping aside for the figures is the first sign of his second quirk: a courier’s habit of making room, which becomes care.',
 17: 'The volunteer is E. Lisle. His bench sign: “Break it here, not out there.” She asked for the placement; he let her try.',
 30: 'The Works’ sampling periscope looks out on the old tree. Mara’s yearly drawings of it, grass, then wildflowers, then saplings, show the world reclaiming it. Orme can’t come up the shaft: “Tell me what the light’s like.”',
 34: 'The custody wards were the survey party’s quarantine. The adults were terrified, right about the danger and wrong about the cage.',
 35: 'Three friends in three rooms, a season apart, tapping to each other through the pipes: the cup at the pipe, from the school refuge.',
 36: 'Not breach tools: the survey kit. The line was her guardian hauling them back. A dated jar of soil (the nursery’s first tray) and the photograph of a grey field with one dead, gnarled tree. What they brought back began the restoration; what they gave was Orme’s lungs and a season apart. Nobody died because of them.',
 38: 'Orme’s breathing set, kept and cared for: the cost, lived with for a lifetime.',
 42: 'Everything in the workshop has been mended at least once. The pumps have names. Her guardian’s folded shirt and whistle on a shelf, dusted, never used; her apology to them, never sent.',
 43: 'Her calling meets him: keeping company with something until it can go on without her.',
 46: 'Having been mended, D-17 mends something himself and makes her two witness taps.',
 49: 'Hope, physically: light on her face, eyes closed, her hands shaking until she grips the handle. Before going anywhere she sits down on the threshold, overwhelmed. D-17 sits with her.',
 50: 'The tree is old and dead: woody, gnarled, almost haunted, a great branch long fallen, alone in a wild field brimming with light and wildflowers, young growth around it. On the way, D-17 hopscotches across the stepping stones and Mara taps the squares with her stick.',
 51: 'D-17 steps back while she opens the boots, giving her room; then she makes room for him. Two together under the old tree as the world grows back around it. Loneliness ends; the delivery is only how it began.',
}
for l in levels:
    if l['n'] in REVISED: l['rows'].append(['Revised (23 Oct)', REVISED[l['n']]])
# Save the Cat (section 4's table), each beat placed on the scenes that carry it. B Story runs under the others.
SPANS = {'Opening Image': (1, 1), 'Theme Stated': (6, 6), 'Set-Up': (1, 11), 'Catalyst': (11, 11), 'Debate': (12, 16),
         'Break into Two': (17, 17), 'B Story': (18, 43), 'Fun and Games': (18, 28), 'Midpoint': (29, 30),
         'Bad Guys Close In': (31, 39), 'All Is Lost': (40, 40), 'Dark Night': (41, 41), 'Break into Three': (42, 43),
         'Finale': (44, 50), 'Final Image': (51, 51)}
BEAT_ROWS = plan_section('4. Save the Cat').split('| Beat |', 1)[1].split('\n\n', 1)[0].splitlines()[2:]
BEATS = [dict(name=c[0], first=SPANS[c[0]][0], last=SPANS[c[0]][1], text=c[1])
         for c in ([x.strip() for x in r.strip('|').split('|')] for r in BEAT_ROWS)]

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
 ['316', 'The Commons', 'Mara, fourteen, enters irrigation work at the Works. She asked for the placement; Lisle helped arrange it.', 'DL-17: the placement drawer.'],
 ['319', 'The survey', 'Mara, Abel and Orme go outside without leave to see a real tree. They bring back soil, two seedlings and a photograph of one dead tree in a grey field: the restoration begins. Orme’s mask seal fails; he lives, but breathes through a filter for the rest of his life. The three spend a season in quarantine, apart. Nobody dies because of them.', 'Ch 4: the custody wards were their quarantine; the soil jar, the photograph, the pipes they tapped through.'],
 ['320s on', 'Change of purpose', 'Recovering the population becomes implausible. The community keeps caring for its living while turning abandoned expansion capacity into surface restoration. Shelter replies dwindle; planting dates continue.', 'Ch 2 and Ch 3: nursery pipes in cancelled housing routes, trays on the ration track.'],
 ['adulthood', 'Change of purpose', 'Mara shares a home and work with Rowan, a propagation worker. Rowan dies; Mara keeps some things, alters others, and adapts shared tools for solo work.', 'Ch 2: two coats, repaired bowls, the withdrawn second chair, the jig adapted for one.'],
 ['to 378', 'The final thinning', 'Work rotas shrink. The last other resident dies in P.A. 378. Mara has lived alone for nine years.', 'Ch 4: a final shared rota, then Mara’s single mark.'],
 ['387', 'Now', 'Mara’s rerouting wakes D-17. She is about 85, the last human alive (inferred from long silence, not certainty). Recovery is visible but incomplete.', 'The opening relay pulse; the living workshop; the final bypass.'],
]
BIBLE = """Theme: nothing stays, not the refuge, not its people, not the tree. What we get is the time in between, and it is best spent close to someone: mending what's near, making room for what comes next, and playing for no reason at all. Three strands, always together. Endings are part of the pattern: humanity is the old tree, and the world grows back around it. Loneliness is the worst of fates: Mara's nine years alone are the real danger, and protection that isolates (Order, the protocols) is the same enemy in a kinder coat. Whimsy, joy for its own sake, is the game's signature. Against noble sacrifice: care matters, but it cannot eat a life. Don't change the world; change what's around you.

The story: a little courier wakes beneath the last human refuge with a birthday parcel seventy-six years overdue. It follows a girl through the places where she learned, loved, worked and grew old, and finds Mara, an old irrigation technician still keeping her corner of the world going, alone. Helping each other, they finish one modest part of her work and step outside. The parcel holds the little outdoor boots her parent hoped she would someday need. She cannot wear them; she can finally stand where they were meant to take her. She sits beneath the old dead tree in its field of light and wildflowers. The delivery completes. The robot sits beside her because it wants to remain.

Mara's calling: she mends and she grows, and to her they are one act, keeping company with something until it can go on without her. She learned it by being mended (a patched toy, sleeves let down year after year) and hoped for ("keep drawing your trees"). She keeps the old going as long as it can go and makes room for the new to start. Alone, her repairs have become her company: she names the pumps and logs her work to nobody. Her habit is one more thing to mend; her need is to let someone mend her, then to sit.

D-17: persistence and whimsy. He plays when nothing asks him to (the hopscotch is the signature; one moment of play per chapter), and a courier's habit of stepping aside grows into care: making room for someone.

The survey, P.A. 319: Mara, Abel and Orme went outside without leave to see a real tree, rebelling against protection that kept them safe and alone. Beautiful and consequential at once. They brought back soil, two seedlings (the nursery's first tray) and a photograph of a grey field with one dead, gnarled tree in it, the crooked tree Mara had always drawn: the restoration began there. They gave Orme's lungs (his mask seal failed; he lived, breathing through a filter, and built the nursery's air filters), a season apart in quarantine (the custody wards), and Mara's guardian's trust; her apology was never sent. Nobody died because of them. The adults were terrified: right about the danger, wrong about the cage.

The tree: one dead tree, woody, gnarled, almost haunted, a great branch long fallen, alone in a wild field brimming with light and wildflowers. The player watches the world reclaim it over time, out of order: Mara's yearly drawings through the Works' sampling periscope, then, late, the survey's photograph of the grey field where it began. Outside, it stands among young growth.

The world: the surface suffered a long, fictional mix of contamination and ecosystem collapse. Filtration, soil work, propagation and planting have slowly improved the region; no single valve cleanses a planet and no tree grows instantly. D-17 helps finish a local regulator and access bypass, not a biosphere. People are wonderful and weird: quirks, odd hobbies, jokes in rota margins, personal rules. Order's survivors could be privately kind and implicated in terrible decisions; the Commons generous, stubborn and inefficient; a protective machine could trap a pupil and later catch a falling courier. No patient lost air to grow a tree.

The gradient, low to high: the lower rings (you are an allocation); the school (you are our future, so you must be kept); the Commons (we can make a life together); the Works (what future are we working for?); the ward (protection can outlive understanding); the workshop (someone particular is here); the surface (life continues beyond our ownership). Mass death gives way to cared-for individuals, then empty places, then one maintained daily routine, then two people under a tree.

Protected decisions: preserve the prologue's puzzles and solutions, its live voice and lit window (a living person is hinted early). Mara appears in person late. D-17 has no hidden human soul. The parcel holds boots, not seeds or a power source. Mara is alive at the end: no death reveal, sacrificial outing or fade on a final breath. No last-second survivor tease."""
t = open('template.html').read()
for k, v in [('LEVELS', levels), ('TIMELINE', TIMELINE), ('LADDER', LADDER), ('RULES', RULES), ('CHAPTERS', CHAPTERS), ('BEATS', BEATS)]:
    assert f'/*{k}*/[]' in t, k
    t = t.replace(f'/*{k}*/[]', json.dumps(v, ensure_ascii=False))
t = t.replace('/*BIBLE*/""', json.dumps(BIBLE, ensure_ascii=False))
open('/home/user/deadletter/docs/story_board.html', 'w').write(t)
print(len(t), len(levels))

# The puzzle notebook: every puzzle's sheet and every chapter's, for notes on each (docs/puzzle_notes.html).
def sheet(g):
    return dict(type=g['type'].replace('Planned · ', ''), goalLabel=g['box'][0] if g['box'][0] == 'Goal' else 'New here',
                goal=g['box'][1] if not g['box'][2] else '', steps=g['steps'], pairs=g['pairs'])
PUZZLES = [dict(id=l['id'], name=l['name'], part=l['part'], built=l['built'], **sheet(l['game']),
                proposal=sheet(l['game']['proposal']) if l['game'].get('proposal') else None) for l in levels]
# Each chapter gets a page of its own; its id is a bare token so the page can open it from the link's #anchor.
PARTS_NOTES = [dict(id='prologue' if p[2] == 'Prologue' else 'ch' + p[2].split()[1], name=p[2], first=p[0], last=p[1],
                    place=p[4], idea=p[5], belief=p[6], feeling=p[7]) for p in PARTS]
t = open('puzzle_notes.html').read()
for k, v in [('PUZZLES', PUZZLES), ('CHAPTERS', PARTS_NOTES)]:
    assert f'/*{k}*/[]' in t, k
    t = t.replace(f'/*{k}*/[]', json.dumps(v, ensure_ascii=False))
open('/home/user/deadletter/docs/puzzle_notes.html', 'w').write(t)
print(len(PUZZLES), 'puzzles')
