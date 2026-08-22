# Gravshift — one-shot browser game brief

Build **Gravshift**, a compact physics platformer in one standalone `index.html` plus `README.md`. It must play offline straight from `file://` in current desktop Chrome, Firefox, Safari, or Edge. Use inline HTML/CSS/JavaScript and your own canvas/SVG/DOM art only; no dependencies, imports, fetches, CDNs, external media, or build step.

## Core fantasy
The player crosses a small orbital test chamber by changing gravity. The game must have a complete loop: title/instructions, several escalating rooms, hazards/checkpoints, final exit, success screen, failure/retry, and clear return to play.

## Mechanics and controls
- Arrow keys or A/D move; W/Up jumps relative to current gravity; G flips gravity between floor and ceiling. Keep movement responsive with acceleration/deceleration, collision resolution, coyote time or input buffering, and a fixed timestep or otherwise stable update model.
- Create at least four distinct, hand-authored rooms/sections. Require gravity reversal in at least three. Include stationary hazards, moving hazards or platforms, collectibles/energy cells, checkpoints, and a final locked exit that opens only after the room goals are met.
- Death respawns at the most recent checkpoint without corrupting room state. R restarts the current room; Enter starts/restarts after title/end screens; P/Escape pauses. Show current room, collected cells, deaths, and controls.
- Keyboard-only completion is required. Focus must not become trapped; provide labelled buttons for start, reset, and help as a fallback.

## Scope and quality floor
Use original geometric art with a crisp dark-green laboratory style, clear gravity direction indicators, readable player/hazard contrast, and no requirement for pointer input. The playable canvas/area should fit an ordinary 1280×720 viewport and adapt at 390 px wide. Use deterministic room layouts and stable motion—not random procedural levels. Protect against tunnelling through thin floors, double flips from one press, repeated victory triggers, and updates running while paused or ended.

## Read-only verification snapshot
Expose `window.__oneshotSnapshot()` for browser automation. It returns a fresh JSON-serializable object with `schema: "oneshot.playable/v1"` plus phase, room, gravity direction, pause state, player position/velocity, active checkpoint, collected cells, and death count. It accepts no arguments, must not mutate the game, and must not return live internal objects or expose control methods. Document the fields in `README.md`; this diagnostic surface supplements, rather than replaces, an actual keyboard playthrough.

## Required evidence in README
- Static evidence: no external URL/network use and successful `file://` boot.
- Deterministic evidence: list room goals, checkpoint positions, gravity-dependent obstacle in each relevant room, and the fixed update approach; confirm snapshot output agrees with visible room, gravity, checkpoint, and death/recovery states.
- Manual evidence: keyboard walkthrough exercises move/jump/flip, a death/checkpoint recovery, pause, and final exit.
- Visual evidence: capture or describe a view with gravity direction, room HUD, obstacle, and player readable together.

Do not ask for more input. Iterate and repair yourself. Deliver only `index.html` and `README.md`; evidence must describe checks actually performed.
