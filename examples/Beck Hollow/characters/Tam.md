---
type: character
id: tam
---

# Tam Rill

Thirty-one, the miller's son, and the man who keeps the race clear. He is up before anyone in a
frost, breaking ice with a long bar so the wheel does not stop, and he has never once been thanked
for it because nobody has ever seen him do it. He arranges his life so that he is not seen.

He is not lazy and he is not weak. He is afraid — of the fell, of the dark above the last wall, of
being the one everyone turns to look at. When he was nineteen his father went up the fell road after
a strayed ewe in bad light and came back on a hurdle with his hip broken, and Tam, who had been
twenty yards behind him, had stopped at the wall and not gone on. Nobody has ever said a word about
it. That is the worst part.

**What this character exists to test:** whether the arc engine can move a baseline. His courage is
not a stat — it is `baseline.temperament.SEEKING`, and the only mechanism that raises it is
`arc.assess`'s growth fork, which needs resilience ≥ 0.70. See the note under `catalog`.

```json
{
  "fixed": {
    "id": "tam",
    "name": "Tam Rill",
    "people": "human",
    "position": {
      "place": "Beck Hollow — born in the mill, has never slept a night outside the valley",
      "class": "the working freehold: not poor, not owed to anyone, and of no consequence. The mill is his father's and will be his, which is the only status he has and the only one he wants",
      "era": "the third early winter in a row. The pack has been on the fell road in daylight, which is new, and the Hollow has begun to talk about what to do",
      "niche": "the miller's son. Keeps the race clear through a frost, alone, before light. Competent with his hands, exact with the wheel, and does not count any of it as courage because nobody watches him do it"
    },
    "genotype": {
      "_note": "Authored backward from his life (a principal, so not drawn; guide section 1). Each non-typical cell carries its reason beside the word; typical wherever his life gives no evidence. Re-derived 2026-09-27; nothing was translated from the retired six axes.",
      "STIRRING": {
        "hit": "low (he wants what he already knows; asked up to the fold three times, he has found a reason not to go three times)",
        "hold": "long (the want to stop being the man who stopped at the wall has stayed with him since nineteen without once being acted on)"
      },
      "WARINESS": {
        "hit": "high (at nineteen, twenty yards behind his father, fear stopped him at the wall; knowing that about himself has never once helped him go)",
        "hold": "long (he feels things hard and they stay a while)"
      },
      "DISPLEASURE": {
        "hit": "low (a raised voice makes him go quiet and agree; nothing in his life shows anger, not even at the silence about the wall)",
        "hold": "typical"
      },
      "GOODWILL": {
        "hit": "typical",
        "hold": "typical"
      },
      "DEFLATION": {
        "hit": "elevated (the wall went deeper in him than anyone has seen)",
        "hold": "long (he feels things hard and they stay a while; the silence about the wall is still the worst part)"
      },
      "DISTASTE": {
        "hit": "typical",
        "hold": "typical"
      },
      "RECEPTIVITY": {
        "hit": "typical",
        "hold": "typical"
      },
      "SELF-REGARD": {
        "hit": "elevated (he arranges his life so that he is not seen; how he is seen reaches him more than he lets on)",
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
      "_note": "Where he rests on an ordinary day, as rest words beside his voice (guide section 2). No mean is written: the engine seeds it from the word the first time the sheet runs.",
      "STIRRING": {
        "rest": "low (a want he turns over and does not act on)"
      },
      "WARINESS": {
        "rest": "high (afraid of the fell, of the dark above the last wall, of being the one everyone turns to look at; the cowardice is a disposition, not an episode)"
      },
      "DISPLEASURE": {
        "rest": "quiet"
      },
      "GOODWILL": {
        "rest": "raised (he keeps the race clear for a Hollow that has never thanked him; he does care, and it is what makes him reachable)"
      },
      "DEFLATION": {
        "rest": "raised (he has carried the wall, unspoken, since nineteen)"
      },
      "DISTASTE": {
        "rest": "quiet"
      },
      "RECEPTIVITY": {
        "rest": "quiet"
      },
      "SELF-REGARD": {
        "rest": "quiet (he apologises for taking up room and does not count any of his work as courage)"
      },
      "LEVITY": {
        "rest": "quiet"
      }
    },
    "traits": {
      "emotionality": {
        "mean": 0.74
      },
      "agreeableness": {
        "mean": 0.68
      },
      "extraversion": {
        "mean": 0.26
      },
      "conscientiousness": {
        "mean": 0.64
      },
      "openness": {
        "mean": 0.3
      },
      "honesty_humility": {
        "mean": 0.72
      }
    },
    "model": {
      "schwartz": {
        "security": 0.82,
        "conformity": 0.7,
        "benevolence": 0.66,
        "tradition": 0.58,
        "self_direction": 0.28,
        "achievement": 0.24,
        "stimulation": 0.1,
        "power": 0.12,
        "hedonism": 0.3,
        "universalism": 0.5
      },
      "moral_foundations": {
        "care_harm": 0.72,
        "fairness": 0.6,
        "loyalty": 0.64,
        "authority": 0.55,
        "sanctity": 0.4
      },
      "needs": {
        "competence": 0.45,
        "relatedness": 0.62,
        "autonomy": 0.3
      },
      "regard": {
        "hollow": 0.7
      }
    },
    "drives": {
      "goals": [
        {
          "goal": "keep the race clear so the mill never stops",
          "priority": 0.8,
          "satisfaction": 0.7
        },
        {
          "goal": "be no trouble to anyone, and not be looked at",
          "priority": 0.75,
          "satisfaction": 0.55
        },
        {
          "goal": "stop being the man who stopped at the wall",
          "priority": 0.6,
          "satisfaction": 0.05,
          "note": "he would not say this aloud and has never acted on it"
        }
      ],
      "orientation": {
        "locus": "external",
        "agency": "low",
        "coping_engagement": "avoidant",
        "coping_expression": "practical"
      }
    },
    "wounds": [
      {
        "_note": "No wound is minted on this sheet yet (guide section 4: wounds are minted, never hand-written). On 2026-09-27 the composition pass classified his backstory against the formative library and nothing there carries his scars, so it picked nothing: the wall at nineteen (a helplessness wound) and the dread of being the one they all turn to look at (a shame wound). A generic profile for that gap (froze_while_kin_went_on: a helplessness wound and a shame wound, both on WARINESS) was proposed and passed the library's admission gate, but it is not in the library; once the owner admits it there, pick it and re-run the composition pass to mint both. Until then only the story can mint them. The retired fears_wounds triggers, kept here for that day: fell road; the last wall; someone else walking into danger ahead of him; the long hall going quiet; his name said aloud in a group; being asked directly in front of others. Its avoidance lists moved to voice.tics."
      }
    ],
    "catalog": {
      "_note": "Re-derived 2026-09-27; none of the four old rows is kept. The wolves and fell-road row and the hall row were the arithmetic twins of his two wounds, and a wound cannot live in the catalog any more (guide sections 4 and 4b). The row that made care pull harder when a moment is about someone he has come to care for is now the engine's own work: the connection registry scales a reading about a person by his bond to them, so the row would count the bond twice. The rested-reach row aimed at courage as agency, which the path model has not built (self-efficacy is unbuilt), so it has nothing to move. The rested half of the premise still reaches the growth fork through the arc engine's resilience, which reads his allostatic load and his closest bond; when the fork opens, its mastery pricing lowers his resting wariness and raises his resting stirring. That is the only thing that moves his courage now.",
      "rows": []
    },
    "skills": {
      "perception": 0.62,
      "insight": 0.55,
      "combat": 0.15,
      "millwright": 0.8,
      "ice_work": 0.75
    },
    "relationship_priors": {
      "default_trust": 0.55
    },
    "voice": {
      "register": {
        "formality": "plain valley speech, no schooling past the parish",
        "ornament": "spare — he says the smallest true thing and stops"
      },
      "rhythm": "hesitant at the start of a sentence, steady once he is describing work",
      "assertiveness": 0.22,
      "tics": [
        "agrees before he has decided",
        "describes the task instead of answering the question",
        "apologises for taking up room",
        "finds work that must be done here, now, instead",
        "volunteers for the cold job nobody wants so as not to be asked for the frightening one",
        "agrees with whatever is decided and does not go",
        "arrives late and stands at the back",
        "leaves to check the race"
      ],
      "code_switch": [
        {
          "context": "anyone raising their voice",
          "shift": "goes quiet and agrees, regardless of what he thinks"
        },
        {
          "context": "the mill, the race, the wheel",
          "shift": "fluent and exact — the one place he speaks without hedging"
        }
      ],
      "silence_profile": "high, and anxious — he fills a pause only to end it"
    }
  },
  "current": {
    "_note": "Turn zero: chapter one opens on an ordinary cold morning at the mill, and the ordinary is where he is most himself. Every path sits at its resting mean except wariness, a little under its rest and still on the same rung.",
    "affect": {
      "STIRRING": 0.13,
      "WARINESS": 0.23,
      "DISPLEASURE": 0.035,
      "GOODWILL": 0.225,
      "DEFLATION": 0.24,
      "DISTASTE": 0.075,
      "RECEPTIVITY": 0.04,
      "SELF-REGARD": 0.05,
      "LEVITY": 0.05
    },
    "condition": {
      "energy": 0.58,
      "allostatic_load": 0.35,
      "health": 0.9,
      "fatigue": 0.42,
      "injuries": []
    },
    "location": "mill",
    "active_goals": [
      {
        "goal": "get the race broken open before the wheel seizes",
        "urgency": 0.75
      }
    ],
    "relationships": {
      "nell": {
        "trust": 0.62,
        "affinity": 0.45,
        "respect": 0.7,
        "debt": 0.2,
        "known_as": "Nell",
        "history": "she has asked him up to the fold three times this winter and he has found a reason not to go three times. She has never once made him say why."
      },
      "faron": {
        "trust": 0.3,
        "affinity": 0.25,
        "respect": 0.4,
        "debt": 0.0,
        "known_as": "the man with the dogs",
        "history": "a drover wintering over in the hall. Tam has not spoken to him and does not know his name — he thinks of him as the man with the dogs. THIS EDGE EXISTS TO TEST THE NAME-MASKING WALL: known_as is a descriptor, so an actor naming him is a leak faithfulness.check_name_leaks can catch."
      }
    }
  },
  "formative_picks": []
}
```

## Beliefs

- (0.95, I was twenty yards behind him and I stopped) When it matters I will not go, and knowing that about myself has never once helped me go.
- (0.90, nobody has ever said it to me) They all know about the wall, and they are being kind, and the kindness is worse than saying it.
- (0.85, eleven winters of it) If the race ices the mill stops, and if the mill stops the Hollow goes short. That one is mine and I have never failed it.
- (0.80, three refusals this winter) Nell will ask again. She always asks again. One of these times I will have to say something true.
- (0.80, the man with the dogs told the hall, and I was at the back) The man with the dogs killed a wolf on the fell road with a bill-hook, alone, last winter. [[faron]]
- (0.75, what everyone knows) A man who has been hurt by wolves stays hurt. Two men tried and both were carried back.
- (0.60, I have thought about it and not moved) If I went up there once and came back, it would be different afterwards. I do not know how to make myself start.
