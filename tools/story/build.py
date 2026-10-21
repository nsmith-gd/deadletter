import json, re
scenes = json.load(open('scenes.json'))


def read_gameplay(path='../../docs/gameplay_breakdown.md'):
    """The puzzle-by-puzzle breakdown: the ladder table, each chapter's summary, and each level's fields."""
    ladder, chapters, levels = [], [], {}
    chap = lv = sec = None
    field = None
    for line in open(path, encoding='utf-8').read().split('\n'):
        m = re.match(r'^## (.+)$', line)
        if m:
            lv = None
            chap = None if m.group(1).startswith(('The ', 'How ', 'Checks ')) else dict(name=m.group(1), notes=[])
            if chap: chapters.append(chap)
            sec = m.group(1)
            continue
        m = re.match(r'^### (DL-\d\d) (.+)$', line)
        if m:
            lv = levels[m.group(1)] = dict(chapter=chap['name'] if chap else '', type='', builds='', new='', steps=[], wrong='', aha='', carries='')
            field = None
            continue
        if sec == 'The ladder' and line.startswith('| **'):
            ladder.append([c.strip() for c in line.strip().strip('|').split(' | ')])
            continue
        if lv is not None:
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
            if m and field == 'steps':
                lv['steps'].append(m.group(1).strip())
        elif chap is not None and line.startswith('**'):
            chap['notes'].append(line.strip())
    return ladder, chapters, levels


LADDER, CHAPTERS, GAMEPLAY = read_gameplay()
PARTS = [(1, 11, 'Prologue', ['order', 'failure'], 'The lower works: the depot to ring C'),
         (12, 17, 'Ch 1 Attendance', ['order', 'protocols'], 'Ring B: the school'),
         (18, 25, 'Ch 2 Someone Home', ['commons', 'rebellion'], 'The homes'),
         (26, 33, 'Ch 3 The Work Above', ['commons', 'thinning'], 'The works above'),
         (34, 41, 'Ch 4 Protective Custody', ['protocols', 'rebellion'], 'The custody wards'),
         (42, 46, 'Ch 5 Recipient Found', ['now'], 'The top'),
         (47, 51, 'Ch 6 First Delivery', ['now'], 'The top, and out')]
OVR = {
 15: dict(says='D-17 takes the place of the child he is following. Three seats kept ready in a class built for forty; the third is Mara’s, her tree carved in the lid, her chair pulled out as if she got up in a hurry. Under the sick bay balcony, her hiding place.',
          play='Bring the sick-bay figure down the pupil lift (it won’t move unaccompanied), push both figures into seats (one stops in Mara’s first), then sit in her chair: three lamps, the bell, dismissal.'),
 16: dict(says='The dismissal procession goes where the PLAYGROUND arrow points: into a storage rack of folded figures, dozens of them. D-17 steps aside for them as if they were children.',
          play='Hold the crossing lever until both figures are over the light well; the rack takes them, latches the bridge and lifts its counterweight out of the way.'),
 17: dict(says='The school’s workshop, the most lived-in room: pupils’ growing experiments with names on them, a volunteer’s bench. Mara’s crooked tree has become an irrigation drawing, and the drawer holds her placement at the Works.',
          play='Move the seed tray wedged against the drawer, pull the drawer, read it. D-17’s label is forwarded again: Works Dept., ring A.'),
}
levels = []
for s in scenes:
    n = s['n']
    part = next(p for p in PARTS if p[0] <= n <= p[1])
    o = OVR.get(n, {})
    g = GAMEPLAY.get('DL-%02d' % n)
    play = ' '.join('%d. %s' % (i + 1, t) for i, t in enumerate(g['steps'])) if g and g['steps'] else o.get('play', s['play'])
    levels.append(dict(id='DL-%02d' % n, n=n, name=s['name'], part=part[2], eras=part[3], depth=part[4], built=n <= 17,
                       says=o.get('says', s['evidence']), play=play, learn=s['understanding'], game=g))
TIMELINE = [
 ['268', 'Sealing', 'Sealed overcrowded by design. The Steward rules through the Grade Council; grades 1 to 6, higher number lower down.', 'The prologue’s signage, grades and rations.'],
 ['268–308', 'Order', 'Everything allocated: shifts, rations, air, licensed births. ORDER ABOVE ALL everywhere.', 'The depot, the ration hall, the relocation lobby.'],
 ['~298–302', 'Order', 'Births fall. Mara born P.A. 302, the last birth recorded; nobody knows yet.', 'Ch 4: the birth register.'],
 ['~306', 'Protocols', 'Protection protocols: every remaining child a Protected Pupil, never alone.', 'Ch 1 (the school), Ch 4 (the machinery).'],
 ['309–311', 'The Failure', 'Systems fail; order triages by grade. Lower rings die in heaps. Mara, nine, relocated up; her birthday parcel never delivered.', 'The prologue.'],
 ['311–328', 'The Commons', 'The few left rebuild as equals. Portraits come down; grades painted over with names; shared kitchens; the dead laid out with care.', 'Ch 2 and Ch 3.'],
 ['~316', 'The Commons', 'Mara, fourteen, placed at the Works (water and irrigation), sponsored by a school volunteer.', 'Ch 1, DL-17.'],
 ['~317–320', 'The rebellion', 'The over-protected teenagers rebel; one night they force a sealed hatch. The air kills a ward, and the last man.', 'Ch 2, Ch 3 (signs); Ch 4 (the ward).'],
 ['320', 'The rebellion', 'No more births are possible. The register’s last line is Mara’s.', 'Ch 4: all hope lost.'],
 ['320–378', 'The thinning', 'One by one the rest die; Mara works on the restoration, alone at the end.', 'Ch 3 to Ch 5.'],
 ['387', 'Now', 'Mara’s work brings power back to the depot. D-17 wakes.', 'The opening card.'],
]
BIBLE = """The refuge was sealed with far more people than it could hold and survived by ORDER: a benevolent, harsh ruler, the Steward, and a Grade Council grading every life (grades 1-6; the lower the ring, the higher the number), rationing air, food and space by grade, under the motto ORDER ABOVE ALL. Births began to fail (Mara D., born P.A. 302, is the last birth recorded). From ~P.A. 306 child protection protocols: every remaining child a Protected Pupil, never alone, escorted. P.A. 309-311 the Failure: systems failed and order triaged by grade; the lower rings died in heaps; Mara, nine, was relocated up and her parent's birthday parcel (something "for outside") was never delivered. P.A. 311-328 the Commons: the few left above rebuilt as equals; portraits came down, grades painted over with names, shared kitchens and rotas, the dead laid out with care. ~P.A. 316 Mara, fourteen, placed at the Works (water, irrigation). ~P.A. 317-320 the rebellion: the over-protected teenagers rebelled (graffiti over the motto, the Den grown into a gang) and one night forced a sealed hatch; the poisoned air killed a ward, among them the last man; no more births were possible. P.A. 320-378 the thinning; Mara works on alone. P.A. 387 now: her work brings power back to the depot and D-17, a courier robot with the parcel for Mara, nine, wakes and follows her trail upward.
Vertical gradient: deeper rings = earlier era and more dead (heaps low down, few and cared-for higher up). Lower works: Order and the Failure. Ring B school: late Order and the first protocols (the school was left, not died in). Homes: the Commons and the rebellion. Works above: the Commons and the thinning. Custody wards: protocols and the breach. The top: Mara alone.
Telling rules: wordless; two or three independent cues per beat; show the change, not the state (a motto painted over, a portrait turned to the wall, a headcount crossed out smaller); voices are ordinary people talking about rations, coats, birthdays and rotas, never narrators explaining history; big truths land on objects; show what people did, not cause-of-death signs; never on the nose. Threads: the motto as a refrain (enamelled, then painted over, then defaced, then scratched out); Mara's crooked tree with a knot in one branch (crayon at nine, pencil behind the painted sky, graffiti, engineering drawings, a real seedling); the lights came on, someone turned them on."""
t = open('template.html').read()
t = t.replace('/*LEVELS*/[]', json.dumps(levels, ensure_ascii=False)).replace('/*TIMELINE*/[]', json.dumps(TIMELINE, ensure_ascii=False)).replace('/*BIBLE*/""', json.dumps(BIBLE, ensure_ascii=False))
t = t.replace('/*LADDER*/[]', json.dumps(LADDER, ensure_ascii=False)).replace('/*CHAPTERS*/[]', json.dumps(CHAPTERS, ensure_ascii=False))
open('/home/user/deadletter/docs/story_board.html', 'w').write(t)
print(len(t), len(levels))
