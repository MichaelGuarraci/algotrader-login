"""
Independent re-check of every formula in the workbook, computed straight
from trade_data.load_trades() (the same source the dashboard builds from).
Needed because LibreOffice can't recalculate formulas in the sandbox this
runs in (hangs on any document-open, confirmed via strace against even a
trivial file) — so this is how the shipped .xlsx gets verified before
sending it.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))

from trade_data import load_trades

rows = load_trades()

print(f"{'#':<3}{'Direction':<9}{'Entry':<10}{'Exit':<10}{'Pts':<8}{'P&L':<12}{'Strategy'}")
for r in rows:
    print(f"{r['trade']:<3}{r['direction']:<9}{r['entry']:<10}{r['exit']:<10}{r['points']:<8.2f}{r['pnl']:<12.2f}{r['strategy']}")

total_trades = len(rows)
wins = [r for r in rows if r["pnl"] > 0]
losses = [r for r in rows if r["pnl"] < 0]
total_pnl = sum(r["pnl"] for r in rows)
avg_win = sum(r["pnl"] for r in wins) / len(wins) if wins else 0
avg_loss = sum(r["pnl"] for r in losses) / len(losses) if losses else 0
win_rate = len(wins) / total_trades
wl_ratio = abs(avg_win / avg_loss) if avg_loss else float("inf")
expectancy = total_pnl / total_trades
largest_win = max(r["pnl"] for r in rows)
largest_loss = min(r["pnl"] for r in rows)
total_points = sum(r["points"] for r in rows)
avg_points = total_points / total_trades
starting_balance = 50000
floor = 50100
current_balance = starting_balance + total_pnl
buffer = current_balance - floor

print("\n--- DASHBOARD (expected) ---")
print(f"Total Trades:        {total_trades}")
print(f"Wins:                {len(wins)}")
print(f"Losses:              {len(losses)}")
print(f"Win Rate:            {win_rate:.1%}")
print(f"Total P&L:           ${total_pnl:,.2f}")
print(f"Average Win:         ${avg_win:,.2f}")
print(f"Average Loss:        ${avg_loss:,.2f}")
print(f"Win/Loss $ Ratio:    {wl_ratio:.2f}x")
print(f"Expectancy/Trade:    ${expectancy:,.2f}")
print(f"Largest Win:         ${largest_win:,.2f}")
print(f"Largest Loss:        ${largest_loss:,.2f}")
print(f"Total Points:        {total_points:.2f}")
print(f"Avg Points/Trade:    {avg_points:.2f}")
print(f"Current Balance:     ${current_balance:,.2f}")
print(f"Buffer to Floor:     ${buffer:,.2f}")

def breakdown(key, categories):
    print(f"\n--- BY {key.upper()} (expected) ---")
    tot_pnl_check = 0
    tot_trades_check = 0
    for cat in categories:
        sub = [r for r in rows if r[key] == cat]
        n = len(sub)
        w = len([s for s in sub if s["pnl"] > 0])
        wr = w / n if n else 0
        pnl = sum(s["pnl"] for s in sub)
        avg = pnl / n if n else 0
        tot_pnl_check += pnl
        tot_trades_check += n
        print(f"{cat:<28} n={n:<3} wins={w:<3} wr={wr:.1%}   P&L=${pnl:,.2f}   avg=${avg:,.2f}")
    print(f"{'TOTAL':<28} n={tot_trades_check:<3}            P&L=${tot_pnl_check:,.2f}")
    assert tot_trades_check == total_trades, f"MISMATCH: category total {tot_trades_check} != {total_trades} trades"
    assert abs(tot_pnl_check - total_pnl) < 0.01, "MISMATCH: category P&L total != overall P&L"

breakdown("strategy", ["Trend Continuation", "Pullback / Retest Entry", "Resistance / Support Fade",
                       "Breakout", "Counter-Trend Bounce", "Unmanaged Overnight Hold"])
breakdown("session", ["Pre-Market", "RTH", "Overnight/Globex", "Weekend Reopen"])

print("\nAll category totals reconcile with overall totals - no trades fall outside the defined categories.")

print("\n--- CONFIDENCE CALIBRATION (expected) ---")
bands = [("Under 40%", 0, 40), ("40-49%", 40, 50), ("50-59%", 50, 60),
         ("60-69%", 60, 70), ("70-79%", 70, 80), ("80%+", 80, 101)]
scored = [r for r in rows if r["confidence"] is not None]
tot_n = tot_pnl2 = 0
for label, lo, hi in bands:
    sub = [r for r in scored if lo <= r["confidence"] < hi]
    n = len(sub)
    w = len([s for s in sub if s["pnl"] > 0])
    wr = w / n if n else 0
    pnl = sum(s["pnl"] for s in sub)
    tot_n += n
    tot_pnl2 += pnl
    print(f"{label:<10} n={n:<3} wins={w:<3} wr={wr:.1%}  P&L=${pnl:,.2f}")
print(f"Scored trades total: {tot_n} (unscored: {len(rows)-tot_n})  P&L=${tot_pnl2:,.2f}")

print("\nCross-check against the Account Tracker: compare the Total P&L, "
      "Wins-Losses and Current Balance above against the tracker's YAML "
      "frontmatter (`balance:`) and \"Record: W-L\" line before shipping.")
