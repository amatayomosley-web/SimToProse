---
type: character
id: nell
---

# Nell Harrow

Forty, shepherd, four ewes lost to the pack since the first frost. She walks the fold at night alone
with a lamp and a bill-hook because there is nobody else to do it and she has stopped expecting
there to be. Blunt, warm, and entirely without pity — she asks people for things directly and does
not hold it against them when they say no, which is exactly why being asked by her is so hard to
bear.

She has asked Tam Rill up to the fold three times this winter. She knows why he does not come. She
has never said so.

**What this character exists to test:** she is the attachment term in `arc.derive_resilience`. Tam's
growth fork opens only when his affinity toward her clears roughly 0.90 while his allostatic load
sits under 0.15. Everything she does in a scene is either raising that number or not.

```json
{
  "fixed": {
    "id": "nell",
    "name": "Nell Harrow",
    "people": "human",
    "position": {
      "place": "Beck Hollow — came down from a fell farm at nineteen and has kept sheep here since",
      "class": "working freehold, land-poor and stock-rich; her wealth walks around on the low pasture and can be eaten in a night",
      "era": "the third early winter. She is the only person in the Hollow who has actually seen the pack up close, twice, and the only one who talks about them as animals rather than as a judgement",
      "niche": "shepherd. Walks the fold after dark alone, lambs in the cold, and has buried four ewes this winter. Knows the fell road better than anyone alive in the valley"
    },
    "genotype": {
      "_note": "Authored backward from her life (a principal, so not drawn; guide section 1). Each non-typical cell carries its reason beside the word; typical wherever her life gives no evidence. Re-derived 2026-09-27; nothing was translated from the retired six axes.",
      "STIRRING": {
        "hit": "elevated (she goes straight at a thing, and asks for what she needs directly)",
        "hold": "typical"
      },
      "WARINESS": {
        "hit": "typical (the dread does not get easier for her; she has only found out she can do it anyway)",
        "hold": "brief (she walks the fold again every night after a loss)"
      },
      "DISPLEASURE": {
        "hit": "typical",
        "hold": "brief (she does not hold it against anyone who tells her no)"
      },
      "GOODWILL": {
        "hit": "elevated (the fold is not property to her, it is charges)",
        "hold": "long (eleven winters of watching Tam, three refusals, and she still thinks he will come up the hill)"
      },
      "DEFLATION": {
        "hit": "elevated (she finished the third ewe herself and has told no one the details)",
        "hold": "typical"
      },
      "DISTASTE": {
        "hit": "low (she lambs in the cold, buries her ewes, and finished one that was still alive with the bill-hook)",
        "hold": "typical"
      },
      "RECEPTIVITY": {
        "hit": "typical",
        "hold": "typical"
      },
      "SELF-REGARD": {
        "hit": "typical",
        "hold": "typical"
      },
      "LEVITY": {
        "hit": "typical",
        "hold": "typical"
      }
    }
  },
  "baseline": {
    "temperament": {
      "_note": "Where she rests on an ordinary day, as rest words beside her voice (guide section 2). No mean is written: the engine seeds it from the word the first time the sheet runs.",
      "STIRRING": {
        "rest": "raised (there is always a next thing to ask for: hands at the fold, company after dark, Tam on the hill)"
      },
      "WARINESS": {
        "rest": "low (steady; she talks about the pack as animals, not as a judgement)"
      },
      "DISPLEASURE": {
        "rest": "quiet"
      },
      "GOODWILL": {
        "rest": "high (care as work done: the fold walked every night whether anyone else comes or not)"
      },
      "DEFLATION": {
        "rest": "low (she has stopped expecting anyone else to come)"
      },
      "DISTASTE": {
        "rest": "quiet"
      },
      "RECEPTIVITY": {
        "rest": "quiet"
      },
      "SELF-REGARD": {
        "rest": "low (self-possessed; she can outwait anyone and knows it)"
      },
      "LEVITY": {
        "rest": "quiet"
      }
    },
    "traits": {
      "emotionality": {
        "mean": 0.44
      },
      "agreeableness": {
        "mean": 0.62
      },
      "extraversion": {
        "mean": 0.58
      },
      "conscientiousness": {
        "mean": 0.8
      },
      "openness": {
        "mean": 0.48
      },
      "honesty_humility": {
        "mean": 0.78
      }
    },
    "model": {
      "schwartz": {
        "benevolence": 0.84,
        "security": 0.6,
        "self_direction": 0.66,
        "universalism": 0.58,
        "achievement": 0.4,
        "conformity": 0.34,
        "tradition": 0.44,
        "stimulation": 0.32,
        "power": 0.16,
        "hedonism": 0.28
      },
      "moral_foundations": {
        "care_harm": 0.82,
        "fairness": 0.7,
        "loyalty": 0.66,
        "authority": 0.36,
        "sanctity": 0.3
      },
      "needs": {
        "competence": 0.7,
        "relatedness": 0.66,
        "autonomy": 0.62
      },
      "regard": {
        "hollow": 0.78
      }
    },
    "drives": {
      "goals": [
        {
          "goal": "keep the fold whole through to the thaw",
          "priority": 0.88,
          "satisfaction": 0.3
        },
        {
          "goal": "stop being the only one who walks up there after dark",
          "priority": 0.7,
          "satisfaction": 0.15
        },
        {
          "goal": "get Tam Rill onto the hill once, on any pretext",
          "priority": 0.55,
          "satisfaction": 0.05,
          "note": "she thinks he would be all right afterwards. She has not told him that"
        }
      ],
      "orientation": {
        "locus": "internal",
        "agency": "high",
        "coping_engagement": "approach",
        "coping_expression": "practical"
      }
    },
    "wounds": [
      {
        "_note": "No wound is minted on this sheet yet (guide section 4: wounds are minted, never hand-written). On 2026-09-27 the composition pass classified her backstory against the formative library and nothing there carries her scar, so it picked nothing: finishing the third ewe herself, alone, in the dark (a helplessness wound). A generic profile for that gap (flock_keeper_predator_winter: a helplessness wound on WARINESS) was proposed and passed the library's admission gate, but it is not in the library; once the owner admits it there, pick it and re-run the composition pass to mint it. Until then only the story can mint it. The retired fears_wounds triggers, kept here for that day: a sheep in distress; blood on snow; being the only one there. Its avoidance list moved to voice.tics."
      }
    ],
    "catalog": {
      "_note": "Re-derived 2026-09-27 on the path ladder, not carried over. Her one old row was a vocation's standing conditioning (her charges in the scene), not an investment and not a wound, so it stays a lever, now on GOODWILL. Sized so that at her resting goodwill (concern) her charges being in the scene lift her one full rung, to tenderness, landing mid-band so a fired row is visible to the actor. Plurals added because a percept matches whole words only.",
      "rows": [
        {
          "when": {
            "percept": [
              "ewe",
              "ewes",
              "lamb",
              "lambs",
              "sheep",
              "flock",
              "fold",
              "blood"
            ]
          },
          "lever": "GOODWILL",
          "op": "x",
          "magnitude": 1.3,
          "source": "the fold is not property to her, it is charges"
        }
      ]
    },
    "skills": {
      "perception": 0.78,
      "insight": 0.7,
      "combat": 0.35,
      "shepherding": 0.88,
      "fell_lore": 0.82
    },
    "relationship_priors": {
      "default_trust": 0.62
    },
    "voice": {
      "register": {
        "formality": "blunt valley speech, no softening",
        "ornament": "plain, and warmer than the words look on the page"
      },
      "rhythm": "unhurried; she lets a silence sit until the other person fills it",
      "assertiveness": 0.78,
      "tics": [
        "asks for the thing directly, once",
        "says the hard fact and then waits",
        "uses a person's name when she wants them to hear it",
        "goes straight at a bad job and gets it over with",
        "does not describe the details afterwards"
      ],
      "code_switch": [
        {
          "context": "someone frightened",
          "shift": "slower and more concrete — she describes the next small task rather than reassuring"
        }
      ],
      "silence_profile": "comfortable — she can outwait anyone and knows it"
    }
  },
  "current": {
    "_note": "Turn zero: first light, walked down to the mill after losing a fourth ewe in the night. Every path sits at its resting mean except wariness and deflation, each one rung above rest for that loss (at that rung's middle, so the loss still reads a rung up when the engine's balance halves her mood toward rest while she faces someone).",
    "affect": {
      "STIRRING": 0.24,
      "WARINESS": 0.175,
      "DISPLEASURE": 0.035,
      "GOODWILL": 0.315,
      "DEFLATION": 0.24,
      "DISTASTE": 0.075,
      "RECEPTIVITY": 0.04,
      "SELF-REGARD": 0.16,
      "LEVITY": 0.05
    },
    "condition": {
      "energy": 0.62,
      "allostatic_load": 0.4,
      "health": 0.88,
      "fatigue": 0.45,
      "injuries": []
    },
    "location": "mill",
    "active_goals": [
      {
        "goal": "get another pair of hands to the fold before dark",
        "urgency": 0.8
      }
    ],
    "relationships": {
      "tam": {
        "trust": 0.7,
        "affinity": 0.66,
        "respect": 0.55,
        "debt": 0.0,
        "known_as": "Tam",
        "history": "she has watched him break the race open at first light in weather that would stop most men, and she has watched him find a reason not to come up the hill three times. She does not think those are two different men."
      }
    }
  },
  "formative_picks": []
}
```

## Beliefs

- (0.95, twice, close enough to smell them) They are animals. They are hungry and they are clever and they are not a judgement on anybody.
- (0.90, four ewes since the first frost) The pack is working down, not passing through. It will not stop on its own.
- (0.90, I have done it since the first frost) Nobody else walks the fold after dark. If I stop, it stops.
- (0.85, eleven winters of watching him) Tam Rill is not a coward about work. He is out on that race at four in the morning in weather that would keep me in.
- (0.80, three times asked, three times refused) He will come up that hill one day, and it will not be because anyone shamed him into it.
- (0.70, I finished her myself and told no one the details) Doing the thing you dread does not get easier. You just find out you can, and then you know it.
