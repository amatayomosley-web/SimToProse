# Building a settlement — the sheet for a village, town or city

**Status: PROCEDURE.** Written 2026-10-01, beside `guide-building-a-nation.md`. The nation sheet says what a people
holds; this says what one place holds, from a hamlet of forty to a city of millions, and how to see what a place you
have already written is missing. What you lack, you add.

It is the method, not a place: the worked example is the template's public test book, `examples/Beck Hollow`.

---

## The one thing to know before you start

A place is not its scene. A town that exists only where the story needs a street is a backdrop: nobody could tell you
the way to the market, what the place lives on, or what everyone there complains about. A built place could be walked
by a stranger, and it is tied to other places by what it sends them and what it needs from them, because no place
feeds itself.

## Three sizes

- **A gazetteer line, for every place.** One line in the nation sheet's part 3: name; kind (hamlet, village, market
  town, port, fort, city); how many people; where, and how many days to the capital and to the nearest market; why it
  is here; what it sends; what it needs.
- **The full sheet, for a place a scene touches or a character comes from.** The eleven parts below.
- **Districts, for a city a scene enters.** The city keeps parts 0 to 3, 6, 9 and 10. Each district a scene enters
  gets its own parts 4, 5, 7 and 8 and its own test, and the city's count is the sum of its districts. A stranger can
  only be given directions at district scale.

## What a built place is: eleven parts and the test

The number in brackets is the layer of the nation sheet that fills the part, so the place fills up as its nation does.

0. **At a glance.** Name; kind; how many people; where; one sentence a local would say about it. *Coming in:* what
   you see, hear and smell from the road, and what the place is built of.
1. **Why it is here** [1, 3]. Water, ore, a harbour, a crossing, a pass, good soil, a fort, a shrine.
2. **What it does for others** [3]. What leaves it, and where it goes.
3. **What it needs from others** [3]. Food, fuel, tools, salt, people; from where, and how many days away.
4. **Who lives here** [2, 4]. The main trade and its rough share; the trades every place has (food, building,
   carting, keeping accounts, healing, entertaining); rich, poor and outsiders, with rough shares; and the people a
   local would name, six or so, one line each.
5. **The places in it** [all]. The half-dozen a local would name, each as what you see standing there (the conditions
   a scene would open in, not a description of the view).
6. **Who runs it, and why people obey** [5]. The local leader, how chosen, answering to whom; who keeps order; what
   the nation takes from here and who collects it.
7. **What it is proud of and what it fears** [6, 9]. Its customs, feast days and sayings, each custom with what
   breaking it costs.
8. **A day there** [2, 9]. Dawn, midday and night. In a city, one district's day.
9. **How it breaks** [11]. Fire, flood, siege, plague, a bad harvest, a road cut; its one weak link; who leaves
   first. A city also says how it is fed and watered, and where its waste goes.
10. **How it is changing** [3, 11]. What is growing and what is dying; who is arriving and who is leaving.

Rows, tags and rules are the nation sheet's: one fact a row, an id and a tag first (`S4.2 [C ...]`), canon checked by
copied words, proposals kept out of the book until adopted, open rows naming what needs them, numbers that close,
every custom with its cost, cite and never copy. A place's named people become `people/` notes (`type: reference`
until a scene needs them) and its named places become `locations` a scene can open in, by the table in
`guide-building-a-world.md`.

## The test

1. **Directions.** Send a stranger from the edge of the place to its market, its seat of authority and its worst
   street, naming who they meet on the way. Parts 4 and 5 must make this answerable.
2. **Five scenes.** Five places a scene could open in, and what you see from each.
3. **The match.** Everything in part 3 arrives from a named place whose sheet or gazetteer line sends it; everything in
   part 2 is received somewhere named.
4. **The worst day.** What happens on the worst day of the year, and who leaves first.
5. **Scale.** In a city, each district passes 1 and 2 on its own.

## A worked example: a hamlet

From `examples/Beck Hollow/world/BeckHollow.md`, the public test book.

The gazetteer line: *Beck Hollow — hamlet, about forty people, in a fold of the hills, three days' ride from any lord;
here for the beck that turns the mill; sends nothing anyone has written down; needs salt and lamp oil from somewhere
nobody has named.*

A few rows of the full sheet, showing the tags:

- `S0.1 [C BeckHollow.md "Forty-odd people in a fold of the hills"]` about forty people.
- `S1.1 [C BeckHollow.md "The beck drives the mill"]` it is here for the beck.
- `S3.1 [open: a scene where the store runs low]` where the salt and the lamp oil in the winter store come from, and
  how many days away.
- `S5.1 [C BeckHollow.md "the only building with a hearth big enough"]` the long hall: one hearth, benches, the tithe
  chest.
- `S6.1 [D from "Where the Hollow argues and where it decides" and "No lord within three days' ride"]` nobody rules
  the Hollow; it decides things together in the long hall, where the man who counts the winter store says out loud
  what everyone is thinking.
- `S9.1 [C BeckHollow.md "a stopped mill in winter means no flour"]` its weak link is the mill race in a hard frost.

The gaps fall out at once: what the Hollow sends to anyone (part 2), where its salt and oil come from (part 3), and
the feast it keeps in a good year (part 7). Those are the rows to fill next.

## What usually goes wrong

- **The backdrop.** The place has streets only where the plot walks. Directions catch it.
- **The island.** It needs nothing from anywhere. The match catches it.
- **Everyone is the main trade.** A mining town of only miners has nobody to cook, carry, heal or count. Part 4's
  shares catch it.
- **A city treated as one street.** Give it districts.

## Where to go next

`docs/guide-building-a-nation.md` for the people the place belongs to · `docs/guide-building-a-world.md` for what
reaches the engine · `docs/guide-building-a-cast.md` for the people who live there.
