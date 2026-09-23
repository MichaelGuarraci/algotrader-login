"""
Real (not mocked) logistic-regression model trained on the funded-account
trade history in trades.csv. Re-run this after every closed trade — append
the trade to trades.csv first, then run:

    python3 ml_train.py

Honesty check built in: with a small trade count this WILL overfit on some
categories. Leave-one-out cross-validation accuracy is reported so the
output isn't overstated.
"""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut, cross_val_score, cross_val_predict
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from trade_data import load_trades

rows = load_trades()
df = pd.DataFrame(rows)
# median-impute missing confidence (trades that predate scoring, or were
# the user's own off-script entries)
df["confidence"] = df["confidence"].fillna(df["confidence"].median())

X = df[["strategy", "session", "direction", "confidence", "contracts", "account"]]
y = df["win"]

pre = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), ["strategy", "session", "direction", "account"]),
], remainder="passthrough")

model = Pipeline([
    ("pre", pre),
    ("clf", LogisticRegression(max_iter=2000, C=0.5)),
])

# Leave-one-out CV -- honest accuracy check for a small dataset
loo = LeaveOneOut()
scores = cross_val_score(model, X, y, cv=loo)
print(f"Trades in training set: {len(df)}")
print(f"Overall win rate: {y.mean():.1%}")
print(f"Leave-one-out CV accuracy: {scores.mean():.1%}  "
      f"(baseline = always-predict-win = {y.mean():.1%})")
print(f"-> {'Model beats the naive baseline' if scores.mean() > y.mean() else 'Model does NOT beat just predicting the majority class yet'}")
print()

# Per-trade leave-one-out backtest: for each trade, the prediction comes
# from a model trained on every OTHER trade only -- this is what "run the
# model against all previous trades" actually means; it's never allowed to
# see the trade it's scoring.
loo_proba = cross_val_predict(model, X, y, cv=loo, method="predict_proba")[:, 1]
df["model_p"] = loo_proba
df["predicted"] = (df["model_p"] >= 0.5).astype(int)
df["correct"] = (df["predicted"] == df["win"]).astype(int)

print("--- Per-trade leave-one-out backtest (model never sees the trade it's scoring) ---")
print(f"{'#':<3}{'Strategy':<28}{'Session':<18}{'Conf':<6}{'Actual':<8}{'Model p':<9}{'Call':<8}{'Hit?'}")
for _, r in df.iterrows():
    actual = "WIN" if r["win"] == 1 else "LOSS"
    call = "WIN" if r["predicted"] == 1 else "LOSS"
    hit = "✓" if r["correct"] == 1 else "✗"
    conf = f"{r['confidence']:.0f}%" if pd.notna(r["confidence"]) else "-"
    print(f"{r['trade']:<3}{r['strategy']:<28}{r['session']:<18}{conf:<6}{actual:<8}{r['model_p']:.1%}    {call:<8}{hit}")

print(f"\nLOO backtest hit rate: {df['correct'].mean():.1%} "
      f"({df['correct'].sum()}/{len(df)} calls matched the actual outcome)")

# biggest misses -- where the model was most confidently wrong
misses = df[df["correct"] == 0].copy()
if len(misses):
    misses["confidence_gap"] = (misses["model_p"] - 0.5).abs()
    misses = misses.sort_values("confidence_gap", ascending=False).head(5)
    print("\n--- Biggest model misses (most confident, still wrong) ---")
    for _, r in misses.iterrows():
        actual = "WIN" if r["win"] == 1 else "LOSS"
        print(f"Trade {r['trade']:<3} {r['strategy']:<28} model said {r['model_p']:.1%} win, actually {actual}")
print()

model.fit(X, y)

print("--- Predicted win probability by Strategy (RTH, direction=BUY, confidence=50, contracts=4) ---")
for strat in df["strategy"].unique():
    row = pd.DataFrame([{"strategy": strat, "session": "RTH", "direction": "BUY",
                          "confidence": 50, "contracts": 4, "account": "Sim-50K-Flex"}])
    p = model.predict_proba(row)[0, 1]
    n = len(df[df["strategy"] == strat])
    actual_wr = df[df["strategy"] == strat]["win"].mean()
    print(f"{strat:<28} model_p={p:.1%}   actual_wr(n={n})={actual_wr:.1%}")

print()
print("--- Predicted win probability by Session (strategy=Resistance/Support Fade, SELL, conf=50) ---")
for sess in df["session"].unique():
    row = pd.DataFrame([{"strategy": "Resistance / Support Fade", "session": sess,
                          "direction": "SELL", "confidence": 50, "contracts": 4, "account": "Sim-50K-Flex"}])
    p = model.predict_proba(row)[0, 1]
    n = len(df[df["session"] == sess])
    actual_wr = df[df["session"] == sess]["win"].mean()
    print(f"{sess:<20} model_p={p:.1%}   actual_wr(n={n})={actual_wr:.1%}")

print()
print("--- Predicted win probability by Account (RTH, direction=BUY, confidence=50, contracts=4) ---")
for acct in df["account"].unique():
    row = pd.DataFrame([{"strategy": "Resistance / Support Fade", "session": "RTH",
                          "direction": "BUY", "confidence": 50, "contracts": 4, "account": acct}])
    p = model.predict_proba(row)[0, 1]
    n = len(df[df["account"] == acct])
    actual_wr = df[df["account"] == acct]["win"].mean()
    print(f"{acct:<20} model_p={p:.1%}   actual_wr(n={n})={actual_wr:.1%}")
