"""
Local web UI for the ES scanner. No terminal needed after first setup.

Double-click run.bat, or:  python app.py
Opens http://127.0.0.1:7100 in the browser.

Binds to 127.0.0.1 only -- not reachable from the network.
"""
import threading, webbrowser
from flask import Flask, jsonify, render_template_string

import es_scan

app = Flask(__name__)

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>ES</title>
<style>
  :root {
    --bg:#0e1116; --card:#171b22; --line:#262c36;
    --txt:#e6e9ef; --dim:#8b95a5; --buy:#3ddc84; --sell:#ff6b6b; --none:#8b95a5;
  }
  * { box-sizing:border-box; }
  body {
    margin:0; min-height:100vh; background:var(--bg); color:var(--txt);
    font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
    display:flex; align-items:center; justify-content:center; padding:24px;
  }
  .card {
    background:var(--card); border:1px solid var(--line); border-radius:16px;
    padding:32px; width:100%; max-width:420px; text-align:center;
  }
  h1 { margin:0 0 24px; font-size:13px; letter-spacing:.14em; color:var(--dim); font-weight:600; }
  button {
    width:100%; padding:16px; font-size:17px; font-weight:650; cursor:pointer;
    background:#2b6cff; color:#fff; border:0; border-radius:10px;
  }
  button:hover { background:#1d5ae8; }
  button:disabled { opacity:.5; cursor:default; }
  .dir { font-size:44px; font-weight:750; letter-spacing:.02em; margin:28px 0 2px; }
  .buy { color:var(--buy); } .sell { color:var(--sell); } .none { color:var(--none); }
  .conf { font-size:14px; color:var(--dim); margin-bottom:22px; }
  table { width:100%; border-collapse:collapse; margin-bottom:6px; }
  td { padding:11px 0; border-top:1px solid var(--line); text-align:left; font-size:14px; }
  td.k { color:var(--dim); }
  td.v { text-align:right; font-variant-numeric:tabular-nums; font-size:19px; font-weight:650; }
  .sub { font-size:12px; color:var(--dim); font-weight:400; }
  .src { margin-top:18px; font-size:11px; color:var(--dim); letter-spacing:.04em; }
  .hidden { display:none; }
</style>
<div class="card">
  <h1>ES · E-MINI S&amp;P 500</h1>
  <button id="go" onclick="scan()">Scan</button>
  <div id="out" class="hidden">
    <div id="dir" class="dir"></div>
    <div id="dconf" class="conf"></div>
    <table id="levels">
      <tr><td class="k">Entry</td><td class="v" id="entry"></td></tr>
      <tr><td class="k">Exit</td><td class="v" id="exit"></td></tr>
    </table>
    <div id="econf" class="conf" style="margin:8px 0 0"></div>
    <div id="src" class="src"></div>
  </div>
</div>
<script>
async function scan() {
  const b = document.getElementById('go');
  b.disabled = true; b.textContent = 'Scanning…';
  try {
    const r = await (await fetch('/scan')).json();
    const out = document.getElementById('out');
    const dir = document.getElementById('dir');
    out.classList.remove('hidden');
    dir.textContent = r.direction;
    dir.className = 'dir ' + r.direction.toLowerCase();
    document.getElementById('dconf').textContent = 'confidence ' + r.dir_conf + '%';
    const lv = document.getElementById('levels');
    const ec = document.getElementById('econf');
    if (r.direction === 'NONE') {
      lv.classList.add('hidden'); ec.classList.add('hidden');
    } else {
      lv.classList.remove('hidden'); ec.classList.remove('hidden');
      document.getElementById('entry').textContent = r.entry.toFixed(2);
      document.getElementById('exit').textContent  = r.exit.toFixed(2);
      ec.textContent = 'exit confidence ' + r.exit_conf + '%';
    }
    document.getElementById('src').textContent = r.source ? r.source.toUpperCase() : '';
  } catch (e) {
    document.getElementById('out').classList.remove('hidden');
    document.getElementById('dir').textContent = 'ERROR';
    document.getElementById('dir').className = 'dir none';
    document.getElementById('dconf').textContent = String(e);
  }
  b.disabled = false; b.textContent = 'Scan';
}
</script>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/scan")
def scan():
    return jsonify(es_scan.scan())


if __name__ == "__main__":
    url = "http://127.0.0.1:7100"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"ES scanner running at {url}  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=7100, debug=False)
