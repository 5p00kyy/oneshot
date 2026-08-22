# Loopback — a rotation circuit puzzle in one HTML file

## 1. Role

You are acting as a senior front-end engineer and game designer.

You are responsible for the complete outcome: a polished, fully playable
puzzle game that runs directly from a single HTML file, including its
mechanics implementation, twelve verified-solvable levels, visual design,
accessibility, persistence, and verification evidence.

Use expert judgment. Optimize in this order:

1. Correct, complete game logic with no soft-locks.
2. Full keyboard and pointer playability.
3. Twelve levels that are each solvable and verified solvable.
4. Visual polish and restrained motion.

## 2. Mission

Create **Loopback**, a single-file browser puzzle game, playable by anyone who
double-clicks `index.html`, in which the player rotates wire tiles to connect a
power source to every lamp on the board simultaneously.

The initial release must be a complete, finished game with a real win condition,
progression, and persistence — not a tech demo, not a prototype grid, not a
description of a game.

The result should demonstrate: precise deterministic rules, honest completion
feedback, accessible controls, handcrafted level pacing, and an editorial,
restrained visual identity.

## 3. Definition of one shot

This is one self-contained brief with no human follow-up. Nobody will answer
questions or supply missing decisions after you start.

You may and should, when your environment supports it:

- Create files and run commands.
- Open the built game in a browser and inspect it.
- Write throwaway test scripts to verify solvability of your levels.
- Find defects in your own work, repair them, and re-verify.
- Iterate internally as much as needed until the definition of done is met.

Do not interpret "one shot" as "one attempt with no testing" or "produce output
without checking it". Do not stop at planning, scaffolding, or a mock-up.

## 4. Operating contract

Work autonomously through the complete task.

- Resolve noncritical ambiguity with conventional, reversible assumptions; record them in the README.
- Implement the critical path before optional polish.
- Run and inspect the actual artifact, not only the source code.
- Repair defects found during verification before finishing.
- Report only verification that actually occurred.

Do not expose hidden chain-of-thought. Keep private planning private; record
durable decisions in the README where useful.

## 5. Environment

Target environment:

- Executor: autonomous coding agent with file and shell access.
- Workspace: empty directory (or a fresh subdirectory you create).
- Runtime for players: any current version of Chrome, Firefox, Edge, or Safari, desktop or mobile.
- Network policy for the artifact: none. The game must work offline from `file://`.
- Output limit: at most three files (`index.html`, `README.md`, plus one optional verification log).

Workspace rules:

- No build step, package manager, framework, or external asset may be required to play.
- All CSS and JavaScript are inline in `index.html`.
- If your environment cannot render the page, say so plainly in the README and rely on scripted DOM-level verification instead of claiming a visual check you did not perform.

## 6. Game rules (normative)

Implement exactly these rules; they are deliberately deterministic so results
are comparable across executors.

### Board

- The board is a square grid of cells, from 5×5 (level 1) up to at most 8×8 (final levels).
- Each cell is either empty or holds exactly one fixed tile. Tiles never move between cells; they only rotate in place.
- Tile types are defined by their connector sets, expressed as directions N/E/S/W:
  - `source`: one connector (exactly one per level).
  - `lamp`: one connector (one or more per level).
  - `straight`: two opposite connectors (N+S or E+W).
  - `elbow`: two adjacent connectors (e.g. N+E).
  - `tee`: three connectors.
  - `cross`: four connectors (rotation is visually irrelevant but still costs a move).
- Empty cells are always empty. The solution uses only rotations of pre-placed tiles.

### Power flow

- Power originates at the `source` tile and propagates through the grid: power enters a tile through one of its connectors only if the neighboring tile has a connector facing back.
- A lamp is lit when power reaches it through an unbroken chain of mutually facing connectors.
- The level is solved when **every lamp is lit simultaneously**. Extra lit paths, loops, and unconnected dead wire are all allowed and cost nothing beyond the moves spent creating them.

### Moves

- One player action rotates one tile 90° clockwise. That action increments the move counter by exactly 1.
- Rotating a `cross` tile is legal and counts as a move even though its connector set is unchanged.
- Undo restores the previous board state and decrements the counter; the undo stack must support at least 200 entries.
- Reset returns the level to its initial orientation and zeroes the counter (this does not clear the undo stack's existence requirement — after reset, undo is unavailable until new moves are made).

### Progression and persistence

- Exactly 12 levels, identified `L01`…`L12`, strictly increasing in minimum-board size and intended difficulty.
- Levels unlock sequentially: completing level N unlocks N+1. On first load only `L01` is unlocked.
- Best (lowest) move count per completed level persists in `localStorage` under a single namespaced key (for example `loopback.progress.v1`) as JSON. Corrupt or missing data must fall back safely to a fresh profile without console errors.
- A level-select screen shows, per level: number, lock state, personal best or "—", and par.

### Par

- Each level definition includes `par`: a reference move count achieved by a correct solution you actually constructed and verified. Par is advisory text for the player ("par 14"), never a gate.

## 7. Levels

Embed all 12 levels as a readable data table (ASCII rows plus a legend) inside the source, for example:

```text
L03  6x6  par 14
. . . . . .
. a . b . .
. . . . . .
. c . d . e
. . . . . .
. f . g . .
legend: a=elbow(NE) b=lamp(W) c=source(N) ...
```

Requirements:

- Every level is solvable within its stated par by a rotation sequence you have actually executed (manually or via script). Do not ship an unverified level.
- At least four levels contain decoy tiles (wires that are useful-looking but unnecessary), and at least three levels require lighting two or more lamps.
- Level 1 must teach rotation and connection in under 30 seconds for a first-time player.
- Include the full solution orientation for each level as a comment in the source, so verification does not depend on re-solving.

## 8. Controls and accessibility

- Pointer: click or tap a tile to rotate it clockwise.
- Keyboard: arrow keys move a visible focus cursor between cells; Enter/Space rotates the focused tile; U undoes; R resets; Escape opens/closes the level menu.
- Every interactive element has a visible focus indicator meeting WCAG 2.1 AA contrast against its background.
- Lit/unlit lamp state must never rely on color alone: lit lamps additionally change glyph/shape (for example filled core plus a check-style marker).
- Board state changes are announced through an `aria-live="polite"` region ("Lamp 2 of 3 lit", "Level complete in 14 moves").
- Respect `prefers-reduced-motion`: animations collapse to instant state changes.
- The full game — start through level 12 completion — is completable with keyboard only.

## 9. Visual direction

Editorial-lab aesthetic: the game should feel like a beautifully typeset
instrument panel, not a neon arcade.

- Palette: warm paper background (#F4F1EA), near-black ink (#1A1917), one accent (#C24D2C burnt orange) used only for powered wires, lit lamps, and primary actions. Unpowered elements render in ink outlines.
- Flat color only: no gradients, no glows, no drop shadows heavier than a 1px hairline.
- Typography: system font stack; the title set large and tight; counters and labels in tabular figures.
- Tiles drawn as crisp SVG strokes with rounded joins; rotation animates over 120–180ms with an ease-out curve (instant when reduced motion is preferred).
- Win feedback: lamps pulse once, then a summary panel shows moves, par, and personal best, with next-level and replay actions.

## 10. Required deliverables

1. `index.html` — the complete game, self-contained, valid HTML5, no console errors or warnings during normal play.
2. `README.md` — how to run, controls, rules summary, assumptions made, known limitations, and a verification section listing what was actually tested and how.
3. Optional `verification.log` — output of any scripts you ran (solvability checks, DOM smoke tests).

Do not substitute interface labels, TODOs, stubs, or roadmap entries for required functionality.

## 11. Verification (perform these; record actual results)

Before finishing, verify each item and record the real outcome in the README:

1. **Boot**: opening `index.html` via `file://` renders the title screen with zero console errors.
2. **Core loop**: rotating tiles changes connectivity; connecting a lamp lights it immediately.
3. **Win condition**: a level completes only when all lamps are lit; the completion panel shows correct move count.
4. **Solvability**: every level was solved at least once by you (or by a script driving the rules engine) at or below par; record per-level move counts.
5. **Undo/reset**: undo reverts moves correctly across at least 10 consecutive actions; reset restores the initial board.
6. **Persistence**: best scores survive a full page reload; corrupting the storage key does not break boot.
7. **Keyboard**: levels 1–3 are completable using only the keyboard.
8. **Reduced motion**: emulating `prefers-reduced-motion` removes animated transitions.
9. **Offline integrity**: the HTML contains no external URLs (no CDN links, no fetched assets); confirm by searching the source.

If any check fails, repair the game and re-run the check. Do not report a check as passed unless you ran it and it passed.

## 12. Priority order

### Priority 0 — Never cut

- Deterministic rules engine exactly as specified in section 6.
- 12 verified-solvable levels with sequential unlocking.
- Persistence with safe fallback.
- Full keyboard operability.
- Zero console errors.

### Priority 1 — Strongly required

- Visual direction of section 9.
- Screen-reader announcements and non-color state encoding.
- Level-select screen with bests and par.

### Priority 2 — Cut first under pressure

- Rotation animation polish.
- Sound (omit entirely if time-constrained; do not ship half-working audio).

When forced to reduce scope, remove Priority 2 breadth before coherence, and never silently downgrade a Priority 0 rule.

## 13. Completion ledger and final response

Before handoff, reconcile every planned item as done-and-verified, deliberately
cut under the priority policy, or blocked with evidence. Do not finish with
unexamined pending items.

Respond with: what was built; exact command or path to run it; verification
actually performed with real outcomes; key file locations; remaining genuine
limitations. Do not describe missing Priority 0 work as a future enhancement.

## 14. Final directive

Execute the complete task now. Inspect, implement, run, inspect the running
game, test, repair, and hand off the finished result. Do not restate this
specification, and do not stop at planning or scaffolding.
