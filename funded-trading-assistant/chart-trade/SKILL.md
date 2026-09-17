---
name: chart-trade
description: Read an ES (E-mini S&P 500) chart screenshot and return a NOW / ZONE A / ZONE B trade call with per-fill risk, reward, and R-multiple. Use whenever the user posts a chart image and asks for a call, "anything now", "what should I do", or reports a fill/exit that needs a fresh read afterward. Sized for the current active account (see Account context below).
---

# Chart Trade Call

## Account context — read this before every call

**Active simulation (replaced the prior 50K funded sim on 2026-09-17):**
5x **Tradeify Select 150K** accounts, stacked, starting from **EVALUATION**
(not funded). The prior 50K Select Flex funded sim ended at Trade 37,
record 22-15, net +$25,825, balance $75,825 — preserved in its history in
the Account Tracker, not carried forward as this account's starting state.

- **Per-account eval rules:** profit target $9,000, EOD trailing drawdown
  $4,500, floor locks permanently at $150,100 (start + $100) once earned,
  **no daily loss limit during eval**, 40% consistency rule (biggest single
  day ≤ 40% of total profit) — this only delays qualifying to pass, it does
  not fail the account or restrict trading.
- **Contracts during eval: 12 mini / 120 micro per account, full size from
  day one** (same pattern as the prior 50K eval). $50/point/contract →
  **$600/point per account**.
- **Mirroring across the 5 accounts:** same direction, same instrument,
  same trade on all 5 simultaneously is explicitly allowed scaling, not a
  violation — every call in this skill is priced per-account (12 contracts,
  $600/point); the Account Tracker separately multiplies by 5 for the true
  combined P&L across all accounts. Never combine size across accounts
  into one account's position, and never hold opposing positions on the
  same instrument across the 5.
- **Funded-phase rules (once an account passes)**: starts at a reduced
  contract count (3 mini confirmed; intermediate steps up to 12 not yet
  confirmed — still open), scales back to 12 mini / 120 micro once that
  account's EOD balance reaches $154,500 (+$4,500 profit), at which point
  its floor also locks. No consistency rule once funded. Daily-loss-limit
  status once funded not yet reconfirmed for Select 150K specifically —
  treat as unresolved until sourced.
- Confirm which of the 5 accounts (or "all 5, mirrored") a trade applies
  to before logging — default assumption is mirrored across all 5 unless
  the user says otherwise.

## Risk-sizing rule — SL/TP must respect eval limits

Added 2026-09-17 at user's request. Before setting SL/TP on any call:

- **SL sizing must survive at least 3 consecutive max-loss trades before
  touching the floor.** Max per-trade risk = current buffer ÷ 3, recomputed
  from the current buffer (not always $4,500 — it shrinks after a loss and
  only resets upward after a new equity peak). At a full $4,500 buffer
  that's ≤$1,500/account (≤2.5 pts at 12 contracts); after any loss,
  recompute from the smaller buffer and shrink size accordingly.
- **State the drawdown distance every time**, not just when asked: current
  buffer to floor, and how many max-size losses in a row it would take to
  hit it (target: always ≥3). This goes in every trade-result report and
  before every new call that risks capital.
- **TP sizing must respect the day's remaining room under the 40%
  consistency cap** whenever that day already has profit booked. Compute
  remaining room = (40% × $9,000) − today's profit-so-far *before*
  sizing a new target — don't print a structural TP without checking
  this first, and say explicitly when a TP is capped short of structure
  for this reason.
- Recompute both of these fresh from the current balance/target progress
  before every call — they change after every closed trade, not just once
  per session.

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
4. Confirm current contract count before computing dollars. Default is 12
   contracts per account ($600/point per account), full eval size. If an
   account passes to funded and its count is temporarily reduced, use that
   account's actual current count and update the multiplier — don't assume
   all 5 accounts are always in sync once any of them pass.

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
