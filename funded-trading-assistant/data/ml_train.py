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
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from trade_data import load_trades

rows = load_trades()
df = pd.DataFrame(rows)
# median-impute missing confidence (trades that predate scoring, or were
# the user's own off-script entries)
df["confidence"] = df["confidence"].fillna(df["confidence"].median())

X = df[["strategy", "session", "direction", "confidence", "contracts"]]
y = df["win"]

pre = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), ["strategy", "session", "direction"]),
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

model.fit(X, y)

print("--- Predicted win probability by Strategy (RTH, direction=BUY, confidence=50, contracts=4) ---")
for strat in df["strategy"].unique():
    row = pd.DataFrame([{"strategy": strat, "session": "RTH", "direction": "BUY",
                          "confidence": 50, "contracts": 4}])
    p = model.predict_proba(row)[0, 1]
    n = len(df[df["strategy"] == strat])
    actual_wr = df[df["strategy"] == strat]["win"].mean()
    print(f"{strat:<28} model_p={p:.1%}   actual_wr(n={n})={actual_wr:.1%}")

print()
print("--- Predicted win probability by Session (strategy=Resistance/Support Fade, SELL, conf=50) ---")
for sess in df["session"].unique():
    row = pd.DataFrame([{"strategy": "Resistance / Support Fade", "session": sess,
                          "direction": "SELL", "confidence": 50, "contracts": 4}])
    p = model.predict_proba(row)[0, 1]
    n = len(df[df["session"] == sess])
    actual_wr = df[df["session"] == sess]["win"].mean()
    print(f"{sess:<20} model_p={p:.1%}   actual_wr(n={n})={actual_wr:.1%}")
