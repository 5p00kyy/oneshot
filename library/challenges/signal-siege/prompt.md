# Signal Siege — one-shot browser game brief

Create **Signal Siege**, a complete tower-defence game in a single self-contained `index.html`, with a short `README.md`. It must work offline when opened from `file://` in current desktop Chrome, Firefox, Safari, or Edge. No frameworks, packages, build output, network requests, imports, external images, or external fonts. All visuals and audio must be inline/generated.

## Game contract
A hostile signal moves along a clearly drawn fixed path toward a core. The player earns credits by stopping waves and spends them to place or upgrade relay towers. The result must be a finished, replayable defence loop—not a static mockup.

## Required loop and keyboard controls
- Draw a legible map, path, core health, credits, wave number, selected tower, and wave status. Enemy movement and projectile travel must be visibly continuous.
- Include three distinct original tower roles: a fast low-damage pulse, a slower high-damage beam, and a slowing jammer. Each must have clear range/target feedback and a restrained upgrade path (at least one upgrade per role).
- Supply at least five deterministic waves, including a fast enemy, a durable enemy, and a mixed final wave. The core loses health for leaks; victory after the final wave and defeat at zero core health must both be explicit end states with restart.
- **Keyboard-only play is mandatory:** Tab/Shift+Tab reaches every interactive control; Enter/Space activates selection; arrow keys move a placement cursor over valid build pads; 1/2/3 select tower type; U upgrades the selected tower; N starts the next wave; R resets. Mouse support may be added but is not required.
- Towers may only be built on marked pads; placements need clear success/failure feedback. The game must be beatable with a sensible small build plan, but must not auto-play.

## Boundaries and quality
Use fixed wave data and deterministic targeting tie-breaks. Prevent obvious repeated-click exploits, invalid placements, negative credits, duplicated wave starts, and timers continuing after end state. Build a dark signal-console visual system with original shapes and color cues. At 390 px wide, preserve controls and avoid horizontal page scrolling.

## Read-only verification snapshot
Expose `window.__oneshotSnapshot()` for browser automation. It returns a fresh JSON-serializable object with `schema: "oneshot.playable/v1"` plus phase, wave number/status, credits, core health, selected tower type, placement cursor, and compact arrays for placed towers and active enemies. It accepts no arguments, must not mutate the game, and must not return live internal objects or expose control methods. Document the fields in `README.md`; this diagnostic surface supplements, rather than replaces, an actual keyboard playthrough.

## Evidence required in README
1. Offline/static evidence: `file://` boot with no network-capable code or console errors.
2. Deterministic evidence: enumerate five waves and each tower's damage/range/cost/upgrade values, then confirm snapshot output agrees with visible build and active-wave states.
3. Manual interactive evidence: a keyboard-only run that builds, upgrades, starts waves, and reaches either a documented win plan or a defensible loss.
4. Visual evidence: a screenshot or honest visual inspection note showing map/path, a selected pad, active enemies, and HUD.

Work autonomously; test and repair within this run. Deliver only `index.html` and `README.md`, with no fabricated evidence claims.
