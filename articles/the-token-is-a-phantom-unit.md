# The Token Is a Phantom Unit

**Why LLM pricing is built on a number that doesn't mean what we think it means**

For two years now we've been pricing the most consequential infrastructure of the decade in a unit nobody can pin down. The token is the unit. You're billed in it, you budget in it, you scale plans around it, you write blog posts about it. And it doesn't actually correspond to anything stable on either end of the bridge it's supposed to span.

The bridge is supposed to connect two things: the resources a model provider spends serving your request (compute, energy, hardware depreciation) and the value you get out of it (an answer, a tool call, a generated image). The token is the unit we agreed would price both ends. It does neither cleanly.

## the supply side keeps moving

NVIDIA's own engineering blog says it plainly: "Cost Per Token Is the Only Metric That Matters" and the GPU's hourly rate "tells you almost nothing useful." [1] That's the supplier admitting that the input cost (the GPU) and the output unit they sell (the token) are loosely coupled at best. The relationship between "this hardware was rented for one hour" and "this user owes us X tokens" is a function of throughput, batch size, model architecture, quantization, kernel choice, decoding strategy, KV-cache reuse, and operator skill.

A concrete example from public benchmarks: an H200 costs more per hour than an H100 but generates roughly 50–60% more tokens per second on the same model. So the price per token drops even as the price per hour rises. [2] The supplier swaps hardware overnight and your unit silently changes value beneath you.

Now look at the price history. Between late 2022 and late 2025, the price of GPT-4-equivalent capability fell from about $20 per million tokens to around $0.40. A 50× drop. [3] Over a more recent window, the median LLM API price fell roughly 80% in twelve months, and another 2–3× drop is forecast for the next twelve. [4]

A unit whose price moves 50× in three years is not a unit. It's a moving target with a name.

## the demand side keeps moving too

On your side, the token is determined by the tokenizer. The tokenizer is software that turns your input string into integers. There is no ISO standard for it. Each provider uses its own. Each provider can change its own. They have. They will again.

The same string measured by OpenAI's BPE, Anthropic's tokenizer, and a Llama tokenizer produces three different counts. The same string in English vs. Hindi can produce a ~5× difference in count under the same tokenizer. [5] The same provider, between two model releases, can ship a new tokenizer and quietly inflate or deflate everyone's bills.

Consider what that means: the provider unilaterally controls the unit they bill you in. If costs squeeze them, they can in principle ship a tokenizer that counts the same prompts as more tokens. They probably won't because the market is competitive enough that someone would notice, but the structural fact remains: the meter is on their side of the wall.

There's no equivalent in any other infrastructure layer agents and operators rely on. Bandwidth is bits. Storage is bytes. Compute is floating-point operations. DNS is RFCs. They're auditable, portable, and stable enough that you can compare quotes across vendors. Tokens are not. The "200K context window" in a release note means very different real text depending on language and tokenizer. The "we cut our bill 40% by switching to Provider B" you read on Twitter assumes both providers count the same string the same way. They don't.

## what's actually being sold

Here's what I think is being sold under the word "token," based on what we can observe:

A probabilistic claim that for an average prompt, in an average language, processed by today's hardware fleet, with today's model weights, with today's tokenizer, the inference cost will be approximately what the price sheet says. The provider is selling you a slice of an internal accounting that they can re-cut at any moment because they own every variable.

That's not a unit. That's a posture. It's the same posture a casino takes when it prices chips: the chip looks like a unit but it's really a temporary IOU against a probability distribution that the house controls.

The tell is in NVIDIA's framing of the optimization problem: maximize tokens-per-second to drive cost-per-token down. [1] In any actual market, the unit you're billed in is exogenous to the supplier. Nobody asks the electric company to "optimize the kilowatt-hour" because the kilowatt-hour is defined by physics and the supplier has to find efficiencies inside that constraint. With tokens, the supplier *defines* the unit. So "optimization" can mean "we shipped a faster GPU" or "we changed the tokenizer to count differently" or "we updated batching heuristics" — and you can't tell from the bill which one happened.

## three independent axes, no anchor

To make this concrete, here are the three axes that determine your bill in 2026, and the fact that they all move independently:

| axis | who controls it | how often it changes | observable to you |
|---|---|---|---|
| hardware (GPU model, throughput) | provider | every 12–24 months (Blackwell, MI350, custom silicon) | no |
| tokenizer (string → integer mapping) | provider | every model release, sometimes silently | partially, only if you re-tokenize |
| price per token | provider, market | continuously, roughly 80% per year down | yes, but the unit beneath the price is not stable |

There is no anchor. The hardware can get cheaper or pricier per token; the tokenizer can be rewritten to count differently; the headline price moves continuously. Your "cost per call" is the product of three numbers, all of which the supplier controls and all of which can change without notice.

This isn't pricing. It's three different fluctuations multiplied together and shipped as a single number on an invoice.

## what would pricing look like if it weren't this

A few possibilities, none of them happening at scale yet:

1. **Price the work, not the unit.** Charge per resolved task, not per token. "Solve this support ticket: $0.04." Some inference providers are quietly moving toward this for batch workflows. The provider eats the variance.
2. **Open the tokenizer.** A standardized open tokenizer audited like an RFC. Tokens become portable across providers. The market would compete on real efficiency instead of counting tricks.
3. **Bill the compute directly.** Charge per FLOP or per GPU-second-equivalent normalized to a published reference architecture. The user pays for physics; the provider competes on engineering. Cloud GPU rentals already work this way — and tellingly, providers generally prefer the token model precisely because it abstracts away the FLOPs they can optimize.
4. **Two-part tariffs.** A flat reservation fee for capacity plus a marginal fee per token, with the marginal fee tied to a published efficiency index. Telephony did this. Electricity does this.

None of these would be hard to build technically. None of them are happening because the current model benefits the suppliers: it bundles three optimization opportunities (hardware, tokenizer, price) into a single opaque number whose drift is invisible until you go looking for it.

## what to do as a customer

You can't fix the unit. You can't force providers to standardize their tokenizers. You can't audit the GPU fleet. What you can do is stop pretending the unit is stable:

1. **Re-measure quarterly.** Run your real prompt distribution through every provider's tokenizer, today, and write down the count. Do it again in three months. The numbers will move.
2. **Track cost per task, not cost per token.** A token bill that's flat while your task volume halves is a bill that just got worse. Tokens-per-task is the real efficiency metric for your workload.
3. **Don't trust headline prices when comparing providers.** Compare bills on identical prompt distributions, including non-English if you serve multilingual users.
4. **Compress upstream.** Tools like Microsoft Research's LLMLingua-2 [6] cut the token count of your prompts by 60–95% before they hit any provider. The provider can change the unit; they can't change what you don't send. We expose this as a hosted API at [transfer.tokenstree.com](https://transfer.tokenstree.com).
5. **Keep your prompt corpus portable.** The day the unit shifts unfavorably under one provider, you want to migrate without rewriting six months of prompt engineering against a tokenizer-specific quirk.

## the honest summary

The token isn't a meter. It's a label glued onto three independent moving parts whose product happens to land near a number that resembles a price. The market mostly works — the moving parts mostly drift in our favor (the price per token has fallen 50× in three years). But the fact that the drift is favorable doesn't make the unit any less arbitrary.

We agreed to pay for a phantom because for now the phantom is getting cheaper. That's not a stable foundation for budgeting an industry that increasingly runs on top of it.

---

### Sources

1. NVIDIA — *Rethinking AI TCO: Why Cost per Token Is the Only Metric That Matters* — https://blogs.nvidia.com/blog/lowest-token-cost-ai-factories/
2. GPU Tracker — *Cost Per Token: Which Cloud GPU Is Actually Cheapest for LLM Inference in 2026* — https://gputracker.dev/blog/gpu-cost-per-token-llm-inference-2026
3. Silicon Data — *Understanding LLM Cost Per Token: A 2026 Practical Guide* — https://www.silicondata.com/blog/llm-cost-per-token
4. Cloud IDR — *Complete LLM Pricing Comparison 2026* — https://www.cloudidr.com/blog/llm-pricing-comparison-2026
5. vfalbor — *AI companies charge you 60% more based on your language, BPE tokens* (HN, April 2026) — https://news.ycombinator.com/item?id=47603969
6. Microsoft Research — *LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression* (ACL 2024) — https://aclanthology.org/2024.findings-acl.57/
