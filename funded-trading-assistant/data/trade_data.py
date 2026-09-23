"""
Single source of truth for the funded-account trade log. trades.csv is the
only file you edit when logging a new trade — every script (dashboard
builder, formula verifier, ML trainer) loads through here so nothing goes
out of sync again.
"""
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "trades.csv")


def load_trades(path=CSV_PATH):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            entry = float(r["entry"])
            exitp = float(r["exit"])
            contracts = int(r["contracts"])
            direction = r["direction"]
            points = (exitp - entry) if direction == "BUY" else (entry - exitp)
            pnl = points * contracts * 50
            confidence = int(r["confidence"]) if r["confidence"].strip() else None
            rows.append({
                "trade": int(r["trade"]),
                "date": r["date"],
                "time": r["time"],
                "session": r["session"],
                "direction": direction,
                "entry": entry,
                "exit": exitp,
                "contracts": contracts,
                "strategy": r["strategy"],
                "confidence": confidence,
                "management": r["management"],
                "notes": r["notes"],
                "account": r.get("account", "Sim-50K-Flex"),
                "points": points,
                "pnl": pnl,
                "win": 1 if pnl > 0 else 0,
            })
    return rows


if __name__ == "__main__":
    trades = load_trades()
    total_pnl = sum(t["pnl"] for t in trades)
    wins = sum(t["win"] for t in trades)
    print(f"{len(trades)} trades loaded. Wins: {wins}-{len(trades)-wins}. "
          f"Total P&L: ${total_pnl:,.2f}.")

    # Different accounts have different starting balances, so a single
    # combined "50000 + total_pnl" figure would be misleading once more
    # than one account is in the log -- break it out per account instead.
    starting_balance = {"Sim-50K-Flex": 50000, "Eval-150K-Select": 150000}
    accounts = sorted(set(t["account"] for t in trades))
    for acct in accounts:
        acct_trades = [t for t in trades if t["account"] == acct]
        acct_pnl = sum(t["pnl"] for t in acct_trades)
        acct_wins = sum(t["win"] for t in acct_trades)
        base = starting_balance.get(acct)
        bal = f"${base + acct_pnl:,.2f}" if base is not None else "unknown starting balance"
        print(f"  {acct}: {len(acct_trades)} trades, {acct_wins}-{len(acct_trades)-acct_wins}, "
              f"P&L ${acct_pnl:,.2f}, balance {bal}")
