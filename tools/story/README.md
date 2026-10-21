# The story board

`docs/story_board.html` is the published story board (https://claude.ai/artifact/CRnFEUpGbxb4LEPzfTATuM). Build it
with `python3 build.py` here: `template.html` plus the levels, timeline and bible below.

**The story** comes from the director's plan, `docs/full_game_plan.md` (revision 0.3): each chapter's place, idea and
turn (section 4 and the environmental gradient), the prologue's story direction (section 6), and each level's story
after it (section 7: the aha's first sentence goes to the gameplay panel, the rest is the level's story). The
timeline, the bible notes and the reference sheets in `build.py` and `template.html` condense the plan's sections 1 to
3 and 8. `scenes.json` (from `docs/scene_overview.md`) still supplies what the built levels say in the game.

**Gameplay:** DL-01 to DL-17 show their puzzles as built, from `docs/gameplay_breakdown.md` (keep its field names and
`### DL-nn Name` headings when editing). DL-12 to DL-17 also show what the plan proposes for them, and DL-18 to DL-51
show the plan's puzzles (goal, play, wrong first try, aha, recovery and forward). The ladder is the plan's learning
ladder and permanent rules; the chapter sheets beneath it are each chapter's turn, the plan's prototype chains and its
puzzle rules. Every DL-nn becomes a link on the board.

**The story arc** at the top of the board plots tension scene by scene (0 calm to 10 most tense), with the Save the
Cat beats on a lane beneath. The beats and their wording are the plan's (section 4); which scenes carry each beat
(`SPANS`) and every scene's tension and moment (`ARC`) are the writer's estimates in `build.py`. Change them there.

Its cards live in the artifact's database (`elements`), with the timeline and the story-bible notes in `meta/timeline`
and `meta/bible` once a Markdown import has set them. Claude reads and writes them with the ArtifactData tool.

**Markdown export and import** (buttons at the top of the board):
- `## Timeline`: a table (P.A. | Era | What happened | Where the player meets it).
- `## Story bible`: free text.
- `## DL-15 One Pupil Missing`: one per level, then one card per `### Kind · Title` (kinds: Plot room, Musical moment,
  Tableau, Voice letter, Sign or writing, Object, Secret room, Story beat, Note).
- Optional lines `- Era: The Commons`, `- Status: Idea | Planned | In the game`, then the card's text.
- An exported card carries `<!-- id: ... -->`. Keep it to update that card in place; without it a card is matched by
  its title within its level, or added.

**Gameplay in exports:** Export all ends with a `## Gameplay` section, and **Export gameplay** saves it alone: the
ladder, the rules, each chapter's notes and each level's panel, as the board shows them. It is for reading; importing
skips it. Edit the plan or the breakdown and rebuild.

Imports show a preview (new, changed, unchanged, removed) before anything is written.
