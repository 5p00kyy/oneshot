# Neon Courier — one-shot browser game brief

Build a complete **top-down delivery-and-pursuit game** called **Neon Courier**. Deliver exactly one self-contained `index.html` plus a short `README.md`. It must run offline when opened directly with `file://` in current desktop Chrome, Firefox, Safari, or Edge. Use only inline HTML, CSS, JavaScript, SVG/canvas primitives, generated sound if desired, and browser APIs that work from `file://`; do not use a build step, external assets, imports, fonts, fetches, CDNs, or network requests.

## Player promise
The player pilots a courier through a compact neon city. Collect a parcel at a marked depot, deliver it to a marked destination before its timer expires, then chain deliveries while patrol drones pursue. The game needs a readable start, escalating middle, and explicit win/lose/restart end states—not a movement toy.

## Required loop and controls
- **Move** with WASD and arrow keys. Movement is smooth but bounded by walls/buildings; diagonal input must not be faster than cardinal movement.
- **Sprint/dash** with Space: a short cooldown, visible meter, and meaningful escape option.
- Pick up only at the current depot and deliver only to the current destination. Show package state, delivery count, time remaining, score, and a compact objective label.
- Spawn at least three deterministic delivery routes and cycle them in a fixed order. Each successful delivery increases patrol pressure (more drones, faster drone, or tighter timer) without becoming unwinnable in a normal run.
- Drones must visibly pursue the player, collide with buildings sensibly (or use a clearly explained grid/path rule), and cost one of three visible integrity pips on contact with a brief invulnerability window. At zero integrity, show a loss screen.
- After five deliveries, show a win screen with score and elapsed time. Enter starts/restarts; R resets immediately. Include a pause toggle (P or Escape).
- Provide focusable, labelled controls and a visible keyboard help panel. No mouse is required to complete a run.

## Design and robustness
Use an original high-contrast neon-on-dark visual system, readable at 1280×720 and still usable at 390 px wide. Render the city, player, parcels, destinations, drones, particles, and UI yourself. Use a seeded or fixed deterministic layout; do not use hidden randomness that makes verification ambiguous. Avoid fatal errors if localStorage is unavailable. Reset must clear transient state cleanly.

## Read-only verification snapshot
Expose `window.__oneshotSnapshot()` for browser automation. It returns a fresh JSON-serializable object with `schema: "oneshot.playable/v1"` plus current phase, route index, delivery count, score, integrity, pause state, player position, current depot/destination IDs, remaining time, and drone positions/states. It accepts no arguments, must not mutate the game, and must not return live internal objects or expose control methods. Document the fields in `README.md`; this diagnostic surface supplements, rather than replaces, an actual keyboard playthrough.

## Acceptance checks and evidence
Before handoff, test from `file://` and record honest evidence in `README.md`:
1. Static/offline check: no external URLs, imports, fetch/XHR/WebSocket, or console errors at boot.
2. Manual play: keyboard-only pickup, delivery, dash, pause, damage, and restart were exercised.
3. Deterministic check: list the five route pairs and explain the fixed patrol escalation; a fresh restart reproduces the first route, and snapshot output agrees with the visible initial and post-delivery states.
4. Visual check: capture or describe a desktop view showing the objective, map, drones, and integrity HUD.

Do internal iteration and repairs yourself. Do not ask for clarification. Finish with only the stated files and a concise README covering controls, rules, architecture, and checks actually run.
