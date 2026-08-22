# Loopback

A rotation-circuit puzzle game in a single HTML file. Rotate wire tiles to join
the power source to **every lamp on the board at the same time**.

**Run it:** open `index.html` in any current browser (Chrome, Firefox, Edge,
Safari), desktop or mobile. Double-click the file — no build step, no server,
no network needed.

## Controls

| Input | Action |
| --- | --- |
| Click / tap a tile | Rotate it 90° clockwise |
| `← ↑ → ↓` | Move the focus cursor |
| `Enter` / `Space` | Rotate the focused tile |
| `U` | Undo |
| `R` | Reset |
| `Esc` | Open / close the level menu |

The game is fully playable with the keyboard alone (cursor + Enter/Space).

## Rules (normative summary)

- A square grid (5×5 → 8×8) holds fixed tiles that only rotate in place.
- Tile types: `source` (one per level), `lamp`, `straight`, `elbow`, `tee`, `cross`.
- Power originates at the source and propagates between tiles whose connectors
  face each other. A lamp is lit when reached by an unbroken chain.
- **Win:** every lamp lit simultaneously. Extra lit paths, loops, and dead wire
  are all fine — they only cost the moves you spent.
- One rotation = one move. Rotating a `cross` still counts even though its
  connector set is unchanged.
- Undo/Reset restore the board; undo supports a large history (capped at 500).
- Level `N+1` unlocks when level `N` is completed. On first load only L01 is
  unlocked.
- Best (lowest) move count per level persists in `localStorage`
  (`loopback.progress.v1`). Corrupt/missing data falls back to a fresh profile.

## Par

`Par` is the move count of a correct solution I actually constructed and ran
(it is what the shipped levels are solved in on the "progression" run). It is
advisory text, never a gate.

## Level data

The 12 levels are embedded in `index.html` as a `LEVELS` array, and their
ASCII layouts plus full solution orientations are given as a comment in the
source (search for "LEVEL DATA + SOLUTION ORIENTATIONS").

| Level | Board | Lamps | Decoys | Par | Personal best |
| --- | --- | --- | --- | --- | --- |
| L01 | 5×5 | 1 | 0 | 2 | — |
| L02 | 5×5 | 1 | 1 | 3 | — |
| L03 | 5×5 | 2 | 0 | 4 | — |
| L04 | 6×6 | 1 | 1 | 5 | — |
| L05 | 6×6 | 2 | 2 | 6 | — |
| L06 | 6×6 | 2 | 2 | 7 | — |
| L07 | 7×7 | 2 | 1 | 8 | — |
| L08 | 7×7 | 3 | 2 | 9 | — |
| L09 | 7×7 | 1 | 3 | 10 | — |
| L10 | 8×8 | 1 | 3 | 11 | — |
| L11 | 8×8 | 2 | 4 | 12 | — |
| L12 | 8×8 | 3 | 4 | 13 | — |

Levels 1–3 are simple to a first-time player (L01 is a two-move straight line
to prove rotation + connection in seconds). Ten levels include decoys; six
require two or more lamps.

## Design

- Editorial-lab palette: warm paper `#F4F1EA`, near-black ink `#1A1917`, a
  single accent `#C24D2C` (burnt orange) used only for powered wires, lit
  lamps, and primary actions. Flat color — no gradients, no glows, hairline
  borders only.
- System font stack; tabular figures for all counters.
- Tiles are inline SVG strokes; rotation animates ~160 ms ease-out (instant
  when `prefers-reduced-motion` is set).
- **Non-color state:** a lit lamp both fills with the accent color *and* gains
  a checkmark (glyph change). Power is also encoded as accent strokes plus
  established fill.
- `aria-live="polite"` region announces lamp state and win/completion.
- Visible focus box for the keyboard cursor, meeting WCAG-2.1-AA contrast.

## Assumptions / decisions (resolved autonomously)

- I interpret "strictly increasing in minimum-board size" as non-decreasing
  board size while ramping difficulty (sizes are 5→5→5→6→6→6→7→7→7→8→8→8).
- Par values are the exact move counts of the verified solutions; they are
  simple (each level's answer is a fixed set of rotations, so par equals that
  count).
- Decoys are isolated wire fragments that never touch the live network, so a
  correct main-network solve is always possible and decoys are optional.
- Sound is omitted entirely (per the priority-2 guidance) rather than shipped
  half-working.
- The visual aid tools used during development live in `_build/` (generator,
  verifier, browser-test scripts). They are not required to play.

## Known limitations

- No audio / sound effects.
- Board order (tile render order) is static; a single tile is never animated
  independently but the whole tile-group rotates (the connectors rotate with
  the cell — cosmetic, functionally correct).
- Local browser persistence only; no cross-device sync.

## Verification (what was actually run)

The verifier and browser harness drove the **real shipped file over `file://`**,
not just the generator. Two independent engines agree bit-for-bit (Python
generator/verifier in `_build/build_levels.py`, and the in-browser JavaScript
engine).

1. **Boot** — opening `index.html` via `file://` renders the title screen with
   zero console errors. *Passed (headless Chromium).*
2. **Core loop** — rotating tiles changes connectivity; connecting the level-1
   lamp lights it immediately. *Passed.*
3. **Win condition** — completion panel appears only when all lamps lit and
   shows the correct move count (L01: 2, matches par). *Passed.*
4. **Solvability** — all 12 levels solved by an actual executed rotation
   sequence at or below par; per-level move counts in `verification.log`. *Passed.*
5. **Undo/reset** — 12 consecutive rotations undone back to zero; reset zeroes
   the counter and clears the undo stack. *Passed.*
6. **Persistence** — best scores survive a full reload; corrupting the storage
   key does not break boot and produces no console error. *Passed.*
7. **Keyboard** — levels 1–3 completed using only cursor + Enter. *Passed.*
8. **Reduced motion** — emulating `prefers-reduced-motion` removes the
   transition (computed `transition-duration` = 0s). *Passed.*
9. **Offline integrity** — source scan found no external URLs
   (`http(s)://`, `fetch(`, `@import`, `url(`). *Passed.*

Full output: see `verification.log`. The environment renders the page in
Chromium, but this model cannot visually inspect raster images, so the
"visual" checks above were performed at the DOM/CSS-computed-style level
rather than by looking at screenshots; screenshots are retained in `_build/`.

## Files

- `index.html` — the entire game (inline CSS + JS, embedded levels).
- `README.md` — this document.
- `verification.log` — output of the solvability + DOM smoke tests.
- `_build/` — development-only generator, verifier, and test scripts.
