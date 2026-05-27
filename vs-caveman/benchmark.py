#!/usr/bin/env python3
"""
Token-savings benchmark: TokensTransfer (LLMLingua-2) + TokenTranslation
vs Caveman-style compression vs baseline.

Three suites:
  A) caveman_native     — caveman's own 10 prompts (favors caveman style)
  B) multilingual       — non-English prompts (favors translation→en)
  C) llm_context_heavy  — long verbose context (favors LLMLingua-2 compression)

Token counting: tiktoken cl100k_base (Claude tokenizer is very close to this).
"""

import json, re, requests, time, sys, statistics
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
def tok(s: str) -> int: return len(ENC.encode(s))

TRANSFER_URL = "https://transfer.tokenstree.com/compress"
TRANSFER_KEY = "REPLACE_WITH_YOUR_TRANSFER_KEY"
TRANSLATE_URL = "https://translation.tokenstree.com/translate/in"
TRANSLATE_KEY = "REPLACE_WITH_YOUR_TRANSLATION_KEY"

# -------- Caveman-style rule-based compressor (replicates skill rules) --------
ARTICLES = {"a", "an", "the"}
FILLERS = {"just","really","basically","actually","simply","essentially","generally"}
PLEASANTRIES_RX = [
    (r"\bsure[,.]?\s*", ""), (r"\bcertainly[,.]?\s*", ""),
    (r"\bof course[,.]?\s*", ""), (r"\bhappy to\b\s*", ""),
    (r"\bI'?d recommend\s*", ""), (r"\bplease\s*", ""),
]
HEDGING_RX = [
    (r"\bit might be worth\b", ""), (r"\byou could consider\b", ""),
    (r"\bit would be good to\b", ""), (r"\bperhaps\b", ""),
    (r"\bmaybe\b", ""), (r"\bI think\b", ""),
]
REDUNDANT_RX = [
    (r"\bin order to\b", "to"), (r"\bmake sure to\b", "ensure"),
    (r"\bthe reason is because\b", "because"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bat this point in time\b", "now"),
    (r"\butilize\b", "use"), (r"\butilizes\b", "use"),
    (r"\bimplement a solution for\b", "fix"),
    (r"\bin addition to\b", "and"), (r"\bin order for\b", "for"),
]
CONNECTIVES = {"however","furthermore","additionally"}
YOU_SHOULD = [r"\byou should\b", r"\byou must\b", r"\byou need to\b",
              r"\bremember to\b", r"\bdon't forget to\b"]

CODE_BLOCK = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`]+`")
URL = re.compile(r"https?://\S+")

def caveman_compress(text: str) -> str:
    # protect code/URLs
    placeholders = {}
    def protect(rx, s):
        def repl(m):
            k = f"\x00P{len(placeholders)}\x00"
            placeholders[k] = m.group(0)
            return k
        return rx.sub(repl, s)
    out = protect(CODE_BLOCK, text)
    out = protect(INLINE_CODE, out)
    out = protect(URL, out)

    # apply regex substitutions
    for rx, rep in PLEASANTRIES_RX + HEDGING_RX + REDUNDANT_RX:
        out = re.sub(rx, rep, out, flags=re.I)
    for rx in YOU_SHOULD:
        out = re.sub(rx, "", out, flags=re.I)

    # word-level removals
    def filter_words(line):
        words = line.split()
        kept = []
        for w in words:
            wl = re.sub(r"[^a-zA-Z']", "", w).lower()
            if wl in ARTICLES or wl in FILLERS or wl in CONNECTIVES:
                continue
            kept.append(w)
        return " ".join(kept)
    out = "\n".join(filter_words(l) for l in out.split("\n"))

    # collapse whitespace, restore
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r" *\n *", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    for k, v in placeholders.items():
        out = out.replace(k, v)
    return out

# -------- API callers --------
def call_transfer(text, rate=0.5):
    try:
        r = requests.post(TRANSFER_URL,
            headers={"X-API-Key": TRANSFER_KEY, "Content-Type":"application/json"},
            json={"text": text, "rate": rate}, timeout=120)
        d = r.json()
        return d.get("compressed_text", ""), d.get("metrics", {})
    except Exception as e:
        return "", {"error": str(e)}

def call_translation(text, backend=None):
    try:
        payload = {"text": text}
        if backend: payload["backend"] = backend
        r = requests.post(TRANSLATE_URL,
            headers={"X-API-Key": TRANSLATE_KEY, "Content-Type":"application/json"},
            json=payload, timeout=60)
        d = r.json()
        return d.get("optimized_text", ""), d
    except Exception as e:
        return "", {"error": str(e)}

# -------- Suites --------
with open("/tmp/bench-out/caveman_prompts.json") as f:
    suite_a = [(p["id"], p["prompt"]) for p in json.load(f)["prompts"]]

suite_b = [
    ("es-django", "Tengo una aplicación Django con un modelo de usuario personalizado y necesito migrar la base de datos sin perder datos existentes. ¿Cuáles son los pasos correctos para hacer esta migración en producción de forma segura?"),
    ("fr-react", "Mon composant React se re-rend à chaque mise à jour de l'état même si les props n'ont pas changé. Je passe un objet en tant que prop. Pourquoi cela arrive-t-il et comment puis-je le résoudre?"),
    ("de-postgres", "Wie richte ich einen PostgreSQL-Verbindungspool in Node.js mit ordnungsgemäßer Timeout- und Fehlerbehandlungskonfiguration ein? Bitte erkläre die wichtigsten Parameter."),
    ("pt-microservices", "Temos um aplicativo Django monolítico que está ficando lento. A equipe está debatendo microsserviços. Quais são os principais fatores a considerar antes de dividir o monolito?"),
    ("it-docker", "Spiegami come ottimizzare un Dockerfile multi-stage per ridurre la dimensione dell'immagine finale e migliorare il tempo di build. Quali sono le migliori pratiche?"),
]

suite_c_long = (
    "You are a helpful assistant that specializes in software engineering best practices. "
    "Given the following large context about our codebase, you should carefully analyze the architecture and provide recommendations. "
    "The application is a monolithic Django app that has been growing steadily over the past five years. "
    "It currently handles approximately ten thousand requests per minute during peak hours and stores about two terabytes of user data. "
    "The team is debating whether to break the monolith into microservices or to invest in vertical scaling. "
    "There are concerns about deployment complexity, debugging difficulty, and the operational overhead of running many small services. "
    "However, there are also concerns about the maintainability of a large codebase and the difficulty of onboarding new engineers. "
    "Please consider the tradeoffs carefully and provide a recommendation that takes into account both short-term and long-term implications. "
    "Make sure to discuss the costs and benefits of each approach and provide concrete examples where appropriate. "
    "Remember to also consider the team's current expertise and the existing tooling infrastructure they have in place. "
)
suite_c = [
    ("ctx-arch", suite_c_long + "Question: should we migrate to microservices now or scale the monolith vertically first?"),
    ("ctx-review", suite_c_long + "Question: what specific signals would tell us that the monolith has reached its limits?"),
    ("ctx-team", suite_c_long + "Question: what team structure changes are typically required when adopting microservices?"),
    ("ctx-cost", suite_c_long + "Question: what are typical hidden costs of microservices migrations that teams underestimate?"),
    ("ctx-roll", suite_c_long + "Question: how should a gradual rollout from monolith to microservices be sequenced?"),
]

ALL = [("A_caveman_native", suite_a), ("B_multilingual", suite_b), ("C_llm_context", suite_c)]

# -------- Run benchmark --------
results = {"suites": {}}
for suite_name, prompts in ALL:
    rows = []
    for pid, text in prompts:
        t0 = tok(text)
        # Transfer / LLMLingua-2 @ rate=0.5
        tx_text, tx_meta = call_transfer(text, rate=0.5)
        tx_tok = tok(tx_text) if tx_text else None
        time.sleep(0.3)
        # Translation
        tr_text, tr_meta = call_translation(text)
        tr_tok = tok(tr_text) if tr_text else None
        # Caveman rule-based
        cv_text = caveman_compress(text)
        cv_tok = tok(cv_text)
        # Transfer + Caveman stacked (apply caveman to transfer output)
        tcv_tok = tok(caveman_compress(tx_text)) if tx_text else None

        def pct(a, b): return None if b is None or a == 0 else round((1 - b/a)*100, 1)
        rows.append({
            "id": pid,
            "tokens_original": t0,
            "transfer": {"tokens": tx_tok, "saved_pct": pct(t0, tx_tok)},
            "translation": {"tokens": tr_tok, "saved_pct": pct(t0, tr_tok),
                             "src": tr_meta.get("source_lang"), "tgt": tr_meta.get("target_lang")},
            "caveman_rules": {"tokens": cv_tok, "saved_pct": pct(t0, cv_tok)},
            "transfer+caveman": {"tokens": tcv_tok, "saved_pct": pct(t0, tcv_tok)},
        })
        print(f"[{suite_name}/{pid}] orig={t0}  transfer={tx_tok}  translation={tr_tok}  caveman={cv_tok}  stacked={tcv_tok}")
    results["suites"][suite_name] = rows

# Aggregates
agg = {}
for s, rows in results["suites"].items():
    def avg(key):
        vals = [r[key]["saved_pct"] for r in rows if r[key]["saved_pct"] is not None]
        return round(statistics.mean(vals), 1) if vals else None
    agg[s] = {k: avg(k) for k in ["transfer","translation","caveman_rules","transfer+caveman"]}
results["averages"] = agg
print("\n=== AVERAGE SAVINGS % ===")
print(json.dumps(agg, indent=2))

with open("/tmp/bench-out/results.json","w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to /tmp/bench-out/results.json")
