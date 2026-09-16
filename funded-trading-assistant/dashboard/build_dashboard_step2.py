import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))

import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.utils import get_column_letter

from trade_data import load_trades

FONT = "Arial"
OUT_DIR = os.environ.get("DASHBOARD_OUT_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "_build"))
PATH = os.path.join(OUT_DIR, "dashboard_step1.xlsx")

wb = load_workbook(PATH)
tl = wb["Trade Log"]

FIRST_DATA_ROW = 5
N_TRADES = len(load_trades())
LAST_TEMPLATE_ROW = FIRST_DATA_ROW + N_TRADES - 1
LAST_ROW = LAST_TEMPLATE_ROW + 60
TL_RANGE = f"'Trade Log'!$K${FIRST_DATA_ROW}:$K${LAST_ROW}"
TL_L = f"'Trade Log'!$L${FIRST_DATA_ROW}:$L${LAST_ROW}"
TL_D = f"'Trade Log'!$D${FIRST_DATA_ROW}:$D${LAST_ROW}"
TL_F = f"'Trade Log'!$F${FIRST_DATA_ROW}:$F${LAST_ROW}"
TL_I = f"'Trade Log'!$I${FIRST_DATA_ROW}:$I${LAST_ROW}"

header_font = Font(name=FONT, bold=True, color="FFFFFF", size=11)
header_fill = PatternFill("solid", fgColor="1F4E78")
title_font = Font(name=FONT, bold=True, size=16, color="1F4E78")
sub_font = Font(name=FONT, italic=True, size=10, color="666666")
section_font = Font(name=FONT, bold=True, size=12, color="1F4E78")
normal_font = Font(name=FONT, size=11)
bold_font = Font(name=FONT, size=11, bold=True)
blue_input = Font(name=FONT, size=11, color="0000FF", bold=True)
label_fill = PatternFill("solid", fgColor="D9E1F2")
input_fill = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center")

CUR0 = '$#,##0;[RED]($#,##0)'
PCT = '0.0%'
NUM1 = '0.0'

# =========================================================
# Column P on Trade Log: running balance (for equity curve)
# =========================================================
tl.cell(row=4, column=16, value="Balance After Trade").font = header_font
tl.cell(row=4, column=16).fill = header_fill
tl.cell(row=4, column=16).alignment = center
tl.cell(row=4, column=16).border = border
tl.column_dimensions["P"].width = 14
for r in range(FIRST_DATA_ROW, LAST_ROW + 1):
    tl.cell(row=r, column=16,
            value=f"=IF(K{r}=\"\",\"\",Dashboard!$C$5+SUM($K${FIRST_DATA_ROW}:K{r}))")
    tl.cell(row=r, column=16).number_format = CUR0
    tl.cell(row=r, column=16).border = border
    tl.cell(row=r, column=16).font = normal_font

# =========================================================
# SHEET 2: DASHBOARD
# =========================================================
dash = wb.create_sheet("Dashboard")
wb.move_sheet("Dashboard", offset=-(len(wb.sheetnames) - 2))  # put right after Trade Log
dash.sheet_view.showGridLines = False

dash["A1"] = "Funded Account Dashboard"
dash["A1"].font = title_font
dash["A2"] = "All figures pull live from the Trade Log tab — add a trade there and everything below updates."
dash["A2"].font = sub_font

for col, w in zip("ABCDEF", [26, 16, 4, 26, 16, 4]):
    dash.column_dimensions[col].width = w

def stat_row(ws, row, label, formula_or_value, col_label, col_val, fmt=None, is_input=False):
    lc = ws.cell(row=row, column=col_label, value=label)
    lc.font = normal_font
    lc.fill = label_fill
    lc.border = border
    lc.alignment = left
    vc = ws.cell(row=row, column=col_val, value=formula_or_value)
    vc.border = border
    vc.alignment = Alignment(horizontal="right")
    if is_input:
        vc.font = blue_input
        vc.fill = input_fill
    else:
        vc.font = bold_font
    if fmt:
        vc.number_format = fmt
    return vc

# --- Account block ---
dash["A4"] = "ACCOUNT"
dash["A4"].font = section_font
r = 5
stat_row(dash, r, "Starting Balance", 50000, 1, 3, CUR0, is_input=True); r += 1
stat_row(dash, r, "Drawdown Floor", 50100, 1, 3, CUR0, is_input=True); r += 1
stat_row(dash, r, "Current Balance", "=C5+SUM(" + TL_RANGE.replace("'Trade Log'!","'Trade Log'!") + ")", 1, 3, CUR0); r += 1
stat_row(dash, r, "Buffer to Floor", "=C7-C6", 1, 3, CUR0); r += 1
r_acct_end = r

# --- Performance block ---
dash["A11"] = "PERFORMANCE"
dash["A11"].font = section_font
r = 12
stat_row(dash, r, "Total Trades", f"=COUNT({TL_F})", 1, 3); r += 1
stat_row(dash, r, "Wins", f"=COUNTIF({TL_RANGE},\">0\")", 1, 3); r += 1
stat_row(dash, r, "Losses", f"=COUNTIF({TL_RANGE},\"<0\")", 1, 3); r += 1
stat_row(dash, r, "Win Rate", "=IFERROR(C13/C12,\"\")", 1, 3, PCT); r += 1
stat_row(dash, r, "Total P&L", f"=SUM({TL_RANGE})", 1, 3, CUR0); r += 1
stat_row(dash, r, "Average Win", f"=IFERROR(AVERAGEIF({TL_RANGE},\">0\"),0)", 1, 3, CUR0); r += 1
stat_row(dash, r, "Average Loss", f"=IFERROR(AVERAGEIF({TL_RANGE},\"<0\"),0)", 1, 3, CUR0); r += 1
stat_row(dash, r, "Win / Loss $ Ratio", "=IFERROR(ABS(C17/C18),\"\")", 1, 3, "0.00\"x\""); r += 1
stat_row(dash, r, "Expectancy per Trade", "=IFERROR(C16/C12,\"\")", 1, 3, CUR0); r += 1
stat_row(dash, r, "Largest Win", f"=MAX({TL_RANGE})", 1, 3, CUR0); r += 1
stat_row(dash, r, "Largest Loss", f"=MIN({TL_RANGE})", 1, 3, CUR0); r += 1
stat_row(dash, r, "Total Points Captured", f"=SUM({TL_I})", 1, 3, NUM1); r += 1
stat_row(dash, r, "Avg Points per Trade", f"=IFERROR(AVERAGE({TL_I}),\"\")", 1, 3, NUM1); r += 1

wb.save(os.path.join(OUT_DIR, "dashboard_step2.xlsx"))
print("Step 2 saved. LAST_ROW =", LAST_ROW)
