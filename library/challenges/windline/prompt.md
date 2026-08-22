# Windline

Build **Windline**, a compact side-view paper-glider game in one self-contained `index.html`. It must run offline from `file://` in current desktop browsers with no imports, external assets, network calls, dependencies, or build step.

The glider moves steadily to the right. Up/Down or W/S changes pitch and lift. Create one fixed course with two clearly visible thermal columns and three hanging wind chimes. The chimes must be touched in left-to-right order; an out-of-order touch does not advance progress and gives visible feedback. After all three chimes, land on the marked rooftop pad. A gentle, nearly level descent succeeds. A hard rooftop impact, obstacle strike, or leaving the play area crashes.

Provide distinct `start`, `flying`, `crashed`, and `success` states. Enter starts. R always restarts a fresh run. P or Escape pauses only during flight. Include labelled Start, Restart, and Help buttons without making pointer input necessary. Show the next objective and concise controls. The full course and HUD must remain readable at 1280×720 and 390×844.

Keep the course and motion deterministic: no randomness, procedural layouts, or saved progress. Use original inline Canvas, SVG, or DOM art.

Expose `window.__oneshotSnapshot()` for independent browser checks. It returns a fresh JSON-serializable object with `schema: "oneshot.windline/v1"`, `phase`, `paused`, `next_chime`, normalized `glider` position/velocity/pitch, and compact arrays or objects describing chimes, thermals, and the rooftop pad. It accepts no arguments, changes nothing, returns no live internal objects, and exposes no control methods.

Do not ask for follow-up. Before finishing, test keyboard start, steering, pause, crash/restart, ordered chimes, rooftop success, and both viewport sizes.
