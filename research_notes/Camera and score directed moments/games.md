# Camera and score: how cinematic games build "directed moments"

**For:** the composer and the camera programmer adding about five directed moments to Dead Letter (2.5D side-on,
one continuous shot, Web Audio + three.js).
**Date:** 22 October 2026.

> **Method note.** Pages were fetched with curl through the session proxy and read in full where the site allowed
> it. Some hosts blocked direct reads: mcvuk.com (429), audiokinetic.com (403), vgmonline.net (403), the Berklee
> archive, archive.org and the Leeds Beckett eprint. YouTube refused transcripts ("sign in to confirm you're not a
> bot"), so the GDC talks themselves (Andersen's *A Game That Listens*, Nesky's *50 Game Camera Mistakes*,
> Wintory's *Journey vs Monaco*) were **not** watched. Their content here comes from written coverage and from
> lists reposted from them.
>
> Labels:
> - **(search extract)**: the quote came from a search engine's summary of the page, not from reading the page.
> - **(observation)**: my own memory of playing the game. Check it by replaying before quoting it to anyone.
> - **(recommendation)**: my synthesis, not a sourced fact.
>
> The Wwise and FMOD feature names in section 2 come from vendor documentation I know but could not fetch this
> session. Confirm the exact option names in the version you use.

---

## 1. How specific games build their moments

### Journey (thatgamecompany, 2012; music by Austin Wintory, audio by Steve Johnson)

**Takeaway.** Journey's moments are mostly not frame-locked. Each cue is written to the *expected* length of a
player action. A neutral bed stays underneath, so a slow player hears a gap rather than a broken sync. The big
reveals add brief camera control and a slope that slows the walk. The ending works by subtraction: the orchestra
falls away and leaves the soloist.

- **A cue written to the length of a walk.** Wintory, describing the opening of chapter 3:
  - On entering the area, "there's a long solo for a bass flute. If you do nothing, the solo will play out and then
    stop, and then this bed of electronic, sort of, waves of color … will continue to play … indefinitely."
  - "As soon as you sing to the wreckage … the music will suddenly shift into … 'Threshold'."
  - "The length of the flute solo … is written to be about the length where, if you walk straight to the wreckage
    and sing, the flute solo will end right on time as you unlock the wreckage. But you may not walk that fast, in
    which case the flute solo will just end and [you'll] have … this brief moment of, not silence — because the
    electronic accompaniment … [is] left behind — but you'll feel the gap."
  - "Every single moment of the game is like this."
  - Source: [Polygon, "How Austin Wintory brought Journey Live to life" (2016)](https://www.polygon.com/features/2016/2/16/10970474/journey-live-austin-wintory-fifth-house-ensemble-kickstarter)
- **The aim: an invisible composer.**
  - "The goal of course was to make it totally seamless, so that it feels like the music is unfolding in real time,
    as if being written by an unseen (and very fast!) composer."
  - "I never wrote a piece of music without detailed instructions from thatgamecompany on how to implement it …
    Once a mockup of a piece was in the game, I could reiterate on it and continuously refine both how it felt, and
    how its being triggered by the system."
  - The interviewer noted that where the player "takes a large dive after a rapid section … the music always fits
    perfectly".
  - Source: [The Sixth Axis interview (2012)](https://www.thesixthaxis.com/2012/03/15/interview-journey-composer-austin-wintory/)
- **Design intent.** Johnson felt that short loops which ignored the player would be a "missed opportunity". He
  wanted music that "changed while still containing a composed emotional arc". The score is one theme, with the
  cello as the player: "like a big cello concerto where you are the soloist and all the rest of the instruments
  represent the world around you". Harp and viola join when another player is present. The whole game takes
  "two to three hours". At D.I.C.E., Chen said 3 of 25 testers cried at the end. —
  [Wikipedia, Journey](https://en.wikipedia.org/wiki/Journey_(2012_video_game))
- **The ending was solved by thinning, not by adding.**
  - Wintory and the team were "planning a large, dramatic conclusion".
  - In a concert of *Woven Variations*, Wintory had the orchestra fall away at the end to showcase Tina Guo's cello.
  - "Inspired, Wintory and the team ended 'Apotheosis' and the game the same way, with the game world fading away to
    leave only the player."
  - Sources: [Wikipedia, Journey](https://en.wikipedia.org/wiki/Journey_(2012_video_game));
    [Polygon video, "Why Journey's ending was so hard to score"](https://www.polygon.com/videos/2019/11/18/20970945/journey-ending-soundtrack-austin-wintory-interview-video)
- **The first reveal: slowed walk, swell, brief camera takeover. (search extract)** Reviewers describe:
  - "As you walk towards the hill, your character slows as the incline increases, and the music builds to the
    dramatic reveal of the Mountain."
  - "Upon climbing up the first hill … the camera slowly takes a back scene and control away from the player to
    present the far away mountain."
  - The title then appears over the shot.
  - Sources: [Jesuit Roundup review](https://jesuitroundup.org/2019/03/simulator-game-journey-captivating-and-breathtaking/);
    [Reviewed.com](https://www.reviewed.com/reviewed/reviews/journey-review)
- **Camera.** Journey's dynamic camera designer was John Nesky. His GDC 2014 list of 50 camera mistakes includes:
  - #16 "Shifting pitch, distance, and field-of-view independently";
  - #34 "Giving the player control over the camera, and then taking it away";
  - #42 "Rapidly shifting field-of-view";
  - #46 "Rapidly transitioning to a new camera position".
  - Sources: [list reposted from the talk](https://t.me/s/disdoc/811); [GDC Vault listing](https://gdcvault.com/play/1021262/50-Camera)

**Inferences**
- Write the cue to the median walk time and put a sustaining bed underneath. Then a slow player gets a gap, and a
  fast one gets an early transition. Neither gets a broken sync.
- The mountain reveal pairs *slower movement* (terrain, not a lock) with a short camera takeover. That is the
  gentlest way to make a fixed swell land.

### Inside (Playdead, 2016) and Limbo (2010); audio by Martin Stig Andersen

**Takeaway.** Playdead treats sound and music as one composition. The game *listens to the audio* rather than only
sending it triggers. Andersen's line about timing is the key engineering point: hook timing to "music or clock time,
rather than the usual but much more unstable game-time".

- **"A game that listens."** Andersen's GDC 2016 premise:
  - "the game resembles a dancer unable to hear and respond to the sound playing."
  - "In order to retain continuity in such temporal experiences, and transition seamlessly from one temporal quality
    to another, the game needs to listen and adapt to the sound playing."
  - The talk covers "audio-driven gameplay, situations in which sound conducts in-game actions, and seamless
    incorporation of death-respawn situations in the overall sound structure".
  - Sources: [Game Developer write-up](https://www.gamedeveloper.com/audio/video-designing-the-audio-for-i-inside-i-a-game-that-listens);
    [GDC Vault](https://www.gdcvault.com/play/1023731/A-Game-That-Listens-The)
- **Clock time over game time.** "Prototyping gameplay where timing and mechanics are hooked on music or clock time,
  rather than the usual but much more unstable game-time, is great for tight integration between music and gameplay.
  But it's a technical challenge – you have to demonstrate it's worth the effort early on." —
  [MCV/Develop, Broomhall interview (2015)](https://mcvuk.com/development-news/heard-about-how-playdead-used-a-real-human-skull-for-insides-audio/)
- **Audio drives animation.** In the same interview: the breathing system interpolates between recorded rhythms
  "ranging from relaxed to panic", and "the rise and fall of [the boy's] chest – is controlled by the 'breathing'
  audio data".
- **Respawn is part of the score.** Also from that interview:
  - "I easily get annoyed hearing the same line or music cue over again as I die and respawn."
  - "Making a distinction between load and respawn, and creating unique mix and music transitions for every
    situation is integral to Inside's sound design."
- **Respawn in the shockwave section. (search extract)** In the shockwave section, rhythmic cues "loop continuously
  both during gameplay and after player death". A similar Limbo section "was compromised due to the fact that the
  audio would not loop continuously". —
  [Arnold, "Inside the Loop", Computer Games Journal (2018)](https://link.springer.com/article/10.1007/s40869-018-0071-x)
- **Silence first, then one distinct cue.**
  - Andersen: "I enjoy these very long action scenes where there is no music at all and then a car randomly drives
    by and there's a very distinct music cue inserted in" (citing John Carpenter).
  - The early pig chase has no music. "When the pig hits a wall, it triggers a musical stinger that follows you into
    the next puzzle."
  - In the line-up puzzle, a recorded heartbeat is the pulse: "a kind of metronome for keeping the rhythm of the
    queue".
  - Source: [Kill Screen](https://www.killscreen.com/mad-science-behind-insides-soundtrack/)
- **One fluid compositional process.** "Instead of doing sound design, and then music … I would take one area and
  decide what it needs. Then occasionally what you would traditionally think of as music becomes sound design, and
  vice versa … each moment has its own soundscape." —
  [Pro Sound Effects interview (2017)](https://blog.prosoundeffects.com/expressive-machines-martin-stig-andersens-award-winning-game-audio-for-inside)
- **Structure and recognition.**
  - Inside is "mostly silent, with the exception of occasional musical cues".
  - Andersen "collaborated with the design team on the game's general structure and pacing to provide scenes where
    the music builds up atmospheric tension".
  - Inside won NAVGTR's *Camera Direction in a Game Engine* award.
  - Source: [Wikipedia, Inside](https://en.wikipedia.org/wiki/Inside_(video_game))
  - A reviewer singles out its "organic camera scripting" in 2.5D and notes a game of about four hours. —
    [Cubed3](https://www.cubed3.com/games/reviews/pc/inside-2)
- **Limbo's camera and silence.**
  - Limbo's camera has per-region anchoring, with "certain objects [providing] further camera cues, e.g. attractor
    objects on enemies". — [Itay Keren, "Scroll Back"](https://www.gamedeveloper.com/design/scroll-back-the-theory-and-practice-of-cameras-in-side-scrollers)
  - A conventional "'spooky' stylised interactive orchestral score" would have "tromped on" the game's "notional
    silence". — [Develop via Designing Sound (2011)](https://designingsound.org/2011/09/develop-martin-stig-andersen-on-limbo/)
- **The ending. (observation)** The Huddle's escape runs as player-controlled chaos. It comes to rest on a lit shore
  in a long, static, wide hold, carried mostly by ambience rather than a score peak. The release is the stop: motion
  ends, sound thins, the frame holds.

**Inferences**
- For Dead Letter, the moment's timeline should read the **audio clock**, not the game's `dt`-accumulated clock.
  See section 6.
- Silence before a moment is part of the moment. Inside spends its music as rarely as Limbo spends its silence.

### Ori and the Blind Forest (2015) and Ori and the Will of the Wisps (2020); music by Gareth Coker

**Takeaway.** In Ori, the cutscenes are *music-first*: animation is timed to the music's "peaks and valleys".
Gameplay music is horizontal: before and after loops, plus stingers and transitions placed by a dedicated
implementer.

- **Blind Forest cutscenes were cut to the music.** "The cutscenes … were largely driven by music and the
  visuals/editing/animation reacted to the music. I'd write to rough storyboards, and then the timing would be
  tweaked." Coker also put "at least 1000 hours into playing the game". —
  [The Sixth Axis interview](https://www.thesixthaxis.com/?p=242385)
- **The same process on Will of the Wisps.** "I generally work to storyboards at first to produce a piece of music
  that I feel is well-paced. Then the animation team animates something … more tightly timed to my musical peaks
  and valleys." Some timing changes "couldn't be solved by simple music editing, so we were able to re-record". The
  end of the prologue, Ku's First Flight, was "a rewrite of a rewrite!" —
  [Game Developer, "Behind the music … part 2"](https://www.gamedeveloper.com/audio/behind-the-music-crafting-the-score-for-ori-and-the-will-of-the-wisps-part-2)
- **Implementation by a specialist.**
  - "Guy [Whitmore] implemented every single musical cue, stinger and transition in the game."
  - Ori "favours a horizontal approach".
  - "Every game has peaks and valleys. I'd suggest that those are identified early on."
  - "You're not going to make every minute of a 70 hour experience memorable but you'd like to hope that you can
    carve out moments within that."
  - Source: same Game Developer article.
- **The state problem.** Coker uses a rotating puzzle room as his example: four lever pulls, each a re-arranged cue
  "at a higher pitch, higher tempo, and with a few more instruments". He then asks: "what happens when the player
  presses pause. What happens if the player dies at the 2nd rotation … return?" Implementation must track state so
  the cues "follow the narrative the way you intend". —
  [Spitfire Audio interview](https://composer.spitfireaudio.com/en/articles/gareth-coker-the-music-of-ori-and-the-will-of-the-wisps)
- **Before and after loops.** "Almost all of the environments have at least two musical loops … the 'before you did
  the thing' loop and the 'after you did the thing' loop." The Wisps finale's "multiple phases, all transitions
  seamlessly." — [Inverse](https://inverse.com/gaming/ori-will-of-the-wisps-interview)
- **Sync is what will separate scores.** "What's going to separate a good soundtrack from a really great soundtrack
  is going to be where and how the music plays in the game … It's going to come down to how well we can get the
  soundtrack to sync up to the game." —
  [SPIN (2020)](https://www.spinmagazine.com/2020/09/gareth-coker-ori-soundtracks-interview/)
- **Escapes. (observation)** The Ginso Tree and other escapes are player-paced runs with driving cues and
  checkpoints. I found no source on how they restart the music at a checkpoint (see Gaps).

### Abzû (Giant Squid, 2016; Austin Wintory, director Matt Nava)

- **A scene built around the music.** "There's a moment in the game where you see the diver swimming in this
  diagonal alongside these giant blue whales. That was completely and totally designed around the music. I wrote it
  first based on what Matt Nava … said he was envisioning … just purely a verbal description. So I wrote this grand
  waltz." — [LAist / The Frame](https://laist.com/shows/the-frame/abzu-composer-austin-wintory-on-his-ambitious-video-game-score)
- **One piece, several remixes.** "I designed the piece so it could be remixed by the game several different ways."
  Nava "designed the experience to last much longer so we would hear every kind of variation". Wintory had logged
  82 hours in the game. "We aren't actually making tracks or even cues in the traditional film sense … The music is
  actually written from the ground up to be dynamic and interactive." —
  [Player.One (quoting iDigitalTimes)](https://www.player.one/abzu-soundtrack-composor-austin-wintory-how-music-and-gameplay-can-go-hand-hand-547959)
- **Linear storytelling.** Wintory contrasts it with The Pathless: "ABZÛ is quite linear in its storytelling". —
  [Laced Records](https://www.lacedrecords.com/blogs/blog/austin-wintory-on-precursors-to-sword-of-the-sea-part-1)
- **Camera. (observation)** The big reveals (leaving the first cave, the whale waltz, the meditation statues) are
  slow crane or orbit moves while the player keeps swimming. The game rarely locks input. It frames the player inside
  the move.

### Gris (Nomada Studio, 2018; music by Berlinist)

- Berlinist "were able to play [a prototype of a level] and start composing for it". Nomada worked with them "through
  each iteration". — [Film Stories](https://filmstories.co.uk/gaming/hands-on-with-nomada-studios-gris/)
- "The game itself led us in the process of composition and its implementation." When Nomada loved a first take,
  "we didn't change it or decorate it more". "A great part of the ambient soundtrack was made with just a Yamaha VSS-33" (as printed; probably the VSS-30
  sampling keyboard). —
  [gamemusic.net interview](https://gamemusic.net/?p=20097)
- **Colour.** The game "evolves with the colours". Each chapter restores a colour.
  — [PCGamesInsider](https://www.pcgamesinsider.biz/indie-interview/67589/what-happens-when-two-ubisoft-vets-and-spanish-artist-conrad-roset-tenllado-start-making-an-indie-platformer-meet-gris/)
- **Middleware. (search extract)** A developer post says the shipped game used Wwise; FMOD was used for an early
  demo. — [Medium](https://medium.com/@rubenrincon/gris-eng-873e9a3fa374)
- **Observation.** Gris's big moments are camera pull-backs to a wide frame as colour floods the scene and the
  music blooms. The player keeps walking, and Gris's song (a late ability) is diegetic music *and* a mechanic.
- **Gap.** I found no developer source describing exact music-to-camera or music-to-colour triggering.

### Brothers: A Tale of Two Sons (Starbreeze, 2013; music by Gustaf Grefberg)

- **The controls.** The left stick and trigger are the older brother; the right side is the younger. "Holding down
  the left trigger, which has signified everything his brother could do that he couldn't, makes him desperately
  paddle across the water." — [Kotaku](https://kotaku.com/brothers-tale-of-two-sons-remake-ending-older-younger-1851302128)
- **The ending.** After Naia's death, Naiee "must face his inability to swim … with Naia's spiritual guidance". —
  [Wikipedia](https://en.wikipedia.org/wiki/Brothers:_A_Tale_of_Two_Sons)
- **Lesson.** The strongest moment in the set needs no camera lock and no swell sync. It *gives* control: it moves
  the meaning into the player's hand. Music supports it; it does not drive it.

### The Last of Us (Naughty Dog, 2013; Gustavo Santaolalla): the giraffes

- **Placement made the scene work.** Druckmann: "We just called that section of the game 'wild animals' … we were
  struggling with where to put it … once we put it after the David sequence, the whole structure kind of fell into
  place … without that structure, it wouldn't have worked as well." Deer were "too mundane"; "there's nothing
  threatening about a giraffe." — [Kotaku (2013)](https://kotaku.com/the-last-of-us-climactic-moments-could-have-been-very-600685013)
- **Setup.** Ellie ignores Joel's boost and drops the ladder. She runs. The player doesn't know what she has seen,
  so the beat plays like a threat, and it turns out to be giraffes. Then the two stand together over the herd (same
  source).
- **Music used judiciously.** Inspired by *No Country for Old Men*, "the team used music judiciously". A program
  "moved" the stems "depending on how long the player remained in a given area". —
  [Wikipedia, Music of The Last of Us](https://en.wikipedia.org/wiki/Music_of_The_Last_of_Us)
- **Lesson.** A directed moment is defined by what comes *before* it: maximum tension, then release. Rationing works
  at the level of story structure, not only the mix.

### Red Dead Redemption (Rockstar, 2010): "Far Away" on the ride into Mexico

- **The trigger.** After the fight crossing the river with Irish, you mount a horse: "when Far Away by Jose Gonzalez
  begins on this ride … The slow acoustic build leads into the first actual lyrics in the game, trumping every sound
  except the rolling clap of your horse's hooves." — [Game Informer, "Moments: Welcome to Mexico"](https://gameinformer.com/b/features/archive/2012/12/03/moments-welcome-to-mexico)
- **Why it lands.** "You play Red Dead Redemption for many hours with sparse music until you reach the
  aforementioned memorable moment." "Songs with vocals and lyrics are rarely used during gameplay." —
  [Game Developer, The Musical Box #03](https://www.gamedeveloper.com/audio/the-musical-box-03-breaking-the-silence)
- **Rationing.** Only four vocal songs were recorded for the entire game. —
  [Wikipedia, Music of RDR](https://en.wikipedia.org/wiki/Music_of_Red_Dead_Redemption)
- **The underlying system.**
  - "The whole score is composed in A minor and at 130 beats per minute" so that loops "segue into each other".
  - "We're working in five-minute loops."
  - "You don't know how long you're going to be staying in that mood – you can't state too much … you could be
    riding that horse for 15 minutes."
  - Source: [The Guardian, "Redemption songs" (2010)](https://www.theguardian.com/technology/gamesblog/2010/may/26/red-dead-redemption-soundtrack)
- **Lesson.** This moment has *no sync points at all*. The player has full control of a horse for a 4:39 song. It
  works because the trigger is a threshold (new land) and the song is the only one of its kind. A non-synchronous
  moment is cheap, robust, and is the right tool when the player must keep control.

### Shadow of the Colossus (Team Ico, 2005; Kow Otani)

- **Three parts per battle.** The approach music is "unsettling … when the hero is on the ground"; the battle music
  is epic; the kill is "haunting vocals, poignant violins" instead of triumph. —
  [Game Developer, "The Art of Shadow of the Colossus (5/6): Music"](https://www.gamedeveloper.com/audio/the-art-of-shadow-of-the-colossus-5-6-music)
- **State switches on climbing. (fan source)** On the 2nd colossus the music "switch[es] to Revived Power when
  climbing it … switching back to A Violent Encounter if Wander falls". — [Team Ico Wiki](https://teamico.fandom.com/wiki/Revived_Power)
- **Exploration is silent.** The music is "found in three different situations: during cutscenes, when approaching
  a colossus, and when fighting him", with a "lack of music during the phases of exploration" (Game Developer,
  above).
- **Lesson.** A *state* (on the body or off it) is a cleaner trigger than a position, and the "victory" can be
  scored against expectation.

### Others relevant to the brief

- **Celeste (Lena Raine).** The "Anxiety" gondola scene was rebuilt to match the music: Matt Thorson said "I need to
  completely change this, because it doesn't live up to the experience you've created with the music." The music
  went through FMOD, and "Matt and Noel would take the triggers generated by FMOD and implement them in the level
  scripting." — [Vice](https://www.vice.com/en/article/lena-raine-oneknowing-celeste-interview);
  [Destructoid](https://destructoid.com/?p=215576)
- **Hi-Fi Rush (Tango), the extreme of music-time.**
  - The game "was animated for 120BPM … at 60 frames per second and dynamically modified thereafter. Key poses hit
    on the beat." That is 30 frames per beat, time-stretched to each stage's tempo. —
    [GameAnim](https://www.gameanim.com/?p=106877); [Hitmarker](https://hitmarker.net/news/syncing-music-with-gameplay-a-closer-look-at-this-rhythm-based-action-game-519880)
  - **(search extract)** Cutscenes were animated to a click track, which took "about three times as long" as usual.
    Early or late actions were interpolated "so that it'll land on the beat".
- **Outer Wilds and Sheepy.** See the sibling notes in
  `research_notes/Dead Letter soundtrack composer studies/` (`prahlow_outer_wilds.md`, `tal_richards_sheepy.md`).
  Prahlow: constant music becomes "wallpaper", so music enters only at important moments. The Travelers' song at the
  Eye is a stem gathering. Sheepy: music "fades into the background … but swells at key moments".
- **Little Nightmares, Planet of Lana, Stray.**
  - The searches found only general composer interviews: Lilja's processed music-box and voice textures, and
    Furukawa's simple, "bold" themes. No implementation detail on directed moments was found.
    — [PCGamesN, Little Nightmares](https://www.pcgamesn.com/little-nightmares-interview);
    [Laced, Furukawa](https://www.lacedrecords.co/blogs/blog/takeshi-furukawa-bet-big-on-bold-melodies-for-planet-of-lana)
  - **(observation)** Planet of Lana's chase set pieces run on a fixed-pace camera, and its vistas are
    walk-and-pan reveals.

---

## 2. Techniques for locking music to camera in an interactive context

Ordered from least to most control taken from the player.

### 2.1 Non-synchronous: trigger and let it play (RDR "Far Away", SotC's state switches)

- **How it works.** A threshold or state change starts a cue or song with no sync points.
- **Strengths.** It is robust to any player speed. Pick it when control must stay total.
- **Cost.** No hit can coincide with an image. The emotion comes from the setting and the rarity of the cue.

### 2.2 Written to the expected duration, with a bed underneath (Journey's flute solo)

- **How it works.** The cue's length equals the median time for the action. A sustaining bed covers early finishes,
  and the next section enters on the *action*, not the clock.
- **Rule of thumb (recommendation).** Measure the median and the 90th percentile of the walk in playtests. Write the
  solo to the median. Make sure the bed can sustain to the 90th percentile and beyond with no sense of "waiting".

### 2.3 Triggering from camera or position, with music written to the shot's length

- **How it works.** When the authored shot starts, the cue starts. The composer receives the shot's exact duration
  and keyframes, as Ori's composer received storyboards.
- **Works only if the shot's duration is fixed.** That means the shot must be timed on a clock the game cannot slow
  (see 2.7), or the player must be soft-locked during it (see 2.4).

### 2.4 Briefly taking control: authored camera plus slowed movement

- **What the games do.** Journey's hill slows the walker as the music builds and the camera takes over to show the
  mountain. Dead Letter already does a version: the `SadWalk` at 0.39 m/s, no running.
- **Soft lock (recommendation).** The player still steers, but speed is clamped and the camera is authored. The cue
  still has a variable start-to-arrival time, so use 2.6 (a speed governor) to land the peak.
- **Hard lock.** Input is ignored and the timeline runs on the audio clock. Use it only for the 4 to 10 s around the
  peak.
- **Costs.** Nesky's #34 ("Giving the player control over the camera, and then taking it away") and #46 ("Rapidly
  transitioning to a new camera position") are the costs to manage.
- **Slow walking as a pacing tool.** Slow-walk sections are "the interactive equivalent of lengthy establishing
  shots in film". They draw criticism when overused or arbitrary. —
  [CGMagazine on Everybody's Gone to the Rapture](https://www.cgmagonline.com/articles/features/taking-your-time-in-everybodys-gone-to-the-rapture/);
  [Giant Bomb, "Forced Slow Walking"](https://giantbomb.com/wiki/Concepts/Forced_Slow_Walking)

### 2.5 Quantising starts to the beat or bar (horizontal resequencing)

- **The idea.** Wilbert Roget: "With the horizontal approach, you can have like beat synchronization and say, 'We're
  going from this piece to the next, so let's wait until the next bar or every two bars until we transition.' And
  then with the vertical, you can say, 'Okay, let's organize the piece into stems that can be stacked.'" —
  [EGM, "Playing Your Song"](https://egmnow.com/playing-your-song-the-evolution-of-dynamic-music-in-games/)
- **iMUSE** (LucasArts, 1991) already did this. It recognised "what measure a track was in and what beat it was on",
  then picked "an appropriate musical fill to bridge the transition" (same source).
- **Wwise transition rules.** These were not fetched this session; check the names in your version.
  - **Source exit:** *Immediate*, *Next Grid*, *Next Bar*, *Next Beat*, *Next Cue* (any or a named one), or *Exit
    Cue*.
  - **Destination entry:** *Entry Cue*, *Same Time as Playing Segment*, or a named or random cue.
  - **Optional parts:** pre-entry and post-exit (an anacrusis and a tail), per-side fades with offsets, and a
    *transition segment* (a bridge).
  - **Stingers:** play at *Next Beat*, *Next Bar*, *Next Cue* and so on, with a "don't play again within X s" guard.
  - **Callbacks:** the game can receive `AK_MusicSyncBeat`, `AK_MusicSyncBar` and `AK_MusicSyncUserCue`. One
    community answer derives BPM as `60 / segmentInfo_fBeatDuration`, and another reports user cues arriving
    "sporadically" after a segment loops in a playlist. —
    [Audiokinetic Q&A 2288](https://www.audiokinetic.com/qa/2288/access-multiple-callbacks);
    [Q&A 4945](https://www.audiokinetic.com/qa/4945/callback-custom-erratic-looping-playlist-repeated-container)
  - **Gotchas:** *Next Grid* ignores the Exit Cue
    ([Q&A 10882](https://www.audiokinetic.com/qa/10882/music-exit-source-next-grid-should-include-the-exit-falls-grid)).
    *Next Beat* between segments at different tempos lands on an unexpected bar
    ([Q&A 12956](https://www.audiokinetic.com/qa/12956/transition-to-the-next-beat-of-a-track-with-a-different-tempo)).
- **FMOD Studio equivalents** (same caveat):
  - tempo markers;
  - destination markers;
  - transition markers and transition *regions* with quantisation (beat or bar);
  - transition timelines (a bridge with its own fades);
  - timeline beat and marker callbacks to the game.
  - An indie team used "the quantized transition region feature in FMOD to constrain transitions to the pulse of
    the music" ([itch.io devlog post](https://itch.io/post/11510633)).
- **One tempo and key across a score makes any bar a legal transition.** RDR used A minor at 130 bpm. Dead Letter's
  prologue already uses a shared 60 bpm grid, 8-bar (32 s) loops and a shared D pedal (`docs/prologue_music.md`).

### 2.6 Camera moves driven by musical time (the camera waits for the downbeat)

- **Waiting.** Once a moment is armed, the camera's *departure* is scheduled to the next bar line of the music
  already playing. The reveal frame is keyed to the cue's peak bar, and every camera key is expressed in bars and
  beats.
- **The speed governor (recommendation).** It lands a peak in a soft lock.
  - When the player passes a commit point, compute the time to the target downbeat.
  - Set the walk speed to `distance / time`, clamped to about ±15% of the authored speed.
  - If the clamp can't make it, move the peak one bar later rather than speeding the player.
  - Precedent: Hi-Fi Rush interpolated actions "so that it'll land on the beat" (search extract).
- **Precedent for music-first timing.** Ori's cutscenes, Abzû's whale waltz and Celeste's "Anxiety" scene were all
  built, or rebuilt, to match the music.

### 2.7 Letting the player's walking drive progress through a swell ("music lerp by position")

- **Vertical version.** Progress `p = clamp((x − x0) / (x1 − x0))` along the approach drives stem gains (strings →
  octave violins → timpani roll → cymbal swell). The swell is "played" by walking, and stopping holds it. The
  closest sourced precedents:
  - Journey's slope (slower walk, building music);
  - Wintory's "unseen (and very fast!) composer";
  - TLOU's stems moved by time spent in an area;
  - Inside's breathing interpolation, which shows parameter-driven audio driving animation.
- **Horizontal version.** The approach is cut into 1-bar or 2-bar segments. Each next segment is allowed only if `p`
  has crossed its threshold; otherwise the current bar vamps (loops).
- **Limit.** A pure position lerp can't produce a *crest on a frame*: a crescendo you can stop is not a peak. Use
  the lerp for the approach. Hand the last 1 to 2 bars to the clock (2.6) so the peak lands.

### 2.8 The Web Audio + three.js specifics (all sourced)

- **The audio clock is the reference.** `AudioContext.currentTime` is the audio hardware clock. "It advances in
  increments of one … render quantum": 128 frames, which is "2.7 ms at 48 kHz". It "stops advancing while the
  context is suspended". — [MDN, currentTime](https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/currentTime)
- **Never schedule audio from `setTimeout` or rAF directly.** Main-thread timers "can easily be skewed by tens of
  milliseconds or more by layout, rendering, garbage collection". Use a lookahead scheduler. The reference metronome
  wakes every 25 ms and schedules everything due in the next 100 ms, and survived a 50 ms timer delay without missing
  a beat. For visuals, read the audio clock inside `requestAnimationFrame`. —
  [Chris Wilson, "A tale of two clocks" (web.dev)](https://web.dev/articles/audio-scheduling)
- **Output latency.**
  - `baseLatency` is the graph-to-system-mixer latency.
  - `outputLatency` is the time from handing a buffer to the system until "the first sample … is actually processed
    by the audio output device". It became Baseline in March 2025.
  - `getOutputTimestamp()` returns `{contextTime, performanceTime}`: which sample is at the speaker *now*, mapped to
    `performance.now()` units.
  - Sources: [MDN outputLatency](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/outputLatency);
    [MDN baseLatency](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/baseLatency);
    [MDN getOutputTimestamp](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/getOutputTimestamp)
- **Drift is real.** The audio and system clocks "are almost always running off different crystals". The
  relationship "needs to be estimated using a linear model, at least". This W3C thread led to `getOutputTimestamp`.
  — [W3C public-audio, 2013](https://lists.w3.org/Archives/Public/public-audio/2013JanMar/0189.html);
  [W3C bug 20698](https://www.w3.org/Bugs/Public/show_bug.cgi?id=20698)
- **Decoding.** `decodeAudioData` is asynchronous and resamples to the context rate.
  ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/decodeAudioData)) A cue decoded *at the
  trigger* starts late. Decode at scene load.
- **MP3 priming and padding.** MP3 files carry encoder delay and padding. The exact values are "in metadata included
  within each file", and gapless playback needs them trimmed. —
  [Chrome, MSE for audio](https://developer.chrome.com/blog/media-source-extensions-for-audio/)
  - **(search extract)** A typical LAME delay is 576 samples plus a 529-sample decoder delay, 1105 samples in all:
    23 ms at 48 kHz, 25 ms at 44.1 kHz.
  - Dead Letter's loops already carry 2 s of padding to dodge this. Hit points in one-shot cues need the same care.

---

## 3. Anatomy of a good moment

The structure below is a synthesis of the cases above, with numbers converted to Dead Letter's 60 bpm 4/4 grid
(1 beat = 1.0 s, 1 bar = 4.0 s). **(recommendation, grounded in the cited cases)**

| Phase | What the camera does | What the player can do | What the music does | Length at 60 bpm |
|---|---|---|---|---|
| **0. Quiet before** | Normal side-on follow | Full control | Sparse: bed low, or silence and room tone (Inside, SotC, RDR) | ≥ 2–3 min since the last moment |
| **1. Anticipation** | Narrow the frame: closer, lower, or start drifting the look-target toward the subject. Eases slowed ("the camera eases more slowly", direction.md) | Soft lock: `SadWalk` 0.39 m/s, no run, or terrain slows him (Journey's slope) | **Thin out.** Bed ducks or drops; one voice remains (Journey's cello alone; Inside's silence before a cue). The swell starts *quietly*, from the bottom | 1–2 bars (4–8 s) |
| **2. The move or reveal** | One continuous move (crane, pull-back, push-in). Pitch, distance and FOV change *together* (Nesky #16), on an ease-in-out curve. Departure on a bar line | Soft lock continues. Speed governor lands him | Build: stems added per half-bar or bar; timpani roll and suspended-cymbal swell in the last bar | 1–3 bars (4–12 s) |
| **3. Arrival** | The reveal frame *settles* (velocity → 0) on the downbeat | Hard lock allowed here only | **Peak on the downbeat** of the bar where the frame settles: tutti, violins in octaves, cymbal crest | The downbeat itself |
| **4. Hold** | Frame held still, or a very slow drift (≤ 2–3% of frame width per second) | Input accepted; any input ends the hold early (Nesky #34) | Peak decays; the tail carries; the "turn" begins (music box, theme in major) | ≥ 1 bar (4 s), up to 2 bars (8 s) |
| **5. Hand-back** | Blend back to the side-on rig over 1.5–3 s, ease-in-out (SmoothDamp-style; Keren's "Scroll Back"). The rig is retargeted to his *current* position, not where he was | Speed ramps from `SadWalk` to walk over about 1 s; full control | Music doesn't stop with the camera. The tail rings under the return; the bed re-enters ≥ 1 bar later, quietly | 1 bar (4 s) overlap |

**Notes on the numbers**
- **Hold.** Dead Letter's current holds are a 2.6 s marks shot (`MARKS_HOLD`), a 0.8 s label hold and about 10.5 s
  for the vista. One bar (4 s) is the minimum that reads as *held* rather than *passed*. Two bars suit the one or two
  biggest reveals. Longer than that, the player is waiting rather than feeling.
- **Total loss of control.** The table keeps the hard lock to the arrival and early hold: about 4–8 s, at most 10 s.
  RDR kept full control for 4:39, and Brothers' best moment *gives* control. A swell with a soft lock is usually
  enough.
- **Why the camera settles on the peak, not before or after.** If the camera arrives early, the frame waits for
  the music and the peak sounds late. If the peak comes before the frame has settled, the music "tells" before the
  image "shows". See 5.2 for the perceptual numbers.

---

## 4. Rationing

**Evidence that restraint is what makes moments land**
- RDR: "many hours with sparse music" before "Far Away", and only four vocal songs in the game (Musical Box #03;
  Wikipedia).
- Inside is "mostly silent, with … occasional musical cues". Andersen prizes "very long action scenes where there is
  no music at all and then … a very distinct music cue" (Wikipedia; Kill Screen).
- Limbo's "notional silence" would have been "tromped on" by a conventional score (Develop).
- Shadow of the Colossus: no music while exploring, only at approach, battle and cutscenes (Game Developer).
- TLOU used music "judiciously", inspired by *No Country for Old Men* (Wikipedia).
- Outer Wilds: constant music becomes "wallpaper" (sibling note).
- Andrew High: "Movies, television, and games certainly don't require a wall-to-wall score … The score can often
  have far more impact if it is present only when it is needed."
  - The *Saving Private Ryan* landing has music only in "one tiny section" across about 20 minutes.
  - His *Gears of War* example has no music for a minute, then "a barely-perceptible string pad", then release 20 s
    later.
  - Source: [Game Developer, "When less is more in game music"](https://www.gamedeveloper.com/audio/when-less-is-more-in-game-music)
- P.T. Adamczyk on moving from The Witcher 3 ("notorious for having the music on all the time") to Cyberpunk 2077:
  "we were really keen about learning to use the silence". Also: "You don't need to bring out the orchestra for
  every new moment in the game". After 40 hours, "just playing a few notes of this character's theme is enough". —
  [Inlingo interview](https://inlingogames.com/blog/the-appropriate-use-of-silence-is-important-an-interview-with-p-t-adamczyk-senior-composer-at-cd-projekt-red/)
- Coker: "You're not going to make every minute … memorable but you'd like to hope that you can carve out moments."
- Druckmann: the giraffe scene worked only once placed after the David sequence.

**Why swelling at every reveal numbs the player (inference)**
- The swell is a signal: "this matters". Repeating it trains the player to expect it, and an expected swell carries
  no information.
- A swell also spends loudness headroom. Dead Letter's prologue theme already uses an 18.3 LU loudness range from
  −48 dB to −15 dB. Each full-orchestra peak lowers the next one's contrast unless quiet time is restored in between.
- Swelling on *every* vista also teaches the player that the camera's departure means "orchestra incoming". That
  kills surprise.

**How many per hour (recommendation)**
- Dead Letter plans about five moments. Over a chapter of roughly 60–90 minutes that is about one per 12–18
  minutes, which matches the density of the cited games.
- Keep at least 3 minutes of sparse music before any moment.
- Never place two full swells within 5 minutes.
- Only one or two of the five should be the full "strings in octaves + timpani + cymbal" peak. The direction doc's
  "wide and high … about once a chapter" lens rule is the same principle for the camera.
- The others should be *small*: a theme fragment, a single solo, or silence plus a held frame, in Adamczyk's
  "don't put a hat on a hat" sense.
- At least one should be scored by **subtraction**: the music drops out and the frame holds (Journey's ending,
  Inside's ending).

---

## 5. Pitfalls

### 5.1 Music out of step with the camera

- **Two clocks.**
  - In Dead Letter the cue plays on the audio clock, but shots are timed by `game.clock` or animation `time`.
  - The frame loop clamps `dt = Math.min(0.05, rawDt)` (`index.html` line ~7086). Any frame longer than 50 ms makes
    game time fall behind audio time permanently.
  - A 300 ms hitch at the trigger (shader compile, decode, garbage collection) puts the camera 250 ms behind the
    music for the rest of the moment.
  - This is Andersen's "unstable game-time" problem.
- **Frame-rate variance.** Exponential camera smoothing like `k = min(1, dt * ease * 1.6)` (`applyShots`) depends on
  frame rate in how it *settles*. The arrival frame therefore drifts by tens of milliseconds between 30, 60 and
  144 Hz.
- **Decode latency.**
  - `Music.play()` decodes on demand if needed, then starts the source at an offset equal to the elapsed time. That
    keeps the *music* anchored to the request time (good).
  - But the first moment of a cold cue may start mid-fade, and the cue's own 1.2 s default fade-in blunts any hit
    near its start.
- **Output latency.** On Bluetooth headphones `outputLatency` can be large: hundreds of milliseconds is commonly
  reported (unverified number). A camera timed to `currentTime` will then look *early* relative to what is heard.
- **Tab or background.** rAF stops when the tab is hidden, but the AudioContext keeps running. Coming back mid-moment
  puts the camera seconds behind.

### 5.2 Swells that peak before or after the image

**Perceptual tolerance.** ITU-R BT.1359 gives detectability thresholds of about **+45 ms (sound early) to −125 ms
(sound late)** and acceptability of about **+90 / −185 ms**. ATSC recommends tighter limits for broadcast: sound
never more than 15 ms early or 45 ms late.
- Sources: [ITU-R BT.1359 (PDF)](https://itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-0-199802-S!!PDF-E.pdf);
  [TV Technology](https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad)
- **Sign conventions differ between sources.** What matters is that audio *leading* the picture is noticed about
  three times sooner than audio lagging.
- Target: the downbeat between 0 and +40 ms *after* the frame settles, never more than about 15 ms before it.

**Where the error comes from**
- **The composer's side.** A swell "peaks" where its loudest point is, often the cymbal crest or the tutti attack.
  The composer must state the exact sample of that peak, not "bar 9" in the abstract. A rubato or ritardando into
  the peak moves it.
- **The camera's side.** An ease-out move has no sharp arrival, so define "arrival" as the frame where camera speed
  falls below a threshold (for example 1% of the frame per second). Key that frame to the downbeat.
- **Peaks too early.** Common causes:
  - the cue is triggered on the shot's *start* and the shot then stretches (player slower than tested);
  - the player is faster and the camera's arrival was keyed to his position.

### 5.3 Moments fighting voice-over

- Dead Letter has voice cards, tannoys that "play on their own as he passes", and a music duck of 0.4 (about −8 dB)
  with ramps of 0.4 s down and 1.5 s up (`Music.duck`). A tannoy triggered inside a moment will duck the peak.
- **Rule of placement (recommendation):** no voice line from 1 bar before the peak to the end of the hold. Voice goes
  either in the anticipation (the music is thin there anyway) or after the hand-back.
- If a voice must overlap, the cue is written *around* it: thin orchestration in the 250 Hz–3.5 kHz voice band,
  which is also the band of the game's old-recording chain. Don't rely on the duck alone.

### 5.4 Taking control too long

- Nesky #34 ("Giving the player control … and then taking it away") and #46 ("Rapidly transitioning to a new camera
  position"); Keren on vestibular discomfort from fast camera acceleration.
- Players resent slow-walk sections when they feel "arbitrary" (Giant Bomb; CGMagazine).
- Coker's pause, death and re-entry questions show the state cost of every lock.
- Andersen's respawn point: replaying a moment after a death annoys. Dead Letter's "cinematics play once" rule
  already covers this. Its *music* must follow the same rule: no replayed swell after a respawn.

### 5.5 The music re-fires or doubles

- A moment that can be re-entered (backtracking, or a reload near the trigger) must remember it was played, as
  Coker's Ori state-tracking shows.
- Stingers need a "don't replay within N s" guard, as Wwise stingers have.

---

## 6. Notes on the current Dead Letter code (as of this research)

These are things the composer and camera programmer should know before building the five moments. They come from
reading `game/undelivered/index.html` and `docs/direction.md`.

- **The shot system.** `currentShot()` returns `{pos, look, focal, ease}` per moment, keyed to `game.clock`,
  animation `time` (`actions.X.time`) or scene phase timers. `applyShots()` blends with `k = min(1, dt * ease * 1.6)`
  and an outer weight `shotCam.w` (in at rate 1.4/s, out at 0.8/s, smoothed).
  - There is no musical time anywhere in the shot keys.
  - The arrival depends on frame rate and on game time.
- **The game clock.** It is clamped (`dt ≤ 0.05`), so it runs slow under load relative to audio.
- **Music cues.**
  - `Music.play(name, fadeIn = 1.2)` starts immediately, not on a bar.
  - It fades in over 1.2 s by default; a hit cue needs `fadeIn ≈ 0.05` or a pre-roll that is meant to be faded.
  - It anchors the cue to the request time even if decode is late.
  - `queue()` chains on `onended` (main thread), which is not sample-accurate.
- **The score grid.** The prologue score is 60 bpm 4/4 with 8-bar (32 s) loops, and 2 s of padding before
  `loop_start = 2.0 s` (`docs/prologue_music.md`). Bars are therefore at `2.0 + 4n` s within each loop file. That
  makes bar-quantised entries easy.
- **The direction doc.** It already asks for:
  - "the music swells … the pacing slows";
  - `SadWalk` at 0.39 m/s;
  - "hold the moment for several seconds";
  - eased shots;
  - "sparseness still holds";
  - cinematics that play once.
  The rules below make those requirements timeable.

---

## 7. Rules for directed moments in a side-on game

1. **Five moments, rationed.**
   - At most one directed moment per 12–15 minutes.
   - At least 3 minutes of sparse music before each.
   - No two full swells within 5 minutes.
   - Only one or two of the five get the full orchestral peak and the wide, high lens.
   - At least one is scored by subtraction: the music drops out and the frame holds.
   - (RDR, Inside, SotC, Adamczyk, High)
2. **Write every moment on the bar grid.** At 60 bpm one bar is 4.0 s. The composer delivers a cue sheet per moment
   (JSON beside the files):
   - `bpm`;
   - `firstBarSample` (after MP3 priming);
   - `peakSample` (the crest or downbeat);
   - `holdBars`;
   - `tailBars`;
   - an optional `voiceHoleBars`.
   The camera programmer keys every shot keyframe in **bars and beats from the peak**, never in seconds from the
   trigger.
3. **The moment's timeline reads the audio clock, not `game.clock`.** While a moment is live:
   - `t = audioNow() − peakTime`;
   - camera keys and any locked animation (`action.time = …`, not `mixer.update(dt)`) are sampled at `t`.
   - Never integrate `dt` for a moment. (Andersen: "music or clock time, rather than … game-time".)
4. **Compensate for output latency.** `audioNow()` = `getOutputTimestamp()` extrapolated to now. Fall back to
   `currentTime − (outputLatency || baseLatency || 0)`. Smooth it with a linear fit of `(performance.now(),
   contextTime)` pairs, and limit corrections to about 5 ms per frame so the camera never jumps.
5. **Decode before the moment, never at it.**
   - Decode every moment cue at scene load. `Music.get(name)` already caches.
   - Arm the trigger only when the buffer is ready.
   - If it isn't ready, play the moment *non-synchronously*: the camera on its own clock, the music entering on the
     next bar with its fade.
6. **Quantise the cue's start to the bar of what is playing.**
   - Schedule `src.start(when, offset)` with `when` = the next bar line of the current bed or loop, and at least
     100 ms ahead (Wilson's lookahead). Use the bar grid from `loop_start` + 4n.
   - If nothing is playing, start at `currentTime + 0.1` and let that *define* bar 1.
   - Use Web Audio scheduling, not `setTimeout` and not `onended` chaining.
7. **Anticipate by thinning, for 1–2 bars (4–8 s).**
   - The bed ducks or drops.
   - One solo line or room tone remains.
   - The camera narrows (closer, lower, or the look-target drifting to the subject) with slow eases.
   - D-17 slows to `SadWalk` (0.39 m/s), no run.
   - No new information, no voice.
8. **Move once, all axes together, for 1–3 bars.**
   - A single crane, pull-back or push-in.
   - Position, aim and focal length driven by *one* eased parameter (ease-in-out), not three independent lerps
     (Nesky #16, #42).
   - Departure on a bar line.
   - Camera speed should never exceed what reads as a deliberate move: about one frame-width per bar at the peak of
     the curve (recommendation).
9. **Land the peak on the frame.**
   - Define "arrival" as the first frame where camera speed falls below 1% of frame width per second.
   - Key it so the musical downbeat sounds 0 to +40 ms after it, never more than about 15 ms before (BT.1359 and
     ATSC: early sound is noticed first).
   - Test with a 1-frame flash and a click track, on speakers *and* Bluetooth.
10. **Land a walking approach with a speed governor, not a lock.**
    - When D-17 passes the commit point, compute `v = distanceToMark / (peakTime − now)`.
    - Clamp it to 0.85–1.15 × 0.39 m/s.
    - If the clamp fails, push the peak one bar later (vamp the pre-peak bar) rather than speed him up.
    - Before the commit point, let position drive the build by stem gains: a music lerp with `setTargetAtTime`,
      τ 0.3–0.5 s.
11. **A hard lock only around the peak, and at most about 10 s.**
    - Ignore input from about 1 beat before the peak through at most 1 bar after it: 4–5 s typically, never more than
      10 s.
    - Everywhere else, the player steers at reduced speed.
    - After the first bar of the hold, *any* input ends the hold early (Nesky #34).
12. **Hold for 1 bar, 2 for the biggest.**
    - The frame is still, or drifts at most 2–3% of frame width per second.
    - The music's tail and "turn" (music box, theme in major) live in the hold.
    - Under 1 bar reads as passing; over 2 bars reads as waiting.
13. **Hand back over 1.5–3 s, with an ease-in-out to the rig's live position.**
    - Blend toward where the side-on camera is *now* (retarget each frame), not where it was when the moment began.
    - Ramp walk speed from 0.39 m/s to normal over about 1 s.
    - The music doesn't end with the camera: the tail overlaps the return by about 1 bar, and the bed re-enters at
      least 1 bar later, quietly.
14. **No voice from 1 bar before the peak to the end of the hold.**
    - Suppress tannoys and voice-card auto-plays while a moment is live.
    - If speech must overlap, write a hole in 250 Hz–3.5 kHz and tell the mix: don't rely on the 0.4 duck alone.
15. **No fade-in on a hit.** Moment cues start with `fadeIn ≈ 0.05` s at a written pre-roll. The default 1.2 s fade
    belongs to beds, not hits.
16. **Account for MP3 priming in hit points.**
    - Give every moment cue 1–2 s of lead-in padding, as the loops already have.
    - Put the peak at a known sample *after* the padding.
    - Measure the actual decoded offset once per browser (Chrome, Firefox, Safari) with a click at a known sample.
    - Alternatively, ship the hit cues as WAV or FLAC: they are short.
17. **Play once, remember forever (in a run).**
    - After a respawn or reload, skip both the camera move *and* the swell.
    - Re-enter at the "after you did the thing" bed (Coker's before and after loops).
    - Track this state per moment so pause, death and backtracking can't double-fire a cue.
18. **Survive the tab and the hitch.**
    - On `visibilitychange` to hidden during a moment, `ctx.suspend()`; resume both together.
    - If a frame stall exceeds 250 ms mid-moment, let the camera *jump* forward to the audio clock rather than
      drift. A jump of one frame is less noticeable than a late peak.
19. **Prototype music-first for the biggest one.**
    - For the one or two full-peak moments, the composer writes a 30–45 s sketch to the storyboard first, and the
      camera and animation are timed to it (Ori, Abzû, Celeste).
    - For the small ones, the camera is blocked first and the music is fitted to its bar-rounded length.
20. **Check it in the side view.** A directed moment must never show puzzle information the side view doesn't
    (direction.md). The reveal is emotional, not instructional, so if the player misses it nothing is lost but
    feeling.

---

## 8. Implementation sketch (Web Audio + three.js)

The sketch is untested and illustrative. The names fit the existing `Sound`, `Music` and `currentShot` code.

```js
// ---- 1. A smoothed "what sample is at the speaker now" clock -------------------------
const AClock = (() => {
  let a = 0, b = 0, n = 0; // contextTime ≈ a + b * perfNow (b ≈ 0.001), fitted online
  function sample() {
    const ts = ctx.getOutputTimestamp ? ctx.getOutputTimestamp() : null;
    if (ts && ts.performanceTime > 0) {
      // contextTime was at the speaker at performanceTime. Keep a slow fit to absorb drift.
      const p = ts.performanceTime, c = ts.contextTime;
      if (!n) { a = c - p / 1000; b = 0.001; }
      const err = c - (a + b * p);
      a += 0.05 * err;          // gentle correction: about 20 frames to converge
      n++;
    } else {
      const lat = (ctx.outputLatency || 0) || (ctx.baseLatency || 0);
      a = ctx.currentTime - lat - performance.now() / 1000; b = 0.001;
    }
  }
  return {
    sample,
    // Audio time that is audible at a given rAF timestamp (add about one display frame for scan-out if you measure it).
    at(perfNow) { return a + b * perfNow; },
  };
})();

// ---- 2. Arming a moment on the bar grid --------------------------------------------
// cue sheet from the composer (per moment):
// { file:'m_dl04_racks', bpm:60, beatsPerBar:4, padS:2.0, peakS:26.0, holdBars:1, tailBars:2 }
function armMoment(sheet, bedOriginCtxTime) {
  const bar = 60 / sheet.bpm * sheet.beatsPerBar;          // 4.0 s at 60 bpm
  const earliest = ctx.currentTime + 0.1;                   // Wilson's lookahead
  const k = Math.ceil((earliest - bedOriginCtxTime) / bar); // next bar of the playing bed
  const startAt = bedOriginCtxTime + k * bar;               // context time the cue's bar 1 sounds
  const buf = Music.decodedNow(sheet.file);                 // must already be decoded (rule 5)
  if (!buf) return null;                                    // fall back to a non-synced moment
  const src = ctx.createBufferSource(); src.buffer = buf;
  const g = ctx.createGain(); g.gain.value = 1; src.connect(g).connect(Music.bus());
  src.start(startAt, sheet.padS);                           // skip padding; no fade on a hit (rule 15)
  return { sheet, startAt, peakAt: startAt + (sheet.peakS - sheet.padS), bar };
}

// ---- 3. Sampling the shot from musical time ----------------------------------------
// keys are in bars relative to the peak: [{bar:-3, pos, look, focal}, {bar:0, ...}, {bar:+1, ...}]
function momentShot(m, keys, perfNow) {
  const tBars = (AClock.at(perfNow) - m.peakAt) / m.bar;    // negative before the peak
  return sampleKeys(keys, tBars, easeInOutCubic);           // one eased parameter drives pos, look and focal (rule 8)
}

// in frame(now): AClock.sample(); if (moment) shot = momentShot(moment, KEYS[moment.id], now);
// Return it from currentShot() with a very high ease (or bypass the lerp) so the authored keys are what you see.

// ---- 4. Speed governor for a walking approach (rule 10) ------------------------------
function governWalk(m, xNow, xMark, perfNow, vAuthored = 0.39) {
  const tLeft = m.peakAt - AClock.at(perfNow) - m.bar / 4;  // arrive one beat early, then stop on the mark
  if (tLeft <= 0) return 0;
  const v = (xMark - xNow) / tLeft;
  return Math.min(vAuthored * 1.15, Math.max(vAuthored * 0.85, v));
  // If v was clamped for more than about 1 s, re-arm the peak one bar later (vamp) instead.
}

// ---- 5. Hidden tab ------------------------------------------------------------------
document.addEventListener('visibilitychange', () => {
  if (!moment) return;
  if (document.hidden) ctx.suspend(); else ctx.resume();
});
```

---

## Gaps

- **Not watched:** Andersen's GDC 2016 talk (it has the concrete Inside examples), Nesky's GDC 2014 talk (only the
  list), Wintory's GDC 2012 *Journey vs Monaco* and Jenova Chen's *Designing Journey* (the emotional-arc curve). All
  are free on the GDC YouTube channel and worth an hour.
- **Not documented anywhere found:**
  - how Ori's escape music restarts at checkpoints;
  - Gris's music-to-colour triggering;
  - how Journey's summit or "Apotheosis" segments are gated by progress;
  - any Little Nightmares, Planet of Lana or Stray moment implementation.
- **Not verified:**
  - the exact Wwise and FMOD option names (vendor docs blocked);
  - typical Bluetooth `outputLatency` values;
  - whether each browser's `decodeAudioData` trims LAME priming. Measure it (rule 16).
