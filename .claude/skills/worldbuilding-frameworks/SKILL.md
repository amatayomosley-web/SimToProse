---
name: worldbuilding-frameworks
description: A framework-neutral, example-rich reference well for building grounded worlds — the toolbox the world-builder agent draws on. Covers physical geography (plate tectonics, Köppen/Whittaker/Holdridge climate, biomes, hydrology, resource genesis & spread), ecology & evolution (trophic webs, niches, island biogeography, speciation, speculative-biology creature design), economic systems (subsistence→market, Polanyi's forms of integration, money & debt, trade networks, scarcity/surplus), political & power structures (Service/Fried typology, Weber's authority, Mann's IEMP, Ibn Khaldun, state formation), religion & mythology (Campbell's monomyth, Dumézil's trifunctional hypothesis, pantheon design, real-vs-believed), magic-system design (Sanderson's Laws, hard/soft, cost & limit, sympathetic magic), social structure & kinship (descent, the six terminology systems, marriage & residence, stratification, honor/dignity/face), linguistics & naming (phonotactics, morphological typology, toponymy, conlang levels), historical causation & the rise/fall of societies (secular cycles, elite overproduction, complexity collapse, longue durée), and technology levels (three-age system, energy-capture, tech trees). Use when settling any layer of a world — law, community, planet, history, or present systems — or whenever an invented element needs a real-world analog to make it plausible. Grounds the invented in the real. Deep reference files live in references/.
triggers:
  keywords:
    - worldbuilding
    - biome
    - tectonic
    - pantheon
    - faction
    - cosmology
  concepts:
    - build the world
    - design the world
    - magic system
    - world bible
    - universal law
    - present systems
    - how does the economy work
    - make it plausible
    - broader community
---

# Worldbuilding Frameworks — the reference well

## Purpose
This is the **toolbox** the `world-builder` agent draws on to author grounded worlds. It is a **vast well to draw from, not a single prescribed method**: many frameworks per domain, presented neutrally, each with its real-world provenance so an invented world can be *justified by* an earthly analog rather than set arbitrarily. It exists to serve the world workflow in `docs/` (premise → universal law → broader community → planet → history → present systems), supplying the analogs and structures that make each layer plausible and give it teeth.

**Discipline this skill serves (from the project's world docs):**
- **Ground the invented in the real.** A made-up climate, economy, faith, or kinship system earns its place by tracing to a real framework and analog — never "poverty = high," always "poor *because that war*, on *that* exhausted soil."
- **Every "yes, X exists" carries a Limit (teeth) and an Epistemic status (known vs believed).** These frameworks supply the *plausible* limits — real economies, ecologies, and powers all have them.
- **Depth rule.** Reach for the framework that fits the hinge you're authoring; don't simulate a whole planet's geology to place one mountain pass.
- **Framework-neutral.** Where a domain has rival schools (geographic determinism vs contingency; alliance vs descent theory; hard vs soft magic), the well holds *all* of them and names the tension — you choose per world, per premise.

## How to use this well (the method)
1. **Locate the layer.** Which world-workflow step are you on — law, community, planet, history, present systems? Each reference file below is tagged to the step(s) it feeds.
2. **Pull the fitting framework, not the whole shelf.** Take the one that fits *this* hinge. A framework you don't lever is a framework you don't author (the depth rule applies to research too).
3. **Instantiate, then perturb.** Most frameworks below are *schemas* (dimensions a system fills) or *archetypes* (templates to assign-and-perturb). Use the schema to know *what must be decided*; use an archetype as a fast starting point; perturb it toward this premise. (Same assign-and-perturb pattern as the character model's `models`.)
4. **Chain across layers.** Frameworks compose downstream: plate tectonics → orogeny → rain shadow → biome → where crops grow → where cities sit → what a war is fought over. Follow the causal chain; that chain *is* the grounding.
5. **Keep the two rival stances live.** For any contested framework (determinism vs contingency most of all), hold both and let the premise decide. Grounding means *plausible*, not *inevitable*.
6. **Cite the analog in the bible.** When you invent, name the real framework/analog it rests on, so the world-state is auditable and the critic can check it.

---

## The framework index (organized by reference file)
Each entry is **name — one line**. Depth treatments are authored in `references/` (see the note at the end).

### 1. `physical-geography.md` — the stage's bones *(feeds: planet)*
- **Plate tectonics** — drifting plates whose convergent / divergent / transform boundaries place mountains, rifts, volcanoes, and earthquakes; the master control on terrain.
- **Wilson cycle** — the ~supercontinent open-and-close rhythm that assembles and rifts landmasses over deep time.
- **Orogeny (mountain-building)** — how collision and subduction raise ranges, which then gate movement and wring rain from the sky.
- **Hotspots & mantle plumes** — fixed deep-mantle sources that string volcanic island chains across a moving plate (the Hawaii pattern).
- **Isostasy & erosion** — crust floats and rebounds; uplift fights weathering, setting how long highlands and canyons last.
- **Atmospheric circulation (Hadley / Ferrel / Polar cells)** — the three-cell engine that puts rainforests on the equator and deserts near 30° latitude.
- **Coriolis effect & prevailing winds** — planetary rotation bends winds (trade winds, westerlies), setting which coasts are wet and where storms track.
- **Orographic lift & rain shadow** — windward slopes soak, leeward slopes starve; the reason a desert sits behind every big range.
- **Ocean currents & thermohaline circulation** — gyres and the global conveyor redistribute heat, warming some coasts and chilling others at the same latitude.
- **Köppen–Geiger climate classification** — the standard A–E (tropical / arid / temperate / continental / polar) grid from temperature and precipitation thresholds; the workhorse climate map.
- **Trewartha modification** — a Köppen refinement that better separates mid-latitude climates; useful when the temperate zone is load-bearing.
- **Whittaker biome diagram** — biomes plotted directly on mean-temperature × annual-precipitation axes; the fastest "what grows here" lookup.
- **Holdridge life zones** — biomes from biotemperature, precipitation, and evapotranspiration ratio; more physically grounded than Whittaker for ecological modeling.
- **Milankovitch cycles** — orbital eccentricity/tilt/precession drive ice ages and long climate swings; the clock behind deep-time climate history.
- **Biome catalogue** — the standard terrestrial biomes (tundra, taiga, temperate forest, grassland, savanna, desert, tropical rainforest, etc.) and their defining life-form signatures.
- **Drainage basins & the hydrological cycle** — watersheds, divides, and the evaporation→precipitation→runoff loop that fills every river and lake.
- **Strahler stream order & Horton's laws** — the branching arithmetic of river networks; why big rivers are rare and tributaries many.
- **Fluvial / karst / glacial / aeolian landforms** — the sculptors: rivers cut valleys, water dissolves limestone caves, ice carves fjords, wind builds dunes.
- **Coastlines & sea level** — emergent vs submergent coasts, estuaries, deltas, and how sea-level change makes or drowns harbors and land bridges.
- **Ore genesis & resource concentration** — why metals cluster: hydrothermal veins at plate boundaries, magmatic segregation, banded iron formations, placer deposits.
- **Fossil-fuel & mineral formation** — coal from swamps, oil from marine plankton, salt/evaporites from dried seas; the deep-time recipes for buried wealth.
- **Resource spread (uneven distribution)** — the worldbuilding principle that scarcity-here / abundance-there is the *conflict substrate*: geography matters dramatically only when what's valuable is unevenly placed.
- **Pedology (soil types & fertility)** — loess, alluvium, laterite, chernozem; why some valleys feed empires and some highlands never do.
- **Biogeographic realms & Wallace's Line** — deep faunal provinces separated by ancient barriers; why continents have distinct casts of creatures.

### 2. `ecology-and-evolution.md` — what lives here, and why *(feeds: planet — ecology & creatures)*
- **Natural selection & adaptation** — differential survival of heritable variation; the engine that fits every organism to its niche and every niche to its place.
- **Sexual selection** — mate choice and competition drive ornament, display, and dimorphism (the peacock's tail); traits costly for survival but rewarded in reproduction.
- **Ecological niche & competitive exclusion (Gause)** — no two species occupy the identical niche indefinitely; competition forces divergence or displacement.
- **Trophic levels & the 10% rule (Lindeman)** — energy pyramids: producers → herbivores → carnivores, losing ~90% per step; why apex predators are few and large.
- **Food webs & keystone species (Paine)** — some species hold a whole web together; remove them and it collapses or flips (the wolf/otter cases).
- **Trophic cascades & ecosystem engineers** — top-down control and habitat-makers (beavers, coral, earthworms) that build the stage other life depends on.
- **r/K selection theory** — the fast-many-cheap-offspring vs slow-few-invested strategy axis; predicts life-history from environment stability.
- **Carrying capacity & logistic growth** — the ceiling an environment imposes; populations overshoot, crash, and oscillate around it.
- **Lotka–Volterra predator–prey dynamics** — coupled boom-and-bust cycles between hunter and hunted; the math of population rhythm.
- **Island biogeography (MacArthur & Wilson)** — species richness balances immigration against extinction by island size and isolation; the theory behind endemics and refugia.
- **Adaptive radiation** — one lineage explodes into many forms to fill empty niches (Darwin's finches); how a barren world gets populated fast.
- **Convergent evolution** — unrelated lineages evolve similar solutions to similar problems (eyes, wings, streamlining); the grounding for plausible alien-but-familiar creatures.
- **Coevolution & the Red Queen** — predators and prey, parasites and hosts, flowers and pollinators locked in escalating mutual arms races.
- **Speciation (allopatric / sympatric)** — how one species splits into two, usually by geographic isolation; the source of biodiversity across barriers.
- **Founder effect & genetic drift** — small isolated populations diverge by chance, not just selection; why islands and refugia breed oddities.
- **Punctuated equilibrium (Eldredge & Gould)** — long stasis broken by rapid change; the tempo model behind sudden faunal turnovers in the fossil record.
- **Mass extinction & recovery** — the big resets (impact, volcanism, anoxia) that clear the board and hand survivors an open world; deep-time hinges for history.
- **Latitudinal diversity gradient** — life piles up toward the tropics and thins toward the poles; sets where ecosystems are rich vs sparse.
- **Bergmann's & Allen's rules** — cold-climate animals run larger and stubbier-limbed to conserve heat; simple levers for climate-plausible creature design.
- **Biomimicry & functional morphology** — designing a creature from its job: the square-cube law, gait, metabolism, and sensory apparatus its niche demands.
- **Speculative biology (Dixon lineage)** — the *After Man* / *All Tomorrows* tradition of rigorously extrapolated invented life; the discipline of making a monster evolutionarily earned, not arbitrary.

### 3. `economic-systems.md` — the material base *(feeds: present systems — economy; planet — resource stakes)*
- **Modes of subsistence** — foraging → horticulture → pastoralism → intensive agriculture → industry; the ladder that gates population, surplus, and social complexity.
- **Surplus & the origin of complexity (Childe)** — no storable surplus, no specialists, cities, or ruling class; the Neolithic and Urban "revolutions" as thresholds.
- **Substantivism vs formalism (Polanyi)** — is the economy *embedded* in social relations or a self-regulating market? The stance that decides how your economy even works.
- **Polanyi's forms of integration** — reciprocity (symmetry), redistribution (a center), and market exchange (price-making) as the three ways economies cohere.
- **Sahlins' reciprocity spectrum** — generalized (kin, no ledger) → balanced (equivalent return) → negative (strangers, haggling and theft); moral distance made economic.
- **Gift economy (Mauss)** — the obligation to give, receive, and repay; prestige and alliance carried by objects, not cash (the *Kula* ring, the potlatch).
- **Prestige-goods & sumptuary economies** — wealth as status objects and their controlled display; who may own or wear what, and the power in gatekeeping it.
- **Emergence & theory of money** — barter's double-coincidence problem; commodity money → coinage → fiat; metallism vs chartalism as rival accounts of what money *is*.
- **Debt as social relation (Graeber)** — credit and obligation predate coinage; debt, bondage, and jubilee as engines of power and revolt.
- **Scarcity, supply & demand** — price as the meeting of what's wanted and what's available; the base logic every market runs on.
- **Comparative advantage & division of labor (Ricardo, Smith)** — specialization and trade make everyone richer; the reason regions and peoples become interdependent.
- **Trade networks & routes** — Silk Road, Trans-Saharan, Indian-Ocean monsoon trade, the Hanseatic League; how goods, wealth, disease, and ideas move along terrain-gated corridors.
- **Central place theory (Christaller)** — market towns arrange in a nested hierarchy by the range and threshold of goods; the geometry of where settlements sit.
- **Malthusian trap** — population outruns food until famine, war, or plague resets it; the ceiling on pre-industrial growth.
- **Boserup's intensification** — population pressure *drives* agricultural innovation (the inverse of Malthus); the pressure-valve that sometimes breaks the ceiling.
- **Property & surplus capture** — who owns land, labor, and capital, and who takes the surplus (communal / feudal / private / state / temple); the source of class.
- **Labor organization** — free / serf / slave / guild / wage / caste; the terms on which work is compelled or sold, tying economy to law and custom.
- **Economic archetypes** — subsistence-agrarian · feudal-extraction · mercantile-market · command-redistribution · guild-craft · (magical-production, if law permits); assign-and-perturb templates.
- **The three dramatic drivers** — *what's scarce* (the director's levers), *who controls the surplus* (class → factions), *who depends on whom* (trade leverage: embargo, monopoly, debt).

### 4. `political-and-power-systems.md` — order and its structure *(feeds: present systems — governance, factions; history — state formation)*
- **Service's sociopolitical typology** — band → tribe → chiefdom → state; the standard evolutionary ladder of political scale and centralization.
- **Fried's typology** — egalitarian → ranked → stratified → state; a complementary axis keyed to *inequality of access*, not just scale.
- **Weber's three types of legitimate authority** — traditional (it's always been so), charismatic (the extraordinary leader), and legal-rational (rules and office); why people obey.
- **The state as monopoly on legitimate violence (Weber)** — the definitional core of a state; who *may* use force, and what it means when that monopoly breaks.
- **Aristotle's six regimes** — monarchy/tyranny, aristocracy/oligarchy, polity/democracy; the rule-by-one/few/many grid crossed with good/corrupt.
- **Polybius' anacyclosis** — the cycle of regimes decaying and revolving (monarchy → tyranny → aristocracy → oligarchy → democracy → mob → monarchy); constitutional decline as a wheel.
- **Ibn Khaldun's asabiyyah** — group solidarity rises on the hard frontier, conquers the soft center, then dissolves in luxury over ~three generations; the classic dynastic rise-and-fall engine.
- **Montesquieu's separation of powers** — dividing legislative, executive, judicial to check tyranny; the architecture of balanced government.
- **Mann's IEMP model** — social power flows through four autonomous networks (ideological, economic, military, political); no single engine of history, but their contingent interplay.
- **Lukes' three faces of power** — power as winning decisions, as setting the agenda, and as shaping what people even want; visible, hidden, and invisible control.
- **Carneiro's circumscription theory** — states arise where population is hemmed by geography or rivals and can't flee, forcing submission; a materialist origin-of-the-state.
- **Tilly's bellicist theory** — "war made the state and the state made war"; military competition drives taxation, bureaucracy, and centralization.
- **Wittfogel's hydraulic hypothesis** — large-scale irrigation demands a managerial despotism ("Oriental despotism"); contested, but a clean water-power link.
- **Segmentary lineage & acephalous order (Evans-Pritchard)** — societies that hold together and wage feud without any central authority; "me against my brother, my brother and I against our cousin."
- **Patron–client & principal–agent structures** — power as webs of personal loyalty, patronage, and delegation; how rule actually runs beneath the formal chart.
- **Divine kingship (Frazer)** — the ruler as sacred, embodying the land's fertility and sometimes ritually killed; sovereignty fused with religion.
- **Governance & legal archetypes** — theocratic-code · imperial-statute · feudal-obligation · tribal-elder-law · common-law-precedent · clan-feud/honor · mercantile-contract; assign-and-perturb templates.
- **Faction structure (collective character)** — a faction as identity (fault-line) + interest + resources + status + inter-faction relations; where society's tensions become agents and the director's primary lever-source.

### 5. `religion-and-mythology.md` — the sacred, structured *(feeds: universal law — metaphysics; present systems — religion-as-lived; history — belief as driver)*
- **The real-vs-believed axis** — the project's Epistemic check applied to faith: is the religion *true* (real gods, operative fate) or *sincere false belief*? The single fork that makes a praying character talk to *someone* or to *nothing* — and simulated identically either way.
- **Types of religious system** — animism, polytheism, henotheism, monotheism, dualism, pantheism, ancestor worship; the structural menu a faith is built from.
- **Pantheon design** — theogony, divine domains and portfolios, syncretic mergers, and god-triads; building a coherent divine cast (and the Dumézil pattern below often underlies it).
- **Dumézil's trifunctional hypothesis** — Proto-Indo-European myth and society split into three functions: sovereign/priestly, warrior, and producer/fertility (Odin–Thor–Freyr; the priest/warrior/commoner castes).
- **Campbell's monomyth (the Hero's Journey)** — departure → initiation → return as a claimed universal narrative deep-structure; powerful and *notoriously over-applied* — hold it with its critics.
- **Campbell's four functions of myth** — metaphysical (awe), cosmological (a world-image), sociological (sanctioning an order), and pedagogical (how to live); what a mythology *does* for its people.
- **Lévi-Strauss's structuralism** — myth as the working-out of binary oppositions (raw/cooked, life/death) mediated toward resolution; myth as a logic-machine.
- **Durkheim's sacred/profane** — religion as society worshipping itself; the sacred is what the group sets apart and forbids, binding it into one moral community.
- **Weber's routinization of charisma** — the prophet's fire cools into priesthood, doctrine, and institution; how a living revelation becomes a church.
- **Eliade's sacred space & eternal return** — hierophany, the axis mundi, sacred center vs profane periphery, and cyclical ritual time that renews the cosmos.
- **Otto's numinous** — the raw religious experience as *mysterium tremendum et fascinans*: dread and fascination before the wholly other; the felt core beneath doctrine.
- **Geertz's religion as cultural system** — religion as a web of symbols fusing an *ethos* (how to feel) with a *worldview* (what's real); the interpretive stance.
- **Myth typologies** — cosmogony (creation), eschatology (end times), etiology (why things are), theomachy (wars of gods), flood, and dying-and-rising-god myths; the recurring plots.
- **Van Gennep's rites of passage** — separation → liminality → incorporation; the three-phase structure of every threshold ritual (birth, initiation, marriage, death).
- **Turner's liminality & communitas** — the betwixt-and-between phase where structure dissolves and a raw fellowship forms; the anthropology of transformation.
- **Propp's morphology of the folktale** — 31 recurring narrative functions and a fixed cast of roles behind wondertales; structural grammar for myth and legend.
- **Aarne–Thompson–Uther tale-type index** — the catalogue of migratory folktale plots and motifs; a menu of story-shapes a culture's oral tradition can carry.
- **Frazer's magic → religion → science** — his evolutionary sequence of how humans try to control the world (contested, but a useful axis for a culture's cast of mind).
- **Theodicy** — how a faith explains suffering and evil under its cosmology; the doctrine that keeps belief coherent when the world hurts.
- **Syncretism, millenarianism & cargo cults** — how faiths blend under contact, and how deprivation breeds movements promising an imminent, world-overturning deliverance.

### 6. `magic-and-the-supernatural.md` — designing the impossible with teeth *(feeds: universal law — the magic switch; present systems — magic's role)*
- **Sanderson's First Law** — the ability to solve conflict with magic is proportional to how well the reader understands its rules; understood magic can resolve, mysterious magic can only threaten.
- **Sanderson's Second Law** — limitations matter more than powers; a magic is defined and made dramatic by its costs, weaknesses, and what it *can't* do (this *is* the project's Limit/teeth check).
- **Sanderson's Third Law** — expand what you have before adding something new; depth over sprawl.
- **Sanderson's Zeroth Law** — "err on the side of what's awesome"; the wonder override the other three serve, not smother.
- **The hard–soft magic spectrum** — hard (explicit rules, can resolve plot) ↔ soft (mysterious, preserves wonder, shouldn't resolve plot); a dial, not a binary — and most systems sit in between.
- **Cost / limitation / consequence** — the three teeth: what the power *takes* (cost), what it *can't do* (limit), and what it *leaves behind* (consequence); an unbounded magic breaks the world's ability to say no.
- **Frazer's sympathetic magic** — the Law of Similarity (like produces like — the effigy) and the Law of Contagion (things once in contact stay linked — hair, blood, a name); the real folk-logic most magic systems rest on.
- **Mana** — the Oceanic concept (Codrington, Marett) of an impersonal supernatural potency that inheres in people and things; the anthropological root of the "magic as substance/energy" model.
- **True-name magic** — power over a thing through knowledge of its real name; the naming-is-binding tradition (and its sympathetic-magic kinship).
- **Vancian / preparatory magic** — spells as expendable, memorized-and-forgotten charges; the fire-and-forget model that builds in scarcity as a limit.
- **Elemental & correspondence systems** — classical elements, humors, planetary and directional correspondences; ready-made internal logics for a magic's taxonomy.
- **Source, wielder, cost, limit (the design schema)** — the four questions the project's law-guide forces on any "yes, magic exists": where power comes from, who can use it, what it takes, what it can't do.
- **The supernatural-beings switch** — whether undead, demons, spirits, and magical beasts can exist (a law-level "yes," unlike mundane animals); each needs its own existence-Limit-Epistemic triple.
- **The Epistemic status of magic** — is the magic *known-true* (it demonstrably works) or *believed* (rituals that may do nothing)? A world of real sorcery and a world of sincere superstition are simulated differently.
- **Magic's economic & political role (the specials hook)** — how a real magic *breaks* an assumption (production without labor), *adds* a factor (mana as a resource), or *creates* an institution (a mages'-guild monopoly); grounding magic in the systems it warps.

### 7. `social-structure-and-kinship.md` — who counts as us *(feeds: present systems — culture/custom; character positions)*
- **Descent systems** — patrilineal, matrilineal, bilateral, ambilineal; the rule that decides which ancestors you belong to and inherit through.
- **Lineage, clan, moiety, phratry** — the nested descent groups above the household; the scaffolding of kin-based society.
- **The six kinship terminology systems (Morgan)** — Eskimo, Hawaiian, Sudanese, Iroquois, Crow, Omaha; how a culture *carves up* relatives into named categories, and what that reveals about its structure.
- **Marriage rules** — endogamy/exogamy, monogamy/polygyny/polyandry, cross-cousin marriage, bride-price/dowry, levirate/sororate; who may marry whom, and what changes hands.
- **Residence rules** — patrilocal, matrilocal, neolocal, avunculocal; where a new couple lives, which quietly shapes power and daily life.
- **Alliance vs descent theory (Lévi-Strauss vs Radcliffe-Brown/Fortes)** — is kinship built on *exchange of spouses between groups* or on *lines of descent*? The great anthropological debate; hold both.
- **Social stratification** — caste, estate, class, and slavery; ascribed (born-into) vs achieved (earned) status, and how rigid the ladder is.
- **Age sets & grades** — cohorts that move through life-stages together, structuring society by generation rather than (or alongside) kin.
- **Dunbar's number** — the ~150 cognitive ceiling on stable personal relationships; a natural grain for band, village, and unit size.
- **Honor / dignity / face cultures** — three worth-systems (honor = reputation defended, often violently; dignity = inherent inner worth; face = harmony and social standing); the deep grammar of a culture's slights and its violence.
- **Guilt vs shame cultures (Benedict)** — is transgression policed by internal conscience or by external exposure? Sets how deviance feels and is punished.
- **Hofstede's cultural dimensions** — individualism/collectivism, power distance, uncertainty avoidance, and the rest; comparative axes to give cultures distinct textures (use with its critics).
- **Douglas's grid/group** — plotting cultures by how much rule-boundedness (grid) and group-belonging (group) they impose; predicts cosmology and attitude to risk.
- **Cultural materialism (Harris)** — infrastructure (subsistence, ecology) shapes structure (social organization) shapes superstructure (ideology); a causal stance linking a culture to its material base.
- **In-group / out-group & ethnocentrism** — the us/them boundary, hospitality vs hostility to outsiders; the multi-culture hinge where contact becomes friction.
- **Values-weighting (culture as collective model)** — a culture *is* a shared weighting over the worth-menu (Schwartz's values, Moral Foundations); the collective analog of a character's model (`docs/values-and-stakes.md`).

### 8. `language-and-naming.md` — the sound of a world *(feeds: present systems — culture; the naming surface across all layers)*
- **Phoneme inventory** — the set of distinctive sounds a language uses; the palette that makes one tongue feel guttural, another liquid.
- **Phonotactics** — the rules for how sounds may combine into syllables; the constraint that makes coined words feel like they *belong* to one language.
- **Morphological typology** — isolating, agglutinative, fusional, polysynthetic; how a language packs meaning into words, and the texture that gives its names.
- **Language families & the comparative method** — descent from proto-languages and reconstruction from cognates; the grounding for related peoples having related tongues.
- **Regular sound change (Grimm's Law)** — languages drift by systematic shifts; the mechanism that makes a family's daughter-languages diverge plausibly.
- **Writing systems** — logographic, syllabary, abjad, abugida, alphabet; how a script encodes speech, and what its existence implies about literacy and power.
- **Toponymy (place-names)** — descriptive, commemorative, incident, and possessive naming; place-names as fossilized history written on the map.
- **Anthroponymy (personal names)** — patronymics, matronymics, clan-names, teknonyms, praise-names; naming conventions as a badge of lineage, status, and culture.
- **Onomastic layering** — older names surviving in a newer language's landscape (substrate names); how conquest and migration leave linguistic strata.
- **Conlang depth levels** — from a *naming language* (just enough phonology to coin consistent names) to a full grammar; matching linguistic effort to what the story levers (the depth rule for language).
- **Sound symbolism / phonaesthetics** — the felt tone of sounds (Tolkien's "cellar door"); why some names read as harsh, sweet, ancient, or menacing.
- **Zipf's law** — word frequency follows a steep regularity; a texture-check that invented text feels like real language.
- **Linguistic relativity (Sapir–Whorf)** — the contested claim that language shapes thought; a lever for making a culture's worldview feel embedded in its speech (use the weak version).
- **Tolkien's language-first method** — building the mythology to house the languages rather than the reverse; the exemplar of language as a world's root, not its decoration.

### 9. `history-and-societal-change.md` — the rise and fall engine *(feeds: history — causation; present systems — live tensions)*
- **Ibn Khaldun's asabiyyah cycle** — the dynastic rise-and-fall by solidarity gained on the frontier and lost in the luxurious center; history's oldest structural model of collapse.
- **Turchin's structural-demographic theory** — instability from the interplay of population, elite numbers, and state finance; a testable model of *secular cycles* of integration and crisis.
- **Elite overproduction** — too many aspirants for too few elite positions breeds rivalry, faction, and upheaval; a precise, portable engine of political crisis.
- **Secular cycles (Goldstone/Turchin)** — century-scale oscillations of population growth, price inflation, and state breakdown in agrarian societies; the rhythm history moves in.
- **Tainter's collapse (diminishing returns on complexity)** — societies solve problems by adding complexity until its marginal returns go negative, then collapse *because* simplifying pays; complexity as the trap.
- **Diamond's geographic determinism (*Guns, Germs, and Steel*)** — the contested thesis that continental geography and biology, not culture, set which peoples dominated; the strong-determinism pole (hold it against its critics).
- **Diamond's *Collapse* framework** — five drivers of societal failure (environmental damage, climate change, hostile neighbors, lost trade partners, and a society's *response*); a checklist for engineering a fall.
- **Toynbee's challenge-and-response** — civilizations rise by meeting hard challenges with creative minorities and fall when that creativity fails; a contingency-friendly counter to determinism.
- **Spengler's organic cycles (*Decline of the West*)** — civilizations as organisms with a spring-to-winter life-course; the deep-pessimist morphology of history.
- **Quigley's *Evolution of Civilizations*** — expansion driven by an "instrument" that ossifies into an "institution," stalling growth until reform or collapse; a mechanism for the plateau.
- **Braudel's longue durée (Annales school)** — history on three timescales: slow geography, medium social/economic structures, and the fast froth of events; sets *which* causes actually move a world.
- **Great-man vs structural vs contingent causation** — the standing debate over whether individuals, deep forces, or accident drive history; the stance a world's history is authored under.
- **McNeill's *Plagues and Peoples*** — disease as a prime mover of conquest, collapse, and population; the microbial hinge often left out of history.
- **Crosby's Columbian Exchange** — biological consequences of contact (crops, animals, and above all pathogens crossing between worlds); the template for what contact *does* to a planet.
- **Path dependence & lock-in** — early, sometimes accidental choices constrain everything after (the QWERTY effect); why worlds carry the fossils of old decisions.
- **Diffusion vs independent invention** — did an idea spread from a source or arise separately? The axis behind how technologies and religions populate a map.
- **Demographic transition** — the shift from high-birth/high-death to low/low as a society develops; the population dynamics behind modernization and its strains.
- **Environmental & climate causation** — drought, cooling, and disaster as collapse triggers (the Bronze Age collapse, the 4.2-kiloyear event, the Little Ice Age); the planet writing history.

### 10. `technology-and-material-culture.md` — the level of the possible *(feeds: planet → history → present systems, cross-cutting)*
- **The three-age system (Thomsen)** — Stone → Bronze → Iron, with Paleolithic/Mesolithic/Neolithic subdivisions; the archaeological ladder of material capability.
- **Lenski's sociocultural evolution** — societies classed by their subsistence technology (hunter-gatherer → horticultural → agrarian → industrial); tech-level as the master variable behind social form.
- **White's energy-capture law** — culture advances as energy harnessed per capita rises (C = E × T); a thermodynamic yardstick for a civilization's level.
- **Childe's revolutions** — the Neolithic (farming) and Urban (cities, writing, states) thresholds; the two jumps that reset what a society can be.
- **The tech-tree & prerequisite chains** — technologies as a dependency graph (no steel without iron without smelting without fuel); why levels can't be skipped and why one invention unlocks a cascade.
- **Lynn White's *Medieval Technology and Social Change*** — how a single device (the stirrup, the heavy plow) can restructure a whole society; technology as a social hinge, not just a tool.
- **Rogers's diffusion of innovations** — how a new technology spreads (innovators → early adopters → majority → laggards); the S-curve of adoption and resistance.
- **Metallurgy stages** — cold-working → smelting → bronze alloying → iron → steel; the specific chain that gates tools, weapons, and the wealth of whoever controls the ore.
- **Key hinge-inventions** — the plow, the wheel, the sail, writing, the printing press, gunpowder, the water/wind mill; individual technologies whose arrival reorders economy and war.
- **Appropriate & path-dependent technology** — why societies adopt (or refuse) a technology by fit to their ecology, economy, and values, not by "advancement"; guards against a linear tech-ladder.
- **Kardashev scale** — energy-use tiers for high-tech / SF civilizations (planetary → stellar → galactic); the far-future extension of the energy-capture idea.
- **Tech level ↔ everything** — how a fixed tech-level bounds economy (surplus, trade range), war (who beats whom), governance (how far a state can reach), and daily life; the coupling that keeps a world consistent.

### 11. `worldbuilding-method-and-grounding.md` — how to build with the well *(feeds: all layers — the discipline)*
- **Tolkien's sub-creation & secondary belief** — the maker builds a Secondary World with such inner consistency that the mind enters and *believes*; consistency, not realism, is the goal.
- **The iceberg / 1% theory** — author far more than shows, but show only the load-bearing tip; the depth beneath the surface is what makes the surface feel real (Hemingway's iceberg, applied to worlds).
- **The real-world analog method** — grounding every invention in an earthly parallel and the framework that explains it; the core practice this whole skill serves.
- **The reskinning pitfall** — the failure mode of the analog method: lifting a real culture wholesale as costume, producing flat stereotype; analogize the *structure and cause*, then diverge.
- **Architect vs gardener (Martin)** — planning a world top-down vs growing it organically; two working styles, and the project's answer (authored-backward, validated-forward: architect the target, garden the path).
- **The MICE quotient (Card)** — Milieu / Idea / Character / Event as what a story is *about*; a lens for how much world a given story actually needs (the premise as curator).
- **Authored-backward, validated-forward** — the project's own discipline: author toward the premise's demanded present, then run the dependency chain forward to confirm it's earned; the antidote to arbitrary decree.
- **The depth rule (hinges, not census)** — author only what the probe/story levers; stub the rest "undetermined — fill when levered"; the frame-problem discipline against over-building.
- **"Worldbuilding disease"** — the caution against building a world at the expense of the story it exists to serve; the well is a means, never the end.
- **Consistency & the no-contradiction floor** — a world adds without silently rewriting itself; internal consistency is the property that lets characters (and readers) trust the ground beneath them.
- **The Limit + Epistemic checks** — every invented "yes" carries what it *can't* do and whether it's *known or believed*; the two habits that keep a world able to refuse a lever and hold a truth its people can be wrong about.

---

## Note on the reference files
The deep treatments in `references/` are **authored in a later pass**. This `SKILL.md` is the curated, comprehensive **index** — the map of what the well holds and where each framework sits in the world workflow. `references/_index.md` outlines the eleven reference files above. None of the eleven exist on disk yet: until they're written, a routed reference is absent by default — act on this index's own one-line entry for that framework and proceed; never stall on, or invent, the file. Nothing here is prescriptive: it is a well to draw from, framework-neutral, holding rival schools side by side so the premise — not the toolbox — decides.
