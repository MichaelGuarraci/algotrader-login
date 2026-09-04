"""
Tradeify Select 50K account simulator.

Enforces the funded-account rules, not just P&L. A strategy can be profitable
and still fail an evaluation -- this module is what catches that.

Rules enforced:
  * $2,000 EOD trailing drawdown, locks at $50,100
  * 40% consistency (no single day above 40% of total profit)
  * 3 minimum trading days
  * $3,000 profit target
  * 4:45 PM ET hard flatten
  * No holding through the 5-6 PM ET maintenance break
  * No weekend holds

⚠️ Rules sourced from third-party write-ups; tradeify.co was unreachable.
Verify against their help center before trusting a PASS result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum

# --- Account constants ----------------------------------------------------

STARTING_BALANCE = 50_000.00
PROFIT_TARGET = 3_000.00
MAX_DRAWDOWN = 2_000.00
DRAWDOWN_LOCK_AT = 50_100.00      # floor stops trailing once balance reaches this
MIN_TRADING_DAYS = 3
CONSISTENCY_PCT = 0.40            # no single day above 40% of total profit

# ES contract mechanics
POINT_VALUE = 50.00
TICK = 0.25
TICK_VALUE = 12.50

# Session boundaries, US/Eastern
FLATTEN_TIME = time(16, 45)       # 4:45 PM ET hard close
BREAK_START = time(17, 0)         # 5:00 PM ET maintenance
SESSION_OPEN = time(18, 0)        # 6:00 PM ET next session


class Status(Enum):
    ACTIVE = "ACTIVE"
    PASSED = "PASSED"
    FAILED_DRAWDOWN = "FAILED — drawdown breached"
    BLOCKED_CONSISTENCY = "TARGET HIT but blocked by consistency"


@dataclass
class PropAccount:
    """Tracks balance, the trailing floor, per-day P&L and pass/fail state.

    Reusable for any strategy -- it only needs closed trades fed to it.
    """
    balance: float = STARTING_BALANCE
    floor: float = STARTING_BALANCE - MAX_DRAWDOWN
    floor_locked: bool = False
    status: Status = Status.ACTIVE

    daily_pnl: dict[date, float] = field(default_factory=dict)
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)

    # Diagnostics
    peak_balance: float = STARTING_BALANCE
    closest_to_floor: float = MAX_DRAWDOWN   # smallest buffer ever seen
    consistency_blocks: int = 0

    # --- Reporting helpers ------------------------------------------------

    @property
    def total_profit(self) -> float:
        return self.balance - STARTING_BALANCE

    @property
    def buffer(self) -> float:
        return self.balance - self.floor

    @property
    def trading_days(self) -> int:
        """Days with non-zero P&L. Adjust if Tradeify requires a minimum
        per-day profit for a day to count -- unconfirmed."""
        return sum(1 for v in self.daily_pnl.values() if v != 0)

    @property
    def best_day(self) -> float:
        wins = [v for v in self.daily_pnl.values() if v > 0]
        return max(wins) if wins else 0.0

    @property
    def best_day_pct(self) -> float:
        """Best day as a share of total profit. Must stay under 40%."""
        if self.total_profit <= 0:
            return 0.0
        return self.best_day / self.total_profit

    def max_legal_day(self) -> float:
        """Largest a single day can be, given the current target."""
        return CONSISTENCY_PCT * PROFIT_TARGET

    def required_total_for_consistency(self) -> float:
        """Total profit needed for the current best day to be legal."""
        if self.best_day == 0:
            return PROFIT_TARGET
        return max(PROFIT_TARGET, self.best_day / CONSISTENCY_PCT)

    # --- Core mechanics ---------------------------------------------------

    def record_trade(self, entry_dt, exit_dt, direction, entry, exit_px,
                     contracts, reason):
        """Apply a closed trade. Returns False once the account is dead."""
        if self.status != Status.ACTIVE:
            return False

        points = (exit_px - entry) if direction == "LONG" else (entry - exit_px)
        pnl = points * POINT_VALUE * contracts

        self.balance += pnl
        day = exit_dt.date()
        self.daily_pnl[day] = self.daily_pnl.get(day, 0.0) + pnl
        self.equity_curve.append((exit_dt, self.balance))

        self.trades.append({
            "entry_dt": entry_dt, "exit_dt": exit_dt, "direction": direction,
            "entry": entry, "exit": exit_px, "points": points, "pnl": pnl,
            "contracts": contracts, "reason": reason, "balance": self.balance,
        })

        self.peak_balance = max(self.peak_balance, self.balance)
        self.closest_to_floor = min(self.closest_to_floor, self.buffer)

        # Intraday drawdown breach is immediate death.
        if self.balance <= self.floor:
            self.status = Status.FAILED_DRAWDOWN
            return False

        return True

    def end_of_day(self, day: date):
        """Trail the floor on the closing balance. EOD, not intraday --
        this is why Tradeify is survivable for multi-bar holds.

        The floor trails at (balance - $2,000) and stops permanently once it
        reaches $50,100 -- i.e. when the balance first closes at or above
        $52,100. After that the account can never be lost back to zero.
        """
        if self.floor_locked:
            return

        trailed = max(self.floor, self.balance - MAX_DRAWDOWN)
        if trailed >= DRAWDOWN_LOCK_AT:
            self.floor = DRAWDOWN_LOCK_AT
            self.floor_locked = True
        else:
            self.floor = trailed

    def check_pass(self) -> bool:
        """Target + minimum days + consistency, all three."""
        if self.status != Status.ACTIVE:
            return False
        if self.total_profit < PROFIT_TARGET:
            return False
        if self.trading_days < MIN_TRADING_DAYS:
            return False

        if self.best_day_pct > CONSISTENCY_PCT:
            # Not a failure -- the pass is blocked until more days dilute it.
            self.consistency_blocks += 1
            self.status = Status.BLOCKED_CONSISTENCY
            return False

        self.status = Status.PASSED
        return True

    # --- Pre-trade rule checks -------------------------------------------

    def can_enter(self, dt: datetime, stop_points: float, contracts: int):
        """Reject an entry that would violate a rule. Returns (ok, reason)."""
        if self.status != Status.ACTIVE:
            return False, "account not active"

        t = dt.time()

        # No new entries close to the flatten -- needs room to resolve.
        if time(15, 45) <= t < FLATTEN_TIME:
            return False, "too close to 4:45 PM ET flatten"
        if FLATTEN_TIME <= t < SESSION_OPEN:
            return False, "inside the maintenance window"

        # Friday: no position may survive the weekend halt.
        if dt.weekday() == 4 and t >= time(15, 45):
            return False, "Friday — cannot hold through the weekend"

        # Would a full stop-out kill the account?
        risk = stop_points * POINT_VALUE * contracts
        if self.balance - risk <= self.floor:
            return False, f"stop-out (${risk:,.0f}) breaches floor"

        return True, "ok"

    def target_cap_points(self, day: date, contracts: int) -> float:
        """Max additional points today before the 40% cap is threatened.

        The rule is measured on the FINAL total, so this uses the target as
        the planning assumption -- the same thing a trader does live.
        """
        already = self.daily_pnl.get(day, 0.0)
        headroom = self.max_legal_day() - already
        if headroom <= 0:
            return 0.0
        return headroom / (POINT_VALUE * contracts)


def must_flatten(dt: datetime) -> bool:
    """True when an open position must be closed at this bar."""
    t = dt.time()
    if t >= FLATTEN_TIME:
        return True
    if dt.weekday() == 4 and t >= time(16, 30):   # Friday buffer
        return True
    return False
