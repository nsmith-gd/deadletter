// A simulated first-time player for Dead Letter, DL-01 to DL-05. It runs inside the page, one call per game step
// (60 Hz of game time), and drives the same input object the keyboard does. Everything it does is a real action in the
// game; on top of that, a player model adds the time a person spends looking, reading, thinking and trying the wrong
// thing first. Each run draws its own player (skill, curiosity) from a seed.
window.__startBot = function (seed, opts = {}) {
  const D = window.__dl01, G = D.game, I = D.input;
  // --- random numbers ---------------------------------------------------------------------------------------------
  let a = seed >>> 0;
  const R = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const gauss = () => Math.sqrt(-2 * Math.log(1 - R())) * Math.cos(2 * Math.PI * R());
  const U = (lo, hi) => lo + (hi - lo) * R();
  const LN = (median, sigma) => median * Math.exp(sigma * gauss());
  const chance = (p) => R() < p;
  // --- the player ---------------------------------------------------------------------------------------------------
  const P = { skill: opts.skill ?? U(0, 1), curious: opts.curious ?? U(0, 1) };
  const slow = 1.45 - 0.9 * P.skill;                                   // 0.55 (quick) to 1.45 (slow) on thinking
  const think = (m) => (opts.mechanical ? 0 : LN(m * slow, 0.7));        // working out what to do next (median m for an average player)
  const look = (m) => (opts.mechanical ? 0 : LN(m * (0.6 + 0.8 * P.curious), 0.45));   // taking in a new space
  const react = () => (opts.mechanical ? 0.12 : LN(0.35 + 0.45 * slow, 0.35));          // noticing he has stopped
  const mistakes = !opts.mechanical;
  const out = { seed, player: { skill: +P.skill.toFixed(2), curious: +P.curious.toFixed(2) }, marks: {}, events: [], done: false, error: null };
  const mark = (k) => { if (out.marks[k] === undefined) out.marks[k] = +G.clock.toFixed(2); };
  const note = (s) => out.events.push(`${(G.clock - (out.marks.play ?? G.clock)).toFixed(1)} ${s}`);
  // --- input --------------------------------------------------------------------------------------------------------
  let jumpUp = 0;
  const move = (dir) => { I.right = dir > 0; I.left = dir < 0; };
  const jump = () => { I.jumpPressed = true; I.jumpHeld = true; jumpUp = 8; };
  const use = () => { I.usePressed = true; };
  // --- coroutines ---------------------------------------------------------------------------------------------------
  function* wait(sec) { const t = G.clock + sec; while (G.clock < t) yield; }
  function* until(pred, max, label) { const t = G.clock + max; while (!pred()) { if (G.clock > t) throw new Error('stuck: ' + label + ' x=' + G.x.toFixed(2)); yield; } }
  // Walk one way until pred; hop when he has stood still against something for a reaction time.
  function* walk(dir, pred, label, o = {}) {
    let last = G.x, still = 0, r = react(); const t0 = G.clock;
    try {
      while (!pred()) {
        if (G.clock - t0 > (o.max ?? 240)) throw new Error('stuck walking: ' + label + ' x=' + G.x.toFixed(2));
        move(G.act && !o.keepHolding ? 0 : dir);
        const moved = Math.abs(G.x - last) > 0.0008; last = G.x;
        if (!moved && G.grounded && !G.mantle && !G.act && !G.riding) still += 1 / 60; else still = 0;
        if (o.stall && still > o.stall) return 'stalled';
        if (o.hop !== false && still > r) { jump(); still = 0; r = react(); }
        yield;
      }
    } finally { move(0); }
    return 'arrived';
  }
  function* goTo(x, label, o) { const d = Math.sign(x - G.x) || 1; yield* walk(d, () => (d > 0 ? G.x >= x : G.x <= x), label, o); }
  // Walk toward x until the game offers this interaction, then press Use until it starts.
  function* useAt(kinds, x, started, label) {
    const ok = () => kinds.includes(D.near());
    if (!ok()) { const d = Math.sign(x - G.x) || 1; yield* walk(d, () => ok() || (d > 0 ? G.x >= x + 0.4 : G.x <= x - 0.4), label); }
    if (!ok()) { const d = Math.sign(x - G.x) || 1; yield* walk(d, ok, label + ' (back)', { max: 30 }); }
    for (let k = 0; k < 12; k++) {
      yield* wait(react() * 0.5);
      use(); yield; yield;
      const t = G.clock + 1.2; while (G.clock < t && !started()) yield;
      if (started()) return;
    }
    throw new Error('use failed: ' + label + ' near=' + D.near());
  }

  // Walking about a room while working it out: to somewhere else in it and back.
  function* wander(lo, hi, p) {
    if (!mistakes || !chance(p)) return;
    const x = U(lo, hi), back = G.x; note('wanders to ' + x.toFixed(1));
    try { yield* goTo(x, 'wander', { max: 25 }); yield* wait(think(2)); yield* goTo(back, 'wander back', { max: 25 }); } catch (e) { /* got as far as he got */ }
  }
  // --- the scenes ---------------------------------------------------------------------------------------------------
  function* opening() {
    mark('opening');
    yield* until(() => G.mode === 'play', 120, 'opening');
    mark('play'); mark('DL-01');
  }

  function* dl01() {
    yield* wait(think(3));                                            // getting the feel of the controls
    if (chance(0.15 + 0.2 * (1 - P.skill))) { note('tries left first'); yield* walk(-1, () => G.x < 0.75, 'left first'); yield* wait(think(1)); }
    if (chance(0.3 + 0.45 * P.curious)) {                              // the cord lamp, optional
      note('pulls the cord'); yield* useAt(['cord'], 0.59, () => G.act && G.act.kind === 'cord', 'cord');
      yield* until(() => !G.act, 20, 'cord done'); yield* wait(look(1.5));
    }
    // The shutter: he crouches under it and finds it latched.
    yield* walk(1, () => G.x >= 2.98, 'to the shutter', { stall: 1.2 });
    if (mistakes && chance(0.7 - 0.45 * P.skill)) {
      note('pushes at the shutter');
      try { yield* walk(1, () => false, 'push', { stall: 1.5 + R() * 2, hop: false, max: 8 }); } catch (e) { /* pushed a while */ }
    }
    yield* wait(think(8));
    yield* useAt(['latch'], 3.0, () => G.act && G.act.kind === 'latch', 'latch');
    yield* until(() => G.released && !G.act, 30, 'latch done'); note('shutter up');
    yield* wait(look(1.2));
    // Over the conveyor, the crate and the trench to the hall.
    yield* walk(1, () => G.x > 8.2, 'to the hall');
    mark('hall'); yield* wait(look(3.0));
    // The crank. A first-timer often walks to the door first.
    if (mistakes && chance(0.75 - 0.5 * P.skill)) {
      note('tries the door');
      try { yield* walk(1, () => false, 'to the door', { stall: 1.0 + R(), hop: false, max: 30 }); } catch (e) { /* walked a while */ }
      yield* wait(think(10));
    }
    else yield* wait(think(6));
    yield* useAt(['crank'], 9.62, () => G.act && G.act.kind === 'crank', 'crank');
    yield* until(() => G.doorOpen >= 1 && !G.act, 60, 'door open'); note('door open');
    yield* wait(look(1.0));
    yield* walk(1, () => G.region === 2, 'through the door');
    mark('DL-02');
  }

  function* dl02() {
    yield* until(() => !G.transit, 60, 'passage');
    yield* wait(look(2.5));
    // The plate: stand on it, see the gate rise, walk for the gate, and it drops.
    const tries = mistakes ? (chance(0.85 - 0.3 * P.skill) ? (chance(0.45) ? 2 : 1) : 0) : 0;
    for (let k = 0; k < tries; k++) {
      note('stands on the plate');
      yield* walk(1, () => G.x > 16.1, 'to the plate');
      yield* until(() => G.gate.y > 1.15, 20, 'gate up'); yield* wait(think(1.2));
      yield* walk(1, () => G.x > 16.9 || G.gate.y < 0.5, 'for the gate');
      yield* wait(1.2 + think(3)); yield* goTo(15.6, 'back off');
    }
    yield* wander(12.6, 15.4, 0.5 - 0.3 * P.skill);
    yield* wait(think(tries ? 20 : 14));
    // The weight onto the trolley, the trolley onto the plate.
    yield* useAt(['lift'], 12.7, () => G.act && G.act.kind === 'lift', 'lift');
    yield* until(() => G.hold === 'weight', 20, 'carrying'); note('carries the weight');
    yield* wait(think(6));
    yield* walk(1, () => G.x >= G.trolley.x - 0.42, 'to the trolley', { stall: 0.3, hop: false });
    for (let k = 0; k < 8 && !(G.act && G.act.kind === 'setdown'); k++) {
      use(); yield; yield; yield* wait(0.3);
      if (!(G.act && G.act.kind === 'setdown')) { move(1); yield* wait(0.08); move(0); }
    }
    yield* until(() => G.weight.state === 'trolley' && !G.act, 20, 'weight on trolley'); note('weight on the trolley');
    yield* wait(think(8));
    yield* useAt(['grabL'], G.trolley.x - 0.62, () => G.hold === 'trolley', 'grab');
    yield* walk(1, () => G.trolley.x > 16.1, 'push to the plate', { hop: false, keepHolding: true });
    use(); yield* until(() => !G.hold, 10, 'let go');
    yield* until(() => G.revealed, 30, 'revealed'); note('racks light');
    yield* until(() => !G.act, 30, 'reveal act');
    yield* wait(look(3.0));
    yield* walk(1, () => G.x > 18.0, 'over the trolley, through the gate');
    // The racks and the couriers: the realisation plays as he walks in; then on to the scanner.
    if (chance(0.3 + 0.5 * P.curious)) { yield* walk(1, () => G.x > 20.5, 'among the couriers'); note('looks at the couriers'); yield* wait(look(3)); }
    yield* walk(1, () => G.region === 3, 'to the scanner corridor', { max: 300 });
    mark('DL-03');
  }

  function* dl03() {
    yield* walk(1, () => G.scan.phase !== 'idle', 'to the scanner');
    yield* until(() => G.scan.phase === 'reveal', 60, 'refusal');
    yield* wait(look(2.5));
    try { yield* walk(1, () => false, 'slow walk', { max: U(1, 4), hop: false }); } catch (e) { /* walked for a while */ }
    yield* until(() => G.scan.phase === 'done', 90, 'label check');
    yield* wait(look(2.0));
    // Many first-timers ride a carrier to see where it goes: into the pile, and back at the scanner.
    if (mistakes && chance(0.35 + 0.25 * P.curious + 0.15 * (1 - P.skill))) {
      note('rides a carrier to the chute');
      yield* goTo(G.x < 31.0 ? 30.9 : 31.1, 'to the dock');
      yield* until(() => D.carriers().some((c) => c.state === 'dock'), 40, 'docked');
      yield* wait(react());
      for (let k = 0; k < 30 && !G.riding; k++) { jump(); yield* wait(0.4); }
      yield* until(() => G.act && G.act.kind === 'fall', 60, 'tipped');
      yield* until(() => G.mode === 'play' && !G.act && !G.riding && G.y > -0.1 && Math.abs(G.x - 30.3) < 0.05, 30, 'respawned');
      mark('DL-03 respawn'); note('respawned at the scanner'); yield* wait(think(8));
    }
    // The return line: work out the levers.
    yield* wander(30.0, 35.8, 0.6 - 0.3 * P.skill);
    yield* wait(think(15));
    let triedLocked = false, triedNoStart = false;
    for (let guard = 0; guard < 12 && !(G.route === 'exit' && G.belt.running); guard++) {
      if (G.belt.running && G.route !== 'exit') {
        if (mistakes && !triedLocked && chance(0.75 - 0.3 * P.skill)) {
          triedLocked = true; note('tries the points: locked');
          yield* useAt(['leverPoints'], 34.25, () => G.act && G.act.kind === 'lever', 'points (locked)');
          yield* until(() => !G.act, 20, 'locked'); yield* wait(think(10));
        }
        yield* useAt(['leverStop'], 32.9, () => G.act && G.act.kind === 'lever', 'stop');
        yield* until(() => !G.act, 20, 'stopped'); note('belt stopped'); yield* wait(think(4));
      } else if (!G.belt.running && G.route !== 'exit') {
        yield* useAt(['leverPoints'], 34.25, () => G.act && G.act.kind === 'lever', 'points');
        yield* until(() => !G.act, 20, 'thrown'); note('points thrown'); yield* wait(look(2.5));   // the route shot
      } else if (!G.belt.running && G.route === 'exit') {
        if (mistakes && !triedNoStart && chance(0.4 - 0.25 * P.skill)) {
          triedNoStart = true; note('waits at the dock with the belt stopped');
          yield* goTo(31.1, 'dock'); yield* wait(U(5, 10)); yield* wait(think(6));
        }
        yield* useAt(['leverStop'], 32.9, () => G.act && G.act.kind === 'lever', 'start');
        yield* until(() => !G.act, 20, 'started'); note('belt started');
      }
      yield;
    }
    yield* wait(think(1.5));
    yield* goTo(G.x < 31.0 ? 30.9 : 31.1, 'to the dock 2');
    yield* until(() => D.carriers().some((c) => c.state === 'dock'), 40, 'docked 2');
    yield* wait(react());
    for (let k = 0; k < 30 && !G.riding; k++) { if (D.near() === 'board') use(); else jump(); yield* wait(0.4); }
    note('rides up the ramp');
    yield* until(() => G.upper && !G.riding && !G.act, 60, 'landed');
    yield* wait(look(1.5));
    // The gallery: the desk, the stopped clock, the day board.
    yield* walk(1, () => G.x > 42.6, 'to the desk');
    if (chance(0.35 + 0.5 * P.curious)) { note('reads the desk and the board'); yield* wait(look(4)); yield* walk(1, () => G.x > 44.6, 'board'); yield* wait(look(3)); }
    yield* walk(1, () => G.region === 4, 'to the doorway');
    mark('DL-04');
  }

  function* dl04() {
    yield* wait(look(2.5));
    if (chance(0.3 + 0.5 * P.curious)) { note('reads the lift sign'); yield* wait(look(3.5)); }
    yield* wander(48.6, 52.6, 0.4 - 0.25 * P.skill);
    yield* wait(think(12));
    // The trolley onto the pan.
    yield* useAt(['grab4L'], G.trolley4.x - 0.7, () => G.hold === 'trolley4', 'grab trolley');
    yield* walk(1, () => G.trolley4.x >= 51.45, 'push onto the pan', { hop: false, keepHolding: true, max: 120 });
    yield* until(() => G.plat.h >= 0.999, 30, 'at the landing'); note('platform at the landing');
    yield* wait(look(1.5));
    use(); yield* until(() => !G.hold, 10, 'let go');
    // Onto the platform: it drops under him.
    yield* walk(1, () => G.act && G.act.kind === 'teeter', 'onto the platform', { max: 60 });
    note('teeters'); yield* until(() => !G.act, 20, 'teeter done');
    yield* wait(think(10));
    yield* useAt(['pawl'], 52.45, () => G.plat.latched || (G.act && G.act.kind === 'pawl'), 'pawl');
    yield* until(() => G.plat.latched, 20, 'latched'); note('pawl set');
    yield* until(() => !G.act, 20, 'proud');
    // Across, past the trolley (he pats it), to the far landing; the belt's warning.
    yield* walk(1, () => G.x > 56.1, 'to the far landing', { max: 90 });
    yield* until(() => G.belt4.state === 'run' && D.crates().length > 0, 40, 'belt running');
    yield* wait(look(1.5) + think(4));
    // The crossing: hop or climb whatever comes down; timing varies with skill.
    note('starts the crossing');
    const t0 = G.clock; let hops = 0, carried = 0, lastX = G.x, trigger = 0, stuck = 0, stuckAt = react(), lastStep = G.x;
    move(1);
    try {
      while (G.x < 64.8) {
        if (G.clock - t0 > 400) throw new Error('stuck on the belt x=' + G.x.toFixed(2));
        move(G.act ? 0 : 1);
        const c = D.crates().filter((k) => k.state === 'belt' && k.x > G.x).sort((p, q) => p.x - q.x)[0];
        const ahead = c ? c.x - G.x : 9;
        if (G.grounded && !G.mantle && !G.act) {
          if (!trigger) trigger = 0.62 + (mistakes ? gauss() * 0.14 * (1.3 - P.skill) : 0);
          if (ahead < trigger) { jump(); hops++; trigger = 0; stuck = 0; }
          // Pushed back against a crate: he jumps once he notices.
          stuck = G.x < lastStep + 0.002 ? stuck + 1 / 60 : 0;
          if (stuck > stuckAt) { jump(); hops++; stuck = 0; stuckAt = react(); }
        }
        lastStep = G.x;
        if (G.x < lastX - 0.6) { carried++; lastX = G.x; } else if (G.x > lastX) lastX = G.x;
        yield;
      }
    } finally { move(0); }
    note(`crossed (${hops} hops, carried back ${carried} times)`);
    // The tunnel and the refuge: the look back, the hopscotch, the awe are his own.
    yield* walk(1, () => G.dl4.awed && !G.act, 'through the tunnel', { max: 200 });
    yield* wait(look(4.0));                                           // taking in the city
    yield* walk(1, () => G.region === 5, 'to the stair', { max: 120 });
    mark('DL-05');
  }

  function* dl05() {
    yield* wait(look(2.0));
    yield* walk(1, () => G.checkpoint === 'ringc', 'under the seal');
    if (chance(0.3 + 0.5 * P.curious)) { note('looks along ring C'); yield* wait(look(2.5)); }
    yield* walk(1, () => G.dl5.knocked && !G.act && G.x > 88.3, 'to C-114', { max: 120 });
    yield* wait(look(2.0));
    yield* walk(1, () => G.dl5.toyUp && !G.act, 'past the bed', { max: 120 });
    if (chance(0.3 + 0.5 * P.curious)) { note('looks at the photograph'); yield* walk(1, () => G.x > 93.2, 'photo'); yield* wait(look(3.5)); }
    // The desk: find that it moves.
    if (mistakes && chance(0.6 - 0.35 * P.skill)) {
      note('walks past the desk to the back door');
      try { yield* walk(1, () => G.x > 95.3, 'to the back door', { hop: false, max: 8 }); } catch (e) { /* blocked */ }
      yield* wait(think(8));
    }
    yield* wait(think(12));
    yield* useAt(['grabDeskL'], G.desk5.x - 0.9, () => G.hold === 'desk', 'grab desk');
    yield* walk(-1, () => G.dl5.revealed, 'drag the desk', { hop: false, keepHolding: true, max: 60 });
    note('desk clear');
    yield* wait(0.8); use(); yield* until(() => !G.hold, 10, 'release');
    yield* wait(look(3.5));                                           // the marks and the tree
    yield* wait(think(5));
    yield* useAt(['present'], 94.7, () => G.act && G.act.kind === 'present', 'terminal');
    yield* until(() => G.dl5.forwarded && !G.act, 30, 'forwarded'); note('forwarded');
    yield* wait(look(2.5));
    yield* walk(1, () => G.ended, 'out the back', { max: 120 });
    mark('end');
  }

  const script = (function* () { yield* opening(); yield* dl01(); yield* dl02(); yield* dl03(); yield* dl04(); yield* dl05(); })();
  // Scene splits by where he is, as the game draws them.
  window.__sim = {
    steps: opts.steps ?? 8, frames: 0, render: false, out,
    bot() {
      if (jumpUp > 0 && --jumpUp === 0) I.jumpHeld = false;
      if (out.done) return;
      if (G.mode === 'play' && G.checkpoint) mark('cp ' + G.checkpoint);
      try {
        const r = script.next();
        if (r.done) out.done = true;
      } catch (e) { out.error = e.message; out.done = true; move(0); }
    },
  };
  return out;
};
