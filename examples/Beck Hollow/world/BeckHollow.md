---
type: world
id: Beck Hollow — a valley village under a hard winter, and the wolves working down off the fell
---

# Beck Hollow

Forty-odd people in a fold of the hills, a mill on the beck, sheep on the low pasture and the fell
above them going white. No lord within three days' ride, no garrison, no one coming. What the
Hollow has, the Hollow does itself.

This is the third winter in a row that has come early, and the second in which the pack has been
seen on the fell road. Last winter they took lambs. This winter they have started coming down in
daylight.

## The premise this world exists to test

A man who is afraid can be made brave by his circumstances, or broken further by them, and the
difference is not courage — it is whether he is rested and whether he is loved. The village is the
apparatus. The wolves are the pressure. Nobody writes what he does.

```json
{
  "world": "Beck Hollow",
  "season": "the third week of a winter that came a month early",
  "switches": {
    "magic": false,
    "divine": false,
    "beings": false
  },
  "blueprint_defaults": true,
  "standing_facts": [
    "Beck Hollow holds about forty people. There is no garrison, no lord in reach, and no help coming before the thaw.",
    "The beck drives the mill. If the race ices over the mill stops, and a stopped mill in winter means no flour.",
    "Sheep are the Hollow's whole wealth. A fold lost is a family ruined, not inconvenienced.",
    "The pack came down off the fell twice last winter and took lambs. This winter they have been seen on the fell road in daylight, which is new.",
    "Wolves are animals. They are not spirits, they are not sent, and nothing in this valley is supernatural.",
    "A hard frost holds the beck for three or four days at a stretch; the ice has to be broken by hand or the race stops.",
    "Winter dark comes by mid-afternoon and holds until nine. Most of the day is not lit.",
    "The long hall is the only building with a hearth big enough for the whole village. People gather there when something is decided.",
    "Nobody in the Hollow has killed a wolf. Two men have tried, in living memory, and both were hurt doing it."
  ],
  "locations": [
    {
      "id": "mill",
      "what": "the mill house on the beck — the wheel, the race, the grinding floor, and the cot above it where Tam sleeps. Warm when the wheel turns, freezing when it stops"
    },
    {
      "id": "beck",
      "what": "the stream through the hollow, running fast and shallow, iced at the edges. The mill race is cut from it and must be kept clear by hand in a frost"
    },
    {
      "id": "fold",
      "what": "the drystone sheep fold on the low pasture, walls chest-high, a hurdle gate. Close enough to the village to hear a dog from, far enough that nobody sees what happens at night"
    },
    {
      "id": "fell-road",
      "what": "the track climbing out of the hollow onto open fell. Above the last wall there is no cover, no light, and no help. This is where the pack is seen"
    },
    {
      "id": "long-hall",
      "what": "the village hall — one hearth, benches, the tithe chest. Where the Hollow argues and where it decides"
    },
    {
      "id": "winter-store",
      "what": "the turf-roofed store behind the hall: grain, salt meat, lamp oil, and the count of how many weeks are left"
    }
  ],
  "people": [
    {
      "id": "tam",
      "name": "Tam Rill",
      "what": "the miller's son, thirty-one, who keeps the race clear and does not go up the fell road"
    },
    {
      "id": "nell",
      "name": "Nell Harrow",
      "what": "shepherd, forty, blunt and warm, who has lost four ewes to the pack and walks the fold at night alone"
    },
    {
      "id": "orrin",
      "name": "Orrin Cade",
      "what": "the hall-keeper, sixty, who counts the winter store and says out loud what everyone is thinking"
    }
  ],
  "lexicon": {
    "attribute_classes": {
      "threat": [
        "wolf",
        "wolves",
        "pack",
        "tracks",
        "howl",
        "blood",
        "carcass",
        "teeth",
        "growl"
      ],
      "cold": [
        "frost",
        "ice",
        "snow",
        "sleet",
        "wind",
        "frozen",
        "numb",
        "thaw"
      ],
      "work": [
        "race",
        "wheel",
        "flour",
        "grain",
        "hurdle",
        "fold",
        "ewe",
        "lamb",
        "fleece",
        "pail"
      ],
      "light": [
        "lamp",
        "lantern",
        "oil",
        "hearth",
        "dark",
        "dusk",
        "torch",
        "coal"
      ],
      "harm": [
        "wound",
        "bite",
        "bone",
        "blade",
        "axe",
        "spear",
        "bandage",
        "limp"
      ]
    },
    "subtle_cues": {
      "watched": [
        "the dogs went quiet",
        "the sheep bunched",
        "something moved at the wall"
      ],
      "unspoken": [
        "nobody looked at him",
        "the hall went quiet when he came in",
        "she did not ask again"
      ]
    },
    "subtle_cue_classes": [
      "watched",
      "unspoken"
    ]
  },
  "laws": [
    {
      "domain": "legal",
      "modality": "IMPOSSIBLE",
      "epistemic": "known-true",
      "act": "summon-outside-help",
      "statement": "There is no authority within reach of Beck Hollow before the thaw. Nobody can send for anyone.",
      "source_note": "the world's isolation is the premise; removing it removes the pressure",
      "id": "no-help-before-thaw"
    },
    {
      "domain": "cosmology",
      "modality": "IMPOSSIBLE",
      "epistemic": "known-true",
      "act": "treat-the-pack-as-sent",
      "statement": "The pack is animals following food down off the fell. It is not sent, not cursed, and not owed anything.",
      "source_note": "switches.magic is false; this law makes the mundane frame refusable rather than assumed",
      "id": "a-wolf-is-an-animal"
    },
    {
      "domain": "legal",
      "modality": "REQUIRES",
      "epistemic": "known-true",
      "act": "let-the-race-ice-over",
      "statement": "The race must be kept clear through a frost. A stopped mill in deep winter is the village going hungry.",
      "teeth": "the Hollow goes short, and everyone knows whose work it was",
      "source_note": "gives Tam a duty he already discharges — competence he does not count as courage",
      "id": "the-mill-must-run"
    }
  ]
}
```

## Note on what is deliberately absent

No magic, no gods, no monsters — `switches` answers all three false. The wolves are the whole threat
and they are ordinary. Everything that happens to Tam Rill has to come from cold, hunger, dark,
other people, and animals that are simply hungry.
