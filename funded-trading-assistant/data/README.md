# Trade data

`trades.csv` is the single source of truth for the funded-account trade
log. Every other script — the dashboard builder, the formula verifier, and
the ML trainer — loads through `trade_data.py` instead of keeping its own
copy, so the three can never drift out of sync with each other again.

## Logging a new trade

1. Append one row to `trades.csv`:
   `trade,date,time,session,direction,entry,exit,contracts,strategy,confidence,management,notes`
   (leave `confidence` blank if none was scored).
2. Re-run the pipeline:
   ```
   cd ../dashboard
   python3 build_dashboard.py && python3 build_dashboard_step2.py && \
   python3 build_dashboard_step3.py && python3 build_dashboard_step4.py && \
   python3 verify_formulas.py
   ```
3. Re-run the ML model:
   ```
   cd ../data
   python3 ml_train.py
   ```
4. Cross-check `verify_formulas.py`'s printed Total P&L / Wins-Losses /
   Current Balance against the Account Tracker (Google Drive) before
   shipping the .xlsx — that catches any transcription error between the
   tracker and `trades.csv`.

There is no background process that runs this automatically — this
session can't run a persistent daemon that fires on its own. "Self-teaching"
in practice means: one row appended here, then the commands above, and the
model retrains on the full history every time (which is also more correct
than incremental online learning on a dataset this small).
