# Funded Trading Assistant — ES

Standalone. Local. **Manual entry** — this tool never places, sizes, or routes
an order. It reads the market and gives you one call.

Not part of AlgoTrader Pro. No shared code, no shared repo, no imports from it.
The ICT signal weights are copied rather than imported, deliberately, so this
stays independent.

## Output

Four values. Nothing else.

```
BUY  ·  confidence 72%
EXIT 5842.25  ·  confidence 64%
```

Or, when no setup qualifies or data is missing:

```
NONE  ·  confidence 0%
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in your feed
python es_scan.py --probe   # RUN THIS FIRST
```

`--probe` reports which ES feeds your key can actually reach.

## The data problem — read this before trusting output

**A Polygon stocks plan does not cover futures.** If `--probe` comes back empty
on every source, this tool cannot see ES and will correctly print `NONE`
forever rather than guess.

There is no SPY fallback, by design. A SPY-derived level is close enough to read
direction and not close enough to rest an order at, and a wrong exit price on a
funded account is worse than no call.

Feeds that do work, best fit first:

| Feed | Notes |
|------|-------|
| Polygon Futures | Same account, separate subscription |
| Databento | CME direct, pay-as-you-go, cleanest ES data |
| Tradovate / Rithmic | Whatever your prop firm already gives you |
| IBKR | If you hold an account |

Point `ES_BARS_URL` at whichever you land on.

**Set `ES_SYMBOL` to the front month.** Defaults to `ES`. If your feed wants
`ESZ6`, leaving the default means scanning a stale contract with drifting basis
— the numbers will look plausible and be wrong.

## What the confidence numbers are

**Heuristic signal-strength scores on 0–100. Not win probabilities.**

A 72% does not mean 72% of these trades win. It means the signal stack is
strong. Nothing here has been backtested against ES.

- **Direction** — ICT signal score (OB 3.0, FVG 3.0, FIB_OTE 2.5, VOL 1.5,
  STRUCT 1.0, P/D 1.0), scaled by signal-type count, cut 45% when the 15-min
  bias disagrees.
- **Exit** — ATR over distance-to-target, penalized when the target sits beyond
  most of the session's realized range.

To make these mean something, log every call against what actually happened,
then calibrate. Until then treat them as relative, not absolute: a 72% is a
better setup than a 50%, but neither is a probability.

## Contract mechanics

ES is **$50/point, $12.50/tick, 0.25 tick size**. AlgoTrader Pro's 1.5%/4.0%
equity stop rules do not port and are not used here. This works in points:
stop = 1 ATR, target = 2.67R, which preserves the equity config's reward:risk
ratio without borrowing its percentages.

## Stop price

The script computes a stop internally (1 ATR) to derive the target, but does
not print it — you asked for four values. If you want it surfaced for manual
entry, it's a one-line change in `main()`. Worth considering: you're sizing
these by hand, and the stop is what determines risk.

## Known state

Never run against live data. Written and syntax-checked only. The futures
endpoint paths in `ES_SOURCES` are educated guesses at Polygon's URL scheme —
that's precisely what `--probe` is for. Expect the first run to need a patch.
