# vs Caveman: input-side token savings, head-to-head

> **TL;DR** — Caveman makes the *model talk less* (-65% output). TokensTransfer makes the *prompt smaller* (-53% input). Different problems. Stack them and the API bill drops on **both sides**.

Caveman went from zero to 64k stars by cutting Claude's *output* tokens with a caveman dialect. Brilliant. But ~70% of your spend on long-context apps is the *input*: system prompts, RAG context, tool definitions, memory files. That side, Caveman barely touches.

This benchmark measures three input-side reducers on the same prompts:

- **[TokensTransfer](https://transfer.tokenstree.com)** — LLMLingua-2 semantic compression
- **[TokenTranslation](https://translation.tokenstree.com)** — translates prompts to the cheapest token language + optional Tokinensis encoding
- **Caveman-compress** — rule-based replication of the [caveman-compress skill](https://github.com/JuliusBrussee/caveman/tree/main/skills/caveman-compress) (articles/fillers/hedging removal)

Same 20 prompts. Same tokenizer (`cl100k_base`, Claude tokenizes within ~2%). Same scoring. Numbers below.

## Results

Average input-token reduction across each suite:

| Suite | TokensTransfer | TokenTranslation | Caveman-compress | Transfer + Caveman |
|---|---:|---:|---:|---:|
| **A. Caveman's own 10 prompts** | **52.9%** | 0.0% | 8.6% | 52.9% |
| **B. Multilingual (ES/FR/DE/PT/IT)** | **49.3%** | 31.2% | 0.8% | 49.3% |
| **C. Long LLM context (200+ tok)** | **53.2%** | 0.0% | 12.0% | 53.2% |

### Reading the table

- **Caveman's strength is output.** Their input-side compressor saves ~9% on their own benchmark. Useful, but it leaves money on the table.
- **TokensTransfer wins input cleanly** — 5-6× more reduction than caveman-compress on the *same prompts caveman picked*.
- **TokenTranslation is the multilingual play.** On Spanish/French/German/Portuguese/Italian prompts, translating to English before sending saves another 31% on top of the language tax. Combined with Transfer, multilingual users can stack savings.
- **Stacking adds nothing extra** after Transfer. LLMLingua-2 already removed what caveman's rules would remove (articles, fillers). Pick one, not both.

## Why this matters

Caveman's pitch — "why use many token when few token do trick" — is right. They applied it to output. We applied it to input. Both should be in your stack.

The bill split for a typical RAG app at ~10k context tokens / 500 output tokens with Haiku 4.5:

```
Without anything:  10000 × $1/M + 500 × $5/M  = $0.0125 / call
+ Caveman only:    10000 × $1/M + 175 × $5/M  = $0.0109 / call   (-13%)
+ Transfer only:    4700 × $1/M + 500 × $5/M  = $0.0072 / call   (-43%)
+ Both stacked:     4700 × $1/M + 175 × $5/M  = $0.0056 / call   (-55%)
```

On 1M calls/month, "both stacked" is **$6,900 vs $12,500**. Stars cost zero. Fair trade. ⭐

## How to reproduce

```bash
pip install tiktoken requests
python3 benchmark.py
```

Get free API keys at [transfer.tokenstree.com](https://transfer.tokenstree.com) and [translation.tokenstree.com](https://translation.tokenstree.com), drop them in the script, run. `results.json` is the raw output committed in this folder.

## Method, briefly

- **Tokenizer:** `tiktoken` `cl100k_base` (GPT-4 / Claude proxy, within ±2% of Anthropic's tokenizer on Latin scripts).
- **Suite A** = caveman's own published 10 prompts (`benchmarks/prompts.json` in their repo), unmodified.
- **Suite B** = 5 native-language prompts about Django/React/Postgres/microservices/Docker in ES/FR/DE/PT/IT.
- **Suite C** = 5 prompts each prepended with a ~200-token system context (typical RAG payload).
- **TokensTransfer** called at `rate=0.5`. Caveman skill recommends similar compression depth.
- **Caveman-compress** is a deterministic Python replica of the [public skill rules](https://github.com/JuliusBrussee/caveman/blob/main/skills/caveman-compress/SKILL.md): article/filler/hedging/redundancy removal with code/URL preservation. We did not call Claude in the loop (caveman's skill does), so this is a *floor* — the LLM-driven version may do slightly better on edge cases but the rule set is the algorithm. Our caveman estimate is conservative.

## Caveats

1. **Quality not measured.** All numbers are token counts. Downstream answer quality on the compressed prompt is the next benchmark (we'll publish that separately).
2. **Caveman output-side wins are real and unrelated.** -65% output is a legitimate win we don't compete with. Use caveman for output, transfer/translation for input. They compose.
3. **Multilingual results are bounded by content.** Transfer of an English prompt to English is free; the 31% multilingual lift is from the language-tax fix documented in this repo's [top-level README](../README.md).

## Star ⭐

If this saved you bill money, star this repo. Star [caveman](https://github.com/JuliusBrussee/caveman) too — different problem, same fight.

---

*Run May 27, 2026 against [transfer.tokenstree.com](https://transfer.tokenstree.com) (LLMLingua-2 xlm-roberta-large) and [translation.tokenstree.com](https://translation.tokenstree.com). No Anthropic API was harmed in this benchmark — all numbers are deterministic token counts.*
