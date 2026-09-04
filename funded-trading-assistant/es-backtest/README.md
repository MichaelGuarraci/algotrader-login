# ES Backtest — Tradeify Select 50K

Backtests the ES strategy **against real historical ES data**, with the funded
account's rules enforced. Answers the question that matters: not "is this
profitable" but **"would this pass and hold a Tradeify account."**

ES only. `ES=F` is hardcoded and the mechanics are ES's — $50/point, 0.25 tick.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas numpy yfinance tzdata

python es_backtest.py               # 60 days of real ES 5-min bars
python es_backtest.py --days 30
python es_backtest.py -v            # print every trade
python es_backtest.py --csv my_es_bars.csv
```

Data is real market history from Yahoo (`ES=F`). Yahoo caps 5-min data near
**60 days** — enough for a first read, not enough to conclude anything. For
months or years of history use Databento (CME direct) and feed it via `--csv`.

CSV format: `datetime,open,high,low,close,volume`.

## What it enforces

| Rule | Behaviour |
|------|-----------|
| $2,000 EOD trailing drawdown | Floor trails on the **closing** balance, not intraday |
| Floor lock | Freezes at $50,100 once balance closes ≥ $52,100 |
| 40% consistency | Blocks the pass; does **not** fail the account |
| 3 minimum trading days | Target alone is not a pass |
| $3,000 target | Pass requires target **and** days **and** consistency |
| 4:45 PM ET flatten | Open positions closed at market |
| No new entry after 3:45 PM ET | Needs room to resolve before the flatten |
| Maintenance break 5–6 PM ET | No entries |
| No weekend holds | Friday afternoon entries rejected |
| Daily consistency cap | Targets truncated so no day exceeds $1,200 |
| Stop-out survivability | Entry rejected if a full stop breaches the floor |

## The numbers that decide it

**Closest to floor.** How near the account came to dying. Under $500 means it
nearly failed regardless of the final balance.

**Daily P&L distribution.** If the strategy naturally throws days over 40% of a
$3,000 run, the consistency rule fights it structurally — worth knowing before
paying $165.

**Exits breakdown.** A high `flatten:` count means trades aren't resolving
inside the session and the targets are too far.

## ⚠️ Read before trusting a PASS

**Candle-based fills.** No spread, no slippage, no partial fills. The one real
market order in the log gapped **−$1,200** instantly. Live results will be
worse than anything printed here.

**Stops resolve before targets.** When one bar spans both, the loss is taken.
Intrabar sequence is unknowable from OHLC, and the conservative assumption is
the honest one.

**Rules are third-party sourced.** tradeify.co and help.tradeify.co are both
unreachable from Claude's sandbox. Verify every rule in `prop_account.py`
against their help center before acting on a PASS.

**Parameters are decisions, not discoveries.** Everything under `STRATEGY
PARAMETERS` in `es_backtest.py` converts a discretionary rule into a fixed
number. They are unvalidated. Change one and results change — which is exactly
why they sit in one block at the top.

Where the discretion got frozen:

| Judgment call | Became |
|---|---|
| "trending vs ranging" | SMA displacement > 1.5 ATR over 20 bars |
| "the impulse leg" | swing high/low over 40 bars, ≥ 3 ATR |
| "structural stop" | 0.5 ATR beyond the zone's far edge |
| "climax volume" | > 3× the 20-bar average, then 6 bars standing aside |

Those four are the least defensible part of this. Vary them and see how much
the result moves — if it swings wildly, the edge is in the parameters, not the
market.

## Files

- `prop_account.py` — the account simulator. Strategy-agnostic; reusable for
  any ES system you want to test against Tradeify rules.
- `es_backtest.py` — data loading, the mechanized strategy, the runner.
