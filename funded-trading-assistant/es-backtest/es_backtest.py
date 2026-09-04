"""
ES backtest with Tradeify Select 50K rules enforced.

Answers the question that matters: not "is this strategy profitable" but
"would this strategy pass and hold a funded account."

    python es_backtest.py                 # 60 days, yfinance
    python es_backtest.py --days 30
    python es_backtest.py --csv bars.csv  # your own data

⚠️ Every parameter under STRATEGY is a decision, not a discovered truth.
They were converted from discretionary rules and are unvalidated. Change one
and the results change -- that is the point of having them in one place.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd

from prop_account import (
    PropAccount, Status, must_flatten,
    POINT_VALUE, TICK, PROFIT_TARGET, STARTING_BALANCE,
)

# --- STRATEGY PARAMETERS --------------------------------------------------
# These encode the discretionary rules. Each is an assumption.

SWING_LOOKBACK = 40        # bars used to find the impulse leg
ATR_PERIOD = 14
MIN_IMPULSE_ATR = 3.0      # leg must be at least this many ATR to count

# Retrace zone depth. Regime-dependent -- the correction that came out of
# four straight no-fills using OTE in a trending market.
TREND_ZONE = (0.38, 0.50)
RANGE_ZONE = (0.62, 0.79)

# Regime: trending when the SMA has moved more than this many ATR over the
# lookback. Crude but deterministic, which is the requirement.
REGIME_SMA = 20
REGIME_SLOPE_ATR = 1.5

STOP_BEYOND_ZONE_ATR = 0.5   # stop sits this far past the zone's far edge
TARGET_ATR = 2.25            # 2.0-2.5 ATR, midpoint
CONTRACTS = 1

# Volume climax -- stand aside rather than trade into it.
CLIMAX_VOL_MULT = 3.0
CLIMAX_COOLDOWN_BARS = 6

ZONE_EXPIRY_BARS = 24        # a zone unfilled this long is abandoned


# --- Data -----------------------------------------------------------------

def load_bars(days: int = 60, interval: str = "5m", csv: str | None = None):
    """Return a DataFrame indexed by US/Eastern datetimes with o/h/l/c/v."""
    if csv:
        df = pd.read_csv(csv, parse_dates=[0], index_col=0)
        df.columns = [c.lower()[0] if c.lower() != "volume" else "v"
                      for c in df.columns]
    else:
        try:
            import yfinance as yf
        except ImportError:
            sys.exit("pip install yfinance")

        df = yf.download("ES=F", period=f"{days}d", interval=interval,
                         progress=False, auto_adjust=False)
        if df is None or df.empty:
            sys.exit("No data returned. yfinance caps 5m history near 60 days.")
        if getattr(df.columns, "nlevels", 1) > 1:
            df.columns = df.columns.droplevel(1)
        df = df.rename(columns={"Open": "o", "High": "h", "Low": "l",
                                "Close": "c", "Volume": "v"})[["o", "h", "l", "c", "v"]]

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("US/Eastern")
    return df.dropna()


def atr(df: pd.DataFrame, n: int = ATR_PERIOD) -> pd.Series:
    pc = df["c"].shift(1)
    tr = pd.concat([df["h"] - df["l"], (df["h"] - pc).abs(),
                    (df["l"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


# --- Strategy -------------------------------------------------------------

class Zone:
    """A pending entry: price must trade into [lo, hi] to fill."""
    __slots__ = ("direction", "lo", "hi", "stop", "target", "created_idx")

    def __init__(self, direction, lo, hi, stop, target, created_idx):
        self.direction = direction
        self.lo, self.hi = lo, hi
        self.stop, self.target = stop, target
        self.created_idx = created_idx

    def filled_by(self, bar) -> bool:
        return bar["l"] <= self.hi and bar["h"] >= self.lo


def is_trending(df: pd.DataFrame, i: int, a: float) -> bool:
    """SMA displacement over the lookback, measured in ATR."""
    if i < REGIME_SMA * 2 or a <= 0:
        return False
    sma = df["c"].iloc[i - REGIME_SMA:i].mean()
    sma_prior = df["c"].iloc[i - REGIME_SMA * 2:i - REGIME_SMA].mean()
    return abs(sma - sma_prior) / a > REGIME_SLOPE_ATR


def build_zone(df: pd.DataFrame, i: int, a: float, cap_points: float):
    """Find the last impulse leg and price a retracement entry against it."""
    lo_i = max(0, i - SWING_LOOKBACK)
    window = df.iloc[lo_i:i]
    if len(window) < SWING_LOOKBACK // 2:
        return None

    hi, lo = window["h"].max(), window["l"].min()
    leg = hi - lo
    if a <= 0 or leg < MIN_IMPULSE_ATR * a:
        return None

    hi_pos = window["h"].idxmax()
    lo_pos = window["l"].idxmin()
    # Leg direction: whichever extreme came last is the end of the impulse.
    down = hi_pos < lo_pos

    z = TREND_ZONE if is_trending(df, i, a) else RANGE_ZONE

    if down:
        # Impulse down -> sell the bounce.
        zlo, zhi = lo + leg * z[0], lo + leg * z[1]
        stop = zhi + STOP_BEYOND_ZONE_ATR * a
        entry_ref = (zlo + zhi) / 2
        target = entry_ref - min(TARGET_ATR * a, cap_points)
        direction = "SHORT"
    else:
        zhi, zlo = hi - leg * z[0], hi - leg * z[1]
        stop = zlo - STOP_BEYOND_ZONE_ATR * a
        entry_ref = (zlo + zhi) / 2
        target = entry_ref + min(TARGET_ATR * a, cap_points)
        direction = "LONG"

    if abs(entry_ref - target) < 4 * TICK:      # target too close to bother
        return None
    return Zone(direction, round(zlo, 2), round(zhi, 2),
                round(stop, 2), round(target, 2), i)


# --- Backtest -------------------------------------------------------------

def run(df: pd.DataFrame, verbose: bool = False) -> PropAccount:
    acct = PropAccount()
    a_series = atr(df)
    vol_avg = df["v"].rolling(20).mean()

    zone: Zone | None = None
    pos = None                 # (direction, entry_px, stop, target, entry_dt)
    climax_until = -1
    current_day = None

    for i in range(REGIME_SMA * 2 + ATR_PERIOD, len(df)):
        bar = df.iloc[i]
        dt = df.index[i]
        a = a_series.iloc[i]
        if np.isnan(a) or a <= 0:
            continue

        # Day rollover -> trail the floor on yesterday's close.
        if current_day is not None and dt.date() != current_day:
            acct.end_of_day(current_day)
            if acct.check_pass() or acct.status != Status.ACTIVE:
                if acct.status == Status.PASSED:
                    break
        current_day = dt.date()

        # --- manage an open position ---
        if pos:
            direction, entry_px, stop, target, entry_dt = pos
            exit_px = exit_reason = None

            if direction == "LONG":
                # Stop checked first -- conservative when a bar spans both.
                if bar["l"] <= stop:
                    exit_px, exit_reason = stop, "stop"
                elif bar["h"] >= target:
                    exit_px, exit_reason = target, "target"
            else:
                if bar["h"] >= stop:
                    exit_px, exit_reason = stop, "stop"
                elif bar["l"] <= target:
                    exit_px, exit_reason = target, "target"

            if exit_px is None and must_flatten(dt):
                exit_px, exit_reason = bar["c"], "flatten"

            if exit_px is not None:
                alive = acct.record_trade(entry_dt, dt, direction, entry_px,
                                          exit_px, CONTRACTS, exit_reason)
                if verbose:
                    print(f"  {dt:%m-%d %H:%M} {direction:5s} {entry_px:8.2f}"
                          f" -> {exit_px:8.2f} {exit_reason:8s}"
                          f" bal ${acct.balance:,.0f}")
                pos = None
                if not alive:
                    break
            continue

        # --- volume climax: stand aside ---
        if not np.isnan(vol_avg.iloc[i]) and bar["v"] > CLIMAX_VOL_MULT * vol_avg.iloc[i]:
            climax_until = i + CLIMAX_COOLDOWN_BARS
            zone = None
            continue
        if i < climax_until:
            continue

        # --- fill a pending zone ---
        if zone:
            if i - zone.created_idx > ZONE_EXPIRY_BARS:
                zone = None
            elif zone.filled_by(bar):
                entry_px = min(max(bar["o"], zone.lo), zone.hi)
                stop_pts = abs(entry_px - zone.stop)
                ok, why = acct.can_enter(dt, stop_pts, CONTRACTS)
                if ok:
                    pos = (zone.direction, entry_px, zone.stop, zone.target, dt)
                zone = None
                continue

        # --- look for a new setup ---
        cap = acct.target_cap_points(dt.date(), CONTRACTS)
        if cap <= 0:
            continue                      # daily consistency cap reached
        ok, _ = acct.can_enter(dt, 2 * a, CONTRACTS)
        if ok:
            zone = build_zone(df, i, a, cap)

    if current_day:
        acct.end_of_day(current_day)
        acct.check_pass()
    return acct


# --- Reporting ------------------------------------------------------------

def report(acct: PropAccount, df: pd.DataFrame):
    t = acct.trades
    wins = [x for x in t if x["pnl"] > 0]
    losses = [x for x in t if x["pnl"] < 0]
    gross_w = sum(x["pnl"] for x in wins)
    gross_l = abs(sum(x["pnl"] for x in losses))
    pf = gross_w / gross_l if gross_l else float("inf")

    print(f"\n{'='*62}\nTRADEIFY SELECT 50K — BACKTEST\n{'='*62}")
    print(f"Period      {df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d}"
          f"  ({len(df):,} bars)")

    print(f"\n--- ACCOUNT {'-'*49}")
    icon = {"PASSED": "PASS", "ACTIVE": "INCOMPLETE"}.get(acct.status.name, "FAIL")
    print(f"  RESULT            {icon}  ({acct.status.value})")
    print(f"  Balance           ${acct.balance:,.2f}")
    print(f"  Profit            ${acct.total_profit:,.2f} / ${PROFIT_TARGET:,.0f}")
    print(f"  Trading days      {acct.trading_days} (min 3)")
    print(f"  Floor             ${acct.floor:,.2f}"
          f"{'  LOCKED' if acct.floor_locked else ''}")
    print(f"  Closest to floor  ${acct.closest_to_floor:,.2f}"
          f"   <-- under $500 means it nearly died")

    print(f"\n--- CONSISTENCY {'-'*45}")
    print(f"  Best day          ${acct.best_day:,.2f}")
    print(f"  Legal max/day     ${acct.max_legal_day():,.2f}")
    # The rule is only evaluated once the target is reached. Before that a
    # single day is trivially a large share of a small running total, which
    # is not a breach -- it is just an early sample.
    if acct.total_profit >= PROFIT_TARGET:
        print(f"  Best day share    {acct.best_day_pct:.0%} of profit")
        if acct.best_day_pct > 0.40:
            need = acct.required_total_for_consistency()
            print(f"  ⚠️  BREACH — needs ${need:,.0f} total to become legal")
    elif acct.best_day > acct.max_legal_day():
        need = acct.required_total_for_consistency()
        print(f"  ⚠️  A day exceeded the ${acct.max_legal_day():,.0f} cap —"
              f" target rises to ${need:,.0f}")
    else:
        print(f"  Status            on track (no day over the cap)")
    if acct.consistency_blocks:
        print(f"  Pass blocked      {acct.consistency_blocks}x by consistency")

    print(f"\n--- STRATEGY {'-'*48}")
    print(f"  Trades            {len(t)}")
    if t:
        print(f"  Win rate          {len(wins)/len(t):.1%}")
        print(f"  Profit factor     {pf:.2f}")
        print(f"  Avg win / loss    ${gross_w/len(wins) if wins else 0:,.0f}"
              f" / ${gross_l/len(losses) if losses else 0:,.0f}")
        by_reason = {}
        for x in t:
            by_reason[x["reason"]] = by_reason.get(x["reason"], 0) + 1
        print(f"  Exits             " +
              "  ".join(f"{k}:{v}" for k, v in sorted(by_reason.items())))

    if acct.daily_pnl:
        print(f"\n--- DAILY P&L {'-'*47}")
        for d in sorted(acct.daily_pnl):
            v = acct.daily_pnl[d]
            pct = v / acct.total_profit if acct.total_profit > 0 and v > 0 else 0
            flag = "  <-- over 40%" if pct > 0.40 else ""
            print(f"  {d}  ${v:>9,.2f}  {pct:>5.0%}{flag}")

    print(f"\n{'='*62}")
    print("Candle-based fills. No spread or slippage. Live results will be")
    print("worse. Rules are third-party sourced -- verify before trusting a PASS.")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--interval", default="5m")
    p.add_argument("--csv")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    bars = load_bars(args.days, args.interval, args.csv)
    print(f"Loaded {len(bars):,} bars  "
          f"{bars.index[0]:%Y-%m-%d %H:%M} -> {bars.index[-1]:%Y-%m-%d %H:%M} ET")
    report(run(bars, args.verbose), bars)
