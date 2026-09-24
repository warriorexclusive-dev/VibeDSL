# VibeDSL — Model Compatibility Notes (empiric)

Empiric observations from user experiments (Gemini / Alice / Claude Code /
ollama-qwen3 / devstral-24b), used for anything that involves generative
transfer between models.

## Perception
- All tested models perceive the language as native — tokenization is good
  enough that no model flags it as "not a real language" or fights the grammar.

## Self-check dictionary is REQUIRED
- Without the self-check dictionary, model-to-model transfer accuracy drops
  to ~75%.
- With the dictionary and ~3 clean validator passes: ~95%.
- Even 5 passes do not guarantee 100%: the "perfectionist error" — when a
  model is nudged repeatedly it starts INVENTING things to justify another
  pass, degrading a passing artifact.

## Protocol that follows (exit-on-clean, v0.1.9)
- First clean pass (errors=0 + all exam gates) ENDS the loop -> `wrt:goal` -> stop.
- Max 3 passes. Next pass only on a concrete reproduced error.
- Never re-run/re-polish a passing artifact.
- Rules live in `RULES.MD` §6 + agents (`coder-dsl.md`, `dsl-plan.md`).

## Measurements (approx, current)
| metric | value |
|---|---|
| transfer without dictionary | ~75% |
| transfer after 3 clean passes | ~95% |
| 5 passes guarantee | never 100% (perfectionist error) |
| validator py/js parity | always checked (node ide/test_parity.js) |

Status: constant reference. Update when new models are measured.