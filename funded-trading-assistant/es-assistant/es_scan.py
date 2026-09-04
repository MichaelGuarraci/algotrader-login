"""
ES scan -- one call, four values, nothing else.

    BUY  ·  confidence 72%
    EXIT 5842.25  ·  confidence 64%

Reads only. Places no orders, sizes nothing, writes nothing.

Confidence values are heuristic strength scores on a 0-100 scale, NOT
calibrated win probabilities. See SKILL.md.
"""
import os, sys, logging
logging.disable(logging.CRITICAL)

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

import requests
from datetime import datetime, timedelta, timezone

KEY = os.environ.get('POLYGON_API_KEY', '')
FMP_KEY = os.environ.get('FMP_API_KEY', '')

# ES contract mechanics. Equity percentage stops do not port to futures --
# 1 point = $50, 1 tick = 0.25 pt = $12.50.
TICK = 0.25
POINT_VALUE = 50.0

# Signal weights, mirroring AlgoTrader Pro's core.py. Copied, not imported --
# this tool is standalone and must not depend on that repo.
WEIGHTS = {'OB': 3.0, 'FVG': 3.0, 'FIB_OTE': 2.5, 'VOL': 1.5, 'STRUCT': 1.0, 'PD': 1.0}
MAX_SCORE = sum(WEIGHTS.values())   # 11.5
MIN_SCORE = 6.0                     # live entry threshold
MIN_TYPES = 3


def _get(url, **params):
    # FMP authenticates with `apikey` and returns a bare list; Polygon uses
    # `apiKey` and wraps results in an object.
    is_fmp = 'financialmodelingprep.com' in url
    params['apikey' if is_fmp else 'apiKey'] = FMP_KEY if is_fmp else KEY
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
    except (requests.RequestException, ValueError):
        return None

    if isinstance(data, list):
        # FMP returns newest-first with 'date'; normalise to Polygon's shape,
        # oldest-first, so the rest of the module has one format to handle.
        bars = [
            {'o': b['open'], 'h': b['high'], 'l': b['low'],
             'c': b['close'], 'v': b.get('volume', 0)}
            for b in reversed(data)
            if all(k in b for k in ('open', 'high', 'low', 'close'))
        ]
        return {'results': bars} if bars else None
    return data


# Candidate ES bar sources, tried in order. No equity proxy: a SPY-derived
# level is close enough to read direction and not close enough to rest an
# order at, and a wrong exit price is worse than no call.
#
# ES_BARS_URL overrides all of these -- set it once you know which feed you
# are entitled to. Run `python agents/es_scan.py --probe` to find out.
ES_SOURCES = [
    # FMP -- confirmed to carry ESUSD (E-Mini S&P 500). Intraday bars need the
    # Starter plan or above; the free tier serves quotes only, which is not
    # enough for ICT signals. This is the cheapest working path.
    ("fmp", "https://financialmodelingprep.com/stable/historical-chart/{minutes}min", {}),
    # Polygon Futures API (separate entitlement from the stocks plan)
    ("polygon-futures", "https://api.polygon.io/futures/vX/aggs/{sym}",
     {'resolution': '{minutes}min', 'limit': 5000}),
    # Polygon aggregates, in case futures are served on the v2 path
    ("polygon-v2", "https://api.polygon.io/v2/aggs/ticker/{sym}/range/{minutes}/minute/{fr}/{to}",
     {'adjusted': 'true', 'sort': 'asc', 'limit': 5000}),
]

# Front-month symbol. FMP uses continuous 'ESUSD'; Polygon-style feeds want a
# dated contract like 'ESZ6' -- set ES_SYMBOL to match whichever feed answers.
ES_SYMBOL = os.environ.get('ES_SYMBOL', 'ESUSD')


def fetch_yahoo(minutes=5, lookback_days=5):
    """Free ES bars via yfinance (ES=F). Returns [] if yfinance isn't installed.

    Real ES, not a proxy -- but delayed roughly 10-15 minutes and unofficial.
    Fine for testing the scanner and paper trading. Do not rest live orders
    off these levels.
    """
    try:
        import yfinance as yf
    except ImportError:
        return []
    try:
        df = yf.download("ES=F", period=f"{lookback_days}d",
                         interval=f"{minutes}m", progress=False, auto_adjust=False)
    except Exception:
        return []
    if df is None or df.empty:
        return []
    if hasattr(df.columns, 'droplevel') and df.columns.nlevels > 1:
        df.columns = df.columns.droplevel(1)     # yfinance multi-index on single ticker
    return [
        {'o': float(r.Open), 'h': float(r.High), 'l': float(r.Low),
         'c': float(r.Close), 'v': float(r.Volume or 0)}
        for r in df.itertuples()
        if r.Open == r.Open                      # drop NaN rows
    ]


def fetch_bars(minutes=5, lookback_hours=48):
    """Return (bars, source_name). Empty list when no real ES feed answers.

    Never substitutes an equity proxy. If nothing returns ES bars, the caller
    prints NONE.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=lookback_hours)
    fr, to = start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    fmt = {'sym': ES_SYMBOL, 'minutes': minutes, 'fr': fr, 'to': to}

    override = os.environ.get('ES_BARS_URL')
    sources = [("custom", override, {})] if override else ES_SOURCES

    for name, url, params in sources:
        extra = {k: str(v).format(**fmt) for k, v in params.items()}
        if name == 'fmp':
            extra['symbol'] = ES_SYMBOL
        data = _get(url.format(**fmt), **extra)
        if data and data.get('results'):
            return data['results'], name

    # Last resort: free, delayed, real ES. Better than no call while testing.
    y = fetch_yahoo(minutes)
    if y:
        return y, "yahoo (delayed)"

    return [], None


def probe():
    """Report which ES feeds this key can actually reach. Run before trusting output."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=48)
    fmt = {'sym': ES_SYMBOL, 'minutes': 5,
           'fr': start.strftime('%Y-%m-%d'), 'to': end.strftime('%Y-%m-%d')}
    print(f"Probing ES feeds for symbol {ES_SYMBOL!r}\n")
    for name, url, params in ES_SOURCES:
        built = url.format(**fmt)
        extra = {k: str(v).format(**fmt) for k, v in params.items()}
        if name == 'fmp':
            extra['symbol'] = ES_SYMBOL
        data = _get(built, **extra)
        n = len(data.get('results') or []) if data else 0
        print(f"  {name:<18} {'OK  ' + str(n) + ' bars' if n else 'no data / not entitled'}")
        print(f"  {'':<18} {built}")
    y = fetch_yahoo(5)
    print(f"  {'yahoo (delayed)':<18} {'OK  ' + str(len(y)) + ' bars' if y else 'yfinance not installed / no data'}")
    print(f"  {'':<18} ES=F via yfinance -- free, ~10-15min delayed\n")
    print("\nIf none return bars, this key has no ES entitlement.")
    print("Set ES_BARS_URL in .env to a feed you do have (Databento, IBKR, your")
    print("prop firm's API), or add Polygon's Futures product.")


def atr(bars, n=14):
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]['h'], bars[i]['l'], bars[i - 1]['c']
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if not trs:
        return 0.0
    window = trs[-n:]
    return sum(window) / len(window)


def detect(bars):
    """Score the ICT signal stack. Returns (direction, score, types, htf_aligned).

    Deliberately a subset of core.py -- structure, displacement gaps, premium
    /discount, and volume imbalance. It is a read, not the live engine.
    """
    if len(bars) < 60:
        return None, 0.0, 0, False

    closes = [b['c'] for b in bars]
    highs = [b['h'] for b in bars]
    lows = [b['l'] for b in bars]
    vols = [b['v'] for b in bars]
    price = closes[-1]

    session = bars[-78:]                     # ~1 RTH session of 5m bars
    hi, lo = max(b['h'] for b in session), min(b['l'] for b in session)
    rng = hi - lo
    if rng <= 0:
        return None, 0.0, 0, False

    pos = (price - lo) / rng                 # 0 = session low, 1 = session high
    signals, score = [], 0.0

    # Premium / discount
    if pos <= 0.38:
        signals.append('PD'); score += WEIGHTS['PD']; bias = 'BUY'
    elif pos >= 0.62:
        signals.append('PD'); score += WEIGHTS['PD']; bias = 'SELL'
    else:
        bias = None

    # Market structure: last 20 bars vs the 20 before
    recent, prior = closes[-20:], closes[-40:-20]
    trend_up = sum(recent) / 20 > sum(prior) / 20
    if bias is None:
        bias = 'BUY' if trend_up else 'SELL'
    if (bias == 'BUY') == trend_up:
        signals.append('STRUCT'); score += WEIGHTS['STRUCT']

    # Fair value gap: 3-bar displacement, min 0.3% of range
    gap_min = rng * 0.003
    for i in range(len(bars) - 20, len(bars) - 2):
        if bias == 'BUY' and lows[i + 2] - highs[i] > gap_min:
            signals.append('FVG'); score += WEIGHTS['FVG']; break
        if bias == 'SELL' and lows[i] - highs[i + 2] > gap_min:
            signals.append('FVG'); score += WEIGHTS['FVG']; break

    # Order block: displacement bar on 1.5x volume with a real body
    avg_vol = sum(vols[-40:]) / 40 if len(vols) >= 40 else (sum(vols) / len(vols))
    for i in range(len(bars) - 20, len(bars)):
        body = abs(closes[i] - bars[i]['o'])
        if vols[i] > avg_vol * 1.5 and body > rng * 0.004:
            signals.append('OB'); score += WEIGHTS['OB']; break

    # Fibonacci OTE: 0.62-0.79 retracement of the session leg
    ote = (0.21 <= pos <= 0.38) if bias == 'BUY' else (0.62 <= pos <= 0.79)
    if ote:
        signals.append('FIB_OTE'); score += WEIGHTS['FIB_OTE']

    # Volume imbalance on the last bar
    if vols[-1] > avg_vol * 1.5:
        signals.append('VOL'); score += WEIGHTS['VOL']

    # HTF 15-min bias -- hard gate in the live config
    htf = [closes[i] for i in range(len(closes) - 36, len(closes), 3)]
    htf_up = htf[-1] > sum(htf) / len(htf) if htf else trend_up
    htf_aligned = (bias == 'BUY') == htf_up

    return bias, score, len(set(signals)), htf_aligned


def confidence_direction(score, types, htf_aligned):
    """Signal-stack strength on 0-100. Not a win probability."""
    base = min(1.0, score / MAX_SCORE)
    type_factor = min(1.0, types / 5)
    conf = 100 * (0.65 * base + 0.35 * type_factor)
    if not htf_aligned:
        conf *= 0.55                          # counter-HTF is blocked live
    return int(round(max(0, min(99, conf))))


def confidence_exit(distance, atr_val, session_range):
    """How reachable the target is inside recent range. Not a probability."""
    if atr_val <= 0 or distance <= 0:
        return 0
    reach = atr_val / distance                # >1 = target inside one ATR
    conf = 100 * min(1.0, reach)
    if distance > session_range * 0.75:       # target beyond most of the day's range
        conf *= 0.6
    return int(round(max(0, min(99, conf))))


def round_tick(p):
    return round(p / TICK) * TICK


def scan():
    """Return the call as a dict. Shared by the CLI and the web UI."""
    if not (FMP_KEY or KEY or os.environ.get('ES_BARS_URL')):
        return {'direction': 'NONE', 'dir_conf': 0}

    bars, source = fetch_bars()
    if len(bars) < 60:
        return {'direction': 'NONE', 'dir_conf': 0}

    direction, score, types, htf = detect(bars)
    atr_es = atr(bars)
    session = bars[-78:]
    session_range = max(b['h'] for b in session) - min(b['l'] for b in session)
    price = bars[-1]['c']

    if direction is None or score < MIN_SCORE or types < MIN_TYPES:
        return {'direction': 'NONE', 'dir_conf': 0, 'source': source}

    stop_pts = max(atr_es, TICK * 4)
    target_pts = stop_pts * 2.67
    exit_price = price + target_pts if direction == 'BUY' else price - target_pts

    return {
        'direction': direction,
        'dir_conf': confidence_direction(score, types, htf),
        'entry': round_tick(price),
        'exit': round_tick(exit_price),
        'exit_conf': confidence_exit(target_pts, atr_es, session_range),
        'source': source,
    }


def main():
    if '--probe' in sys.argv:
        probe()
        return

    r = scan()
    if r['direction'] == 'NONE':
        print("NONE  ·  confidence 0%")
        return
    print(f"{r['direction']}  ·  confidence {r['dir_conf']}%")
    print(f"ENTRY {r['entry']:.2f}")
    print(f"EXIT  {r['exit']:.2f}  ·  confidence {r['exit_conf']}%")


if __name__ == "__main__":
    main()
