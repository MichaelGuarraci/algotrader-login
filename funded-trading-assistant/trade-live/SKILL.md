---
name: trade-live
description: Read an ES (E-mini S&P 500) chart screenshot and return a NOW / ZONE A / ZONE B trade call for a REAL funded Tradeify account — real money, not the practice simulation. Use once an evaluation has actually passed and the account is genuinely funded. Same call format and risk discipline as the chart-trade simulation skill, plus the real-money considerations that don't exist in a sim: commissions, slippage, platform/execution risk, taxes, and psychology.
---

# Live Trade Call (Real Money)

This is the real-money counterpart to the `chart-trade` simulation skill.
Same call format, same risk discipline — the difference is everything
below that only matters once actual dollars are on the line.

## Account context — Tradeify Select, confirmed plan: single 150K

**Confirmed 2026-09-18: real trading starts on a single Tradeify Select
150K account** — not the 5x150K stack the `chart-trade` simulation runs
(that sim continues in parallel as practice/calibration, it's not what's
actually being traded for real). Use the $150K row below by default;
the table stays here for reference in case the size purchased changes or
more accounts get added later, but don't ask which size before every call
now that it's confirmed — only re-confirm if the user says the plan
changed. All of these are Select-family evaluation accounts — confirmed
no daily loss limit and a 40% consistency rule (delays passing, doesn't
fail the account) during eval, across all sizes.

| Size | Eval profit target | Eval/funded trailing drawdown | Eval contracts (full, day one) | Funded starting contracts | Funded full-scale trigger | Floor lock point |
|---|---|---|---|---|---|---|
| $25K | $1,500 | not confirmed — check dashboard | 2 mini / 20 micro | not confirmed | not confirmed | $25,100 |
| $50K | $3,000 | **$2,000** (confirmed) | 4 mini / 40 micro | 2 mini / 20 micro (confirmed) | $2,000 profit → 4 mini (confirmed) | $50,100 |
| $100K | $6,000 | **$3,000** (inferred from the funded scaling trigger — same pattern as 50K/150K below, not independently confirmed) | 8 mini / 80 micro | not confirmed | $3,000 profit → 8 mini (confirmed) | $100,100 |
| $150K | $9,000 | **$4,500** (confirmed) | 12 mini / 120 micro | 3 mini / 30 micro (confirmed) | $4,500 profit → 12 mini (confirmed) | $150,100 |

Pattern worth knowing: on every size confirmed so far, the funded
full-scale trigger profit **equals** the trailing drawdown amount exactly
— that's how the $100K drawdown above is inferred, not guessed randomly.

**Passing eval does NOT carry the balance/buffer into funded — confirmed
via research.** The funded account resets to the base starting balance
(e.g., $150,000) regardless of what the eval account ended at; the
buffer/drawdown starts trailing fresh from that reset balance, then locks
at the floor-lock point above once earned. Don't assume a healthy eval
buffer means a healthy funded buffer — it starts over.

**300K is a separate "V2" structure, not this table** — it carries its
own multi-step funded scaling (3 mini at $0-1,500 profit up to 16 mini at
$7,000+) and at least one source describes a daily loss limit on 300K V2
eval ($4,000 soft / $8,000 max) that contradicts the "no daily loss limit
during eval" rule above. If 300K is ever the actual purchase, treat it as
needing fresh research, not this table.

**If stacking multiple accounts** (any mix, up to 5 / $750K combined):
same-direction mirroring across your own accounts is allowed scaling, not
a violation; never combine size across accounts into one account's
position, never hold opposing positions across the 5. Execution via
Tradovate Group Trade: Manage Groups → drag in the accounts → Order
Quantity 1 each → group base unit = account count → order quantity =
that count × contracts-per-account, split automatically.

**Always confirm against the live Tradeify dashboard before trusting a
number that matters** — current buffer, exact funded contract count,
whether a daily loss limit applies to this specific size/payout-policy.
This table was researched for planning; the account's actual state is
the source of truth once real fills start happening.

## Tradeify platform rules — session, copying, and automation

- **Trading day:** 6:00 PM ET → 5:00 PM ET the next day. **Flatten all
  positions by 4:45 PM ET** — an entry after 3:45 PM ET may not resolve
  before that deadline, flag it. Dead zone 11:00–13:10 ET (see "Before
  every call" below). News trading is assumed unrestricted unless the
  dashboard says otherwise for this specific account.
- **Multi-account structure:** up to 5 simultaneous Tradeify accounts /
  $750K combined buying power, any mix of Select/Growth/Lightning.
  Same-direction mirroring across accounts **you personally own** is
  allowed scaling, not a violation. Never combine size across accounts
  into one account's position; never hold opposing positions on the same
  instrument across your own accounts.
- **Copy trading / automation policy (confirmed, but verify before
  relying on it — rules can change and differ by account type):**
  Tradeify allows copy trading across up to 5 accounts you personally
  own and manage — copying someone else's strategy, or third-party group
  copying, is not permitted. Trader-owned bots/algorithms are allowed if
  you can prove sole ownership of the strategy; it can't be shared with
  other traders or firms, and HFT bots are prohibited. Third-party tools
  (trade copiers, automation services) are usable **at your own risk** —
  Tradeify isn't responsible for errors or glitches caused by external
  software.
- **ES contract rollover:** E-mini S&P futures expire quarterly (Mar/Jun/
  Sep/Dec). Volume rolls to the next front-month contract about a week
  before expiration — confirm you're trading the current front-month
  symbol (not the about-to-expire one) before entering, don't assume the
  chart's continuous symbol (e.g. `ES1!`) tells you which specific
  contract an order actually routes to.
- **Always verify against the live Tradeify dashboard** for anything
  that materially matters — current buffer, daily loss limit status,
  payout policy, exact automation/copying rules for this account type.
  This section is a planning reference, not a substitute for checking
  the account itself.

## Risk-sizing rule — same discipline as the simulation, now with real stakes

- **Position must survive at least 3 consecutive max-loss trades before
  touching the floor.** Max per-trade risk = current real buffer ÷ 3.
  Pull the current buffer from the actual account dashboard, not a
  remembered number — it changes with every closed trade and every new
  equity peak.
- **Contract count: `floor(max risk ÷ (structural SL distance in pts ×
  $50))`, capped at that account's current limit** — the check, always
  run it, never squeeze the stop instead of sizing down. SL stays at its
  real structural level.
- **Once FUNDED with a buffer that's built real cushion, default to max
  contracts and use judgment rather than rigidly recomputing every time.**
  "Real cushion" means the buffer comfortably covers a max-size loss at
  this setup's typical stop width with room to spare — not just "the
  account is funded." Still sanity-check an unusually wide stop against
  the buffer before defaulting to max. Early post-funding, or whenever
  the buffer is thin, run the formula properly instead of defaulting.
- **Put the recommended contract count at the top of every call**, right
  after the NOW line — one number, sized off the primary zone's
  structural stop (or the account's max, once funded and that clears).
- **State the drawdown distance every time**: current buffer to floor,
  and how many max-size losses in a row it would take to hit it (target:
  always ≥3).
- **All dollar figures are per-account** — no combined/stack-wide totals
  unless explicitly asked for in the moment.
- **TP sizing must respect any consistency-rule room** if the account is
  still subject to one (funded Select accounts typically aren't, per the
  simulation's research — confirm this specific account before assuming).

## Momentum-adaptive zone weighting

Added 2026-09-21 at user's request. In a persistently one-directional
tape (large-bodied candles in one direction, minimal retracement,
repeatedly punching through levels without giving back), offer a
**strength-continuation zone near current price as the primary idea**,
not just the conservative structural pullback zone — a real trend can
skip every pullback level offered and keep running, and treating the
pullback as the only actionable entry misses that.

Revert to weighting the structural pullback/fade zone higher once real
two-way volume or momentum-cooling signs appear: a failed push to a new
high, candle bodies visibly shrinking after a strong run, or an actual
opposing-color reversal candle. State explicitly which regime the call
is reading (strong one-directional momentum vs. cooling/two-sided) so
the confidence split between Zone A and Zone B reflects it — don't
default to the conservative read out of habit when the tape is clearly
saying otherwise.

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

**Say this automatically, every time — never wait to be asked.** Added
2026-09-21 at user's explicit request once real trading started: this is
real money, and the user needs to stay current on account state without
having to remember to ask for it. After every closed real trade, and
before every new real call, state without being prompted:
- Updated account balance and net P&L.
- Current buffer to floor, and how many max-loss trades remain at the
  current risk budget.
- Progress toward the profit target (dollar amount and %).
- Consistency-rule status: today's net so far, and whether it's
  approaching or past the 40%-of-eventual-total planning threshold.
- Anything that just changed materially (a new peak triggering the floor
  lock, a milestone, a rule that just started/stopped applying).
This isn't optional detail to surface only on request — it's a standing
part of every real-trade interaction from here forward.

## Alerts — flag these automatically, don't wait to be asked

Re-added 2026-09-21 at user's request. Check every one of these on every
real-trade interaction (a new call, a trade-result report, or a plain
status check) and speak up the moment one is true — don't bury it, don't
wait to be asked, and don't repeat one that hasn't changed since the last
time it was flagged.

| Trigger | Action |
|---------|--------|
| Buffer < $500 | 🔴 "Drawdown critical — this account is close to the floor" |
| Entry after 3:45 PM ET | ⚠️ "May not resolve before the 4:45 PM flatten" |
| Friday entry | ⚠️ "Weekend flatten applies" |
| Contracts entered > current eligible ceiling | 🔴 "Above this account's hard limit for its current phase" |
| SL wider than the planned call | 🟡 "Actual stop doesn't match the plan — confirm before treating this as protected" |
| Today's profit approaching or past the 40%-of-eventual-total planning threshold | 🟡 Consistency-rule watch — state the exact dollar room left, not just a general warning |
| Two failed setups in the same short window (under ~40 min) | 🟡 "Pause and reassess — this window is reading as low-conviction chop, not a real trend or range" (pattern from the 50K sim's Trades 20-22, carried forward as a real caution) |
| A new equity peak that triggers the floor lock | 🎉 State plainly that the floor is now permanently locked and at what price — this is a one-time milestone, flag it once when it happens |
| Balance/contract state hasn't been confirmed against the actual Tradeify dashboard recently | 🟡 Note that buffer/balance figures are only as accurate as the last number you reported — flag if it's been a while since a real cross-check |

These are checks run against the account state already being tracked —
not new information to look up, just discipline about actually saying it
out loud instead of only computing it silently.

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
Buffer: $<per-acct> — <N> max-loss trades from floor
Recommended: <n> contracts/account

ZONE A ▸ <SELL/BUY> <low> – <high> (<one-clause reason>)          confidence <NN>%  [← primary]
 Fill near TOP    (<high>) → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>
 Fill near BOTTOM (<low>)  → TP <tp>  SL <sl>   R <r>   risk $<risk>   · reward $<reward>

ZONE B ▸ <SELL/BUY> <low> – <high> (<one-clause reason>)          confidence <NN>%  [<n>/account if different from above]
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
