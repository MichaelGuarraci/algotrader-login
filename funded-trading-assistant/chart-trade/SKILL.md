---
name: chart-trade
description: Read an ES (E-mini S&P 500) chart screenshot and return a NOW / ZONE A / ZONE B trade call with per-fill risk, reward, and R-multiple. Use whenever the user posts a chart image and asks for a call, "anything now", "what should I do", or reports a fill/exit that needs a fresh read afterward. Sized for the funded account's current contract count (currently 4 contracts, $50/point/contract = $200/point).
---

# Chart Trade Call

Read the chart, verify the time, return exactly one call in the fixed format
below. No lead-in paragraph, no hedging, no wrap-up recommendation. The
caution flags below are the only prose allowed, and they go inline, not as a
paragraph before the block.

## Before every call

1. Run `TZ=America/New_York date` to get the exact ET time. Never estimate it.
2. Read price from the **colored, timestamped price box** on the right axis
   only (teal/red fill, has a clock time next to it). Never read the
   crosshair-following `⊕` box or the OHLC header — those are not the live
   price.
3. If ET time falls in 11:00–13:10, this is the **dead zone**. Still give the
   call, but append ` [dead zone]` on the NOW line.
4. Confirm current contract count before computing dollars. Default is 4
   contracts ($200/point). If the account's contract count changed (funded
   scaling 2→3→4), use the current count and update the multiplier.

## Output format — exactly this, nothing more

```
NOW  <price>  <one-clause structural read>[ dead zone]

ZONE A ▸ <SELL/BUY> <low> – <high> (<one-clause reason>)          confidence <NN>%  [← primary]
 Fill near TOP    (<high>) → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>
 Fill near BOTTOM (<low>)  → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>

ZONE B ▸ <SELL/BUY> <low> – <high> (<one-clause reason>)          confidence <NN>%
 Fill near TOP    (<high>) → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>
 Fill near BOTTOM (<low>)  → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>
```

Rules for filling it in:

- A zone is a **range**, not one price — always compute both fill scenarios
  (entry at the top of the zone and entry at the bottom of the zone), because
  risk/reward differ meaningfully between them.
- `risk` = `|entry − SL|` in points × $/point. `reward` = `|entry − TP|` in
  points × $/point. `R` = `reward / risk`, one decimal place (two if it
  lands on something like 1.71).
- TP is structural (next real level), not scaled to hit a round R-multiple.
  SL sits beyond the zone/structure, not tight inside it.
- Confidence is per zone, calibrated against the Confidence Calibration tab
  in the dashboard, not a felt sense.
- Mark the zone judged more likely to fill/work with `← primary` — only one
  zone gets it, and only when there's a real lean; omit it if truly a coin
  flip between the two.
- If the setup doesn't warrant a trade at all, print only:

```
NOW  <price>  <one-clause structural read>[ dead zone]

NO TRADE — <one-clause reason>
```

## Never

- Never add commentary, analysis, or a recommendation outside the block
  above. If the dead zone or a calibration concern applies, it's the
  `[dead zone]` tag on the NOW line — not a paragraph.
- Never use the crosshair `⊕` box for price.
- Never skip the ET time check.
- Never log a trade to the Account Tracker from this call alone — logging
  happens when the user reports the actual fill/exit, not on the call.
