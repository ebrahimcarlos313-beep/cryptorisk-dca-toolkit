import csv
import hashlib
import io
import json
import os
from pathlib import Path
from flask import Flask, Response, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CryptoRiskSecretSessionKey2026#!")

DATA_FILE = Path("toolkit_data.json")
FREE_DCA_LIMIT = 3

# رمز عبور اختصاصی شما برای ساخت کد لایسنس
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "Admin2026#Crypto")

# آدرس کیف پول دریافت رمزارز خودتان (هرگز Private Key یا Seed وارد نکنید)
RECEIVE_WALLET_ADDRESS = "0xB980b5d55049107C7205B946Fb42B6BD774ba21b"
RECEIVE_NETWORK_INFO = "USDT / USDC (Check network before sending)"
PRO_PRICE_USD = 9


def generate_license_key(buyer_email_or_id: str) -> str:
    clean = buyer_email_or_id.strip().lower().encode("utf-8")
    digest = hashlib.sha256(b"cryptotoolkit-secret-salt:" + clean).hexdigest().upper()
    return f"PRO-{digest[:4]}-{digest[4:8]}-{digest[8:12]}"


def is_valid_license(code: str) -> bool:
    normalized = code.strip().upper()
    if not normalized:
        return False
    parts = normalized.split("-")
    return len(parts) == 4 and parts[0] == "PRO" and all(len(p) == 4 and p.isalnum() for p in parts[1:])


DEFAULT_DATA = {
    "lang": "en",
    "tab": "profit",
    "profit": {
        "buy_price": 60000.0,
        "sell_price": 66000.0,
        "invest": 1000.0,
        "fee_pct": 0.1,
    },
    "dca": {
        "current_price": 63000.0,
        "orders": [
            {"price": 65000.0, "amount": 500.0},
            {"price": 58000.0, "amount": 700.0},
        ],
    },
    "risk": {
        "balance": 5000.0,
        "risk_pct": 1.5,
        "entry": 62000.0,
        "stop": 60500.0,
        "target": 66500.0,
    },
}

TEXTS = {
    "en": {
        "dir": "ltr",
        "title": "CryptoRisk & DCA Toolkit",
        "subtitle": "All-in-one calculation suite for profit, DCA, and position sizing",
        "lang_btn": "فارسی",
        "tab_profit": "Profit & Fees",
        "tab_dca": "DCA Planner",
        "tab_risk": "Risk & Sizing",
        "pro_badge_on": "PRO ACTIVE",
        "pro_badge_off": "FREE PLAN",
        "deactivate_btn": "Exit Pro",
        "pro_box_title": f"Pro Upgrade (${PRO_PRICE_USD} One-Time)",
        "pro_box_desc": f"Send ${PRO_PRICE_USD} ({RECEIVE_NETWORK_INFO}) to the wallet below, then enter your received license key.",
        "wallet_label": "Receiving Wallet Address:",
        "pro_placeholder": "Enter license key (e.g. PRO-XXXX-XXXX-XXXX)",
        "pro_activate": "Activate Pro",
        "pro_activated_msg": "Pro plan is active. Unlimited DCA steps and CSV export are unlocked.",
        "pro_invalid_msg": "Invalid license key. Please check your code and try again.",
        "gen_title": "Seller / Admin: Generate Buyer License Key",
        "gen_placeholder": "Buyer reference / order note",
        "gen_secret_placeholder": "Admin Password",
        "gen_btn": "Generate Key",
        "gen_err_msg": "Unauthorized: Wrong admin password.",
        "buy_price": "Buy Price ($)",
        "sell_price": "Sell / Target Price ($)",
        "invest": "Investment Amount ($)",
        "fee_pct": "Fee per Side (%)",
        "calc_btn": "Calculate",
        "net_profit": "Net Profit / Loss ($)",
        "roi": "Net Return (%)",
        "total_fees": "Total Fees ($)",
        "break_even": "Break-Even Price ($)",
        "dca_price": "Order Price ($)",
        "dca_amount": "Order Amount ($)",
        "dca_current": "Current Market Price ($)",
        "add_order": "+ Add DCA Step",
        "export_csv": "Export CSV",
        "avg_price": "Average Buy Price ($)",
        "total_invested": "Total Invested ($)",
        "total_units": "Total Units",
        "unrealized": "Unrealized P&L ($)",
        "dca_limit_warn": "Free plan allows up to 3 DCA steps. Activate Pro for unlimited steps.",
        "th_step": "#",
        "th_price": "Price ($)",
        "th_amount": "Amount ($)",
        "th_units": "Units",
        "th_action": "Action",
        "delete": "Remove",
        "balance": "Account Balance ($)",
        "risk_pct": "Risk per Trade (%)",
        "entry": "Entry Price ($)",
        "stop": "Stop-Loss Price ($)",
        "target": "Take-Profit Target ($)",
        "max_risk": "Max Risk ($)",
        "pos_size": "Position Size ($)",
        "pos_units": "Position Units",
        "rr": "Risk / Reward",
    },
    "fa": {
        "dir": "rtl",
        "title": "جعبه ابزار محاسبه سود، میانگین خرید و مدیریت ریسک",
        "subtitle": "ابزار یکپارچه محاسبه سود خالص، خرید پله‌ای (DCA) و حجم معامله",
        "lang_btn": "English",
        "tab_profit": "سود و کارمزد",
        "tab_dca": "خرید پله‌ای (DCA)",
        "tab_risk": "مدیریت ریسک",
        "pro_badge_on": "نسخه PRO فعال",
        "pro_badge_off": "نسخه رایگان",
        "deactivate_btn": "خروج از Pro",
        "pro_box_title": f"ارتقا به نسخه Pro ({PRO_PRICE_USD} دلار یک‌باره)",
        "pro_box_desc": f"مبلغ {PRO_PRICE_USD} دلار ({RECEIVE_NETWORK_INFO}) را به کیف پول زیر واریز کنید و کد لایسنس دریافت‌شده را وارد نمایید.",
        "wallet_label": "آدرس کیف پول دریافت‌کننده:",
        "pro_placeholder": "کد لایسنس را وارد کنید (مثلاً PRO-XXXX-XXXX-XXXX)",
        "pro_activate": "فعال‌سازی Pro",
        "pro_activated_msg": "نسخه Pro فعال است؛ پله‌های نامحدود و خروجی CSV در دسترس هستند.",
        "pro_invalid_msg": "کد لایسنس معتبر نیست. لطفاً کد را بررسی کرده و دوباره وارد کنید.",
        "gen_title": "بخش فروشنده: ساخت کد لایسنس برای خریدار",
        "gen_placeholder": "شناسه یا یادداشت سفارش خریدار",
        "gen_secret_placeholder": "رمز عبور مدیر",
        "gen_btn": "تولید کد لایسنس",
        "gen_err_msg": "خطا: رمز عبور مدیر اشتباه است.",
        "buy_price": "قیمت خرید ($)",
        "sell_price": "قیمت فروش / هدف ($)",
        "invest": "مبلغ سرمایه‌گذاری ($)",
        "fee_pct": "کارمزد هر طرف (%)",
        "calc_btn": "محاسبه",
        "net_profit": "سود / زیان خالص ($)",
        "roi": "بازدهی خالص (%)",
        "total_fees": "مجموع کارمزد ($)",
        "break_even": "قیمت نقطه‌سربه‌سر ($)",
        "dca_price": "قیمت پله ($)",
        "dca_amount": "مبلغ پله ($)",
        "dca_current": "قیمت فعلی بازار ($)",
        "add_order": "+ افزودن پله خرید",
        "export_csv": "خروجی CSV",
        "avg_price": "میانگین قیمت خرید ($)",
        "total_invested": "مجموع سرمایه ($)",
        "total_units": "مجموع واحدها",
        "unrealized": "سود / زیان لحظه‌ای ($)",
        "dca_limit_warn": "در نسخه رایگان حداکثر ۳ پله DCA مجاز است. برای پله‌های بیشتر Pro را فعال کنید.",
        "th_step": "#",
        "th_price": "قیمت ($)",
        "th_amount": "مبلغ ($)",
        "th_units": "واحد",
        "th_action": "عملیات",
        "delete": "حذف",
        "balance": "موجودی حساب ($)",
        "risk_pct": "درصد ریسک معامله (%)",
        "entry": "قیمت ورود ($)",
        "stop": "قیمت حد ضرر ($)",
        "target": "قیمت حد سود ($)",
        "max_risk": "حداکثر ریسک ($)",
        "pos_size": "حجم معامله ($)",
        "pos_units": "تعداد واحد",
        "rr": "نسبت ریسک به ریوارد",
    },
}

PAGE_HTML = """<!DOCTYPE html>
<html lang="{{ lang }}" dir="{{ t.dir }}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ t.title }}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0b1020;
      color: #eef2ff;
      min-height: 100vh;
      padding: 18px 14px 44px;
    }
    .container { max-width: 960px; margin: 0 auto; }
    .card {
      background: #131b33;
      border: 1px solid #27345d;
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 14px;
    }
    .top-bar {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    h1 { font-size: 1.2rem; }
    h2 { font-size: 1rem; margin-bottom: 8px; }
    .sub { color: #9aa7c7; font-size: 0.86rem; margin-top: 4px; }
    .actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
    .btn {
      background: #3b82f6;
      color: #fff;
      border: none;
      padding: 9px 14px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
    }
    .btn-ghost {
      background: #182240;
      color: #eef2ff;
      border: 1px solid #27345d;
    }
    .badge {
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
    }
    .badge-on { background: rgba(16,185,129,0.18); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.4); }
    .badge-off { background: rgba(245,158,11,0.16); color: #fcd34d; border: 1px solid rgba(245,158,11,0.4); }
    .tabs {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 14px;
    }
    .tab-btn {
      background: #131b33;
      border: 1px solid #27345d;
      color: #9aa7c7;
      padding: 11px;
      border-radius: 12px;
      font-weight: 700;
      cursor: pointer;
    }
    .tab-btn.active {
      background: #182240;
      color: #fff;
      border-color: #3b82f6;
    }
    .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .field { display: flex; flex-direction: column; gap: 6px; }
    label { font-size: 0.84rem; color: #9aa7c7; }
    input {
      width: 100%;
      background: #0b1020;
      border: 1px solid #27345d;
      color: #eef2ff;
      padding: 10px 12px;
      border-radius: 10px;
      font-size: 0.94rem;
    }
    .wallet-box {
      margin-top: 10px;
      background: #0b1020;
      border: 1px dashed #3b82f6;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 0.86rem;
      word-break: break-all;
    }
    .results {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 14px;
    }
    .stat {
      background: #0b1020;
      border: 1px solid #27345d;
      border-radius: 12px;
      padding: 12px 14px;
    }
    .stat .lbl { font-size: 0.78rem; color: #9aa7c7; }
    .stat .val { font-size: 1.08rem; font-weight: 700; margin-top: 4px; }
    .pos { color: #10b981; }
    .neg { color: #ef4444; }
    .warn { color: #f59e0b; font-size: 0.85rem; margin-top: 10px; }
    .msg-ok { color: #6ee7b7; font-size: 0.85rem; margin-top: 8px; }
    .msg-err { color: #fca5a5; font-size: 0.85rem; margin-top: 8px; }
    .table-wrap { overflow-x: auto; margin-top: 14px; border: 1px solid #27345d; border-radius: 12px; }
    table { width: 100%; border-collapse: collapse; min-width: 460px; font-size: 0.88rem; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #27345d; text-align: start; }
    th { background: #182240; color: #9aa7c7; }
    .row-inline { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; align-items: center; }
    @media (max-width: 680px) {
      .tabs, .grid-2, .grid-3 { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="top-bar">
        <div>
          <h1>{{ t.title }}</h1>
          <div class="sub">{{ t.subtitle }}</div>
        </div>
        <div class="actions">
          <span class="badge {{ 'badge-on' if data.is_pro else 'badge-off' }}">
            {{ t.pro_badge_on if data.is_pro else t.pro_badge_off }}
          </span>
          {% if data.is_pro %}
          <form method="POST" action="{{ url_for('deactivate_pro_route') }}">
            <button class="btn btn-ghost" type="submit">{{ t.deactivate_btn }}</button>
          </form>
          {% endif %}
          <form method="POST" action="{{ url_for('toggle_lang') }}">
            <button class="btn btn-ghost" type="submit">{{ t.lang_btn }}</button>
          </form>
        </div>
      </div>
    </div>

    <form method="POST" action="{{ url_for('switch_tab') }}" class="tabs">
      <button class="tab-btn {{ 'active' if data.tab == 'profit' else '' }}" type="submit" name="tab" value="profit">{{ t.tab_profit }}</button>
      <button class="tab-btn {{ 'active' if data.tab == 'dca' else '' }}" type="submit" name="tab" value="dca">{{ t.tab_dca }}</button>
      <button class="tab-btn {{ 'active' if data.tab == 'risk' else '' }}" type="submit" name="tab" value="risk">{{ t.tab_risk }}</button>
    </form>

    {% if data.tab == 'profit' %}
    <div class="card">
      <form method="POST" action="{{ url_for('calc_profit_route') }}">
        <div class="grid-2">
          <div class="field">
            <label>{{ t.buy_price }}</label>
            <input type="number" step="any" min="0.01" name="buy_price" value="{{ data.profit.buy_price }}" required />
          </div>
          <div class="field">
            <label>{{ t.sell_price }}</label>
            <input type="number" step="any" min="0" name="sell_price" value="{{ data.profit.sell_price }}" required />
          </div>
          <div class="field">
            <label>{{ t.invest }}</label>
            <input type="number" step="any" min="0.01" name="invest" value="{{ data.profit.invest }}" required />
          </div>
          <div class="field">
            <label>{{ t.fee_pct }}</label>
            <input type="number" step="any" min="0" name="fee_pct" value="{{ data.profit.fee_pct }}" required />
          </div>
        </div>
        <div class="row-inline">
          <button class="btn" type="submit">{{ t.calc_btn }}</button>
        </div>
      </form>

      <div class="results">
        <div class="stat">
          <div class="lbl">{{ t.net_profit }}</div>
          <div class="val {{ 'pos' if profit_res.net_profit > 0 else ('neg' if profit_res.net_profit < 0 else '') }}">${{ "{:,.2f}".format(profit_res.net_profit) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.roi }}</div>
          <div class="val {{ 'pos' if profit_res.roi > 0 else ('neg' if profit_res.roi < 0 else '') }}">{{ "{:.2f}".format(profit_res.roi) }}%</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.total_fees }}</div>
          <div class="val">${{ "{:,.2f}".format(profit_res.total_fees) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.break_even }}</div>
          <div class="val">${{ "{:,.2f}".format(profit_res.break_even) }}</div>
        </div>
      </div>
    </div>
    {% endif %}

    {% if data.tab == 'dca' %}
    <div class="card">
      <form method="POST" action="{{ url_for('add_dca_route') }}">
        <div class="grid-3">
          <div class="field">
            <label>{{ t.dca_price }}</label>
            <input type="number" step="any" min="0.01" name="dca_price" placeholder="60000" required />
          </div>
          <div class="field">
            <label>{{ t.dca_amount }}</label>
            <input type="number" step="any" min="0.01" name="dca_amount" placeholder="500" required />
          </div>
          <div class="field">
            <label>{{ t.dca_current }}</label>
            <input type="number" step="any" min="0" name="current_price" value="{{ data.dca.current_price }}" />
          </div>
        </div>
        <div class="row-inline">
          <button class="btn" type="submit">{{ t.add_order }}</button>
          {% if data.is_pro %}
            <a class="btn btn-ghost" href="{{ url_for('export_dca_csv') }}">{{ t.export_csv }}</a>
          {% endif %}
        </div>
      </form>

      {% if dca_notice %}
        <div class="warn">{{ dca_notice }}</div>
      {% endif %}

      <div class="results">
        <div class="stat">
          <div class="lbl">{{ t.avg_price }}</div>
          <div class="val">${{ "{:,.2f}".format(dca_res.avg_price) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.total_invested }}</div>
          <div class="val">${{ "{:,.2f}".format(dca_res.total_invested) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.total_units }}</div>
          <div class="val">{{ "{:.6f}".format(dca_res.total_units) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.unrealized }}</div>
          <div class="val {{ 'pos' if dca_res.unrealized > 0 else ('neg' if dca_res.unrealized < 0 else '') }}">${{ "{:,.2f}".format(dca_res.unrealized) }}</div>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{{ t.th_step }}</th>
              <th>{{ t.th_price }}</th>
              <th>{{ t.th_amount }}</th>
              <th>{{ t.th_units }}</th>
              <th>{{ t.th_action }}</th>
            </tr>
          </thead>
          <tbody>
            {% for row in dca_res.rows %}
            <tr>
              <td>{{ row.step }}</td>
              <td>${{ "{:,.2f}".format(row.price) }}</td>
              <td>${{ "{:,.2f}".format(row.amount) }}</td>
              <td>{{ "{:.6f}".format(row.units) }}</td>
              <td>
                <form method="POST" action="{{ url_for('delete_dca_route', idx=loop.index0) }}">
                  <button class="btn btn-ghost" type="submit">{{ t.delete }}</button>
                </form>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
    {% endif %}

    {% if data.tab == 'risk' %}
    <div class="card">
      <form method="POST" action="{{ url_for('calc_risk_route') }}">
        <div class="grid-2">
          <div class="field">
            <label>{{ t.balance }}</label>
            <input type="number" step="any" min="0" name="balance" value="{{ data.risk.balance }}" required />
          </div>
          <div class="field">
            <label>{{ t.risk_pct }}</label>
            <input type="number" step="any" min="0" max="100" name="risk_pct" value="{{ data.risk.risk_pct }}" required />
          </div>
          <div class="field">
            <label>{{ t.entry }}</label>
            <input type="number" step="any" min="0.01" name="entry" value="{{ data.risk.entry }}" required />
          </div>
          <div class="field">
            <label>{{ t.stop }}</label>
            <input type="number" step="any" min="0" name="stop" value="{{ data.risk.stop }}" required />
          </div>
          <div class="field">
            <label>{{ t.target }}</label>
            <input type="number" step="any" min="0" name="target" value="{{ data.risk.target }}" required />
          </div>
        </div>
        <div class="row-inline">
          <button class="btn" type="submit">{{ t.calc_btn }}</button>
        </div>
      </form>

      <div class="results">
        <div class="stat">
          <div class="lbl">{{ t.max_risk }}</div>
          <div class="val neg">${{ "{:,.2f}".format(risk_res.max_risk) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.pos_size }}</div>
          <div class="val">${{ "{:,.2f}".format(risk_res.pos_size) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.pos_units }}</div>
          <div class="val">{{ "{:.6f}".format(risk_res.pos_units) }}</div>
        </div>
        <div class="stat">
          <div class="lbl">{{ t.rr }}</div>
          <div class="val pos">{{ "{:.2f}".format(risk_res.rr) }} R</div>
        </div>
      </div>
    </div>
    {% endif %}

    <div class="card">
      <h1>{{ t.pro_box_title }}</h1>
      <div class="sub">{{ t.pro_box_desc }}</div>
      <div class="wallet-box">
        <strong>{{ t.wallet_label }}</strong> <span dir="ltr">{{ wallet_address }}</span>
      </div>
      <form method="POST" action="{{ url_for('activate_pro_route') }}" class="row-inline">
        <input type="text" name="license_code" placeholder="{{ t.pro_placeholder }}" style="max-width: 320px;" required />
        <button class="btn" type="submit">{{ t.pro_activate }}</button>
      </form>
      {% if pro_status == 'ok' %}
        <div class="msg-ok">{{ t.pro_activated_msg }}</div>
      {% elif pro_status == 'err' %}
        <div class="msg-err">{{ t.pro_invalid_msg }}</div>
      {% endif %}

      <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #27345d;">
        <h2>{{ t.gen_title }}</h2>
        <form method="POST" action="{{ url_for('generate_key_route') }}" class="row-inline">
          <input type="text" name="buyer_ref" placeholder="{{ t.gen_placeholder }}" style="max-width: 240px;" required />
          <input type="password" name="admin_secret" placeholder="{{ t.gen_secret_placeholder }}" style="max-width: 200px;" required />
          <button class="btn btn-ghost" type="submit">{{ t.gen_btn }}</button>
        </form>
        {% if gen_error %}
          <div class="msg-err">{{ t.gen_err_msg }}</div>
        {% elif generated_key %}
          <div class="msg-ok" dir="ltr">Generated Key: <strong>{{ generated_key }}</strong></div>
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>
"""


def load_state() -> dict:
    state = json.loads(json.dumps(DEFAULT_DATA))
    if DATA_FILE.exists():
        try:
            saved = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                if saved.get("lang") in ("en", "fa"):
                    state["lang"] = saved["lang"]
                if saved.get("tab") in ("profit", "dca", "risk"):
                    state["tab"] = saved["tab"]
                if isinstance(saved.get("profit"), dict):
                    state["profit"].update(saved["profit"])
                if isinstance(saved.get("dca"), dict):
                    state["dca"]["current_price"] = float(saved["dca"].get("current_price", state["dca"]["current_price"]))
                    if isinstance(saved["dca"].get("orders"), list):
                        state["dca"]["orders"] = saved["dca"]["orders"]
                if isinstance(saved.get("risk"), dict):
                    state["risk"].update(saved["risk"])
        except Exception:
            pass
    state["is_pro"] = bool(session.get("is_pro", False))
    state["active_license"] = str(session.get("active_license", ""))
    return state


def save_state(state: dict) -> None:
    to_save = {
        "lang": state["lang"],
        "tab": state["tab"],
        "profit": state["profit"],
        "dca": state["dca"],
        "risk": state["risk"],
    }
    DATA_FILE.write_text(json.dumps(to_save, indent=2, ensure_ascii=False), encoding="utf-8")


def compute_profit(p: dict) -> dict:
    buy = max(0.01, float(p["buy_price"]))
    sell = max(0.0, float(p["sell_price"]))
    invest = max(0.01, float(p["invest"]))
    fee_rate = max(0.0, float(p["fee_pct"])) / 100.0

    buy_fee = invest * fee_rate
    net_invest = invest - buy_fee
    units = net_invest / buy
    gross_proceeds = units * sell
    sell_fee = gross_proceeds * fee_rate
    net_proceeds = gross_proceeds - sell_fee
    net_profit = net_proceeds - invest
    roi = (net_profit / invest) * 100.0
    total_fees = buy_fee + sell_fee
    denom = units * (1.0 - fee_rate)
    break_even = (invest / denom) if denom > 0 else 0.0

    return {
        "net_profit": net_profit,
        "roi": roi,
        "total_fees": total_fees,
        "break_even": break_even,
    }


def compute_dca(dca: dict) -> dict:
    rows = []
    total_invested = 0.0
    total_units = 0.0
    for idx, item in enumerate(dca["orders"], start=1):
        price = max(0.01, float(item.get("price", 0)))
        amount = max(0.0, float(item.get("amount", 0)))
        units = amount / price
        total_invested += amount
        total_units += units
        rows.append({"step": idx, "price": price, "amount": amount, "units": units})

    avg_price = (total_invested / total_units) if total_units > 0 else 0.0
    current_price = max(0.0, float(dca.get("current_price", 0)))
    unrealized = (total_units * current_price) - total_invested
    return {
        "rows": rows,
        "avg_price": avg_price,
        "total_invested": total_invested,
        "total_units": total_units,
        "unrealized": unrealized,
    }


def compute_risk(r: dict) -> dict:
    balance = max(0.0, float(r["balance"]))
    risk_pct = max(0.0, float(r["risk_pct"]))
    entry = max(0.01, float(r["entry"]))
    stop = max(0.0, float(r["stop"]))
    target = max(0.0, float(r["target"]))

    max_risk = balance * (risk_pct / 100.0)
    risk_per_unit = abs(entry - stop)
    pos_units = (max_risk / risk_per_unit) if risk_per_unit > 0 else 0.0
    pos_size = pos_units * entry
    reward_per_unit = abs(target - entry)
    rr = (reward_per_unit / risk_per_unit) if (risk_per_unit > 0 and target > 0) else 0.0

    return {
        "max_risk": max_risk,
        "pos_size": pos_size,
        "pos_units": pos_units,
        "rr": rr,
    }


def render_page(
    state: dict,
    dca_notice: str = "",
    pro_status: str = "",
    generated_key: str = "",
    gen_error: bool = False,
) -> str:
    lang = state["lang"] if state["lang"] in TEXTS else "en"
    return render_template_string(
        PAGE_HTML,
        lang=lang,
        t=TEXTS[lang],
        data=state,
        wallet_address=RECEIVE_WALLET_ADDRESS,
        profit_res=compute_profit(state["profit"]),
        dca_res=compute_dca(state["dca"]),
        risk_res=compute_risk(state["risk"]),
        dca_notice=dca_notice,
        pro_status=pro_status,
        generated_key=generated_key,
        gen_error=gen_error,
    )


@app.route("/", methods=["GET"])
def index():
    return render_page(load_state())


@app.route("/toggle-lang", methods=["POST"])
def toggle_lang():
    state = load_state()
    state["lang"] = "fa" if state["lang"] == "en" else "en"
    save_state(state)
    return redirect(url_for("index"))


@app.route("/switch-tab", methods=["POST"])
def switch_tab():
    state = load_state()
    tab = request.form.get("tab", "profit")
    if tab in ("profit", "dca", "risk"):
        state["tab"] = tab
        save_state(state)
    return redirect(url_for("index"))


@app.route("/calc-profit", methods=["POST"])
def calc_profit_route():
    state = load_state()
    state["tab"] = "profit"
    try:
        state["profit"]["buy_price"] = max(0.01, float(request.form["buy_price"]))
        state["profit"]["sell_price"] = max(0.0, float(request.form["sell_price"]))
        state["profit"]["invest"] = max(0.01, float(request.form["invest"]))
        state["profit"]["fee_pct"] = max(0.0, float(request.form["fee_pct"]))
        save_state(state)
    except (KeyError, ValueError):
        pass
    return redirect(url_for("index"))


@app.route("/add-dca", methods=["POST"])
def add_dca_route():
    state = load_state()
    state["tab"] = "dca"
    try:
        current_price = max(0.0, float(request.form.get("current_price", state["dca"]["current_price"]) or 0))
        state["dca"]["current_price"] = current_price

        if not state["is_pro"] and len(state["dca"]["orders"]) >= FREE_DCA_LIMIT:
            save_state(state)
            return render_page(state, dca_notice=TEXTS[state["lang"]]["dca_limit_warn"])

        price = float(request.form["dca_price"])
        amount = float(request.form["dca_amount"])
        if price > 0 and amount > 0:
            state["dca"]["orders"].append({"price": price, "amount": amount})
            save_state(state)
    except (KeyError, ValueError):
        pass
    return redirect(url_for("index"))


@app.route("/delete-dca/<int:idx>", methods=["POST"])
def delete_dca_route(idx: int):
    state = load_state()
    state["tab"] = "dca"
    if 0 <= idx < len(state["dca"]["orders"]):
        state["dca"]["orders"].pop(idx)
        save_state(state)
    return redirect(url_for("index"))


@app.route("/export-dca.csv", methods=["GET"])
def export_dca_csv():
    state = load_state()
    if not state["is_pro"]:
        return redirect(url_for("index"))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Step", "Price_USD", "Amount_USD", "Units"])
    for idx, item in enumerate(state["dca"]["orders"], start=1):
        price = max(0.01, float(item.get("price", 0)))
        amount = max(0.0, float(item.get("amount", 0)))
        writer.writerow([idx, price, amount, f"{amount / price:.8f}"])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=dca_plan.csv"},
    )


@app.route("/calc-risk", methods=["POST"])
def calc_risk_route():
    state = load_state()
    state["tab"] = "risk"
    try:
        state["risk"]["balance"] = max(0.0, float(request.form["balance"]))
        state["risk"]["risk_pct"] = max(0.0, min(100.0, float(request.form["risk_pct"])))
        state["risk"]["entry"] = max(0.01, float(request.form["entry"]))
        state["risk"]["stop"] = max(0.0, float(request.form["stop"]))
        state["risk"]["target"] = max(0.0, float(request.form["target"]))
        save_state(state)
    except (KeyError, ValueError):
        pass
    return redirect(url_for("index"))


@app.route("/activate-pro", methods=["POST"])
def activate_pro_route():
    code = (request.form.get("license_code") or "").strip().upper()
    if is_valid_license(code):
        session["is_pro"] = True
        session["active_license"] = code
        return render_page(load_state(), pro_status="ok")
    return render_page(load_state(), pro_status="err")


@app.route("/deactivate-pro", methods=["POST"])
def deactivate_pro_route():
    session.pop("is_pro", None)
    session.pop("active_license", None)
    return redirect(url_for("index"))


@app.route("/generate-key", methods=["POST"])
def generate_key_route():
    state = load_state()
    buyer_ref = (request.form.get("buyer_ref") or "").strip()
    provided_secret = (request.form.get("admin_secret") or "").strip()

    if not ADMIN_SECRET or provided_secret != ADMIN_SECRET:
        return render_page(state, gen_error=True)

    generated = generate_license_key(buyer_ref) if buyer_ref else ""
    return render_page(state, generated_key=generated)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)