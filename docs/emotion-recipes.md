# Emotion recipes — every compound, its variations, and how much of the person survives it

*(GENERATED from `src/engine/compounds.py`. Do not hand-edit — regenerate.)*

A recipe is `{primitive: (weight, role)}`. Three axes vary; only the third needs a new row:

| axis | how it varies | mechanism |
|---|---|---|
| **intensity** | the same state, weaker or stronger | `compose(name, intensity)` scales every weight, preserving the shape |
| **target** | the same shape, different aboutness | the `role` on each primitive, bound to an id at compose time |
| **shade** | a neighbouring coordinate | a separate row (contempt/disdain/scorn share one region on purpose) |

Roles: `self` · `self.act` · `object` · `beneficiary`.

## The SUM is the identity dial

`blend(name, baseline)` returns a FULL vector: `recipe + (1 - sum) x baseline`, clamped.
A recipe alone says what contempt IS and nothing about the rest of the person; the remainder
is filled with their own resting level, so the result is always a whole character.

**How hard a state steers and how much of the person it erases are the same number.** Two
things follow without being coded: the same recipe gives DIFFERENT vectors on different
people (which is what lets one vocabulary carry any cast), and lowering intensity raises the
proportion of baseline that survives (a faint contempt is mostly the person, a total one is
mostly the emotion).

**41 compounds, all expressible on the 8 primitives, and every role admitted by the basis registry** (`records.DIRECTEDNESS`). Five recipes were re-authored on 2026-08-22 when the registry first gave the basis a way to say a role was wrong: `jealousy` bound FEAR reflexively where the basis says FEAR of *the loss*, and `pride` / `spite` / `smug` / `passive_aggressive` bound PLAY reflexively where covertness is a delivery register rather than aboutness. `compounds.validate()["drift"]` is the standing check.

*(GENERATED from `src/engine/compounds.py` — do not hand-edit. Regenerate after any change to the table, the basis, or the registry.)*

| name | recipe | sum | baseline left |
|---|---|---|---|
| `anxious` | FEAR 0.40→object, SEEKING 0.30→object, PANIC_GRIEF 0.20→self | 0.90 | 10% |
| `bitter` | PANIC_GRIEF 0.35→self, DISGUST 0.35→object, RAGE 0.25→object | 0.95 | 5% |
| `bored_contempt` | DISGUST 0.45→object, PANIC_GRIEF 0.20→self | 0.65 | 35% |
| `broken` | PANIC_GRIEF 0.60→self, FEAR 0.25→object | 0.85 | 15% |
| `charming` | PLAY 0.40→object, SEEKING 0.25→object, CARE 0.25→object | 0.90 | 10% |
| `cold` | PANIC_GRIEF 0.30→self, DISGUST 0.25→object, FEAR 0.20→object | 0.75 | 25% |
| `comforting` | CARE 0.50→object, PANIC_GRIEF 0.20→object | 0.70 | 30% |
| `condescending` | DISGUST 0.45→object, PLAY 0.20→object, SEEKING 0.15→self | 0.80 | 20% |
| `contempt` | DISGUST 0.55→object, RAGE 0.35→object | 0.90 | 10% |
| `delight` | PLAY 0.60→object, SEEKING 0.30→object | 0.90 | 10% |
| `devotion` | CARE 0.60→object, SEEKING 0.25→object | 0.85 | 15% |
| `disdain` | DISGUST 0.45→object, RAGE 0.20→object, PANIC_GRIEF 0.15→object | 0.80 | 20% |
| `dread` | FEAR 0.70→object, SEEKING 0.15→object | 0.85 | 15% |
| `embarrassment` | PANIC_GRIEF 0.30→self, FEAR 0.25→object, DISGUST 0.20→self | 0.75 | 25% |
| `excited` | SEEKING 0.55→object, PLAY 0.35→object | 0.90 | 10% |
| `fierce` | RAGE 0.60→object, FEAR 0.25→object | 0.85 | 15% |
| `fond` | CARE 0.40→object, PLAY 0.30→object, PANIC_GRIEF 0.15→object | 0.85 | 15% |
| `fury` | RAGE 0.80→object | 0.80 | 20% |
| `grief` | PANIC_GRIEF 0.75→object | 0.75 | 25% |
| `guilt` | CARE 0.45→beneficiary, PANIC_GRIEF 0.40→self.act | 0.85 | 15% |
| `haughty` | SEEKING 0.40→self, DISGUST 0.25→object | 0.65 | 35% |
| `indignation` | RAGE 0.50→object, CARE 0.40→beneficiary | 0.90 | 10% |
| `jealousy` | CARE 0.40→beneficiary, RAGE 0.35→object, FEAR 0.35→object | 1.10 | 0% |
| `longing` | PANIC_GRIEF 0.45→object, LUST 0.25→object, SEEKING 0.25→object | 0.95 | 5% |
| `love` | CARE 0.50→object, LUST 0.25→object, PANIC_GRIEF 0.20→object | 0.95 | 5% |
| `mocking` | DISGUST 0.40→object, PLAY 0.30→object, RAGE 0.20→object | 0.90 | 10% |
| `nostalgic` | PANIC_GRIEF 0.35→object, PLAY 0.25→object, CARE 0.25→object | 0.85 | 15% |
| `passive_aggressive` | RAGE 0.30→object, DISGUST 0.30→object, PLAY 0.25→object | 0.85 | 15% |
| `pride` | SEEKING 0.45→self, PLAY 0.30→object | 0.75 | 25% |
| `resolve` | SEEKING 0.60→object, FEAR 0.20→object | 0.80 | 20% |
| `revulsion` | DISGUST 0.80→object | 0.80 | 20% |
| `scorn` | DISGUST 0.50→object, RAGE 0.45→object | 0.95 | 5% |
| `self_loathing` | DISGUST 0.65→self, PANIC_GRIEF 0.30→self | 0.95 | 5% |
| `shame` | PANIC_GRIEF 0.50→self, DISGUST 0.45→self | 0.95 | 5% |
| `smug` | SEEKING 0.35→self, DISGUST 0.30→object, PLAY 0.25→object | 0.90 | 10% |
| `spite` | DISGUST 0.40→object, RAGE 0.35→object, PLAY 0.20→object | 0.95 | 5% |
| `stressed` | FEAR 0.30→object, RAGE 0.25→object, PANIC_GRIEF 0.25→self | 0.80 | 20% |
| `tenderness` | CARE 0.55→object, PLAY 0.20→object | 0.75 | 25% |
| `wariness` | FEAR 0.35→object, SEEKING 0.25→object | 0.60 | 40% |
| `warm` | CARE 0.40→object, PANIC_GRIEF 0.25→object, PLAY 0.20→object | 0.85 | 15% |
| `welcoming` | CARE 0.35→object, PLAY 0.35→object, SEEKING 0.20→object | 0.90 | 10% |
