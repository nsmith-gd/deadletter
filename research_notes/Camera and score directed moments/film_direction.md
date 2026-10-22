# Camera and score in directed moments: how film does it

Research notes for the composer and the camera programmer authoring short (5–30 s) directed moments in a 2.5D side-on puzzle game (Inside/Limbo-style, with occasional crane-ups, push-ins, reveals and look-downs).

How to read the tags:
- **[src]**: stated in the cited source.
- **[obs]**: my own description of the film from memory, not checked frame by frame. Check it against the film before you rely on a timing.
- **[derived]**: a rule of thumb I built from several sources. No single source states it.

Timings from concert or album tracks are album timings. They are not film timecode.

---

## 0. The core ideas in one paragraph

Film people consistently say that music works best when it amplifies an emotion the image and story have already earned. They don't use it to create the emotion. The big sync moment is rare, it is prepared by thinning or silence, and it lands on the single frame that tells the story. After it lands, the image and the chord are allowed to sit. Walter Murch: "music seems to function best when it channels an emotion that has already been created out of the fabric of the story and film" ([The Conversations, via Wikipedia](https://en.wikipedia.org/wiki/The_Conversations)) [src]. Denis Villeneuve on Arrival: "First, we edit the entire movie without music. Not a note." Each scene had to work without score, and Jóhannsson's music was then added back as "a strengthener" ([Film Independent](https://www.filmindependent.org/blog/directors-close-recap-arrival-filmmakers-denis-villeneuve-joe-walker/), [Arrival soundtrack, Wikipedia](https://en.wikipedia.org/wiki/Arrival_(soundtrack))) [src].

---

## 1. Spotting, hit points, sync and timing

### 1.1 Vocabulary
- **Spotting session.** Director, composer, editor and often the sound team watch the locked cut together. They decide where each cue starts and stops and what it should do. The output is a set of spotting sheets with timecode in and out points ([Wikipedia: Spotting](https://en.wikipedia.org/wiki/Spotting_(filmmaking))) [src].
- **Sync point / hit point.** A moment where the music must line up with the picture: music-in, music-out, a cut, a door slam, a realization. "Write your music so that musical accents line up with your sync points." The strongest sync point lands on a downbeat ([iZotope, Writing music to picture](https://www.izotope.com/en/learn/writing-music-to-picture-film-tv-beyond.html)) [src].
- **Chion's "point of synchronization."** A "synchronous encounter between concomitant audio and visual elements" that is salient enough for the audience to perceive it as a moment. Chion says such points often reinforce an "effect of meaning" ([USC Scalar, Audiovisualities](https://scalar.usc.edu/works/audiovisualities/point-of-synchronization)) [src]. **Synchresis** is the "spontaneous and irresistible weld" between a sound and an image that occur together. **Added value** is how sound changes what we see. Sound can also **vectorize** an image, "orienting [it] toward a future, a goal" and "creating a feeling of imminence and expectation" (Chion, *Audio-Vision*, 1994, pp. 13–14, 63; quoted in [Basanta, eContact 19.2](https://econtact.ca/19_2/basanta_synchresis.html)) [src]. For us, vectorization is the key idea: a rising phrase under a camera move tells the player that the move is going somewhere.
- **Canonical camera-plus-crescendo example (Chion via USC Scalar).** In René Clair's *Le Million* (1931), a long crane and tracking shot moves over the roofs of Paris while bells grow from faint to loud. "The aural crescendo has reached its peak at the moment the tracking shot shows the tower." The second sync point comes right after: a song grows as the camera nears a window and resolves on the cut at 1'18" ([USC Scalar](https://scalar.usc.edu/works/audiovisualities/point-of-synchronization)) [src]. This is the template for a crane-up synced to a swell.
- **Streamers and punches (free timing).** Before click tracks became standard, conductors synced by eye. A **streamer** is a line that crosses the screen and ends in a **punch**, a white flash on the hit frame. Taddei gives streamer lengths of one yard = 2 s, 4 ft = 2.67 s and 5 ft = 3.33 s ([Marc Taddei, Streamers and Punches](https://www.marctaddei.com/blog/326)) [src]. Sweetwater says streamers typically run 2, 3 or 4 s, at the conductor's preference ([Sweetwater glossary, via search](https://www.sweetwater.com/insync/streamer/)) [src]. Taddei notes that John Williams' *Raiders* recordings lean on streamers and punches rather than click, "as a result, his music breathes in a natural and exciting manner" [src]. **Point for us:** a human performer needs a 2–4 s visual warning to land a hit gracefully. The audience needs the same warning to *feel* a hit coming.
- **Click track / tempo map.** A metronome fed to the players. The method goes back to Disney's Wilfred Jackson, who used bar sheets with "twelve-frame, or sixteen-frame" beats on *Steamboat Willie* ([Wikipedia: Click track](https://en.wikipedia.org/wiki/Click_track)) [src]. A **tempo map** sets all tempos and meter changes so that every hit lands on a beat. Robin Hoffmann recommends building the tempo map and sketching the hit-point material first, then writing the music that "bridges" the hits. Otherwise the bridge either "clearly feels like it is waiting for the next hit point" or the hit "come[s] a bit as a surprise" ([Hoffmann, Bridging hit points](https://www.robin-hoffmann.com/dfsb/filmscoring/bridgeing-hit-points/)) [src].
- **Fitting tools.** Change the tempo, including by decimals such as 142.6 BPM, or insert a 2/4 bar to move a hit onto a downbeat ([iZotope](https://www.izotope.com/en/learn/writing-music-to-picture-film-tv-beyond.html)) [src]. Conventional sync tolerance is about 3–4 frames either way ([Wikipedia: Film score](https://en.wikipedia.org/wiki/Film_score), via search) [src].

### 1.2 Picture cut to music, the reverse direction (very relevant to games)
- **E.T.** Williams struggled to sync the final chase. Spielberg "shut off the projector" and told him to record the music the way he wanted it, then re-edited the scene around the recording ([Wikipedia: E.T. soundtrack](https://en.wikipedia.org/wiki/E.T._the_Extra-Terrestrial_(soundtrack))) [src].
- **Close Encounters.** Much of the score existed before filming. "In a reversal of the normal process, Spielberg set parts of the film to Williams' music" ([The Listeners' Club](https://thelistenersclub.com/2020/01/03/)) [src]. A Japanese account says Williams wrote the finale against a rough cut with no effects, and Spielberg then shaped the final effects footage guided by the music ([CINEMORE](https://en.cinemore.jp/jp/erudition/80/article_111_p2.html)) [src].
- **Up, "Married Life."** It was the first cue written, from storyboards, and the music was then touched up "at various points to match the emotional tone" ([Wikipedia: Up opening sequence](https://en.wikipedia.org/wiki/Up_opening_sequence)) [src].
- **Journey (game).** Wintory wrote a piece for each level, thatgamecompany prototyped the level against it, and he then replayed the level and recomposed ([search summary of Wintory interviews](https://www.keengamer.com/articles/news/interview-with-gaming-composer-austin-wintory/)) [src].
- **For us [derived]:** a camera move in an engine costs almost nothing to retime. When the composer delivers a cue with a strong internal arc, **retime the camera to the music**, as Spielberg did, instead of making the composer chase frame counts.

### 1.3 When to enter, how hard to hit, when NOT to hit (Robin Hoffmann's "Daily Film Scoring Bits")
- **Entrances need a visible reason.** "There should always be a noticeable reason why a film cue enters": a movement, a cut, a line, a facial expression, a change of mood. "Starting music out of the blue… will usually feel pretty disconnected and random." For soft cues, nudge the start until it feels placed ([Musical entrances](https://www.robin-hoffmann.com/dfsb/musical-entrances-in-films/)) [src].
- **Placement.** Often it is "not the most effective thing to place the musical accent exactly on the visual action but rather… leave a bit of time to let it 'sink in'". For a realization, "you simply need one or two seconds to understand", so follow the reaction time of the audience or the character. Explosions need to be dead on ([Placement of hit points](https://www.robin-hoffmann.com/dfsb/placement-of-hit-points/)) [src].
- **Predictability.** Treat a hit the audience can anticipate differently from one that comes out of the blue. If both the event and its timing are predictable, use a clear build such as "a clear V–I cadence in an even meter". If the event is known but its timing is not, keep the build ambiguous about when it peaks. If the hit is a total surprise, consider moving it *off* the downbeat. Score for a first-time viewer, not for yourself after 50 viewings ([Anticipating hit points](https://robin-hoffmann.com/?p=2412)) [src].
- **Intensity.** "Inexperienced composers tend to over-accent." If the image already shouts (slow motion, a flashback montage, heavy SFX), doubling it with music "will rather cause a feeling of redundancy". If the image is understated, the music can step in harder ([Hit point intensity](https://www.robin-hoffmann.com/dfsb/hit-point-intensity/)) [src].
- **Musical logic.** Avoid "random cymbal crashes or brass stabs somewhere in a bar". A hit must be part of the musical grid, or it reads as bad sound design ([Musical logic of hit points](https://www.robin-hoffmann.com/dfsb/musical-logic-of-hit-points/)) [src].
- **Mickey-mousing.** Music that mirrors every on-screen motion. Max Steiner used it heavily in the 1930s and 1940s. It is "somewhat out of favor today… because of overuse", it reads as juvenile or melodramatic, and it can be unintentionally funny ([Wikipedia: Mickey Mousing](https://en.wikipedia.org/wiki/Mickey_Mousing)) [src]. Platform games tend toward it by default (same article) [src].

### 1.4 Perceptual sync numbers (for the programmer)
- ITU-R BT.1359-1 (1998), Appendix 1: viewers **detect** a sound/vision offset at about **+45 ms when audio leads** and **−125 ms when audio lags**. The thresholds of **acceptability** are about +90 ms and −185 ms. A 1940s Bell Labs study found detection at audio leading by more than 35 ms or lagging by more than 100 ms. The old projectionist rule of thumb was "no more than 1 frame early / 2 frames late" at 24 fps, about +42/−84 ms ([TV Technology, "A/V synchronization: how bad is bad"](https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad)) [src]. Reason: hearing a sound *before* its visual cause is physically unnatural, while sound arriving late is normal, because light is faster than sound (same source).
- **At 60 fps** [derived]: audio more than about 3 frames early is detectable, and audio up to about 7 frames late is tolerated. **Never let the musical arrival land before the reveal frame. Aim for 0 to +2 frames after it.**

---

## 2. Camera and music pairings by emotion

### 2.1 Wonder / awe

**Jurassic Park (1993), first sight of the brachiosaur.**
- The "Theme from Jurassic Park" is introduced when the visitors first see the brachiosaur. Williams wanted it "to capture the awesome beauty and sublimity of the dinosaurs in nature" ([Wikipedia: JP score](https://en.wikipedia.org/wiki/Jurassic_Park_(film_score))) [src].
- Analysis by Film Music Notes ([link](https://filmmusicnotes.com/john-williams-themes-part-5-of-6-theme-from-jurassic-park/)) [src]:
  - The film portion begins at 0:47 of the concert version.
  - The theme opens with **no high instruments**: violas, cellos and basses without violins, clarinets and bassoons without flutes or oboes, soft horns and no loud brass. The score is marked "Reverentially".
  - Each new phrase (0:47, 1:08, 1:26) starts **higher in register, louder, with more instruments**. A wordless choir is added later.
  - Harmony leans on **I–IV–I** (plagal, restful) rather than IV–V–I drive, which gives "calm and restfulness".
  - The first climax (1:45–1:55) "coincides with the brachiosaur crashing back down to the ground" after rearing up.
- **Structure [obs]:** Grant's slow realization (glasses off, standing up) plays before the full reveal. The camera holds on the faces, then the creature, then a wide view of the lake and herds. Hammond's "Welcome to Jurassic Park" sits under a broad statement. The music grows across several shots; it does not crash in on the first one.
- **Context:** Spielberg kept the dinosaurs off-screen for almost an hour ([search summary of JP reviews](https://moviemusicuk.us/2019/02/25/jurassic-park-john-williams/)) [src]. *Jaws* likewise withholds the shark until about minute 81 of 124 ([search summary](https://theconversation.com/jaws-and-the-two-musical-notes-that-changed-hollywood-forever-255379)) [src]. Withholding is what pays for the swell.

**Close Encounters (1977).** The five-note motif is seeded across the film and becomes the actual "conversation" at the mothership finale. Spielberg insisted on this: per NPR's account, "It should not be a melody. It should be a signal" ([NPR transcript](https://www.npr.org/transcripts/164615420), via search) [src]. Parts of the film were cut to the music (see 1.2). Pitfall from the same film: at the preview, the original "When You Wish Upon a Star" over the finale drew snickers from some of the 1,400 viewers, and Spielberg replaced it with a Williams coda ([TCM trivia](https://www.tcm.com/articles/467316/trivia-close-encounters-of-the-third-kind-trivia-and-fun-facts-about-close-encounters-of-the-third-kind)) [src]. A swell borrowed from outside the film's own world can tip into kitsch.

**The Return of the King (2003), "The Lighting of the Beacons."** A textbook staged escalation ([Film Music Central](https://filmmusiccentral.com/2019/02/05/the-return-of-the-king-lighting-the-beacons-2003/)) [src]:
1. Pippin's secret climb gets a **tentative string motif**: anticipation, small forces.
2. When the guards see the flame, the music jumps to a "burning" figure. This is the **ignition hit**.
3. "As the next beacon… is lit, the music 'ignites' again, flourishing higher and higher": **one musical step per beacon**, a chain of small sync points.
4. Over the aerial montage of beacons across the mountain range, the Gondor theme plays as a fast reprise led by brass. **The full theme lands on the widest, most epic frames.**
5. "The theme slowly fades as the final beacon is lit and observed by Aragorn… trails off to silence" to hand over to the next cue. This is the **release**.
- The CD and film versions differ in chord progressions ([TheOneRing.net, Tribeca 2004 report](https://www.theonering.net/torwp/2004/05/page/42/)) [src], which suggests the film version was adjusted to picture. Shore, Jackson and the writers chose together which theme played in which scene "to clarify the story" (same source) [src]. Jackson's mixing attitude: "You should never worry about competing against water… We'll just pull the water down" ([TheOneRing.net, AP 2003](https://www.theonering.net/torwp/2003/01/16/25880-rings-composer-a-quest-for-the-right-sound-2/)) [src]. **Duck the effects under the big moment instead of pushing the music up.**

**Interstellar (2014).** Nolan gave Zimmer a one-page story about a father leaving a child, with two lines of dialogue, "I'll come back" and "When?", and one day to write. Zimmer produced a "tiny, tiny little fragile" four-minute piano and organ piece, which Nolan called "the heart" of the film ([Wikipedia: Interstellar soundtrack](https://en.wikipedia.org/wiki/Interstellar_(soundtrack))) [src]. The organ (Temple Church, 1926 Harrison & Harrison) was chosen because its "airiness" evoked breath (same) [src]. In the docking sequence ("No Time for Caution"), a repeating organ figure builds over long, mostly quiet exterior shots [obs]. Critics split on how loud it is. Liam Lacey wrote that the music "throbs obtrusively, occasionally fighting with the dialogue" (same Wikipedia article) [src], which is the pitfall in 5.

**Up, "Married Life," the joyful half.** See 2.2.

**How to Train Your Dragon (2010), "Test Drive."** For Hiccup and Toothless's first flight, the cue opens with bagpipes and brass "bellows" that parallel Hiccup's determination, then woodwinds suggest flight, and the brass swell makes the audience feel they are soaring ([Varsity](https://www.varsity.co.uk/film-and-tv/21230)) [src]. **[obs]** The structure is false start, then fall, then catch. The music thins or breaks when control is lost and returns in full when the pair breaks out into open sky over the sea. The full theme is held back until the frame opens up. Check this against the film.

**Avatar / Inception.** No primary timing sources found; skip, or study from the film directly.

### 2.2 Sadness / grief

**Up (2009), "Married Life."** A wordless montage of about 4.5 min ([Far Out](https://faroutmagazine.co.uk/up-sound-of-heartbreak/)) [src].
- Pete Docter: "the less we had the more emotional it felt… No dialogue, no sound effects — just music and visuals." And: "Oh no, we took out three frames — did we break it?" ([/Film](https://slashfilm.com/1582050/up-opening-emotionally-devastating-pixar-multiple-last-minute-changes-exclusive)) [src].
- Giacchino retimed parts: "maybe this is too fast now. This should be slower here." He used "fix days" to re-target specific areas (same) [src]. His emotional brief to himself: not "This is so awful!" but "a quiet and gentle moment, reverent and present" ([Far Out](https://faroutmagazine.co.uk/up-sound-of-heartbreak/)) [src].
- Musical shape ([Wikipedia: Up opening sequence](https://en.wikipedia.org/wiki/Up_opening_sequence)) [src]: "as the music slows," the couple learn they cannot have a child. When Carl realizes he never kept his promise, the music is "almost stopping entirely". At Ellie's decline, "instruments drop out of the harmony, leaving only a piano". The screen "fades to black as the music ends".
- **Grief is scored by subtraction.** Instruments drop out, the tempo slows, the music nearly stops, and a solo instrument is left.

**Saving Private Ryan (1998).** Spielberg and Williams watched a rough cut together and decided to **leave music out of the fighting sequences**. They placed it instead over "long sequences of eight to nine minutes that lack action", as "a moment of reflection for what happened" (Boston Globe 1998, via [Wikipedia: SPR soundtrack](https://en.wikipedia.org/wiki/Saving_Private_Ryan_(soundtrack))) [src]. The album runs just over an hour for a film of more than two hours (same) [src].

**Schindler's List (1993).** The score is largely silent during the atrocity sequences. In the ghetto liquidation, the girl in the red coat is followed while a children's choir sings the folk song "Oyfn Pripetshik", so source-like song carries the emotion instead of underscore ([search summary of CINEMORE essay](https://en.cinemore.jp/jp/erudition/643/article_781_p2.html)) [src]. Perlman's solo violin carries the main theme ([Wikipedia: SL soundtrack](https://en.wikipedia.org/wiki/Schindler%27s_List_(soundtrack))) [src]. The camera holds on a small, distant figure in a long take [obs].

**The Godfather.** Murch points out that the dramatic music comes *after* Michael kills Sollozzo and McCluskey, not during the build-up ([The Conversations](https://en.wikipedia.org/wiki/The_Conversations)) [src]. During the build-up, a train screech stands in for Michael's inner state ([StudioBinder on Murch](https://www.studiobinder.com/blog/walter-murch-rule-of-six/)) [src]. **Music arrives after the event, as reflection.**

**LOTR, Grey Havens / "Into the West."** The farewell melody grew out of a Grey Havens theme that Shore had been weaving through the score from the start ([Wikipedia: Into the West](https://en.wikipedia.org/wiki/Into_the_West_(song)), via search) [src]. The farewell lands because the motif was planted hours earlier. Williams describes the same method: "Very often I work backwards. I'll try to write the end of the film… and then de-compose it… so that elements of that ending can be exposed in the beginning and then gradually developed" ([Phoenix Symphony Q&A](https://www.phoenixsymphony.org/qa-john-williams-on-accompanying-steven-spielberg/)) [src].

**Arrival (2016), "On the Nature of Daylight."** Villeneuve wanted the intro and outro "in strong contrast to the main bulk of the movie". The opening was cut to Richter's track as temp, and Jóhannsson supported keeping it ([/Film interview](https://www.slashfilm.com/547630/johann-johannsson-arrival-music/)) [src]. The piece is a slow ground bass in B♭ minor: low strings first, violins entering later with an elegiac line ([Wikipedia: On the Nature of Daylight](https://en.wikipedia.org/wiki/On_the_Nature_of_Daylight)) [src]. That is an "entrance of the high solo line over an established low bed" shape. The same article says it has become "a shortcut to heartbreak" that some consider diluted by overuse [src]. Editor Joe Walker: "I like to allow things to breathe so the audience can get immersed in the shot." In a tense scene: "I tried to create as much stillness as possible and really hold on the characters' faces" ([MPA, Oscar Watch](https://www.motionpictures.org/2017/02/oscar-watch-editor-joe-walker-masters-time-and-space-arrival/)) [src].

### 2.3 Intrigue / mystery

- **Hitchcock's bomb.** Suspense comes from the audience knowing more than the characters. "The public is aware that the bomb is going to explode at one o'clock, and there is a clock in the decor… this innocuous conversation becomes fascinating" ([Bordwell quoting Hitchcock/Truffaut](https://www.davidbordwell.net/blog/2013/11/29/hitchcock-lessing-and-the-bomb-under-the-table/)) [src]. **For a 2.5D game:** use a look-down or pull-back that shows the player something the avatar cannot see, keep the music unresolved, and do not cadence.
- **Jaws (Williams in his own words).** "If you play this very softly and slowly, you advertise or you advance the thoughts… if it speeds up and comes closer to you and gets louder and louder… You've got an actor that you can't see." Spielberg: "music substituted for the absent shark" ([Laughing Squid, Colbert interview](https://laughingsquid.com/?p=906604)) [src]. **A motif can stand in for a withheld reveal**, and its tempo and loudness encode distance.
- **Arrival (Jóhannsson).** He avoided Ligeti-style clusters in favor of "irregular and arrhythmic patterns of short notes which start small and are then layered to create a kind of cloud", "Morse code-like phrases". He also used tape loops of attackless piano drones slowed down, with a hum that is "hard to distinguish as a human voice": "an extremely eerie, unsettling piece of music" ([Wikipedia: Arrival soundtrack](https://en.wikipedia.org/wiki/Arrival_(soundtrack))) [src]. Mystery comes from irregularity and sounds with no clear source, not from loudness.
- **Annihilation (Barrow/Salisbury).** A four-note idea runs through the whole score and blooms into the large cue "The Alien" for the 12–15 min lighthouse sequence. Electronics are saved for that sequence ([Wikipedia: Annihilation soundtrack](https://en.wikipedia.org/wiki/Annihilation_(soundtrack)), PopMatters interview) [src]. **The timbre change itself is withheld for the reveal.**
- **Prometheus (Streitenfeld).** To get an "unsettling" sound, the orchestra played reversed parts that were then digitally reversed back ([Wikipedia: Prometheus soundtrack](https://en.wikipedia.org/wiki/Prometheus_(soundtrack))) [src]. The result is familiar instruments with unnatural envelopes.
- **Blade Runner 2049.** No orchestra, a CS-80 palette ([Wikipedia: BR2049 soundtrack](https://en.wikipedia.org/wiki/Blade_Runner_2049_(soundtrack))) [src]. Supervising sound editor Mark Mangini wanted the derelict-building scenes to be "silence interrupted with small sounds", recorded specially, and Villeneuve asked the team to "compose with sound" ([search summary of CineMontage/Laughing Squid](https://laughingsquid.com/sound-of-blade-runner-2049/)) [src].
- **Interstellar, Miller's planet ("Mountains").** A metronomic tick, popularly described as one tick per day passing on Earth, then music that "stretches, breaks, and collides with silence" and harmonies that "never quite resolve" ([No Film School](https://nofilmschool.com/interstellar-music-timed-to-physics)) [src]. The widely quoted 1.25 s tick interval is unverified.
- **Close Encounters.** The five-note signal works as a question that is repeated and never cadenced until the exchange [obs].

---

## 3. Structure of an elevated moment

Assembled from the sources above. Phase lengths are [derived] and sized for 5–30 s game moments.

| Phase | What the camera does | What the music does | Evidence |
|---|---|---|---|
| **1. Anticipation** | Stillness or a held frame. The character notices something. The camera does not move yet. | Thins: drop voices, drop register, or go silent. Ambience stays. | Up ("music almost stopping"; "leaving only a piano"); Beacons (tentative strings); JP (theme starts with no high instruments); Hitchcock's silence |
| **2. Motivation / trigger** | A visible cause: a look, a step, a light, a cut | Music enters or turns *on* that cause, never "out of the blue" | Hoffmann, entrances |
| **3. The move** | Crane, push or pull, with a destination the viewer can infer (a 2–4 s "streamer") | Rising phrase. Each sub-phrase higher and fuller. Length fitted to the move by a tempo map. | JP phrase climb; Beacons "higher and higher"; Le Million crescendo; streamer 2–4 s |
| **4. Arrival** | The move eases into the story frame (widest view, the creature, the face) | Downbeat or cadence or theme entry exactly on that frame, or 1–2 s after for a realization | Le Million ("peak at the moment the tracking shot shows the tower"); JP climax on the brachiosaur's footfall; Hoffmann placement |
| **5. Hold** | Image held still or nearly still | Chord or theme sustained; no new information | Walker ("allow things to breathe"; "hold on the characters' faces") |
| **6. Release** | Camera returns to gameplay framing, or cut | Music decays or "trails off to silence", or hands over to the next cue. No second climax. | Beacons fade; Up "fades to black as the music ends"; SPR music as reflection *after* action |

Corollaries:
- **Seed earlier, pay off now.** Williams writes the ending first and exposes fragments of it earlier. The Grey Havens theme was woven through the trilogy. The Annihilation four-note cell runs throughout. Bond's theme was withheld until the end of *Casino Royale* ([TV Tropes: Theme Music Withholding](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/ThemeMusicWithholding)) [src].
- **Silence can be the arrival.** Williams on *Family Plot*: the music crescendoed, then cut to an open window where the criminal had escaped. Williams proposed an accent; Hitchcock said, "why don't you abruptly stop the music there? The silence will equal the absence of the criminal; we'll just have a faint breeze blowing" ([Legacy of John Williams: Family Plot](https://thelegacyofjohnwilliams.com/works/films/family-plot/)) [src]. Williams elsewhere: "the palate [palette] of what we do is silence" ([CBS transcript](https://www.cbsnews.com/amp/news/extended-transcript-john-williams-on-steven-spielberg-star-wars-and-the-power-of-music)) [src].
- **Emotion over everything.** Murch's "Rule of Six" for a cut, from *In the Blink of an Eye*: emotion 51%, story 23%, rhythm 10%, eye-trace 7%, 2D plane 5%, 3D space 4%. StudioBinder summarizes it as "emotion… accounting for over 50% of what makes a great cut" ([StudioBinder](https://www.studiobinder.com/blog/walter-murch-rule-of-six/)) [src]. Murch also generally thinks music is used too much (Film Quarterly 2000 interview, via search) [src]. Mackendrick's working test for any device: "Your only mistake… is to produce in your audience an effect you didn't intend, or fail to produce the effect you did" (*On Film-making*, via search) [src].

---

## 4. Numbers and rules of thumb found

- **Sync perception:** audio leading by more than about 45 ms is detectable, while audio lagging is tolerated to about 125 ms (ITU-R BT.1359) [src]. Classic film rule: 1 frame early / 2 frames late at 24 fps [src]. Scoring tolerance: about 3–4 frames [src].
- **Warning time:** conductors' streamers run 2–4 s (2, 2.67 or 3.33 s per Taddei) [src].
- **Realization delay:** for a moment the audience must process, delay the musical reaction by 1–2 s (Hoffmann) [src]. For physical impacts, hit dead on [src].
- **Shot length baseline:** average shot length fell from about 12 s in 1930 to about 2.5–4 s in recent decades. *Psychological Science* reported 8–10 s in the 1960s and 3–4 s in 2005 (Cutting; [FlowingData](https://flowingdata.com/2014/09/22/evolution-of-movies/), [PMC3485803](https://pmc.ncbi.nlm.nih.gov/articles/PMC3485803/)) [src]. **A hold of 2× the norm (6–8 s) reads as deliberate, and 3×+ (10 s or more) reads as meditative** [derived].
- **Rationing:**
  - SPR: no score in combat; music in 8–9 min reflective stretches; about 1 h of score in a film of more than 2 h [src].
  - E.T.: almost 80 min of music in a feature, but the *big* themes come in a few places [src].
  - Jaws: shark withheld until about minute 81 of 124 [src].
  - JP: dinosaurs withheld for almost an hour [src].
  - Theme withholding: The Fog's theme plays about 50 s early, then not until the end credits ([MediaCommons](https://mediacommons.org/imr/node/7840), via search) [src].
  - Up's opening: one 4.5 min wordless sequence whose themes then recur for the rest of the film [src].
- **Phrase arithmetic** [derived]: seconds = beats × 60 / BPM. Examples:
  - 8 beats (2 bars of 4/4) at 60 BPM = 8.0 s
  - 8 beats at 72 BPM = 6.67 s
  - 12 beats (4 bars of 3/4) at 72 BPM = 10.0 s
  - 16 beats at 80 BPM = 12.0 s
  - 16 beats at 64 BPM = 15.0 s
  - To land the arrival exactly on a move of length T with N beats, use BPM = 60·N / T. Example: 9.5 s crane, 12 beats → 75.8 BPM.

---

## 5. Pitfalls: why a swell feels uncomfortable or unearned

1. **The emotion has not been built yet.** Music is asked to create the feeling instead of channelling it (Murch) [src]. Test the shot with no music first (Villeneuve) [src].
2. **No visible reason for the entrance.** It feels "disconnected and random" (Hoffmann) [src].
3. **Over-accenting / doubling.** A loud hit on an image that is already loud reads as redundant or over-scored (Hoffmann intensity) [src]. Stingers that aren't in the musical grid sound like "bad sound design" [src].
4. **Peak in the wrong place.** If the peak comes *before* the reveal frame, the music gives away the reveal, and it is also perceptually wrong because audio leading is noticed at about 45 ms [src]. If it comes well *after* without intent, it feels sluggish. If the bridge "clearly feels like it is waiting for the next hit point", it feels mechanical (Hoffmann) [src].
5. **Mickey-mousing.** Hitting every motion reads as cartoon, melodrama or parody [src].
6. **Fighting the voice.** Interstellar's score was criticized as "fighting with the dialogue" [src]. Keep VO and barks out of the arrival window, and duck effects rather than raising the music (Jackson) [src].
7. **Too frequent.** Overuse dilutes; Richter's "Daylight" is "diluted" through ubiquity [src]. Withheld themes land harder (Bond, The Fog) [src].
8. **Wrong register or idiom for the world.** The Disney song at the CE3K preview drew snickers [src]. Giacchino deliberately avoided grandiosity: "quiet and gentle… reverent and present" [src].
9. **Too long or too short by a hair.** Docter: "we took out three frames — did we break it?" [src]. Budget time to iterate timing against picture, like Giacchino's "fix days" [src].
10. **Accent where silence is truer.** In the *Family Plot* window, silence was the right "hit" [src].

---

## 6. Game-specific notes for a 2.5D side-on puzzle game [derived unless cited]

- Inside's audio lead, Martin Stig Andersen, argued at GDC 2016 that "the game should listen to the sound playing", meaning gameplay and audio feed back into each other ([Game Developer](https://gamedeveloper.com/audio/video-designing-the-audio-for-i-inside-i-a-game-that-listens)) [src]. Wintory, on Journey's attention-grabbing score, said "the music has virtually no auditory competition" with dialogue or heavy SFX (via search) [src]. A sparse soundscape gives a single swell a lot of weight, so ration it.
- **Interactive timing problem.** The player decides when they reach the trigger. Solutions:
  - Hold a thin anticipation loop until the player commits.
  - Take camera control at the commit point.
  - Start the camera move on the **next bar line** of the audio clock, not on frame time.
  - Drive both from the audio DSP clock.
  - Compensate for the platform's output latency so the arrival is heard 0 to +2 frames after the reveal frame.
- **In side-on games the default frame is fixed.** Any departure (crane-up, pull-back, look-down) is already an event. Pair the *departure* with the music turning, and the *destination* with the arrival.
- **Retime the camera, not the cue.** Author camera curves as a duration plus ease; let the composer deliver bars and BPM; compute the duration from the music (section 1.2).

---

## Rules for directing a moment

These are meant to be applied literally. Numbers are starting points to tune by eye and ear.

1. **Earn it silently first.** Block the moment with no music. If the camera move and the hold don't land without music, fix the picture before scoring it (Villeneuve; Murch).
2. **Ration.** At most **one full-scale swell per 10–15 min of play**. The main theme's complete, full-forces statement appears **1–3 times per game**. Everywhere else, use fragments of it (Williams "work backwards"; theme withholding; SPR).
3. **Anticipation = subtraction, 1.5–4 s.** Before the move, thin the music to 1–2 voices in low or mid register, or stop it. Drop the ambience by about 3–6 dB. Let the character notice first (JP glasses-off; Up piano-only; Beacons tentative strings).
4. **Give the move a visible motivation and a visible destination.** Start the music turn on an on-screen cause such as a look, a step or a light. Make the camera's goal inferable at least **2–4 s** before arrival, the audience's equivalent of a streamer (Hoffmann; Newman streamers).
5. **Fit the phrase to the move with arithmetic.** Choose a whole number of bars (prefer 2 or 4) from move start to arrival, and set BPM = 60 × beats ÷ move seconds. Example: a 10 s crane with 12 beats is 72 BPM. Otherwise retime the camera to the delivered cue.
6. **Each sub-phrase climbs.** Every 2–4 s, raise the register, add instruments, add dynamics. Keep the top register (violins, choir, high brass) **out until the arrival** (JP orchestration; Beacons "higher and higher").
7. **Arrival on the story frame, never before it.** The downbeat, cadence or theme entry lands on the frame where the reveal is fully legible, **0 to +2 frames at 60 fps**. Never lead the picture: audio more than about 45 ms early is detectable (ITU-R BT.1359; Le Million).
8. **Ease the camera into the arrival.** Finish the camera's deceleration over the last **0.5–1.0 s** so the frame is (nearly) still when the chord lands. A peak on a moving frame reads as busy [derived from Le Million and the JP footfall].
9. **For realizations, delay the hit by 1–2 s.** When the reveal must be understood (a face, a consequence, an absence), let the image land first and bring the musical response 1–2 s later. Physical events (a crash, a light igniting) get a dead-on hit (Hoffmann placement).
10. **Match the build to how predictable the hit is.** Predictable reveal: clear cadential build (V–I, even meter). Known event at an unknown moment: ambiguous build. Surprise: no build, and an accent off the downbeat (Hoffmann).
11. **Hold after arrival.**
    - Wonder: **4–8 s** of held image and sustained chord.
    - Grief: **6–12 s**.
    - Intrigue: hold until the player regains control, with no resolution.
    - These are 2–3× a modern average shot (about 3–4 s), so they read as deliberate (Cutting; Walker).
12. **One big sync point per moment.** In 5–30 s, allow **1 primary + at most 2 secondary** sync points (e.g. ignition, then arrival). Anything more drifts toward mickey-mousing.
13. **Wonder palette.** Major mode, plagal I–IV–I or sustained pedal rather than driving V–I. Slow dotted or long-note melody. Start low or warm, open up high at the arrival (Williams, JP).
14. **Grief palette.** Score by subtraction: slow down, drop instruments, let a **solo instrument enter on a held close-up after the event**, never during the action. Stay at or below **mp**, with no percussion hits (Up; SPR; Godfather; Schindler's List).
15. **Intrigue palette.** No cadence. Use drones, irregular short-note patterns, unnatural envelopes (reversed or attackless), and a ticking pulse. Use slow tracking that shows the player more than the avatar knows but stops short of the full reveal (Hitchcock; Arrival; Prometheus; Interstellar).
16. **Silence is a valid hit.** If the reveal is an absence, a loss or emptiness, **cut the music abruptly on the reveal frame** and leave only ambience (Hitchcock, *Family Plot*).
17. **Duck the world, not up the music.** Under the arrival, lower SFX and ambience by about **4–8 dB**. Keep VO and barks **out of the window from 1 s before to 3 s after the arrival** (Jackson; Interstellar criticism).
18. **Release without a second climax.** After the hold, decay over **2–4 s** or hand off to ambience or the next cue. Return the camera to gameplay framing **during the decay, not during the peak** (Beacons "trails off to silence"; Up fade).
19. **Don't double what the image already does.** If the shot has slow motion, a big VFX event or a loud SFX, cut the musical accent by about half in forces. If the shot is quiet and small, the music may carry more (Hoffmann intensity).
20. **Iterate in frames.** Review each moment at least 3 times with fresh eyes, adjusting in **3–6 frame** steps. Small timing changes make or break these moments (Docter's "three frames"; Giacchino's fix days).

---

## Sources (primary or near-primary first)

- Williams on Hitchcock/*Family Plot* window: https://thelegacyofjohnwilliams.com/works/films/family-plot/
- Williams Q&A (works backwards): https://www.phoenixsymphony.org/qa-john-williams-on-accompanying-steven-spielberg/
- Williams/Spielberg on Jaws (Colbert): https://laughingsquid.com/?p=906604
- Williams CBS transcript: https://www.cbsnews.com/amp/news/extended-transcript-john-williams-on-steven-spielberg-star-wars-and-the-power-of-music
- Villeneuve/Walker on editing without music: https://www.filmindependent.org/blog/directors-close-recap-arrival-filmmakers-denis-villeneuve-joe-walker/
- Joe Walker on stillness: https://www.motionpictures.org/2017/02/oscar-watch-editor-joe-walker-masters-time-and-space-arrival/
- Jóhannsson interview: https://www.slashfilm.com/547630/johann-johannsson-arrival-music/
- Giacchino/Docter on Married Life: https://slashfilm.com/1582050/up-opening-emotionally-devastating-pixar-multiple-last-minute-changes-exclusive ; https://faroutmagazine.co.uk/up-sound-of-heartbreak/ ; https://en.wikipedia.org/wiki/Up_opening_sequence
- Murch: https://en.wikipedia.org/wiki/The_Conversations ; https://www.studiobinder.com/blog/walter-murch-rule-of-six/
- Chion (sync point, Le Million): https://scalar.usc.edu/works/audiovisualities/point-of-synchronization ; https://econtact.ca/19_2/basanta_synchresis.html
- Hitchcock bomb: https://www.davidbordwell.net/blog/2013/11/29/hitchcock-lessing-and-the-bomb-under-the-table/
- Robin Hoffmann scoring notes: https://robin-hoffmann.com/?p=2412 ; https://www.robin-hoffmann.com/dfsb/placement-of-hit-points/ ; https://www.robin-hoffmann.com/dfsb/hit-point-intensity/ ; https://www.robin-hoffmann.com/dfsb/musical-entrances-in-films/ ; https://www.robin-hoffmann.com/dfsb/musical-logic-of-hit-points/ ; https://www.robin-hoffmann.com/dfsb/filmscoring/bridgeing-hit-points/
- Sync points, tempo, meter: https://www.izotope.com/en/learn/writing-music-to-picture-film-tv-beyond.html
- Streamers/punches: https://www.marctaddei.com/blog/326 ; https://www.sweetwater.com/insync/streamer/
- A/V sync thresholds: https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad
- Shot length: https://pmc.ncbi.nlm.nih.gov/articles/PMC3485803/ ; https://flowingdata.com/2014/09/22/evolution-of-movies/
- JP theme analysis: https://filmmusicnotes.com/john-williams-themes-part-5-of-6-theme-from-jurassic-park/ ; https://en.wikipedia.org/wiki/Jurassic_Park_(film_score)
- Close Encounters: https://thelistenersclub.com/2020/01/03/ ; https://en.cinemore.jp/jp/erudition/80/article_111_p2.html ; https://www.tcm.com/articles/467316/trivia-close-encounters-of-the-third-kind-trivia-and-fun-facts-about-close-encounters-of-the-third-kind
- E.T.: https://en.wikipedia.org/wiki/E.T._the_Extra-Terrestrial_(soundtrack)
- Beacons: https://filmmusiccentral.com/2019/02/05/the-return-of-the-king-lighting-the-beacons-2003/ ; https://www.theonering.net/torwp/2004/05/page/42/ ; https://www.theonering.net/torwp/2003/01/16/25880-rings-composer-a-quest-for-the-right-sound-2/
- SPR: https://en.wikipedia.org/wiki/Saving_Private_Ryan_(soundtrack)
- Schindler's List: https://en.wikipedia.org/wiki/Schindler%27s_List_(soundtrack) ; https://en.cinemore.jp/jp/erudition/643/article_781_p2.html
- Interstellar: https://en.wikipedia.org/wiki/Interstellar_(soundtrack) ; https://nofilmschool.com/interstellar-music-timed-to-physics
- Arrival / Daylight: https://en.wikipedia.org/wiki/Arrival_(soundtrack) ; https://en.wikipedia.org/wiki/On_the_Nature_of_Daylight
- Annihilation: https://en.wikipedia.org/wiki/Annihilation_(soundtrack)
- Prometheus: https://en.wikipedia.org/wiki/Prometheus_(soundtrack)
- Blade Runner 2049: https://en.wikipedia.org/wiki/Blade_Runner_2049_(soundtrack) ; https://laughingsquid.com/sound-of-blade-runner-2049/
- HTTYD: https://www.varsity.co.uk/film-and-tv/21230
- Mickey Mousing: https://en.wikipedia.org/wiki/Mickey_Mousing
- Spotting: https://en.wikipedia.org/wiki/Spotting_(filmmaking) ; Click track: https://en.wikipedia.org/wiki/Click_track
- Theme withholding: https://www.tvtropes.org/pmwiki/pmwiki.php/Main/ThemeMusicWithholding ; https://mediacommons.org/imr/node/7840
- Games: https://gamedeveloper.com/audio/video-designing-the-audio-for-i-inside-i-a-game-that-listens ; https://www.keengamer.com/articles/news/interview-with-gaming-composer-austin-wintory/

**Not reached (book-only):** Karlin & Wright, *On the Track*, which has a "Timings" chapter; Chion, *Audio-Vision*, full text; Murch, *In the Blink of an Eye*, full text; Mackendrick, *On Film-making*, suspense chapter; Doug Adams, *The Music of The Lord of the Rings Films*, for frame-level beacon and Minas Tirith analysis. No frame-accurate cue sheets were found for the JP brachiosaur, the Minas Tirith reveal, the HTTYD "Test Drive" or the Interstellar docking. Treat the [obs] structural descriptions as hypotheses to check against the films.
