# TEST-001 Coherence Judgment — blind, no-ties

Runs: haiku=25 turns, sonnet=25 turns. Control = haiku with turn order scrambled (planted negative).
BLIND MAPPING (hidden from judges): A=sonnet  B=control(shuffled-haiku)  C=haiku
Judge models (no-ties, != run models): deepseek/deepseek-v4-pro

## Judge: deepseek/deepseek-v4-pro
- A [sonnet]: score=None  breaks=none
- B [control(shuffled-haiku)]: score=None  breaks=none
- C [haiku]: score=9  breaks=none
- PAIRED (X=haiku, Y=sonnet — hidden): winner=None margin=None tell=None

## Aggregate (mean coherence score)
- A [sonnet]: None
- B [control(shuffled-haiku)]: None
- C [haiku]: 9.0

**Control teeth-check (control must score below both intact runs): FAIL**
