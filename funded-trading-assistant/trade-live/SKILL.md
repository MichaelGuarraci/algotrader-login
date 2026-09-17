---
name: trade-live
description: Read an ES (E-mini S&P 500) chart screenshot and return a NOW / ZONE A / ZONE B trade call for a REAL funded Tradeify account — real money, not the practice simulation. Use once an evaluation has actually passed and the account is genuinely funded. Same call format and risk discipline as the chart-trade simulation skill, plus the real-money considerations that don't exist in a sim: commissions, slippage, platform/execution risk, taxes, and psychology.
---

# Live Trade Call (Real Money)

This is the real-money counterpart to the `chart-trade` simulation skill.
Same call format, same risk discipline — the difference is everything
below that only matters once actual dollars are on the line.

## Account context — same account, same rules as the simulation

This is real Tradeify — **5x Select 150K, stacked**, the same account
structure the `chart-trade` simulation has been modeling. The rules
carry over directly, not as a generic placeholder:

- **Per-account eval rules:** profit target $9,000, EOD trailing drawdown
  $4,500, floor locks permanently at $150,100 (start + $100) once earned,
  no daily loss limit during eval, 40% consistency rule (biggest single
  day ≤ 40% of total profit) — delays passing, doesn't fail the account.
- **Eligible for up to 12 mini / 120 micro per account during eval, full
  size from day one.** $50/point/contract → $600/point per account at
  full size. Actual count per trade follows the risk-sizing rule below,
  not automatically 12.
- **Mirroring across the 5 accounts** via Tradovate Group Trade (Manage
  Groups → all 5 accounts, Order Quantity 1 each → group base unit 5 →
  order quantity 60 = 12/account). Never combine size across accounts
  into one account's position; never hold opposing positions on the same
  instrument across the 5.
- **Funded-phase (once an account passes):** starts at a reduced contract
  count (3 mini confirmed; intermediate steps to 12 still unconfirmed),
  scales back to 12 mini once that account's EOD balance reaches
  $154,500 (+$4,500 profit), floor locks at $150,100. No consistency rule
  once funded. Daily-loss-limit status once funded not yet reconfirmed
  for Select 150K specifically — treat as open until sourced.
- **Still confirm against the live Tradeify dashboard before trusting a
  number that matters** (current buffer, exact funded contract count,
  whether a daily loss limit applies) — these were researched for
  planning, and the account's actual state is the source of truth once
  real fills start happening.

## Risk-sizing rule — same discipline as the simulation, now with real stakes

- **Position must survive at least 3 consecutive max-loss trades before
  touching the floor.** Max per-trade risk = current real buffer ÷ 3.
  Pull the current buffer from the actual account dashboard, not a
  remembered number — it changes with every closed trade and every new
  equity peak.
- **Flex contract count to hit that budget, not the stop distance.** SL
  stays at its real structural level. `contracts = floor(max risk ÷
  (structural SL distance in pts × $50))`, capped at that account's
  current contract limit. Size down for wide structural stops instead of
  shrinking the stop.
- **State the drawdown distance every time**: current buffer to floor,
  and how many max-size losses in a row it would take to hit it (target:
  always ≥3).
- **TP sizing must respect any consistency-rule room** if the account is
  still subject to one (funded Select accounts typically aren't, per the
  simulation's research — confirm this specific account before assuming).

## Real-money considerations that don't exist in the simulation

These have no simulation equivalent — they only matter with real capital
and real execution:

- **Commissions and fees.** Every fill costs real commission + exchange
  fees per contract, round-turn. This eats directly into R multiples that
  looked clean on paper — a scratch trade in the sim can be a small real
  loss after fees. Confirm the actual per-contract round-turn cost on
  Tradovate and factor it into whether a tight-target trade is still worth
  taking.
- **Slippage.** A market order — especially at 12+ contracts, especially
  in the dead zone or on a fast move — can fill meaningfully worse than
  the quoted price. Wide/fast markets (news, the kind of ~30pt plunges
  seen in the simulation) are exactly when slippage is worst. Consider
  limit orders or accepting a wider effective stop on fast markets.
- **Platform and execution risk.** Internet outage, Tradovate/Rithmic
  downtime, or a stuck order can leave a real position unmanaged with real
  money at risk — a simulation call never actually fails to execute. Have
  a plan before it happens: know your broker's phone/emergency order line,
  and don't take a trade you can't afford to have go unmanaged if your
  connection drops.
- **Group Trade execution risk specifically.** One order routes to 5 real
  accounts. If it partially fills on some accounts and not others (liquidity,
  a momentary reject), you can end up net long on one account and flat or
  short-exposed to a stale attempt on another — check fill confirmations
  across all 5 accounts after every order, don't assume the mirror worked.
- **Taxes.** US futures contracts (ES) are Section 1256 contracts — 60%
  long-term / 40% short-term capital gains treatment regardless of actual
  holding period, marked-to-market at year end. This is materially
  different from equity day-trading tax treatment. Track every closed
  trade for tax reporting (Form 6781) — this is a real filing obligation,
  not optional bookkeeping. Consult a real tax professional; this skill
  is not tax advice.
- **Payout mechanics have real friction.** A payout request isn't instant
  cash — it goes through Tradeify's approval/processing window, and profit
  splits mean the number you see in the account isn't the number you
  actually receive. Don't spend against unrealized or unpaid-out profit.
- **Losing a funded account has a real cost, not just a number resetting.**
  Failing a funded account can mean forfeiting the evaluation fee already
  paid and, depending on Tradeify's specific reset/re-purchase terms,
  real money to requalify. This is the sharpest difference from the sim:
  in the sim, blowing an account just meant starting a new tracker file.
- **Psychology changes with real money on the line, even with identical
  numbers on the screen.** The discipline habits built in the simulation
  (recover-don't-revenge-trade, respecting the 3-loss-survival sizing,
  not chasing after a missed setup) are the same habits that matter most
  here — but they're harder to hold to when the P&L is real. If a real
  trade result triggers an urge to immediately override the next call's
  sizing or skip the risk-sizing rule "just this once," that's the moment
  the rule exists for.

## Reporting rule

Report the combined/total figure first (this is real funded money, not an
eval chasing a per-account target) — but always also state per-account
figures, since drawdown and contract limits are still tracked per
account. Every trade-result report must show: current buffer to floor per
account, how many max-loss trades remain before the floor, and — if a
consistency rule still applies to this specific account — the same
consistency math as the simulation.

## Before every call

1. Run `TZ=America/New_York date` to get the exact ET time. Never estimate it.
2. Read price from the **colored, timestamped price box** on the right axis
   only (teal/red fill, has a clock time next to it). Never use the
   crosshair-following `⊕` box or the OHLC header.
3. If ET time falls in 11:00–13:10, this is the **dead zone** — flag it,
   and weigh the slippage risk above more heavily here than in the sim.
4. Compute contract count per the risk-sizing rule above, using the real
   account's actual current buffer and contract limit — not a remembered
   simulation number.

## Reading a result screenshot ("sl hit", "tp hit", etc.)

Same fixed convention as the simulation:

- **Blue = entry**
- **Green = TP**
- **Red = SL**

Read the exact entry/exit price directly off those lines. Only ask if a
line is missing, unlabeled, or the outcome is ambiguous.

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

Same fill-in rules as the simulation: zones are ranges (compute both
fill scenarios), risk/reward in real dollars at the sized contract count,
TP structural not R-scaled, SL beyond structure, confidence calibrated
not felt, `← primary` only when there's a real lean.

If the setup doesn't warrant a trade at all, print only:

```
NOW  <price>  <one-clause structural read>[ dead zone]

NO TRADE — <one-clause reason>
```

## Never

- Never add commentary, analysis, or a recommendation outside the block
  above — real-money considerations go in their own flagged section when
  genuinely relevant (e.g. dead-zone slippage warning), not as a running
  paragraph.
- Never use the crosshair `⊕` box for price.
- Never skip the ET time check.
- Never assume a simulation number (buffer, contract limit, consistency
  rule) applies to the real account without checking the actual dashboard.
- Never log a trade from this call alone — logging happens when the user
  reports the actual fill/exit, confirmed across all funded accounts it
  was mirrored to.
- Never treat this skill's output as tax, legal, or financial advice —
  the taxes/payout/account-loss notes above are informational, not a
  substitute for a real professional.
