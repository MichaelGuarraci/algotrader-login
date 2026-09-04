---
name: es-scan
description: Scan the ES (E-mini S&P 500) market and return a single trade call — direction with confidence, exit price with confidence, nothing else. Use when the user asks for an ES read, an ES setup, "what's ES doing", "should I be long or short", or is trading a funded account and wants a call. Not for equities — use AlgoTrader Pro for those.
---

# ES Scan

Return exactly one call. Four values. No commentary, no analysis, no hedging
paragraph, no "here's what I'm seeing".

## Output format — exactly this, nothing more

```
BUY  ·  confidence 72%
EXIT 5842.25  ·  confidence 64%
```

Direction is `BUY`, `SELL`, or `NONE`. When `NONE`, print only:

```
NONE  ·  confidence 0%
```

Never add a preamble, a reason, a signal list, a risk note, or a follow-up
question. The user asked for four values. Give four values.

## Run it

```bash
python es_scan.py
```

The script prints the block above and nothing else. Relay its output verbatim.
Do not summarize it, expand it, or add context around it.

## Data source

**Real ES bars only. No equity proxy, ever.** A SPY-derived level is close
enough to read direction and not close enough to rest an order at, so the
script prints `NONE` rather than a converted guess.

Every Polygon call elsewhere in this repo hits `market/stocks`, so the stocks
plan likely has no ES entitlement. Check before trusting any output:

```bash
python es_scan.py --probe
```

It reports which feeds the key can actually reach. If none return bars, point
it at a feed you do have:

```bash
# .env
ES_BARS_URL=...        # overrides all built-in sources
ES_SYMBOL=ESH6         # front month; update at roll (Mar/Jun/Sep/Dec)
```

Options, best fit first: Polygon's Futures product (same key, separate
subscription), Databento (CME direct, pay-as-you-go), your prop firm's API
(Tradovate/Rithmic), or IBKR.

**Roll matters.** `ES_SYMBOL` must track the front month or you will be
scanning a stale contract with drifting basis.

## What the confidence numbers mean

Both are **heuristic strength scores, not calibrated probabilities.** A 72% is
not "72% of these win". It is the signal stack's strength expressed on a 0–100
scale.

- **Direction confidence** — derived from the ICT signal score (same weights as
  `core.py`: OB 3.0, FVG 3.0, FIB_OTE 2.5, VOL 1.5, STRUCT 1.0, P/D 1.0),
  scaled by signal-type count and HTF 15-min bias agreement.
- **Exit confidence** — how reachable the target is inside recent range:
  ATR over the distance to target, penalized when the target sits beyond the
  session's realized range.

If asked how a number was derived, explain it. Do not volunteer it.

## Never

- Do not present these as win probabilities or expected value.
- Do not place, size, or route an order. This skill reads and reports.
- Do not carry over an equity percentage stop. ES is $50/point, $12.50/tick —
  the 1.5%/4% equity rules do not port. The script works in points.
- Do not fabricate a call when data is missing or stale. Print `NONE`.
