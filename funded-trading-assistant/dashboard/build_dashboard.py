import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

from trade_data import load_trades

FONT = "Arial"

wb = Workbook()

# ---------- Styles ----------
header_font = Font(name=FONT, bold=True, color="FFFFFF", size=11)
header_fill = PatternFill("solid", fgColor="1F4E78")
subheader_font = Font(name=FONT, bold=True, size=11, color="1F4E78")
title_font = Font(name=FONT, bold=True, size=16, color="1F4E78")
sub_font = Font(name=FONT, italic=True, size=10, color="666666")
normal_font = Font(name=FONT, size=11)
blue_input = Font(name=FONT, size=11, color="0000FF")
black_formula = Font(name=FONT, size=11, color="000000")
bold_black = Font(name=FONT, size=11, bold=True, color="000000")
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center")
stat_label_fill = PatternFill("solid", fgColor="D9E1F2")
stat_value_fill = PatternFill("solid", fgColor="FFFFFF")

CUR = '$#,##0.00;[RED]($#,##0.00)'
CUR0 = '$#,##0;[RED]($#,##0)'
PCT = '0.0%'
PTS = '0.00'

# =========================================================
# SHEET 1: TRADE LOG
# =========================================================
ws = wb.active
ws.title = "Trade Log"
ws.sheet_view.showGridLines = False

ws["A1"] = "Tradeify Select 50K — Funded Trade Log"
ws["A1"].font = title_font
ws["A2"] = "Practice simulation — log every closed trade here. Yellow cells = your inputs. Everything else recalculates automatically."
ws["A2"].font = sub_font

headers = ["Trade #", "Date", "Time (ET)", "Session", "Direction", "Entry", "Exit",
           "Contracts", "Points", "$/Point", "P&L ($)", "Strategy", "Confidence %",
           "Management", "Notes"]
HEADER_ROW = 4
for i, h in enumerate(headers, start=1):
    c = ws.cell(row=HEADER_ROW, column=i, value=h)
    c.font = header_font
    c.fill = header_fill
    c.alignment = center
    c.border = border

col_widths = [8, 11, 9, 16, 10, 10, 10, 10, 9, 9, 12, 22, 12, 16, 46]
for i, w in enumerate(col_widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

# input fill (yellow) for hardcoded trade-record cells the user fills in
input_fill = PatternFill("solid", fgColor="FFF2CC")

# ---- Trade data: single source of truth is ../data/trades.csv ----
trades = [
    (t["date"], t["time"], t["session"], t["direction"], t["entry"], t["exit"],
     t["contracts"], t["strategy"], t["confidence"], t["management"], t["notes"])
    for t in load_trades()
]

FIRST_DATA_ROW = HEADER_ROW + 1
LAST_TEMPLATE_ROW = FIRST_DATA_ROW + len(trades) - 1
EXTRA_ROWS = 60  # blank rows ready for future trades, formulas pre-filled
LAST_ROW = LAST_TEMPLATE_ROW + EXTRA_ROWS

for i, t in enumerate(trades):
    row = FIRST_DATA_ROW + i
    date, time, session, direction, entry, exitp, contracts, strategy, conf, mgmt, notes = t
    ws.cell(row=row, column=1, value=i + 1)
    ws.cell(row=row, column=2, value=date)
    ws.cell(row=row, column=3, value=time)
    ws.cell(row=row, column=4, value=session)
    ws.cell(row=row, column=5, value=direction)
    ws.cell(row=row, column=6, value=entry)
    ws.cell(row=row, column=7, value=exitp)
    ws.cell(row=row, column=8, value=contracts)
    ws.cell(row=row, column=9, value=f"=IF(E{row}=\"\",\"\",IF(E{row}=\"BUY\",G{row}-F{row},F{row}-G{row}))")
    ws.cell(row=row, column=10, value=f"=IF(H{row}=\"\",\"\",H{row}*50)")
    ws.cell(row=row, column=11, value=f"=IF(OR(I{row}=\"\",J{row}=\"\"),\"\",I{row}*J{row})")
    ws.cell(row=row, column=12, value=strategy)
    ws.cell(row=row, column=13, value=conf)
    ws.cell(row=row, column=14, value=mgmt)
    ws.cell(row=row, column=15, value=notes)

# formulas + blank input rows for future trades
for r in range(LAST_TEMPLATE_ROW + 1, LAST_ROW + 1):
    ws.cell(row=r, column=1, value=f"=IF(F{r}=\"\",\"\",F{r-1}+1)" if r == LAST_TEMPLATE_ROW + 1 else f"=IF(F{r}=\"\",\"\",A{r-1}+1)")
    ws.cell(row=r, column=9, value=f"=IF(OR(E{r}=\"\",F{r}=\"\",G{r}=\"\"),\"\",IF(E{r}=\"BUY\",G{r}-F{r},F{r}-G{r}))")
    ws.cell(row=r, column=10, value=f"=IF(H{r}=\"\",\"\",H{r}*50)")
    ws.cell(row=r, column=11, value=f"=IF(OR(I{r}=\"\",J{r}=\"\"),\"\",I{r}*J{r})")

# Fix trade # for template rows too (in case first template row's formula referenced A{r-1} which is a static number - ok since row 22 A=18 static)
ws.cell(row=LAST_TEMPLATE_ROW + 1, column=1,
        value=f"=IF(F{LAST_TEMPLATE_ROW+1}=\"\",\"\",A{LAST_TEMPLATE_ROW}+1)")

# formatting across full range
for r in range(FIRST_DATA_ROW, LAST_ROW + 1):
    for c in range(1, 16):
        cell = ws.cell(row=r, column=c)
        cell.border = border
        cell.font = normal_font
        if c in (6, 7):
            cell.number_format = PTS
        if c == 9:
            cell.number_format = PTS
        if c in (10, 11):
            cell.number_format = CUR0
        if c == 13:
            cell.number_format = '0"%"'
    # yellow highlight the hand-entered input columns for all rows (incl. blank future rows)
    for c in (2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15):
        ws.cell(row=r, column=c).fill = input_fill

ws.freeze_panes = f"A{FIRST_DATA_ROW}"

# conditional formatting on P&L column
green_fill = PatternFill("solid", fgColor="C6EFCE")
red_fill = PatternFill("solid", fgColor="FFC7CE")
pnl_range = f"K{FIRST_DATA_ROW}:K{LAST_ROW}"
ws.conditional_formatting.add(pnl_range, CellIsRule(operator="greaterThan", formula=["0"], fill=green_fill))
ws.conditional_formatting.add(pnl_range, CellIsRule(operator="lessThan", formula=["0"], fill=red_fill))

# data validation dropdowns
dv_session = DataValidation(type="list", formula1='"Pre-Market,RTH,Overnight/Globex,Weekend Reopen"', allow_blank=True)
dv_direction = DataValidation(type="list", formula1='"BUY,SELL"', allow_blank=True)
dv_strategy = DataValidation(type="list",
    formula1='"Trend Continuation,Pullback / Retest Entry,Resistance / Support Fade,Breakout,Counter-Trend Bounce,Unmanaged Overnight Hold"',
    allow_blank=True)
dv_mgmt = DataValidation(type="list",
    formula1='"Held to TP,Held to SL,Trailed for Profit,Early Exit,Scratch"', allow_blank=True)
for dv, col in [(dv_session, "D"), (dv_direction, "E"), (dv_strategy, "L"), (dv_mgmt, "N")]:
    ws.add_data_validation(dv)
    dv.add(f"{col}{FIRST_DATA_ROW}:{col}{LAST_ROW}")

ws["A" + str(LAST_ROW + 3)] = ("Notes: Points/$/Point/P&L are formulas — never type them directly. "
                                 "Confidence % left blank for Trades 1-9 (predates the NOW/Zone A/Zone B call "
                                 "format, so no recorded confidence exists). Strategy/session labels for "
                                 "Trades 1-9 are classified retrospectively from the trade notes.")
ws["A" + str(LAST_ROW + 3)].font = sub_font
ws["A" + str(LAST_ROW + 3)].alignment = Alignment(wrap_text=True)
ws.merge_cells(f"A{LAST_ROW+3}:O{LAST_ROW+4}")

OUT_DIR = os.environ.get("DASHBOARD_OUT_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "_build"))
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "dashboard_step1.xlsx")
wb.save(OUT_PATH)
print("Step 1 (Trade Log) saved. LAST_ROW =", LAST_ROW, "FIRST_DATA_ROW=", FIRST_DATA_ROW, "LAST_TEMPLATE_ROW=", LAST_TEMPLATE_ROW)
