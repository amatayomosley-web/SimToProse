# Trait Models

The dispositional layer — **Level 1** in McAdams' scheme, **Layer 1** in `character-anatomy.md`: broad, comparatively stable consistencies in *how* a person behaves across situations, the through-line that keeps a character recognizable from scene to scene (same goal, different pursuit — methodical vs impulsive, bold vs reserved). This file is the well of trait *structures*: the dimensional theories that carve personality into a handful of continua, the models that add a moral or dark dimension the mainstream ones bury, and the interpersonal and biological schemes that read behaviour from a different angle. The repo commits to **HEXACO** as its trait spine (`docs/trait-theory.md`) and stores every dimension as a **density distribution — a mean plus a variability — not a fixed scalar** (Whole Trait Theory), so a trait is a *lean* the character usually shows and a *spread* they swing through, and out-of-character behaviour is a caused tail-sample, not noise. Those are the reference defaults; they sit inside a much larger library, and this file lays the library out. A trait is never a switch. It is a bipolar continuum, and both ends have to read on the page — so for the two workhorse models each dimension is drawn at **high** and **low**, with the failure mode that lives at each extreme. The whole enterprise rests on the **lexical hypothesis** (Galton 1884; Allport & Odbert 1936, who culled ~18,000 trait words from an English dictionary; Cattell, Goldberg): *the personality differences that matter to human life get encoded as single words in every language, so factor-analysing the vocabulary recovers the true dimensions of temperament.* Every dimensional model below is a different factor-solution to that same lexical corpus — which is why they map onto one another so cleanly.

---

## Big Five / OCEAN — the consensus five-factor model

**Lineage.** The lexical tradition: Allport & Odbert (1936) → Cattell's factor reductions (1940s) → Tupes & Christal (1961, the five recurrent factors) → Norman (1963) → rediscovered and consolidated by **Lewis Goldberg** ("the Big Five", the lexical wing) and **Paul Costa & Robert McCrae** (the "Five-Factor Model", the questionnaire wing, NEO-PI-R, 1985/1992). The dominant paradigm in academic personality psychology for forty years.

**Core idea.** Factor-analyse how people describe themselves and each other and the same **five** broad, orthogonal dimensions fall out across languages and cultures. They are near-normally distributed continua, substantially heritable (~40–60%), and predict real outcomes (health, longevity, job performance, relationship stability). Each is a *domain* built from finer *facets*; above them sit two *metatraits*. The model is descriptive, not explanatory — it says *what* varies, not *why*.

**Structure in full.**

The five domains (mnemonic **OCEAN** / **CANOE**):

- **Openness to Experience** — imagination, aesthetic sensitivity, intellectual curiosity, preference for novelty and variety. *High:* Luna Lovegood, Willy Wonka, the restless polymath. *Low:* Tom Buchanan, the man who has eaten at the same diner for thirty years and wants the world to stop changing.
- **Conscientiousness** — organisation, diligence, dutifulness, impulse control, planfulness. *High:* Hermione Granger, Atticus Finch, the surgeon who scrubs in the same order every time. *Low:* Jack Sparrow, the Dude, the brilliant slob whose desk is a landslide.
- **Extraversion** — sociability, assertiveness, energy, positive emotionality, reward-seeking. *High:* Falstaff, Tigger, Gatsby throwing the party. *Low:* Bartleby, Boo Radley, the person who leaves the party through the bathroom window.
- **Agreeableness** — compassion, cooperativeness, trust, deference to others' needs. *High:* Samwise Gamgee, the nurse who cannot say no. *Low:* Gregory House, Miranda Priestly, the person who assumes everyone is running an angle.
- **Neuroticism** (inverse: Emotional Stability) — proneness to anxiety, anger, depression, self-consciousness, vulnerability to stress. *High:* Hamlet, the Woody Allen persona, C-3PO. *Low:* James Bond, the paramedic who is calm because everyone else is screaming.

**The 10 aspects (DeYoung, Quilty & Peterson, 2007)** — the useful mid-level, two per domain, that distinguishes two "high-X" people:

- Openness → **Openness** (aesthetic/perceptual/imaginative) + **Intellect** (abstract, idea-driven).
- Conscientiousness → **Industriousness** (drive, follow-through) + **Orderliness** (tidiness, routine, rule-adherence).
- Extraversion → **Enthusiasm** (warmth, sociability, positive affect) + **Assertiveness** (drive, dominance, agency).
- Agreeableness → **Compassion** (empathy, care for others' feelings) + **Politeness** (respect, restraint from aggression/exploitation).
- Neuroticism → **Volatility** (irritability, anger, emotional swing — the outward face) + **Withdrawal** (anxiety, depression, avoidance — the inward face).

The aspect level is where two people who both score "high Extraversion" split into the *warm-enthusiastic* host and the *dominant-assertive* commander; two "high N" people split into the one who explodes (Volatility) and the one who broods (Withdrawal).

**The 30 facets (NEO-PI-R, Costa & McCrae)** — six per domain, the finest published grain:

- **Neuroticism:** Anxiety · Angry Hostility · Depression · Self-Consciousness · Impulsiveness · Vulnerability.
- **Extraversion:** Warmth · Gregariousness · Assertiveness · Activity · Excitement-Seeking · Positive Emotions.
- **Openness:** Fantasy · Aesthetics · Feelings · Actions · Ideas · Values.
- **Agreeableness:** Trust · Straightforwardness · Altruism · Compliance · Modesty · Tender-Mindedness.
- **Conscientiousness:** Competence · Order · Dutifulness · Achievement-Striving · Self-Discipline · Deliberation.

**The 2 metatraits (Digman 1997; DeYoung et al. 2002)** — the two highest-order factors, above the five, with no general factor above them. Digman first recovered them from the inter-correlations of the Big Five and gave them the provisional labels **α (Alpha)** and **β (Beta)**; DeYoung, Peterson & Higgins (2002) renamed them for their putative biological substrates:

- **Plasticity** (Digman's β) = Extraversion + Openness (the drive to *explore* and integrate new information, engage novelty — tied to dopaminergic exploration).
- **Stability** (Digman's α) = Agreeableness + Conscientiousness + Emotional Stability (the drive to *maintain* stable goal-directed, social, and emotional functioning — tied to serotonergic regulation).

**How both extremes read on the page** (the load-bearing craft table):

| Domain | High reads as… | Low reads as… | The trap at each pole |
|---|---|---|---|
| O | curious, inventive, sees connections, unconventional | grounded, practical, conventional, values the tried | High → flighty, pretentious, "so open-minded their brain falls out." Low → philistine, incurious, bigoted-by-habit |
| C | reliable, disciplined, thorough, keeps the promise | spontaneous, flexible, relaxed, improvises | High → rigid, workaholic, joyless perfectionist. Low → flaky, chaotic, the one who let everyone down |
| E | warm, bold, energising, fills the room | calm, self-contained, deep, needs no audience | High → domineering, exhausting, needs the spotlight. Low → cold, aloof, invisible, the wallflower |
| A | kind, trusting, cooperative, forgives | tough, sceptical, competitive, holds the line | High → doormat, naïve, conflict-avoidant to a fault. Low → callous, suspicious, contrarian |
| N | sensitive, alert to threat, deeply feeling, cautious | steady, unflappable, resilient under fire | High → anxious wreck, volatile, catastrophising. Low → oblivious to danger, flat, hard to move |

Both directions are *characters*. The reader-realism does not come from where the mean sits; it comes from the mean plus the situation that pushes the sample toward a tail — the low-C improviser who becomes meticulous the one time it is about their daughter's safety.

**What it gives you for character depth.** The lingua franca: the five dimensions the entire field, most readers' intuitions, and every adjacent model translate through. The facet grain lets you distinguish two "warm" people (one high-Warmth low-Assertiveness, one the reverse) without inventing a bespoke attribute — a *structured* refinement (facet → aspect → domain → metatrait), which is why the repo goes fine-grain here without lever-sprawl (`docs/trait-theory.md`). It is the observer-realism layer: strangers read Extraversion, then Conscientiousness, then Agreeableness off seconds of nonverbal behaviour (thin-slicing), so these are the traits your prose must *show* first.

**Combines-with.** HEXACO is the Big Five with Honesty-Humility broken out and Agreeableness/Neuroticism reorganised — everything here carries over. The 16PF's five global factors *are* the Big Five (Extraversion, Anxiety≈N, Tough-Mindedness≈low-O, Independence≈low-A, Self-Control≈C). Eysenck's PEN nests inside it (E=E, N=N, P≈low-A+low-C). The interpersonal circumplex is the plane spanned by Extraversion and Agreeableness rotated 45°. The Panksepp affective basis (`docs/generative-model.md`) underlies the domains: Extraversion tracks SEEKING/PLAY reward-drive, Neuroticism tracks FEAR/RAGE/PANIC-GRIEF threat-sensitivity, Agreeableness tracks CARE — so the trait means bias which primaries fire. Whole Trait Theory converts each domain/facet into the (mean, variability) the repo stores.

**Cautions.** (1) *Descriptive, not causal* — it names the pattern, never the mechanism; do not treat "high N" as an explanation of why she panicked, it *is* the panicking, summarised. (2) *The horoscope trap* — five broad labels invite Barnum-statement flattening ("a curious yet cautious soul"); depth lives at facet/aspect grain and in the tails, not the domain label. (3) *Openness is the weakest, least cross-culturally stable factor* and blends intellect with aesthetics awkwardly. (4) *It buries morality* — honesty/manipulation smears across Agreeableness and Conscientiousness, which is exactly the gap HEXACO fixes and exactly the axis drama needs. (5) The **general factor of personality** (a single "good personality" factor some claim sits above the metatraits) is contested and probably an artefact of evaluative bias — don't build on it.

**Sources.** Costa & McCrae, *NEO-PI-R Professional Manual* (1992); Goldberg, "The structure of phenotypic personality traits" (*American Psychologist*, 1993); DeYoung, Quilty & Peterson, "Between facets and domains: 10 aspects of the Big Five" (*JPSP*, 2007); Digman, "Higher-order factors of the Big Five" (*JPSP*, 1997, the α/β metatraits); DeYoung, Peterson & Higgins, "Higher-order factors of the Big Five predict conformity" (*Personality and Individual Differences*, 2002, the Stability/Plasticity relabel); John, Naumann & Soto, "Paradigm shift to the integrative Big Five taxonomy" (*Handbook of Personality*, 2008); Tupes & Christal (1961/1992).

---

## HEXACO — the six-factor model and Honesty-Humility (repo default)

**Lineage.** Kibeom **Lee** & Michael **Ashton** (2000s), from lexical studies in a dozen-plus languages (Korean, French, German, Italian, Dutch, Polish, Hungarian…). When you factor the trait vocabulary of *most* languages, a **sixth** factor recurs that English-only studies had folded into Agreeableness. HEXACO-PI-R is the instrument.

**Core idea.** Six dimensions, not five. The new one — **Honesty-Humility** — captures the fairness/sincerity/modesty/non-greed axis that the Big Five smears across Agreeableness. Adding it predicts unethical, exploitative, and deceptive behaviour *over and above* the Big Five, and it reorganises two neighbours: HEXACO **Agreeableness** absorbs the anger/patience content (so quick temper is *low A*, not high N), and HEXACO **Emotionality** is Neuroticism minus anger, plus attachment and sentimentality. **This is the repo's trait spine** (`docs/trait-theory.md`): moral character (integrity ↔ manipulation) is central to drama, and HEXACO is the mainstream model that makes it a first-class dimension rather than a buried facet.

**Structure in full.** Six factors, each with four facets, plus one interstitial facet (Altruism) that loads across three factors:

- **H — Honesty-Humility:** *Sincerity* (genuine in relationships, no flattery) · *Fairness* (avoids fraud/corruption) · *Greed-Avoidance* (uninterested in wealth, luxury, status) · *Modesty* (unassuming, no entitlement).
- **E — Emotionality:** *Fearfulness* (experiences fear, avoids harm) · *Anxiety* (worries across contexts) · *Dependence* (needs emotional support) · *Sentimentality* (feels strong bonds, empathic attachment).
- **X — eXtraversion:** *Social Self-Esteem* (positive self-regard socially) · *Social Boldness* (confidence in social situations) · *Sociability* (enjoys company, conversation) · *Liveliness* (enthusiasm, energy, optimism).
- **A — Agreeableness (vs Anger):** *Forgivingness* (trusts/likes again after harm) · *Gentleness* (mild, lenient) · *Flexibility* (compromises, cooperates) · *Patience* (stays calm rather than angry).
- **C — Conscientiousness:** *Organization* (order in surroundings) · *Diligence* (works hard) · *Perfectionism* (thorough, detail-concerned) · *Prudence* (deliberates, inhibits impulse).
- **O — Openness to Experience:** *Aesthetic Appreciation* (beauty in art/nature) · *Inquisitiveness* (seeks knowledge of world) · *Creativity* (innovates, experiments) · *Unconventionality* (accepts the unusual).
- **Interstitial: Altruism (vs Antagonism)** — sympathy and soft-heartedness; splits its loading across H, E, and A. The tender core the three prosocial factors share.

**How the H extreme reads on the page** (the axis the Big Five hides — and the one drama lives on):

| | High H reads as… | Low H reads as… |
|---|---|---|
| in dialogue | plain-spoken, refuses flattery, admits fault, declines the bribe without deliberation | charming when useful, name-drops, cultivates people they can use, entitled to exceptions |
| under temptation | leaves money on the table because it isn't theirs | takes it and constructs the justification before the guilt arrives |
| exemplars | Ned Stark, Atticus Finch, Cordelia (*Lear*), Samwise | Littlefinger, Iago, Gordon Gekko, Tom Ripley, Frank Underwood |

Ned Stark is the whole point of H: high honour is not a bonus stat, it is the tragic lever — it gets him killed in a world of low-H players. That is HEXACO doing narrative work the Big Five cannot.

**What it gives you for character depth.** A dedicated **moral-character axis** that turns "good vs evil" from an authorial verdict into a trait continuum with a mechanism: villains are not a separate species, they are the **low-H corner** of the same space everyone lives in. This is the repo's design (`docs/trait-theory.md`): no bolt-on dark system, a *region* (low H, often with low A and low E) plus named antagonist overlays. Because H is separable from warmth (A) and boldness (X), you can build the *charming sincere hero* (high H, high X), the *cold honest ascetic* (high H, low X, low A), the *warm manipulator* (low H, high X, high A-surface) — the last being the most dangerous and most interesting character in fiction.

**Combines-with.** HEXACO ⊃ Big Five: X/C/O map almost directly; HEXACO-A + HEXACO-H together ≈ Big-Five-A; HEXACO-E ≈ Big-Five-N minus anger plus attachment. The **Dark Triad/Tetrad** projects onto **low H** (see below) — the single cleanest cross-link in this file. **Honesty-Humility ↔ Schwartz values** (`docs/values-and-stakes.md`): low H aligns with power/achievement (self-enhancement), high H with universalism/benevolence (self-transcendence) — Lee & Ashton mapped this at facet level. **H ↔ Moral Foundations:** low H predicts weighting fairness/cheating and care/harm lightly relative to self-interest. **E ↔ Panksepp FEAR & PANIC-GRIEF** and the drives-schema fear family. The repo stores each HEXACO factor and facet as a **(mean, variability)** pair (Whole Trait Theory) and derives metatraits as a summary view.

**Cautions.** (1) *H is not "niceness"* — a high-H person can be cold and blunt (low A, low warmth) yet scrupulously fair; conflating H with Agreeableness loses the whole contribution. (2) *Low H alone is not a villain* — it needs opportunity, low empathy, and (for the dark presets) specific overlays; a low-H, high-A, high-H-Emotionality person is a charming rogue, not a monster. (3) HEXACO-A carrying the anger content means you must not double-count temper in Emotionality. (4) The six-factor solution is well-replicated but the field is not unanimous that H is *fully* independent of Agreeableness across all instruments — treat the reorganisation as a strong default, not settled fact.

**Sources.** Ashton & Lee, "Empirical, theoretical, and practical advantages of the HEXACO model" (*Personality and Social Psychology Review*, 2007); Lee & Ashton, *The H Factor of Personality* (2012); Ashton, Lee & de Vries, "The HEXACO Honesty-Humility, Agreeableness, and Emotionality factors" (*PSPR*, 2014); hexaco.org scale descriptions.

---

## Eysenck's PEN — the biological three-factor model

**Lineage.** Hans **Eysenck** (and Sybil Eysenck), 1947–1985, London. The great rival tradition to lexical factor-solutions: fewer, *biologically grounded* super-factors derived top-down from theory and physiology rather than bottom-up from vocabulary.

**Core idea.** Personality reduces to **three** independent super-factors, each tied to a proposed physiological substrate. Fewer factors than the Big Five, but each carrying a causal-mechanism claim — Eysenck insisted a trait dimension is only real if it has a biological basis and a heritable one. The dimensions are hierarchical: super-factor → traits → habitual responses → specific responses.

**Structure in full.**

- **E — Extraversion–Introversion.** Sociability, liveliness, stimulation-seeking. *Mechanism (the famous claim):* differences in **cortical arousal** — introverts are chronically *more* aroused, so they seek *less* external stimulation (they're already at optimum); extraverts are under-aroused and chase stimulation to reach it. Explains why the introvert leaves the loud party and the extravert throws it.
- **N — Neuroticism–Stability.** Emotional reactivity, anxiety, moodiness. *Mechanism:* lability of the **autonomic/limbic (visceral) nervous system** — high-N people have a hair-trigger fight-or-flight response that fires hard and settles slowly.
- **P — Psychoticism.** Toughmindedness, aggression, egocentrism, coldness, impulsivity, non-conformity, lack of empathy — a dimension of *antisocial/creative-unrestrained* disposition (poorly named; it is not "psychosis"). Added later (1970s). *Mechanism (weaker):* proposed links to testosterone and low monoamine-oxidase/serotonin. High P shades toward criminality, callousness, and — Eysenck argued — creative genius.

**Vivid exemplars.** The stable extravert (low N, high E) — a cheerful salesman, Falstaff. The anxious introvert (high N, low E) — Hamlet, the trembling clerk. The stable introvert (low N, low E) — the unflappable lighthouse keeper, Spock. The high-P figure — the cold, rule-breaking operator: a Moriarty, a Tyler Durden, the amoral artist who treats other people as material.

**What it gives you for character depth.** The **arousal engine** — a physiological *why* under the descriptive *what*. It is genuinely useful for writing the body: the introvert's overload in a crowded market, the extravert going flat and irritable in solitary confinement, the high-N character whose hands are already shaking before the threat is named. P is a compact proto-"dark" axis decades before the Dark Triad. And PEN's small N of super-factors is a virtue for a sparse-authoring engine: three dials get you most of the behavioural signal.

**Combines-with.** E and N are essentially identical to Big-Five E and N. **P ≈ low Agreeableness + low Conscientiousness** (and maps onto **low Honesty-Humility** + low A) — so PEN's P is an early, cruder version of the low-H/Dark-Triad region. Eysenck's arousal theory feeds the repo's **energy/state layer** (`docs/state-engine.md`, Thayer's arousal dimensions in `emotion-and-decision`): trait-E sets the baseline arousal set-point that state modulates. Gray's RST (below) grew directly out of critiquing Eysenck's arousal account.

**Cautions.** (1) The **cortical-arousal theory is not well-supported** by modern neuroscience in its original form — cite it as historically pivotal and phenomenologically evocative, not as established mechanism. (2) *Psychoticism* is a badly named, psychometrically weaker factor that conflates several things (impulsivity, aggression, low empathy, unconventionality) later split apart by HEXACO and the Dark Triad. (3) Three factors *under-carve* the space — Openness has nowhere clean to go, and Agreeableness/Conscientiousness collapse into P. Use PEN for its mechanism flavour, not as your primary taxonomy.

**Sources.** Eysenck, *Dimensions of Personality* (1947) and *The Biological Basis of Personality* (1967); Eysenck & Eysenck, *Personality and Individual Differences* (1985); Matthews, Deary & Whiteman, *Personality Traits* (2009), ch. on biological theories.

---

## Cattell's 16PF — the sixteen primary factors

**Lineage.** Raymond **Cattell**, 1949 onward (Sixteen Personality Factor Questionnaire, now 5th ed.). The bottom-up lexical pioneer: Cattell took Allport & Odbert's ~18,000 words, compressed them to ~171 clusters, then ~35 "surface traits", then factor-analysed to **16 "source traits"** he held to be the underlying causal dimensions.

**Core idea.** Personality is best described at a *finer* grain than five — sixteen primary factors, each a bipolar continuum, which is where the useful predictive detail lives. The five broad factors (which Cattell's own data foreshadowed) are second-order *global* factors sitting above the sixteen. More granular than the Big Five, and explicitly hierarchical: 16 primaries → 5 globals.

**Structure in full.** The sixteen primary factors (letter-coded; each bipolar):

- **A — Warmth** (reserved ↔ warm/outgoing)
- **B — Reasoning** (concrete ↔ abstract; effectively a brief intelligence measure)
- **C — Emotional Stability** (reactive ↔ emotionally stable)
- **E — Dominance** (deferential ↔ dominant/assertive)
- **F — Liveliness** (serious ↔ lively/spontaneous)
- **G — Rule-Consciousness** (expedient ↔ rule-conscious/dutiful)
- **H — Social Boldness** (shy/timid ↔ socially bold/venturesome)
- **I — Sensitivity** (utilitarian/tough ↔ sensitive/tender-minded)
- **L — Vigilance** (trusting ↔ vigilant/suspicious)
- **M — Abstractedness** (grounded/practical ↔ abstracted/imaginative)
- **N — Privateness** (forthright ↔ private/discreet)
- **O — Apprehension** (self-assured ↔ apprehensive/self-doubting)
- **Q1 — Openness to Change** (traditional ↔ open to change/experimenting)
- **Q2 — Self-Reliance** (group-oriented ↔ self-reliant/solitary)
- **Q3 — Perfectionism** (tolerates disorder ↔ perfectionistic/self-disciplined)
- **Q4 — Tension** (relaxed ↔ tense/driven)

The five **global factors** (second-order): **Extraversion** (from A, F, H, N−, Q2−), **Anxiety** (C−, L, O, Q4), **Tough-Mindedness** (A−, I−, M−, Q1−), **Independence** (E, H, L, Q1), **Self-Control** (F−, G, M−, Q3) — mapping onto Big Five E, N, low-O, low-A, and C respectively.

**Vivid exemplars.** The 16 factors are most useful as a *mixing palette* for a distinctive silhouette: a character high on **L (Vigilance)** and **N (Privateness)** but low on **O (Apprehension)** is the calm, guarded spymaster who trusts no one and never sweats (George Smiley). High **E (Dominance)** + high **F (Liveliness)** + low **G (Rule-Consciousness)** is the charismatic rogue leader (Han Solo). High **I (Sensitivity)** + high **M (Abstractedness)** + high **O (Apprehension)** is the trembling poet.

**What it gives you for character depth.** The most granular *published, factor-derived* palette — sixteen independent dials give combinatorial room for silhouettes the five-factor level blurs together. Several primaries (Vigilance, Privateness, Abstractedness, Apprehension, Self-Reliance) name behavioural textures the Big Five domains don't isolate, and they translate straight into observable habits (the *private* character deflects personal questions; the *vigilant* one scans exits). It demonstrates the hierarchy principle the repo relies on: fine primaries roll up into broad globals, so you can author at either altitude.

**Combines-with.** The five globals *are* the Big Five, so 16PF is a finer carving of the same space — a bridge between OCEAN domains and NEO facets. Its Factor B (Reasoning) folds in a cognitive-ability dimension the pure personality models exclude (useful for the repo's **skills** layer). Vigilance/Privateness map onto the interpersonal circumplex's cold/aloof octants; Dominance is the circumplex's agency axis directly.

**Cautions.** (1) Cattell's 16-factor solution has **poor replicability** — independent analyses rarely recover his sixteen, and most collapse to five; treat the sixteen as a rich descriptive vocabulary, not a validated dimensional structure. (2) The letter-coding (A, B, C… skipping some) is opaque and easy to misuse. (3) High grain risks the over-specification the repo warns against (`docs/character-model.md`, "more levers ≠ more real") — pull individual factors for a *specific* texture, don't author all sixteen. (4) Factor B (Reasoning) is a short, weak intelligence proxy, not a real cognitive measure.

**Sources.** Cattell, *The Description and Measurement of Personality* (1946) and *Personality and Motivation Structure and Measurement* (1957); Cattell & Mead, "The Sixteen Personality Factor Questionnaire (16PF)" (in *The SAGE Handbook of Personality Theory and Assessment*, 2008); Boyle et al. critiques of replicability.

---

## The Dark Triad and Dark Tetrad — the aversive-personality cluster

**Lineage.** **Delroy Paulhus & Kevin Williams** coined "Dark Triad" (2002), pulling together three previously separate lines: **Machiavellianism** (Christie & Geis, 1970, from Machiavelli's *The Prince*), subclinical **narcissism** (from clinical NPD, measured by the NPI, Raskin & Hall), and subclinical **psychopathy** (Hare's clinical construct, brought subclinical by the SRP/LSRP). **Chabrol et al. (2009)** first proposed extending it to a **Dark Tetrad** by adding **sadism**; **Buckels, Jones & Paulhus (2013)** gave "everyday sadism" its behavioural confirmation and standard measure, and Paulhus (2014) popularised the four-trait frame.

**Core idea.** Three (or four) *distinct but overlapping* socially aversive traits, all sitting in the normal (subclinical) population, sharing a callous-manipulative core but differing in flavour and strategy. They are correlated but separable: knowing someone is high on one does not tell you which of the others they carry. All are *dispositions to advance the self at others' expense* — the difference is *how*.

**Structure in full.**

- **Machiavellianism** — strategic, cynical, long-game manipulation; deceit, calculation, a low view of human nature, ends-justify-means pragmatism, emotional detachment in service of goals. The planner. *The chess-player of the three.*
- **Narcissism** — grandiosity, entitlement, need for admiration, superiority, low empathy, ego-fragility beneath the grandiosity (narcissistic injury). The self-aggrandiser. *Splits into grandiose (bold, dominant) and vulnerable (fragile, resentful) sub-forms.*
- **Psychopathy** — the "darkest" — callousness plus **impulsivity** and thrill-seeking, shallow affect, lack of remorse or anxiety, superficial charm. The one that most predicts overt antisocial behaviour. *The impulsive predator — unlike Machiavellianism's patient scheming.*
- **Sadism** (Tetrad) — deriving *pleasure* from others' pain; cruelty as intrinsically rewarding, not merely instrumental. The distinguishing mark: the others hurt you to get something; the sadist hurts you because hurting is the point. "Everyday sadism" ranges from trolls to those who enjoy violent media to the guard who lingers.

**The shared core — the D factor** (Moshagen, Hilbig & Zettler, 2018). Beneath all the dark traits sits a single **general dark disposition, "D"**: *the tendency to maximise one's own utility at the expense of others, accompanied by beliefs that serve as justifications.* The nine studied dark traits — egoism, Machiavellianism, moral disengagement, narcissism, psychological entitlement, psychopathy, sadism, self-interest, spitefulness — are specific manifestations of this one core, the way the Big Five domains are facet-clusters. D is more stable over time than any individual dark trait and predicts them all. **This is the theoretical justification for the repo's design** (`docs/trait-theory.md`): the dark traits are not a separate system, they are a **region** of trait space, and D is that region's centre.

**Vivid exemplars.** Machiavellianism: Iago, Frank Underwood, Petyr Baelish, Lady Macbeth, Amy Dunne (with narcissism). Narcissism: Patrick Bateman, Gilderoy Lockhart, Jay Gatsby (softer, aspirational form), Miranda Priestly (grandiose competence). Psychopathy: Anton Chigurh, Hannibal Lecter (with sadism and immense Mach), the Joker (chaotic variant). Sadism: Ramsay Bolton, Joffrey Baratheon, Dolores Umbridge (the bureaucratic sadist — cruelty in a cardigan), O'Brien in *1984*.

**What it gives you for character depth.** A precise **antagonist vocabulary** that replaces "evil" with a mechanism and a *strategy*: the schemer, the self-worshipper, the impulsive predator, the connoisseur of pain behave *differently* and fail differently. Distinguishing them prevents the generic-villain trap — Iago (patient Mach) and the Joker (impulsive psychopathy) are not interchangeable. The grandiose/vulnerable narcissism split is a whole tragic engine (the ego-fragility beneath the grandiosity — the bully who cannot survive being laughed at). And the D-core lets you place any villain on a continuum with ordinary self-interest, which is what makes the best ones frightening — they are us, dialled.

**Combines-with.** The cleanest projection: **Dark Triad = low Honesty-Humility, plus low Agreeableness (all), plus for psychopathy low Conscientiousness (impulsivity) and low Emotionality/Neuroticism (fearlessness).** So in the repo's HEXACO frame, a villain is authored as a **low-H trait profile with a named dark overlay** (Mach / narcissist / psychopath / sadist) as an antagonist preset — *no separate dark subsystem* (`docs/trait-theory.md`). D maps onto the low pole of the Light Triad's axes (below). Psychopathy's fearlessness = low Panksepp FEAR; sadism = RAGE/dominance uncoupled from CARE (`docs/generative-model.md`: "cruelty = RAGE unchecked by CARE"). In `docs/values-and-stakes.md` terms, low-H/high-D means self-enhancement values (power, achievement) crush self-transcendence, and Moral-Foundations weights on care/fairness collapse toward zero — with **moral disengagement** as the belief-machinery that supplies the justifications.

**Cautions.** (1) *Overlap is real but they are separable* — do not collapse a Machiavellian into a psychopath; the strategic/impulsive distinction is the whole point. (2) **Subclinical ≠ clinical** — these are normal-range personality traits, not diagnoses (NPD, ASPD); a Dark-Triad character is a manipulator, not a case study, and framing them as "mentally ill" is both inaccurate and a lazy cliché. (3) *The competence halo* — fiction tends to make Machiavellians hyper-competent chess-masters; real high-Mach people fail, misread rooms, and are often caught (the "smart villain" is a genre convention, not a finding). (4) *Grandiose vs vulnerable narcissism* behave oppositely (bold-dominant vs fragile-resentful) — pick one. (5) Cliché-trap: the monologuing sadist. Umbridge works because her cruelty is banal and administrative; the more the sadism performs, the less it frightens.

**Sources.** Paulhus & Williams, "The Dark Triad of personality" (*Journal of Research in Personality*, 2002); Chabrol, Van Leeuwen, Rodgers & Séjourné, "Contributions of psychopathic, narcissistic, Machiavellian, and sadistic personality traits to juvenile delinquency" (*Personality and Individual Differences*, 2009 — the Dark Tetrad's first formulation); Buckels, Jones & Paulhus, "Behavioral confirmation of everyday sadism" (*Psychological Science*, 2013); Moshagen, Hilbig & Zettler, "The dark core of personality" (*Psychological Review*, 2018); Jones & Paulhus, "Introducing the Short Dark Triad (SD3)" (*Assessment*, 2014); Christie & Geis, *Studies in Machiavellianism* (1970).

---

## The Light Triad — the loving, everyday-saint orientation

**Lineage.** Scott Barry **Kaufman**, David Yaden, Elizabeth Hyde & Eli Tsukayama, "The Light vs. Dark Triad of Personality" (*Frontiers in Psychology*, 2019). Built explicitly as the counterweight to the Dark Triad — a measure of a *beneficent orientation toward others*, the "everyday saints."

**Core idea.** Rather than treating good as merely the *absence* of dark traits, the Light Triad measures a *positive* disposition to see and treat others as valuable. It is **not the mathematical opposite** of the Dark Triad — the correlation is moderately negative (~−0.5), not −1.0 — so a person can carry some of both, and most people load higher on Light than Dark. It taps a loving, forgiving, trusting stance toward human beings as such.

**Structure in full.** Three facets:

- **Kantianism** — treating people as **ends in themselves**, never merely as means (from Kant's second formulation of the categorical imperative). Refuses to instrumentalise or manipulate; deals with people straight because using them is wrong in itself. *The direct inverse of Machiavellianism.*
- **Humanism** — **valuing the dignity and worth of each individual**. Sees inherent value in every person, celebrates others' successes without envy. *The inverse of narcissism's zero-sum superiority.*
- **Faith in Humanity** — **believing in the fundamental goodness of people**. Trusts, assumes good intent, is not cynical about human nature. *The inverse of psychopathy's callous suspicion.*

Correlates: higher Light-Triad loading tracks with higher Agreeableness, higher Honesty-Humility, secure attachment, compassion, life satisfaction, and — notably — a *history of being loved* and lower self-focus; it does **not** require low competence or naïveté (Kaufman stressed the "everyday saints" are not pushovers).

**Vivid exemplars.** Ted Lasso, Samwise Gamgee, Paddington Bear, Atticus Finch, the Mister Rogers archetype, Jean Valjean (post-redemption), Marge Gunderson (*Fargo*) — competent, warm, and unfailingly assuming the good in people without being fools. The narrative interest of the pure Light-Triad character is precisely that they are *tested* against a low-H/high-D world and mostly *do not break* (Valjean's mercy toward Javert; Lasso's kindness weaponised as strength).

**What it gives you for character depth.** A *positive* moral vocabulary so your good characters are more than un-villains — Kantianism, Humanism, and Faith-in-Humanity are three distinct virtues that can be **dialled independently and put in tension**: the character with high Faith-in-Humanity but wavering Kantianism (trusts everyone, yet will use a person "for their own good") is a specific, flawed, interesting saint. Because Light and Dark are near-orthogonal, you can build the *ambivalent* character who carries real warmth *and* real manipulation (the loving parent who lies to control) — richer than a pure-pole hero. It also gives redemption arcs a target: an arc from Dark toward Light is a measurable shift in these three.

**Combines-with.** Directly inverts the Dark Triad facet-for-facet (Kantianism↔Mach, Humanism↔narcissism, Faith↔psychopathy), so the two triads together define a **single evaluative axis with the low-H/D pole at one end and the high-H/Light pole at the other** — the clean moral continuum for the repo's HEXACO spine. High Light ≈ high Honesty-Humility + high Agreeableness + high Emotionality-Sentimentality. In `docs/generative-model.md` terms, Light-Triad warmth is high CARE well-coupled to action; in `docs/values-and-stakes.md`, it is self-transcendence values (benevolence, universalism) and heavy Moral-Foundations weight on care/fairness.

**Cautions.** (1) *Not the opposite of dark* — treating Light as −Dark loses the whole point (the moderate, not perfect, negative correlation is the finding); people are mixtures. (2) *The saccharine trap* — a maxed Light-Triad character with no counter-pull reads as sentimental and inert; give them a cost (their trust is exploited, their mercy endangers others) or a competing drive, or they are cardboard the way a maxed dark character is. (3) The scale is young (2019) and less validated than the Dark Triad or Big Five — cite it as a promising positive-psychology frame, not bedrock. (4) High Light-Triad does *not* imply low competence, low assertiveness, or naïveté — resist writing the good character as a weak one.

**Sources.** Kaufman, Yaden, Hyde & Tsukayama, "The Light vs. Dark Triad of Personality" (*Frontiers in Psychology*, 2019); Neumann, Kaufman et al., structural-validity follow-ups (2020); Kaufman, *popular writing at Scientific American / The Atlantic* on everyday saints.

---

## The Interpersonal Circumplex — personality as a two-axis circle of social behaviour

**Lineage.** Timothy **Leary** and the Kaiser Foundation group (1950s, *Interpersonal Diagnosis of Personality*) built the first version for psychotherapy; **Jerry Wiggins** (1979 onward) formalised it factor-analytically (the Interpersonal Adjective Scales, IAS), and it connects to Bakan's (1966) "Big Two" of **Agency and Communion**. A model of *interpersonal* behaviour specifically, not global personality.

**Core idea.** All interpersonal behaviour, trait, motive, and problem can be located on a **circle** (a circumplex) defined by two orthogonal axes: **Agency/Dominance** (vertical: dominant ↔ submissive) and **Communion/Affiliation** (horizontal: warm/friendly ↔ cold/hostile). Everything social is a *blend* of these two, and its position on the circle is its identity. Two properties make it powerful: **complementarity** (behaviours pull predictable responses — dominance invites submission, warmth invites warmth, hostility invites hostility) and the fact that opposite points on the circle are opposite behaviours.

**Structure in full.** Two axes and **eight octants** (Wiggins' two-letter codes), each a blend:

- **PA — Assured-Dominant** (high agency, neutral communion): commanding, self-assured, takes charge. *Miranda Priestly.*
- **BC — Arrogant-Calculating** (dominant + cold): scheming, exploitative, superior. *Littlefinger. — the low-H/Dark octant.*
- **DE — Cold-Hearted** (cold, neutral agency): unfeeling, callous, detached. *Anton Chigurh.*
- **FG — Aloof-Introverted** (cold + submissive): withdrawn, distant, avoidant. *Boo Radley, early.*
- **HI — Unassured-Submissive** (low agency, neutral communion): meek, self-doubting, yielding. *Neville Longbottom, early.*
- **JK — Unassuming-Ingenuous** (submissive + warm): modest, deferential, trusting-to-a-fault. *Forrest Gump.*
- **LM — Warm-Agreeable** (warm, neutral agency): friendly, cooperative, tender. *Samwise Gamgee.*
- **NO — Gregarious-Extraverted** (warm + dominant): outgoing, sociable, sunny-commanding. *Falstaff, Gatsby-hosting.*

A person's interpersonal *style* is a vector: a direction (which octant) and a length (how extreme/rigid — the intensity of the interpersonal signal).

**Vivid exemplars.** (Woven above, per octant.) The model's special use is *pairs and scenes*: complementarity predicts the dance. A PA (assured-dominant) boss and an HI (unassured-submissive) new hire *lock* — his dominance pulls her submission, her submission confirms his dominance; the drama comes when she moves toward PA herself (defiance) and breaks the complement. A BC (arrogant-calculating) manipulator working an LM (warm-agreeable) mark is the standard con.

**What it gives you for character depth.** The only model here built for the **space between two people**, not inside one. It gives you: (1) a compact two-dial handle on *social presence* — where a character sits on warmth × dominance is most of what a stranger reads in a first scene; (2) **complementarity** as a scene-engine — a reliable default for how another character will *respond*, and a vivid signal when someone *breaks* it (answering hostility with warmth, dominance with dominance); (3) **rigidity vs flexibility** — a healthy character moves around the circle as situations demand; a character *stuck* in one octant (always dominant, always submissive) is exactly a personality problem, which is how the model is used clinically and how you write a character's interpersonal wound.

**Combines-with.** The two axes are the **Big Five's Extraversion and Agreeableness rotated 45°** (Agency ≈ a blend leaning Extraversion-Assertiveness; Communion ≈ Agreeableness-Compassion) — so it is a *social close-up* on two OCEAN domains. The **Big Two (Agency/Communion)** it rests on is one of personality psychology's deepest structures and underlies McAdams' and the values literature's framing too. The Agency axis = 16PF Dominance (E) and the assertiveness aspect; the BC/DE octants = the low-H/Dark-Triad region on the social surface. Complementarity feeds the repo's **relationships** layer (`docs/relationships.md`) and the emotion/ToM reading of another's stance (`emotion-and-decision`).

**Cautions.** (1) It models *interpersonal behaviour only* — no Openness, no Conscientiousness, no inner life; it is a lens on the social surface, not a whole-person model. (2) **Complementarity is a tendency, not a law** — real interactions violate it constantly (that's often the interesting beat); don't let it flatten scenes into mechanical call-and-response. (3) The octant labels carry evaluative baggage ("arrogant", "cold-hearted") — they name *styles*, and a "cold-hearted" reading in one scene may be grief or self-protection, not disposition. (4) A character's *momentary* position (state) is not their *trait* position (baseline) — the circumplex confuses the two unless you hold the Whole-Trait (mean, variability) distinction.

**Sources.** Leary, *Interpersonal Diagnosis of Personality* (1957); Wiggins, "A psychological taxonomy of trait-descriptive terms: the interpersonal domain" (*JPSP*, 1979); Horowitz et al., *Interpersonal Foundations of Psychopathology*; Bakan, *The Duality of Human Existence* (1966); Gurtman, "Exploring Personality with the Interpersonal Circumplex."

---

## Whole Trait Theory — the trait as a density distribution (repo storage default)

**Lineage.** the author **Fleeson** (2001 onward), integrating trait theory with the person–situation debate; developed with Erik Noftle and others. Built on decades of experience-sampling data showing people vary *enormously* moment to moment.

**Core idea.** A trait is **not a fixed scalar** — it is a **density distribution of states**: a *mean* (the person's average level) *and* a *variability* (the spread they swing through). A "high-extraversion" person is not always outgoing; they are outgoing *on average*, sampling the whole range from life-of-the-party to withdrawn depending on the moment. The theory has two halves: a **descriptive** side (the distribution itself) and an **explanatory** side (the goals, interpretations, and situations that *produce* each momentary state). This is **the repo's storage model** (`docs/trait-theory.md`): every HEXACO factor and facet is stored as (mean, variability), not a point.

**Structure in full.**

- **Density distribution** — for any trait, the person's behaviour over time forms a roughly normal distribution of momentary states. Two parameters carry it: the **mean** (their central tendency — "the lean") and the **variability/SD** (how consistent vs erratic they are; a per-person parameter — some people are stable, some swing wildly).
- **Trait = the distribution, not the peak.** Two people with the same mean can differ in spread: one reliably medium-extraverted, one oscillating between hermit and showman around the same average.
- **The explanatory layer** — each momentary state is *caused*: by the situation, by the goal active in that moment, by how the person construes the event. States are not random draws; they are produced by the person × situation interaction. This is the bridge to *why*.
- **Out-of-character behaviour = a tail sample, and it is NOT noise.** The timid person acting brave is a draw from the far tail of their courage distribution — *produced* by a goal or value (protecting their child) overriding the trait-lean under pressure. The tails are where character-defining moments live.

**Vivid exemplars.** Not characters but *the mechanism inside* characters: the reserved professor (low-E mean) who is electric in front of a class he loves (a high-E tail sample, caused by the situation activating a goal); the even-tempered man (low-Volatility mean, but high variability) who, twice in the novel, detonates — rare tail events that *define* him precisely because they are rare; the reliably kind character whose single cruel act (a care-distribution tail under betrayal) is the scene readers never forget.

**What it gives you for character depth.** It **dissolves the central objection to trait models** — "but people aren't just one way" — by making the spread a first-class part of the trait. It is the exact bridge between the stable Level-1 disposition and the moment-to-moment `{thought, action}`: the trait sets the *distribution* the behaviour samples from; **state + situation + relationships shift *where in the distribution* this moment's sample falls** (`docs/trait-theory.md`, `docs/generative-model.md`). And it makes the repo's **realism test** mechanical: the memorable out-of-character beat is *surprising-given-the-lean* (a tail) yet *inevitable-given-the-motivation* (caused by a Level-2/3 drive overriding the trait) — surprise and earnedness are the same event seen from two ends. The `variability` parameter is itself a character knob: the consistent stoic vs the volatile firecracker can share a mean.

**Combines-with.** It is the *operating layer* under every other model in this file: any trait (OCEAN domain, HEXACO facet, circumplex octant, Dark-Triad score) becomes (mean, variability) and gets *sampled*, not read. It links Level 1 to the drives schema (`docs/drives-schema.md`): the explanatory side — goals, values, fears producing each state — *is* the Level-2/3 lever system, so traits don't compete with drives, they compose (trait = the style-distribution, drives = what produces the specific state within it). It feeds the decision engine (`docs/decision-engine.md`): effective disposition = baseline sample × state × situation × relationships. And it grounds `docs/generative-model.md`'s "determinism is the feature": surprise comes from vectors being *distributions not points*, so the same config samples differently — fully caused, not predictable.

**Cautions.** (1) *Don't let variability become an excuse* — if a character can sample anywhere, the trait means nothing; the spread must be bounded and the tail-draws must be *caused* by a named drive/situation, or you get inconsistency masquerading as depth (the repo's "arbitrary → not real" failure). (2) It is a *framework for using* traits, not a rival taxonomy — you still need OCEAN/HEXACO to say *what* varies. (3) Variability itself may be a trait (some people are reliably more variable), which risks infinite regress — treat it as one extra authored parameter, not a new tower. (4) The experience-sampling base is robust, but the precise mean/SD numbers are not portable across instruments — use it structurally (lean + spread + caused tails), not as literal psychometrics.

**Sources.** Fleeson, "Toward a structure- and process-integrated view of personality: traits as density distributions of states" (*JPSP*, 2001); Fleeson & Jayawickreme, "Whole Trait Theory" (*Journal of Research in Personality*, 2015); Jayawickreme, Zachry & Fleeson, whole-trait follow-ups.

---

## Adjacent: biological temperament models — Gray's RST, Cloninger's TCI, Rothbart

**Lineage & core idea.** Where the lexical models describe *what* varies, the **temperament** tradition asks what *neurobiological systems* the variation rides on — early-appearing, heritable, present in infancy and in animals. Three matter for characterisation.

- **Gray's Reinforcement Sensitivity Theory (RST)** — Jeffrey Gray (1970s–80s), revised by Gray & McNaughton (2000). Personality rides on three brain systems: the **BAS** (Behavioural Approach System — sensitivity to reward, drives approach, impulsivity, positive anticipation; ≈ Extraversion/SEEKING), the **FFFS** (Fight-Flight-Freeze System — sensitivity to punishment/threat, drives avoidance and fear; ≈ FEAR), and the **BIS** (Behavioural Inhibition System — activated by *goal conflict*, especially approach–avoidance; produces anxiety, rumination, risk-assessment, the freeze-and-scan; ≈ trait anxiety). The revised model cleanly separates **fear (FFFS)** from **anxiety (BIS)** — a distinction most trait models blur and one the Panksepp basis also honours.
- **Cloninger's psychobiological model (TCI)** — Robert Cloninger (1987/1993). Four **temperament** dimensions tied to neurotransmitters — **Novelty Seeking** (dopamine; exploratory, impulsive, quick-tempered), **Harm Avoidance** (serotonin; anxious, cautious, fatigable), **Reward Dependence** (norepinephrine; warm, approval-needing, sentimental), **Persistence** (perseverance despite frustration) — plus three **character** dimensions that mature with development — **Self-Directedness** (responsible, purposeful, mature), **Cooperativeness** (tolerant, empathic), **Self-Transcendence** (spiritual, part-of-a-whole). The temperament/character split maps loosely onto Level-1 disposition vs Level-2/3 adaptations.
- **Rothbart's developmental temperament** — Mary Rothbart. Infant temperament resolves into three factors: **Surgency/Extraversion** (approach, activity, positive affect), **Negative Affectivity** (fear, frustration, sadness), and **Effortful Control** (the self-regulation capacity — attention, inhibition — that becomes adult Conscientiousness). Shows where the adult traits *come from* developmentally.

**Vivid exemplars.** High-BAS/high-Novelty-Seeking: the restless adventurer who cannot sit still and chases every reward (Gatsby's yearning; the gambler). High-BIS/high-Harm-Avoidance: the vigilant worrier frozen at every fork (Hamlet's paralysis is BIS goal-conflict incarnate — approach [revenge] vs avoid [damnation, doubt]). High-Reward-Dependence: the warm soul who wilts without approval. High-Effortful-Control over high-Negative-Affectivity: the trembling character who acts steady anyway — courage as regulation, not absence of fear.

**What it gives you for character depth.** The **mechanistic *why*** under the descriptive traits — approach vs avoidance vs conflict-inhibition as separate engines, which lets you write the *body and the tempo* of a disposition (the BAS character leans in and grabs; the BIS character freezes and scans; the FFFS character flees). Gray's fear/anxiety split and Cloninger's temperament/character split are genuinely useful carvings the Big Five lacks. Rothbart's **Effortful Control** is the single best construct for writing *willpower and self-regulation* — courage, restraint, and discipline as an active system overriding Negative Affectivity, which is exactly `docs/generative-model.md`'s "virtue = a stronger pull overriding a registered fear, resolved."

**Combines-with.** BAS ≈ Extraversion ≈ Panksepp SEEKING/PLAY; FFFS ≈ Panksepp FEAR; BIS ≈ trait anxiety/Neuroticism-Withdrawal — so RST is the **neurobiological underlay of the repo's affective basis** (`docs/generative-model.md`), and the approach/avoid axis is the drives schema's `coping_engagement` (`docs/drives-schema.md`). Cloninger's character dimensions (Self-Directedness, Cooperativeness, Self-Transcendence) overlap Level-2/3 adaptations and Schwartz self-transcendence values. Rothbart's Effortful Control ≈ Conscientiousness and feeds the decision engine's regulation of impulse. All three convert to (mean, variability) under Whole Trait Theory.

**Cautions.** (1) The **neurotransmitter mappings are oversimplified** — "serotonin = harm avoidance", "dopamine = novelty seeking" are heuristics that the actual neuroscience does not cleanly support; use them for evocative flavour, not as fact. (2) These overlap heavily with the Big Five (don't author BAS *and* Extraversion as separate levers — pick the frame). (3) Cloninger's seven dimensions have mixed replicability. (4) Reach for these when you specifically want approach/avoidance *mechanism* or self-regulation texture; otherwise they add levers without adding signal (the repo's sweet-spot caution).

**Sources.** Gray & McNaughton, *The Neuropsychology of Anxiety* (2000); Corr (ed.), *The Reinforcement Sensitivity Theory of Personality* (2008); Cloninger, Svrakic & Przybeck, "A psychobiological model of temperament and character" (*Archives of General Psychiatry*, 1993); Rothbart, *Becoming Who We Are: Temperament and Personality in Development* (2011).

---

## How to reach into this file

Start from what the moment needs, not from a favourite model:

- **Authoring a character's stable style / a recognisable through-line** → **HEXACO** (repo default), stored as **(mean, variability)** per Whole Trait Theory. Use the **facet grain** only where a texture matters (sparse authoring — `docs/trait-theory.md`); default unspecified facets from the parent factor.
- **Writing a villain or a morally dark character** → the **low-Honesty-Humility region** plus a named **Dark-Triad/Tetrad overlay** (schemer / self-worshipper / impulsive predator / sadist), *not* a separate system; anchor it in the **D core** so the villain sits on a continuum with ordinary self-interest.
- **Writing a good character with a spine** → the **Light Triad** (Kantianism / Humanism / Faith in Humanity), dialled independently and given a cost so it isn't saccharine.
- **Staging a two-person scene** → the **Interpersonal Circumplex** (agency × communion, eight octants, complementarity) — the only model here built for the space *between* people; read where each sits, then honour or *break* the complement.
- **Needing the mechanism/body under a disposition** → **Eysenck's PEN** (arousal), **Gray's RST** (approach/avoid/inhibit), **Cloninger/Rothbart** (temperament, effortful control). Flavour, not taxonomy.
- **Needing a finer or a more familiar palette** → **NEO 30 facets** / **DeYoung 10 aspects** for granularity within OCEAN; the **Big Five** itself as the translation layer every reader and every model shares; **16PF** for an unusually granular silhouette.
- **Making any trait read as a real, inconsistent person** → **Whole Trait Theory** over all of the above: mean = the lean, variability = the swing, and the out-of-character beat = a *caused* tail-sample where a Level-2/3 drive (`docs/drives-schema.md`, `docs/values-and-stakes.md`) overrides the trait-lean under pressure. That collision is where the character-defining moments live.

**The through-line:** every model here is a different factor-solution to one lexical corpus, so they *translate* — HEXACO ⊃ Big Five ⊃ (16PF globals, PEN, circumplex axes), Dark and Light triads are the two poles of the H axis, RST/TCI are the biology underneath. Pick the lens the scene needs; store the lean and the spread; let the situation and the drives push the sample. The repo's spine (`docs/generative-model.md`) then turns disposition into behaviour — traits set the *distribution*, the generator draws the *act*, and the observer supplies the trait-name after the fact.
