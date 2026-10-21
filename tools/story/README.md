# The story board

`docs/story_board.html` is the published story board (https://claude.ai/artifact/CRnFEUpGbxb4LEPzfTATuM). Build it
with `python3 build.py` here: `template.html` plus the level list from `scenes.json` (extracted from
`docs/scene_overview.md`), the timeline and the condensed bible.

**Gameplay** comes from `docs/gameplay_breakdown.md`: each level's panel (type, builds on, new here, the steps, the
wrong first try, the aha, carries forward), the ladder table and each chapter's summary. Every DL-nn in it becomes a
link on the board. Keep its field names (`- **Builds on:**` and the rest) and its `### DL-nn Name` headings when
editing, then rebuild. A level with steps there shows them as its play, and the old one-line play is dropped.

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

**Gameplay in exports:** Export all ends with a `## Gameplay` section (the ladder, each chapter's summary, each level's
fields), and **Export gameplay** saves the breakdown alone in `docs/gameplay_breakdown.md`'s own format, so it can
replace that file. Importing skips the gameplay: edit it in the repo and rebuild.

Imports show a preview (new, changed, unchanged, removed) before anything is written.
