---
type: person
id: faron
---

A drover wintering over in the long hall with three dogs, waiting out the weather before he takes
the road south. Keeps to himself, feeds his dogs before he feeds himself, and has said perhaps forty
words since he arrived.

```json
{ "id": "faron", "name": "Faron", "what": "a drover wintering over in the long hall with three dogs, waiting for the road south to open" }
```

## Note

This entry exists to load through the `people/*.md` path rather than the world note's inline array —
both routes feed `world.people` (`src/engine/vault.py:load_book`) and this book exercises each.

Tam's edge to him carries `known_as: "the man with the dogs"` — a DESCRIPTOR, not a name. That makes
this book able to test `faithfulness.check_name_leaks`, which fires when an actor uses the real name
of someone they know only by a descriptor. No other book the engine has run has a descriptor-masked
edge, so verification-sheet B11 is runnable here and nowhere else.
