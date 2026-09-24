---
name: chart-trade
description: Read an ES (E-mini S&P 500) chart screenshot and return a NOW / ZONE A / ZONE B trade call with per-fill risk, reward, and R-multiple. Use whenever the user posts a chart image and asks for a call, "anything now", "what should I do", or reports a fill/exit that needs a fresh read afterward. Sized for the current active account (see Account context below).
---

# Chart Trade Call

## Account context — read this before every call

**Active simulation (replaced the prior 50K funded sim on 2026-09-17):**
5x **Tradeify Select 150K** accounts, stacked, starting from **EVALUATION**
(not funded). This skill (`chart-trade`) stays scoped to the 5-stack
practice simulation even though real trading (see the `trade-live` skill)
starts on a single 150K account — the two run in parallel, don't conflate
them. The prior 50K Select Flex funded sim ended at Trade 37, record
22-15, net +$25,825, balance $75,825 — preserved in its history in the
Account Tracker, not carried forward as this account's starting state.

- **Per-account eval rules:** profit target $9,000, EOD trailing drawdown
  $4,500, floor locks permanently at $150,100 (start + $100) once earned,
  **no daily loss limit during eval**, 40% consistency rule (biggest single
  day ≤ 40% of total profit) — this only delays qualifying to pass, it does
  not fail the account or restrict trading.
- **Eligible for up to 12 mini / 120 micro per account during eval, full
  size available from day one** (same pattern as the prior 50K eval).
  $50/point/contract → **$600/point per account at full size**. Actual
  count used per trade is governed by the risk-sizing rule below, not
  automatically 12.
- **Mirroring across the 5 accounts:** same direction, same instrument,
  same trade on all 5 simultaneously is explicitly allowed scaling, not a
  violation — every call in this skill is priced per-account (12 contracts,
  $600/point); the Account Tracker separately multiplies by 5 for the true
  combined P&L across all accounts. Never combine size across accounts
  into one account's position, and never hold opposing positions on the
  same instrument across the 5.
- **Funded-phase rules (once an account passes)**: the funded account
  **resets to the base starting balance ($150,000) — eval profit does
  NOT carry over**, confirmed via research. Buffer/drawdown restarts
  trailing fresh from that reset balance, not from wherever the eval
  ended. Starts at a reduced contract count (3 mini confirmed;
  intermediate steps up to 12 not yet confirmed — still open), scales
  back to 12 mini / 120 micro once that account's EOD balance reaches
  $154,500 (+$4,500 profit from the reset $150,000 base), at which point
  its floor locks at $150,100. No consistency rule once funded.
  Daily-loss-limit status once funded not yet reconfirmed for Select
  150K specifically — treat as unresolved until sourced.
- Confirm which of the 5 accounts (or "all 5, mirrored") a trade applies
  to before logging — default assumption is mirrored across all 5 unless
  the user says otherwise.

## Risk-sizing rule — SL/TP must respect eval limits

Added 2026-09-17 at user's request. Before setting SL/TP on any call:

- **Position must survive at least 3 consecutive max-loss trades before
  touching the floor.** Max per-trade risk = current buffer ÷ 3, recomputed
  from the current buffer (not always $4,500 — it shrinks after a loss and
  only resets upward after a new equity peak). At a full $4,500 buffer
  that's ≤$1,500/account per trade.
- **Contract count: `floor(max risk ÷ (structural SL distance in pts ×
  $50))`, capped at the account's current limit** — this is the check,
  always run it, never squeeze the stop instead of sizing down. SL always
  stays at its real structural level.
- **Once FUNDED with a buffer that's built real cushion, default to max
  contracts and use judgment rather than rigidly recomputing every time.**
  "Real cushion" means the buffer comfortably covers a max-size loss at
  this setup's typical stop width with real room to spare — not just
  "the account is funded." Still sanity-check an unusually wide stop
  against the buffer before defaulting to max; don't blindly max out a
  stop that's clearly wider than normal for this setup just because the
  account has grown. Early in eval, or whenever the buffer is thin/fixed,
  run the formula properly instead of defaulting.
- **Put the recommended contract count at the top of every call**, right
  after the NOW line — one number for the call, sized off the primary
  zone's structural stop. If the secondary zone's stop is different enough
  to need a different count, note that inline next to that zone instead of
  changing the top-line number.
- **State the drawdown distance every time**, not just when asked: current
  buffer to floor, and how many max-size losses in a row it would take to
  hit it (target: always ≥3). This goes in every trade-result report and
  before every new call that risks capital.
- **All dollar figures are per-account, not combined.** Keep it to one
  number per line — no ×5 combined figures unless the user explicitly
  asks for the stack-wide total in that moment.
- **TP sizing must respect the day's remaining room under the 40%
  consistency cap** whenever that day already has profit booked. Compute
  remaining room = (40% × $9,000) − today's profit-so-far *before*
  sizing a new target — don't print a structural TP without checking
  this first, and say explicitly when a TP is capped short of structure
  for this reason.
- Recompute both of these fresh from the current balance/target progress
  before every call — they change after every closed trade, not just once
  per session.

## Practice trades — paper reps, separate from the real eval log

Added 2026-09-17 at user's request. The user can call for a "practice"
trade: **always max contract size** (12/account, mirrored across all 5 =
60 combined) — no risk-sizing calculation, no buffer check, none of that
applies here. **Not placed on the real eval accounts** and **not
counted** toward the $9,000 target, the $4,500 drawdown/buffer, or the
40% consistency ratio. These are paper reps for practice/calibration
only — the point is getting used to what actual full-size funded
execution looks like across the stack.

- **No Buffer line on practice calls** — there's no real buffer being
  risked in practice mode, so don't print one. Drop straight from NOW
  into `Recommended: 12 contracts/account (practice — always max)`.
- Log practice trades in the Account Tracker's separate **Practice Log**
  section — never mixed into the Evaluation trade log table or its
  running totals.
- Always default to the real (risk-budgeted) trade unless the user
  explicitly says "practice." Don't assume practice sizing on your own.
- Important caveat to repeat if the user seems to be conflating the two:
  on the actual Tradeify/Tradovate platform, any order actually placed on
  a live eval account counts for real — there's no way to place a real
  fill that Tradeify itself exempts from P&L/drawdown/consistency. This
  practice/real split only works because these are simulated paper reps,
  not real orders.
- Once an account passes and is funded, real (non-practice) trades resume
  at whatever the funded contract sizing allows — practice-log trades
  before that point stay in their own record, not backfilled into the
  funded totals.

## Reporting rule — phase-dependent primary metric

When reporting a closed trade's P&L (in chat and in the Account Tracker):

- **During EVALUATION: report per-account first.** Per-account is the
  number that actually matters (each account has its own $9,000 target and
  $4,500 drawdown) — lead with it. The combined (x5) figure is secondary
  context, not the headline.
- **Once any account passes to FUNDED: report the combined/total figure
  first** for that account's contribution — funded accounts don't have a
  per-account target to chase in the same way, so the aggregate is what
  matters. If some accounts are still in eval and others are funded, report
  both groups separately (don't blend an eval account's progress into a
  funded total).
- **Every trade-result report during eval must show, every time:**
  1. Progress toward the $9,000 per-account profit target (dollar amount
     and %).
  2. Consistency-rule status: current biggest single day's profit as a %
     of total profit so far, and whether that's under or at-risk of the
     40% cap.
  Don't wait to be asked for these — they're part of the standard report,
  not optional detail.

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
4. Compute contract count per the risk-sizing rule below (12 is the
   eval ceiling, not the default — actual count depends on the current
   buffer and this trade's structural stop distance). If an account
   passes to funded and its count is temporarily reduced, use that
   account's actual current count and update the multiplier — don't
   assume all 5 accounts are always in sync once any of them pass.

## Zone identification — ICT concepts (added 2026-09-23, grounded 2026-09-24)

Zone A and Zone B are derived from ICT (Inner Circle Trader) concepts, not
generic support/resistance. This replaces the prior generic-structure
approach for every future call — apply it by default, not just when asked.

**Source of truth: AlgoTrader Pro's own "08 - ICT Strategy Reference" and
"ICT Methodology MOC"** (pulled from the user's Obsidian vault via Google
Drive on 2026-09-24) — this is the real, documented strategy AlgoTrader
Pro's bot runs, not a generic ICT summary. The weighted scoring below
matches what `es_scan.py`'s confidence numbers are already built on.

### Weighted signal score

| Signal | Points | Detection notes |
|---|---|---|
| **Order Block (OB)** | 3.0 | Last opposing candle before an impulsive move (last down-candle before an up-move = bullish OB, and reverse). Requires ~1.5× volume + body ≥0.4%. **Most reliable signal in the system.** |
| **Fair Value Gap (FVG)** | 3.0 | 3-candle imbalance, no overlap between candle 1's wick and candle 3's wick. Requires ≥0.3% gap. **Second most reliable — pairs extremely well with OB.** |
| **Fibonacci OTE** | 2.5 | 62–79% retracement of a significant swing. **Most reliable single BUY confirm**, especially stacked with an OB/FVG at that level. |
| **Volume Imbalance / Liquidity Sweep** | 1.5 | A wick running stops through an obvious swing high/low before reversing (buy-side sweep → bearish reversal; sell-side sweep → bullish reversal), or an abnormal volume spike vs. recent average. |
| **Market Structure (STRUCT)** | 1.0 | Break of Structure (BOS) or Change of Character (ChoCh) confirming trend direction. |
| **Premium/Discount** | 1.0 | Price above the swing's midpoint = premium (look to sell); below = discount (look to buy). |

**Entry threshold: ≥6.0 points from 3+ distinct signal types.** A single
strong signal (e.g. a clean OB alone at 3.0) is not enough on its own —
don't call a zone primary off one concept just because it looks clean.

### Entry gates (non-negotiable)

- **BUY** needs `FIB_OTE` **or** (`DISCOUNT` + `STRUCT`) — a BUY zone in the
  premium half with no OTE confluence fails the gate, full stop, regardless
  of how clean the level looks.
- **SELL** needs `FIB_OTE` **or** `PREMIUM` — same logic in reverse.

**Updated 2026-09-24 at user's request: still show two zones even when the
score is below 6.0 or a gate doesn't clear** — this is an advisory tool, not
the automated bot, and the user is the final human check on every trade, so
show what's there and let them decide. What doesn't change: confidence must
say so honestly. A zone below threshold or missing its gate gets a low
confidence number (well under 50%, often under 30%) and the one-clause
reason states what's missing — "FVG only, 3.0/6.0, no OTE/Premium
confluence" — not a vague hedge. Never quietly round a weak setup up to
sound more solid than it is just to fill the slot.

### Kill zones — this is where the existing dead-zone rule comes from

- **New York Open (9:30–11:00 AM ET)**: high activity, preferred window.
- **Dead Zone (11:00 AM–1:10 PM ET)**: blocked in the live bot
  (`ENABLE_HARD_KILLZONE_BLOCK`), measured at **+0.16 PF** for filtering it
  out — this is the actual origin of the `[dead zone]` tag already in this
  skill, not an arbitrary cutoff.
- **New York Afternoon (1:00–4:00 PM ET)**: moderate activity.
- **London Open (2:00–5:00 AM ET)**: not traded by the bot.
- **HTF 15-min bias filter**: the bot only takes 5-min entries aligned with
  15-min structure — measured at **+0.42 PF**, the single biggest filter in
  the system. Read the higher timeframe before trusting a lower-timeframe
  zone that fights it.

### Filter vs. bonus — the one hard-won lesson worth keeping

*"Only filters improve PF. Bonuses add trades."* Every real improvement to
this system has been a filter that removes bad setups, never an added
signal source that just generates more trades. When in doubt about whether
to add a new concept to a zone's justification or tighten an existing gate,
tighten — don't add.

### What does NOT port over

The live bot's SL/TP (1.5% fixed SL, 4.0% fixed TP, trailing at +1.5%,
breakeven at +1.0%) are **equity-percentage rules for the stock version of
AlgoTrader Pro and do not apply to ES.** ES is $50/point, not a percentage
instrument — SL/TP here stay structural (OB/FVG boundary, swing high/low),
exactly as the existing Output Format rules already require. Don't compute
a 1.5%/4.0% stop on an ES price.

### Writing the zone

Each zone's one-clause reason should name the actual concept and score
driving it — "bearish OB (3.0) + FVG fill (3.0) = 6.0, MSS confirmed," not
generic language like "resistance cluster." Confidence still follows the
existing calibration process; naming an ICT concept doesn't earn a
confidence bump on its own — a weak OB is still a weak OB, and a zone that
scores 6.5 barely over threshold isn't the same conviction as one that
scores 9+.

This changes how a zone's location and reasoning are derived. It does not
change the output format, the risk-sizing rule, or anything else in this
skill.

### Extended ICT pattern library (pulled from the user's Obsidian vault,
### 2026-09-24) — use these to sharpen zone reasoning and stop placement,
### not to replace the 6-signal score above

- **Breaker Block** — a broken order block that flips polarity (former
  support that failed becomes resistance, and vice versa). Needs 2-3 prior
  touches before the break, then a retest from the other side. **Entry is
  on the retest rejection, never the initial break** — the break itself is
  the trap, not the trade.
- **Turtle Soup** — a named liquidity-sweep reversal: price runs a level
  tested 3+ times, sweeps 5-20pts beyond it, then closes back through it.
  **Stop goes beyond the false-break extreme, not the original swing
  level** — placing it at the original level is the single most common
  mistake with this pattern and gets swept too.
- **Rejection Block vs. Order Block** — an OB marks a trend's *origin*
  (continuation play, buy the pullback). A rejection block forms *after*
  an extended move, with a long wick showing exhaustion (reversal play,
  short the breakdown). Don't treat a rejection block like a fresh OB —
  they imply opposite trade directions.
- **Equal Highs / Equal Lows** — two or more swing points at the same
  price are an engineered liquidity pool, and a stronger sweep target than
  a single untested swing. When a zone's stop-hunt target lines up with
  equal highs/lows, that's added conviction the sweep actually happens.
- **Propulsion Block** — a 1-3 candle compression (40-60% of the prior
  impulsive candle's range) after an impulse. Breakout **beyond the prior
  impulse's extreme** = continuation; breakout **through the opposing
  extreme** = reversal. Useful for reading which way a stall resolves
  before it resolves.
- **AMD cycle (Accumulation-Manipulation-Distribution)** — reinforces the
  existing "don't chase the impulse" rule with real vocabulary: the
  impulsive move chasing price *is* the manipulation phase. **Never enter
  during manipulation** — wait for the BOS that confirms distribution has
  started, then enter the retracement into that BOS.
- **Optimal Bias (three-day rule)** — on the daily timeframe: last 3 daily
  candles higher-high+higher-low = UP bias; lower-high+lower-low = DOWN;
  mixed = NEUTRAL. Use this as a sanity check on the bigger-picture reads
  already done on 45-min+ charts — a zone that fights the 3-day bias needs
  a materially higher score to justify taking it.
- **Silver Bullet windows (10-11 AM and 2-3 PM ET)** — inside the
  already-good New York session, these two hours specifically are where
  the strategy reference's data shows the highest institutional activity.
  Not a hard filter like the dead zone, but a real tiebreaker: prefer these
  windows when a setup is marginal.
- **SMT Divergence** — if price data for a correlated instrument (e.g. NQ
  alongside ES) is available, a failure of that instrument to confirm an
  ES move is a real reversal warning. Optional confluence — most chart
  screenshots are single-instrument, so don't block a call for lacking it.
- **Weekly Profiles / Dealing Ranges / IPDA 20-40-60 day ranges / Daily
  Profiles (D+/D-/DN)** — genuine higher-timeframe institutional-flow
  concepts, but they need multi-day OHLC data a single intraday screenshot
  usually doesn't show. Apply them when that data is actually visible
  (e.g. a daily chart is posted); don't fabricate a weekly/IPDA read off a
  5-min crop that doesn't show it.

## Reading a result screenshot ("sl hit", "tp hit", etc.)

When the user posts a chart with horizontal lines already drawn on it after a
trade closed, the line colors are a fixed convention — **always**:

- **Blue = entry**
- **Green = TP**
- **Red = SL**

Read the exact entry/exit price directly off those lines (the labeled price
next to each line, not an eyeballed position). This is enough to log the
trade without asking the user for the fill price — only ask if a line is
missing, unlabeled, or the outcome (which line price was actually hit) is
ambiguous.

## Output format — exactly this, nothing more

```
NOW  <price>  <one-clause structural read>[ dead zone]
Buffer: $<per-acct> — <N> max-loss trades from floor
Recommended: <n> contracts/account

ZONE A ▸ <SELL/BUY> <low> – <high> (<one-clause reason>)          confidence <NN>%  [← primary]
 Fill near TOP    (<high>) → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>
 Fill near BOTTOM (<low>)  → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>

ZONE B ▸ <SELL/BUY> <low> – <high> (<one-clause reason>)          confidence <NN>%  [<n>/account if different from above]
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
