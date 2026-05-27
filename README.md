# The Hidden LLM Language Tax

A reproducible `tiktoken` benchmark showing that non-English prompts pay a systematic token tax on OpenAI APIs.

**Headline**: The same paragraph in Spanish costs 55% more than in English. Arabic: 230% more. Over 1M requests/month, that is $11K+ in delta spend for identical functionality.

> MIT licensed. Copy, paste, verify. If your numbers differ, open an issue.

---

If you pay the OpenAI bill for a Spanish-speaking product, your unit economics are worse than your English-speaking competitor's. Same model. Same prompt. Same answer. More dollars.

**TL;DR** — In a reproducible tiktoken benchmark with GPT-4's `cl100k_base` tokenizer, the same technical paragraph takes **1.55× more tokens in Spanish than in English** (55% more). Arabic and Japanese are far worse: **3.30×** and **2.93×**. At 1M requests/month, that's the difference between a $5K invoice and a $16K one. The fix is not rocket science, but nobody talks about it because the incentives point the other way.

---

## Why this happens: BPE tokenization, briefly

GPT-4, GPT-4o, Claude, Llama — all use some flavor of Byte-Pair Encoding (BPE). BPE builds its vocabulary from whatever corpus the model was trained on. Because these corpora are overwhelmingly English (Common Crawl is roughly 46% English, every other language is in the long tail), the most common English words collapse to single tokens.

- `"function"` → 1 token
- `"the "` → 1 token
- `"implementation"` → 1 token

Now in Spanish:

- `"función"` → 2 tokens (`funci` + `ón`)
- `"implementación"` → 4 tokens
- `"¿"` → 1 token (just the opening question mark — free tax)

And in languages without Latin script — Arabic, Chinese, Japanese — it gets worse. Often one character is one token because the BPE never saw enough training data to merge them.

This is not a bug. It's a consequence of training data distribution. But it's a systematic penalty paid by everyone who doesn't operate in English, every single API call, forever.

## The benchmark: same content, 8 languages

Here's the setup. A realistic developer question about PostgreSQL connection pooling, translated by a native speaker, run through every major OpenAI tokenizer.

Install:

```bash
pip install tiktoken
```

Script (reproducible, no secrets needed — `cl100k_base` is the GPT-4 / GPT-3.5-turbo encoding; `o200k_base` is used by GPT-4o, GPT-5, and the o-series):

```python
import tiktoken

SAMPLES = {
    "english":    "How do I connect to a PostgreSQL database from Python using psycopg2? I need connection pooling, retry on transient errors, and clean shutdown.",
    "spanish":    "¿Cómo me conecto a una base de datos PostgreSQL desde Python usando psycopg2? Necesito pooling de conexiones, reintentos ante errores transitorios y apagado limpio.",
    "french":     "Comment me connecter à une base de données PostgreSQL depuis Python avec psycopg2 ? Il me faut un pool de connexions, des retries et un arrêt propre.",
    "german":     "Wie verbinde ich mich mit einer PostgreSQL-Datenbank aus Python mit psycopg2? Ich brauche Connection-Pooling, Retries und sauberes Herunterfahren.",
    "portuguese": "Como me conecto a um banco PostgreSQL em Python usando psycopg2? Preciso de pool de conexões, retries e shutdown limpo.",
    "japanese":   "psycopg2 を使って Python から PostgreSQL に接続するには？ コネクションプール、一時的エラーの再試行、正常なシャットダウンが必要です。",
    "chinese":    "如何使用 psycopg2 从 Python 连接 PostgreSQL？我需要连接池、瞬时错误重试和干净关闭。",
    "arabic":     "كيف أتصل بقاعدة بيانات PostgreSQL من Python باستخدام psycopg2؟ أحتاج إلى تجمع اتصالات، وإعادة المحاولة، وإغلاق نظيف.",
}

for enc_name in ("cl100k_base", "o200k_base"):
    enc = tiktoken.get_encoding(enc_name)
    print(f"\n{enc_name}")
    baseline = None
    for lang, text in SAMPLES.items():
        n = len(enc.encode(text))
        baseline = baseline or n
        print(f"  {lang:<11} {n:4d} tokens  ({n/baseline:.2f}× vs EN)")
```

## Results (the actual numbers you pay)

Short-prompt benchmark — this is a ~50-token English sentence, translated with comparable fidelity:

### GPT-4 / GPT-3.5-turbo (`cl100k_base`)

| Language    | Tokens | Ratio vs EN | Savings if you pre-translate to EN |
|-------------|-------:|------------:|-----------------------------------:|
| English     |     46 |       1.00× |                                 — |
| Chinese     |     61 |       1.33× |                              24.6% |
| Spanish     |     68 |       1.48× |                              32.4% |
| Portuguese  |     74 |       1.61× |                              37.8% |
| French      |     82 |       1.78× |                              43.9% |
| German      |     90 |       1.96× |                              48.9% |
| Japanese    |    135 |       2.93× |                              65.9% |
| Arabic      |    152 |       3.30× |                              69.7% |

### GPT-4o / GPT-5 / o-series (`o200k_base`)

| Language    | Tokens | Ratio vs EN | Savings if pre-translate |
|-------------|-------:|------------:|-------------------------:|
| English     |     49 |       1.00× |                       — |
| Chinese     |     52 |       1.06× |                    5.8% |
| Spanish     |     61 |       1.24× |                   19.7% |
| Portuguese  |     66 |       1.35× |                   25.8% |
| Arabic      |     66 |       1.35× |                   25.8% |
| French      |     72 |       1.47× |                   31.9% |
| German      |     77 |       1.57× |                   36.4% |
| Japanese    |    100 |       2.04× |                   51.0% |

The `o200k_base` tokenizer (new in GPT-4o) *did* narrow the gap substantially — Spanish drops from 1.48× to 1.24×, Arabic from 3.30× to 1.35×. But "narrowed" is not "closed," and everything older than GPT-4o (which is still the bulk of production workloads) pays the full penalty.

### Long prose is worse

The short-prompt numbers understate the penalty because short English sentences lean on extremely common tokens. Running the same technical article as a ~270-token EN paragraph vs. its faithful Spanish translation:

| Tokenizer     | EN tokens | ES tokens | Ratio  | Savings |
|---------------|----------:|----------:|-------:|--------:|
| `cl100k_base` |       267 |       414 | 1.551× |  35.5% |
| `o200k_base`  |       274 |       367 | 1.339× |  25.3% |

That's where the "up to 60% more tokens" headline lives: sustained prose with agreement (`"de las conexiones"`, `"que se"`, `"más de lo que"`) gets hit harder than a staccato Q&A sentence. On `cl100k_base`, you're paying **55% more** for the Spanish version of the same article.

## What this costs you, in dollars

Assume a mid-sized product: 1M API calls per month, GPT-4-turbo at $0.01 per 1K input tokens, average EN prompt equivalent of 500 tokens.

| User language | Avg tokens/request | Monthly input cost | Delta vs EN |
|---------------|-------------------:|-------------------:|------------:|
| English       |                500 |             $5,000 |           — |
| Spanish       |                739 |             $7,391 |     **+$2,391/mo** |
| Portuguese    |                804 |             $8,043 |     +$3,043/mo |
| French        |                891 |             $8,913 |     +$3,913/mo |
| German        |                978 |             $9,783 |     +$4,783/mo |
| Japanese      |              1,467 |            $14,674 |     +$9,674/mo |
| Arabic        |              1,652 |            $16,522 |    **+$11,522/mo** |

Over a year, the Arabic-language version of your product costs **$138K more** than the English one — for the identical model, identical functionality, identical output quality.

## The workarounds, ranked

### 1. Pre-translate to English, post-translate the answer (the big win)

This is the asymmetric fix: the translation step is cheap (you can do it with a tiny model or a dedicated translation service), the token savings on the main model are large.

Naïve flow:

```
User (ES) → GPT-4 (ES) → Answer (ES)    # 739 tokens, $0.00739
```

Pre/post-translate flow:

```
User (ES) → translator → GPT-4 (EN) → translator → Answer (ES)   # ~500 main + tiny translation
```

With a cheap translation model (GPT-4o-mini at $0.15/1M in, or a dedicated MT service), the round-trip translation cost is negligible (~$0.0003) vs. the $0.0024 you save on GPT-4. That's ~32% net cost reduction on the input side.

Caveats:

- **Idiomatic content loss.** If the user's prompt contains culturally specific references, a two-hop translation can drop nuance. Test it.
- **Output quality.** Top-tier English-only models produce measurably better reasoning than their multi-language peers. This is a side benefit, not a regression.
- **PII and compliance.** A third-party translation layer is another data-processor in your chain. Factor that in.

### 2. System-prompt compression (a steady smaller win)

Your system prompts are probably fat. "You are a helpful customer service agent. Always respond in Spanish. Use a formal register. Do not…" — that's 200+ tokens before the conversation even starts, repeated every turn.

Compressed into an LLMLingua-style prompt or a SafePath-style pointer, that drops to ~15 tokens. See [our benchmarks on prompt compression](https://transfer.tokenstree.com?utm_source=devto&utm_medium=article&utm_campaign=hidden-tax) for numbers.

### 3. Switch to `o200k_base` models (free, partial win)

If you're still on `gpt-4-turbo` and your workload tolerates GPT-4o's quality profile, migrating cuts the language gap from 1.55× to 1.34× for Spanish. Not a complete fix, but a free ~13% cost reduction the day you flip the switch.

### 4. Use a lower-cost model for the non-English leg

If your users write in Spanish and your backend reasoning is in English, the translation doesn't need GPT-4-level quality. A small, dedicated model can handle ES↔EN for a fraction of the cost.

This is the architecture behind [translation.tokenstree.com](https://translation.tokenstree.com?utm_source=devto&utm_medium=article&utm_campaign=hidden-tax) — route translation through a small model, keep the expensive reasoning model operating in its native-efficient language.

## What about a multilingual-native model?

Good question. Models like Aya (Cohere), Qwen (Alibaba), BloombergGPT, or Mistral Large have more multilingual-balanced tokenizers. They do narrow the gap for Spanish, Chinese, and Japanese — some benchmarks show Qwen tokenizing Mandarin 2× more efficiently than GPT-4.

But (a) the per-token price is often higher, (b) the quality ceiling for hard reasoning is still set by the GPT-4 / Claude / Gemini class, and (c) if your product is already on OpenAI, switching model vendors is a non-trivial migration.

For most teams, the translation-layer approach wins on effort-to-savings ratio.

## What I'd do if I were paying this bill

If your OpenAI invoice has a line item above $500/month and a meaningful fraction of your users write in a non-English language, **audit where your tokens go**. Specifically:

1. Log input token counts per request, tagged with detected language.
2. Weight by language share of your traffic.
3. Compute the language-weighted token cost vs. an all-English baseline.
4. If the delta is >15% of your monthly spend, a translation-layer refactor pays for itself within a month.

The industry has internalized "tokens are the unit we pay for." What most teams haven't internalized is that **one token is not one unit of information**, and the exchange rate is rigged against non-English.

---

**Reproducibility note.** All numbers above are from `tiktoken` 0.12.0 against public encoding files. The prompts, script, and raw output are in the benchmark section — copy, paste, verify. If your numbers differ, I want to know.

**Follow-up piece.** Next week: doing this at scale with a 20K-row production log. We'll measure real savings on a real app that flipped from naïve multilingual prompting to a translation-layer architecture, and plot the cost curve over 90 days.

If you want to skip building the translation pipeline yourself, [translation.tokenstree.com](https://translation.tokenstree.com?utm_source=devto&utm_medium=article&utm_campaign=hidden-tax-cta) is the hosted version of exactly this pattern — with the non-English → EN → LLM → non-English round trip handled for you, billed on the savings.

*If you found a specific content type or language pair where the tax is worse than the numbers above, drop it in the comments. Benchmarks welcome.*

---

## Reproduce locally

```bash
git clone https://github.com/vfalbor/llm-language-token-tax
cd llm-language-token-tax
pip install tiktoken
python benchmark.py
```

## License

MIT. Commercial use, modification, redistribution — all permitted.

## About

Maintained by [Victor Fernandez Albor](https://github.com/vfalbor). Hosted mitigation of exactly this pattern: https://translation.tokenstree.com

## Articles

- [The Token Is a Phantom Unit](articles/the-token-is-a-phantom-unit.md) — why LLM pricing is built on a unit decoupled from both the work and the hardware (May 2026)

## Companion benchmark: vs Caveman (May 2026)

After [caveman](https://github.com/JuliusBrussee/caveman) hit 64k stars cutting **output** tokens by 65%, we ran an input-side head-to-head. Same prompts, same tokenizer, three reducers compared.

**Result:** TokensTransfer (LLMLingua-2) saves **52.9%** of input tokens on caveman's own benchmark, vs ~9% for a faithful replica of the caveman-compress skill. They are not competitors — caveman is for output, transfer is for input. Stack them, save on both sides of the bill.

Full numbers, methodology and reproduction script: **[vs-caveman/](vs-caveman/)**
