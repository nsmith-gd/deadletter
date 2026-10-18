// A simulated first-time player for Dead Letter's Chapter 1, DL-01 to DL-09. It runs inside the page, one call per game step
// (60 Hz of game time), and drives the same input object the keyboard does. Everything it does is a real action in the
// game; on top of that, a player model adds the time a person spends looking, reading, thinking and trying the wrong
// thing first. Each run draws its own player (skill, curiosity) from a seed.
window.__startBot = function (seed, opts = {}) {
  const D = window.__dl01, G = D.game, I = D.input;
  const { OFF2, OFF3, OFF4 } = D.offsets;                              // where each stretch of the level now starts
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
  function* useAt(kinds, x, started, label, o = {}) {
    const ok = () => kinds.includes(D.near());
    if (!ok()) { const d = Math.sign(x - G.x) || 1; yield* walk(d, () => ok() || (d > 0 ? G.x >= x + 0.4 : G.x <= x - 0.4), label, o); }
    if (!ok()) { const d = Math.sign(x - G.x) || 1; yield* walk(d, ok, label + ' (back)', { max: 30, ...o }); }
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
  // --- the scenes (Chapter 1, nine scenes) -----------------------------------------------------------------------
  const K = D.k, C = () => G.ch1;
  const actIs = (k) => () => !!(G.act && G.act.kind === k);
  const free = () => !G.act && !G.mantle;
  function* settle(max = 30) { yield* until(() => !G.act && !G.mantle && G.grounded, max, 'settle'); }
  // An optional letter: pick it up if he's curious, and post it if a slot is near.
  function* letter(id, x, p) {
    if (!chance(p) || !/floor|slot/.test(D.letters[id])) return;
    note('picks up the ' + id + ' letter');
    try { yield* useAt(['pickLetter:' + id], x, actIs('pickLetter'), 'letter ' + id); yield* settle(); } catch (e) { note('letter missed: ' + e.message); }
  }
  function* post(slot, x, p) {
    if (!(D.letters.held > 0) || !chance(p)) return;
    note('posts a letter at slot ' + slot);
    try { yield* useAt(['postLetter:' + slot], x, actIs('postLetter'), 'slot ' + slot); yield* settle(); } catch (e) { note('post missed: ' + e.message); }
  }

  function* opening() {
    mark('opening');
    yield* until(() => G.mode === 'play', 120, 'opening');
    mark('play');
  }

  // DL-01 The Wake: the latch, the step, the cart into the trench, the crank.
  function* wake() {
    yield* wait(think(3));
    if (chance(0.15 + 0.2 * (1 - P.skill))) { note('tries left first'); yield* walk(-1, () => G.x < 0.75, 'left first'); yield* wait(think(1)); }
    if (chance(0.3 + 0.45 * P.curious)) {
      note('pulls the cord'); yield* useAt(['cord'], 0.59, actIs('cord'), 'cord');
      yield* until(() => !G.act, 20, 'cord done'); yield* wait(look(1.5));
    }
    if (chance(0.2 + 0.5 * P.curious)) { note('weighs himself'); yield* goTo(2.2, 'scale'); yield* wait(look(2.0)); }
    yield* walk(1, () => G.x >= 2.98, 'to the shutter', { stall: 1.2 });
    if (mistakes && chance(0.7 - 0.45 * P.skill)) {
      note('pushes at the shutter');
      try { yield* walk(1, () => false, 'push', { stall: 1.5 + R() * 2, hop: false, max: 8 }); } catch (e) { /* pushed a while */ }
    }
    yield* wait(think(8));
    yield* useAt(['latch'], 3.0, actIs('latch'), 'latch');
    yield* until(() => G.released && !G.act, 30, 'latch done'); note('shutter up');
    yield* wait(look(1.2));
    // The trench: try to jump it from the cart, fall in, and be back at the shutter.
    yield* walk(1, () => G.x > 4.5, 'over the step');
    if (mistakes && chance(0.6 - 0.35 * P.skill)) {
      note('tries to jump the trench');
      yield* walk(1, () => G.y > K.CART1.h - 0.05 && G.x > C().cart.x + K.CART1.half - 0.3, 'onto the cart', { max: 30 });
      jump(); move(1); yield* wait(0.6); move(0);
      yield* until(() => (G.act && G.act.kind === 'trenchStuck') || G.x > K.PIT.x1 + 0.1, 10, 'the jump');
      if (G.act && G.act.kind === 'trenchStuck') { yield* until(() => G.mode === 'play' && !G.act && G.x < 3.5, 20, 'respawned'); note('back at the shutter'); yield* wait(think(8)); }
    } else yield* wait(think(6));
    if (C().cart.state === 'free') {
      yield* useAt(['grabPush:cart'], C().cart.x - K.CART1.gap, actIs('grabPush'), 'cart', { hop: false });
      yield* until(() => G.hold === 'push', 10, 'grip cart');
      yield* walk(1, () => C().cart.state !== 'free', 'push the cart', { hop: false, keepHolding: true, max: 30 });
      note('cart in the trench'); yield* until(() => C().cart.state === 'bridge', 5, 'bridge'); yield* wait(look(1.0));
    }
    yield* walk(1, () => G.x > 8.6, 'to the hall');
    yield* wait(look(3.0));
    if (mistakes && chance(0.75 - 0.5 * P.skill)) {
      note('tries the door');
      try { yield* walk(1, () => false, 'to the door', { stall: 1.0 + R(), hop: false, max: 30 }); } catch (e) { /* walked a while */ }
      yield* wait(think(10));
    } else yield* wait(think(6));
    yield* useAt(['crank'], 9.62, actIs('crank'), 'crank');
    yield* until(() => G.doorOpen >= 1 && !G.act, 60, 'door open'); note('door open');
    yield* wait(look(1.0));
    yield* walk(1, () => G.region === 2, 'through the door');
  }

  // DL-02 The Sorting Hall: the tube's letter and the slot; the box, the table, the gantry.
  function* sortingHall() {
    yield* until(() => !G.transit, 60, 'passage');
    yield* wait(look(2.5));
    yield* walk(1, () => G.x > K.SH.tubeX + 0.1, 'past the tube');
    yield* until(() => D.letters.tube !== 'falling' && D.letters.tube !== 'cup', 3, 'tube letter');
    yield* wait(look(1.2));
    yield* letter('tube', K.SH.tubeX, 0.55 + 0.4 * P.curious);
    yield* post(2, K.SH.slotX, 0.75);
    yield* wait(look(1.5));
    // The table is too high; the floor is closed. Try the jump, then the box.
    if (mistakes && chance(0.8 - 0.35 * P.skill)) {
      note('tries to climb the table');
      try { yield* walk(1, () => G.x > K.SH.table.x0 + 0.3 && G.y > 0.5, 'at the table', { max: 6 + 6 * R() }); } catch (e) { /* bounced off it */ }
      yield* wait(think(9));
    } else yield* wait(think(5));
    if (G.y > 0.5) { note('is on the table already'); }
    else {
      const box = C().box;
      yield* useAt(['liftItem:box'], box.x, actIs('liftItem'), 'box');
      yield* until(() => G.hold === 'item', 10, 'carrying');
      yield* walk(1, () => G.x >= K.SH.table.x0 - 0.22 - K.GRIP_FWD, 'to the table', { hop: false, max: 30 });
      use(); yield* until(() => G.act && G.act.kind === 'setdownItem', 3, 'set down'); yield* settle();
      note('box at the table');
    }
    yield* wait(think(2));
    yield* walk(1, () => G.x > K.SH.x1 + 0.6 && G.y < 0.05, 'up and over', { max: 60 });
  }

  // DL-03 The Weight of the Job: as before.
  function* weightRoom() {
    const plateX = OFF2 + 16.1;
    yield* wait(look(2.5));
    const tries = mistakes ? (chance(0.85 - 0.3 * P.skill) ? (chance(0.45) ? 2 : 1) : 0) : 0;
    for (let k = 0; k < tries; k++) {
      note('stands on the plate');
      yield* walk(1, () => G.x > plateX, 'to the plate');
      yield* until(() => G.gate.y > 1.15, 20, 'gate up'); yield* wait(think(1.2));
      yield* walk(1, () => G.x > OFF2 + 16.9 || G.gate.y < 0.5, 'for the gate');
      yield* wait(1.2 + think(3)); yield* goTo(OFF2 + 15.6, 'back off');
    }
    yield* wander(OFF2 + 12.6, OFF2 + 15.4, 0.5 - 0.3 * P.skill);
    yield* wait(think(tries ? 20 : 14));
    yield* useAt(['lift'], OFF2 + 12.7, actIs('lift'), 'lift');
    yield* until(() => G.hold === 'weight', 20, 'carrying');
    yield* wait(think(6));
    yield* walk(1, () => G.x >= G.trolley.x - 0.42, 'to the trolley', { stall: 0.3, hop: false });
    for (let k = 0; k < 8 && !(G.act && G.act.kind === 'setdown'); k++) {
      use(); yield; yield; yield* wait(0.3);
      if (!(G.act && G.act.kind === 'setdown')) { move(1); yield* wait(0.08); move(0); }
    }
    yield* until(() => G.weight.state === 'trolley' && !G.act, 20, 'weight on trolley'); note('weight on the trolley');
    yield* wait(think(8));
    yield* useAt(['grabL'], G.trolley.x - 0.62, () => G.hold === 'trolley', 'grab');
    yield* walk(1, () => G.trolley.x > plateX, 'push to the plate', { hop: false, keepHolding: true });
    use(); yield* until(() => !G.hold, 10, 'let go');
    yield* until(() => G.revealed, 30, 'revealed'); note('racks light');
    yield* until(() => !G.act, 30, 'reveal act');
    yield* wait(look(3.0));
    yield* walk(1, () => G.x > K.GATE_X + 0.4, 'over the trolley, through the gate');
  }

  // DL-04 The Racks: the bay wants a courier.
  function* racks() {
    if (chance(0.3 + 0.5 * P.curious)) { yield* walk(1, () => G.x > OFF2 + 20.5, 'among the couriers'); note('looks at the couriers'); yield* wait(look(3)); }
    yield* walk(1, () => G.x > K.RK.courierX + 0.6, 'to the fallen courier', { max: 120 });
    yield* wait(look(3.0));
    if (mistakes && chance(0.8 - 0.3 * P.skill)) {
      note('stands on the bay plate');
      yield* walk(1, () => G.x > K.RK.plate.x0 + 0.3, 'on the plate');
      yield* until(() => C().bayDoor > 0.6, 5, 'door opens'); yield* wait(think(1.5));
      try { yield* walk(1, () => false, 'for the door', { stall: 0.6, hop: false, max: 6 }); } catch (e) { /* the door shut */ }
      yield* wait(think(8));
      if (chance(0.45 - 0.25 * P.skill)) { note('goes back for the trolley'); try { yield* goTo(K.GATE_X + 1.0, 'back toward the trolley', { max: 40 }); } catch (e) { /* */ } yield* wait(think(6)); }
    } else yield* wait(think(6));
    yield* useAt(['grabPush:courier'], C().courier.x + K.RK.gap, actIs('grabPush'), 'courier', { hop: false });
    yield* until(() => G.hold === 'push', 10, 'grip courier');
    yield* walk(1, () => C().courier.state !== 'free', 'drag the courier', { hop: false, keepHolding: true, max: 40 });
    note('courier on the bay');
    yield* until(() => C().courier.state === 'seated' && free(), 30, 'the cradle');
    yield* settle(); yield* wait(look(3.5));
    yield* walk(1, () => G.region === 3, 'through the bay door', { max: 60 });
  }

  // DL-05 Return to Sender: the scanner, the pit, the levers (with a ride into the pile for many).
  function* returnToSender() {
    yield* walk(1, () => G.scan.phase !== 'idle', 'to the scanner');
    yield* until(() => G.scan.phase === 'reveal', 60, 'refusal');
    yield* wait(look(2.5));
    try { yield* walk(1, () => false, 'slow walk', { max: U(1, 4), hop: false }); } catch (e) { /* walked a while */ }
    yield* until(() => G.scan.phase === 'done', 90, 'label check');
    yield* wait(look(2.0));
    if (mistakes && chance(0.35 + 0.25 * P.curious + 0.15 * (1 - P.skill))) {
      note('rides a carrier to the chute');
      yield* goTo(G.x < K.DOCK_X ? K.DOCK_X - 0.1 : K.DOCK_X + 0.1, 'to the dock');
      yield* until(() => D.carriers().some((c) => c.state === 'dock'), 40, 'docked');
      yield* wait(react());
      for (let k = 0; k < 30 && !G.riding; k++) { jump(); yield* wait(0.4); }
      yield* until(() => G.act && G.act.kind === 'fall', 60, 'tipped');
      yield* until(() => G.mode === 'play' && !G.act && !G.riding && G.y > -0.1 && Math.abs(G.x - (OFF3 + 30.3)) < 0.05, 30, 'respawned');
      mark('DL-05 respawn'); note('respawned at the scanner'); yield* wait(think(8));
    }
    yield* wander(OFF3 + 30.0, OFF3 + 35.8, 0.6 - 0.3 * P.skill);
    yield* wait(think(15));
    let triedLocked = false;
    for (let guard = 0; guard < 12 && !(G.route === 'exit' && G.belt.running); guard++) {
      if (G.belt.running && G.route !== 'exit') {
        if (mistakes && !triedLocked && chance(0.75 - 0.3 * P.skill)) {
          triedLocked = true; note('tries the points: locked');
          yield* useAt(['leverPoints'], OFF3 + 34.25, actIs('lever'), 'points (locked)');
          yield* until(() => !G.act, 20, 'locked'); yield* wait(think(10));
        }
        yield* useAt(['leverStop'], OFF3 + 32.9, actIs('lever'), 'stop');
        yield* until(() => !G.act, 20, 'stopped'); note('belt stopped'); yield* wait(think(4));
      } else if (!G.belt.running && G.route !== 'exit') {
        yield* useAt(['leverPoints'], OFF3 + 34.25, actIs('lever'), 'points');
        yield* until(() => !G.act, 20, 'thrown'); note('points thrown'); yield* wait(look(2.5));
      } else if (!G.belt.running && G.route === 'exit') {
        yield* useAt(['leverStop'], OFF3 + 32.9, actIs('lever'), 'start');
        yield* until(() => !G.act, 20, 'started'); note('belt started');
      }
      yield;
    }
    yield* wait(think(1.5));
  }
  function* board() {
    yield* goTo(G.x < K.DOCK_X ? K.DOCK_X - 0.1 : K.DOCK_X + 0.1, 'to the dock');
    yield* until(() => D.carriers().some((c) => c.state === 'dock'), 40, 'docked');
    yield* wait(react());
    for (let k = 0; k < 30 && !G.riding; k++) { if (D.near() === 'board') use(); else jump(); yield* wait(0.4); }
    yield* until(() => G.upper && !G.riding && !G.act, 60, 'landed');
  }

  // DL-06 The Heap: the gallery gate. Most ride up first, find it shut, and slide back down.
  function* heap() {
    const loadFirst = !mistakes || chance(0.3 * P.skill);
    if (!loadFirst) {
      note('rides up first'); yield* board(); yield* wait(look(2.0));
      try { yield* walk(1, () => false, 'to the gate', { stall: 0.6, hop: false, max: 8 }); } catch (e) { /* */ }
      yield* wait(think(10));
      note('slides back down');
      yield* walk(-1, () => G.act && G.act.kind === 'slide', 'to the slide', { hop: false, max: 20 });
      yield* until(() => !G.act && !G.upper, 10, 'slid'); yield* wait(look(1.5) + think(6));
    }
    for (let attempt = 0; attempt < 4 && C().bucket < 1; attempt++) {
      const w = C().weights.find((q) => q.state === 'floor');
      if (!w) { yield* wait(2); continue; }
      yield* useAt(['liftItem:w' + C().weights.indexOf(w)], w.x, actIs('liftItem'), 'weight');
      yield* until(() => G.hold === 'item', 10, 'carrying');
      yield* walk(-1, () => Math.abs(G.x - K.DOCK_X) < 0.5, 'to the dock', { hop: false, max: 20 });
      yield* until(() => D.carriers().some((c) => c.state === 'dock'), 40, 'docked');
      use(); yield* until(() => G.act && G.act.kind === 'loadCarrier', 3, 'load');
      yield* settle(); note('weight in a carrier');
      yield* until(() => C().bucket >= 1 || !D.carriers().some((c) => c.load), 40, 'the delivery');
      yield* wait(look(2.0));
    }
    yield* wait(think(2));
    yield* board();
    yield* walk(1, () => G.x > K.HP.gateX + 0.5, 'through the gate', { max: 30 });
    yield* until(() => D.letters.heap !== 'fallingRail', 3, 'rail letter');
    yield* letter('heap', K.LETTERS[1].x, 0.45 + 0.45 * P.curious);
    yield* post(6, K.SLOTS[1].x, 0.7);
    if (chance(0.35 + 0.5 * P.curious)) { note('reads the desk and the board'); yield* wait(look(4)); yield* walk(1, () => G.x > OFF3 + 44.6, 'board'); yield* wait(look(3)); }
    yield* walk(1, () => G.region === 4, 'to the doorway', { max: 60 });
  }

  // DL-07 The Handbrake: trolley onto the pan, the teeter, the pawl; then the trolley across, and over the rail.
  function* handbrake() {
    yield* wait(look(2.5));
    if (chance(0.3 + 0.5 * P.curious)) { note('reads the lift sign'); yield* wait(look(3.5)); }
    yield* wander(OFF3 + 48.6, OFF3 + 52.6, 0.4 - 0.25 * P.skill);
    yield* wait(think(12));
    yield* useAt(['grab4L'], G.trolley4.x - K.PUSH_GAP4, () => G.hold === 'trolley4', 'grab trolley');
    yield* walk(1, () => G.trolley4.x >= OFF3 + 51.45, 'push onto the pan', { hop: false, keepHolding: true, max: 120 });
    yield* until(() => G.plat.h >= 0.999, 30, 'at the landing');
    yield* wait(look(1.5));
    use(); yield* until(() => !G.hold, 10, 'let go');
    yield* walk(1, () => G.act && G.act.kind === 'teeter', 'onto the platform', { max: 60 });
    note('teeters'); yield* until(() => !G.act, 20, 'teeter done');
    yield* wait(think(10));
    yield* useAt(['pawl'], K.PAWL_X, () => G.plat.latched || (G.act && G.act.kind === 'pawl'), 'pawl');
    yield* until(() => G.plat.latched, 20, 'latched'); note('pawl set');
    yield* until(() => !G.act, 20, 'proud');
    if (mistakes && chance(0.85 - 0.3 * P.skill)) {
      note('tries the rail');
      try { yield* walk(1, () => false, 'at the rail', { stall: 1.0, max: 25 }); } catch (e) { /* */ }
      yield* wait(think(12));
      yield* walk(-1, () => G.x < G.trolley4.x - K.PUSH_GAP4 + 0.1, 'back round the trolley', { max: 40 });
    }
    yield* useAt(['grab4L'], G.trolley4.x - K.PUSH_GAP4, () => G.hold === 'trolley4', 'grab trolley again');
    yield* walk(1, () => G.trolley4.x >= K.RAIL7.x0 - K.T4_HALF - 0.03, 'trolley to the rail', { hop: false, keepHolding: true, max: 60 });
    use(); yield* until(() => !G.hold, 10, 'let go at the rail');
    yield* wait(think(3));
    yield* walk(1, () => G.x > K.RAIL7.x1 + 0.3 && G.y < 1.65, 'over the rail', { max: 30 });
    yield* until(() => G.belt4.state === 'run' && D.crates().length > 0, 40, 'belt running');
    yield* wait(look(1.5) + think(4));
    note('starts the crossing');
    const t0 = G.clock; let hops = 0, trigger = 0, stuck = 0, stuckAt = react(), lastStep = G.x;
    move(1);
    try {
      while (G.x < K.CG.x0 - 0.1) {
        if (G.clock - t0 > 400) throw new Error('stuck on the belt x=' + G.x.toFixed(2));
        move(G.act ? 0 : 1);
        const c = D.crates().filter((k) => k.state === 'belt' && k.x > G.x).sort((p, q) => p.x - q.x)[0];
        const ahead = c ? c.x - G.x : 9;
        if (G.grounded && !G.mantle && !G.act) {
          if (!trigger) trigger = 0.62 + (mistakes ? gauss() * 0.14 * (1.3 - P.skill) : 0);
          if (ahead < trigger) { jump(); hops++; trigger = 0; stuck = 0; }
          stuck = G.x < lastStep + 0.002 ? stuck + 1 / 60 : 0;
          if (stuck > stuckAt) { jump(); hops++; stuck = 0; stuckAt = react(); }
        }
        lastStep = G.x;
        yield;
      }
    } finally { move(0); }
    note(`crossed (${hops} hops)`);
  }

  // DL-08 The Slipping Cage: three climbs, the cage, the pawl at the lit landing; then the tunnel and the city.
  function* cage() {
    yield* wait(look(2.0));
    yield* walk(1, () => G.act && G.act.kind === 'cage', 'into the cage', { max: 60 });
    note('in the cage');
    for (let tries = 0; tries < 6; tries++) {
      const cg = () => C().cage;
      if (mistakes && chance(0.3 * (1 - P.skill))) { yield* until(() => cg().phase === 'lower', 5, 'lowering'); use(); note('throws the pawl early'); }
      yield* until(() => cg().phase === 'stall' || cg().phase === 'crash' || cg().phase === 'caught', 20, 'the stall');
      if (cg().phase === 'stall') {
        yield* wait(opts.mechanical ? 0.1 : LN(0.45 + 0.4 * (1 - P.skill), 0.45));
        use();
      }
      yield* until(() => cg().phase === 'caught' || cg().phase === 'crash', 10, 'bite or crash');
      if (cg().phase === 'caught') { note('pawl bites at the landing'); break; }
      note('missed: the cage drops to the buffers');
      yield* until(() => cg().phase === 'top', 30, 'hauled back');
      yield* wait(think(3));
      yield* walk(1, () => G.act && G.act.kind === 'cage', 'back into the cage', { max: 20 });
    }
    yield* settle();
    yield* wait(look(1.0));
    yield* walk(1, () => G.dl4.awed && !G.act, 'through the tunnel', { max: 200 });
    yield* wait(look(4.0));
    yield* walk(1, () => G.region === 5, 'to the stair', { max: 120 });
  }

  // DL-09 The Child at the Address: the seal, the flood and the duct, C-114.
  function* childAtTheAddress() {
    yield* wait(look(2.0));
    yield* walk(1, () => G.checkpoint === 'ringc', 'under the seal');
    if (chance(0.3 + 0.5 * P.curious)) { note('looks along ring C'); yield* wait(look(2.5)); }
    if (mistakes && chance(0.7 - 0.3 * P.skill)) {
      note('hops the duct toward the water');
      yield* walk(1, () => G.act && G.act.kind === 'waterFlinch', 'to the water', { max: 20 });
      yield* settle(); yield* wait(think(9));
      yield* walk(-1, () => G.x < C().duct.x - K.DUCT9.gap + 0.05, 'back over the duct', { max: 20 });
    } else yield* wait(think(5));
    yield* useAt(['grabPush:duct'], C().duct.x - K.DUCT9.gap, actIs('grabPush'), 'duct', { hop: false });
    yield* until(() => G.hold === 'push', 10, 'grip duct');
    yield* walk(1, () => C().duct.state !== 'free', 'push the duct', { hop: false, keepHolding: true, max: 30 });
    yield* until(() => C().duct.state === 'bridge', 5, 'bridge'); note('duct bridges the flood');
    yield* letter('c110', K.LETTERS[2].x, 0.4 + 0.45 * P.curious);
    yield* post(9, K.SLOTS[2].x, 0.75);
    yield* walk(1, () => G.dl5.knocked && !G.act && G.x > OFF4 + 88.3, 'to C-114', { max: 120 });
    yield* wait(look(2.0));
    yield* walk(1, () => G.dl5.toyUp && !G.act, 'past the bed', { max: 120 });
    if (chance(0.3 + 0.5 * P.curious)) { note('looks at the photograph'); yield* walk(1, () => G.x > OFF4 + 93.2, 'photo'); yield* wait(look(3.5)); }
    if (mistakes && chance(0.6 - 0.35 * P.skill)) {
      note('walks past the desk to the back door');
      try { yield* walk(1, () => G.x > OFF4 + 95.3, 'to the back door', { hop: false, max: 8 }); } catch (e) { /* blocked */ }
      yield* wait(think(8));
    }
    yield* wait(think(12));
    yield* useAt(['grabDeskL'], G.desk5.x - 0.9, () => G.hold === 'desk', 'grab desk');
    yield* walk(-1, () => G.dl5.revealed, 'drag the desk', { hop: false, keepHolding: true, max: 60 });
    note('desk clear');
    yield* wait(0.8); use(); yield* until(() => !G.hold, 10, 'release');
    yield* wait(look(3.5));
    yield* wait(think(5));
    yield* useAt(['present'], OFF4 + 94.7, actIs('present'), 'terminal');
    yield* until(() => G.dl5.forwarded && !G.act, 30, 'forwarded'); note('forwarded');
    yield* wait(look(2.5));
    yield* walk(1, () => G.ended, 'out the back', { max: 120 });
    mark('end');
  }

  const script = (function* () {
    yield* opening(); yield* wake(); yield* sortingHall(); yield* weightRoom(); yield* racks();
    yield* returnToSender(); yield* heap(); yield* handbrake(); yield* cage(); yield* childAtTheAddress();
  })();
  // Scene splits by where he is, as the game draws them.
  window.__sim = {
    steps: opts.steps ?? 8, frames: 0, render: false, out,
    bot() {
      if (jumpUp > 0 && --jumpUp === 0) I.jumpHeld = false;
      if (out.done) return;
      if (G.mode === 'play' && G.checkpoint) mark('cp ' + G.checkpoint);
      if (G.mode === 'play' && out.marks.play !== undefined) mark(D.scene().slice(0, 5));
      try {
        const r = script.next();
        if (r.done) out.done = true;
      } catch (e) { out.error = e.message; out.done = true; move(0); }
    },
  };
  return out;
};
