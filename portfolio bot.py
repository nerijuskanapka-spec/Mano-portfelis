import requests
import json
from datetime import datetime

# === KONFIGŪRACIJA ===
TELEGRAM_TOKEN = "8881877688:AAECdVW10E04_B5pZ8o4wiJPNyvjaHY3MVc"
CHAT_ID = "30001006"
FINNHUB_KEY = "d85v07pr01qmuqqbm26gd85v07pr01qmuqqbm270"

# Portfelis
PORTFOLIO = [
    {"ticker": "O",    "name": "Realty Income",        "weight": 8.47,  "div_yield": 6.0,  "alert_drop": 3.0},
    {"ticker": "PEP",  "name": "PepsiCo",              "weight": 7.44,  "div_yield": 4.0,  "alert_drop": 3.0},
    {"ticker": "CSWC", "name": "Capital Southwest",    "weight": 7.13,  "div_yield": 11.0, "alert_drop": 4.0},
    {"ticker": "VICI", "name": "VICI Properties",      "weight": 5.41,  "div_yield": 6.0,  "alert_drop": 3.0},
    {"ticker": "ARCC", "name": "Ares Capital",         "weight": 5.06,  "div_yield": 10.2, "alert_drop": 4.0},
    {"ticker": "MAIN", "name": "Main Street Capital",  "weight": 4.23,  "div_yield": 7.0,  "alert_drop": 3.0},
    {"ticker": "OHI",  "name": "Omega Healthcare",     "weight": 4.15,  "div_yield": 8.0,  "alert_drop": 3.0},
    {"ticker": "PFE",  "name": "Pfizer",               "weight": 3.04,  "div_yield": 7.0,  "alert_drop": 3.0},
    {"ticker": "OBDC", "name": "Blue Owl Capital",     "weight": 2.72,  "div_yield": 10.0, "alert_drop": 4.0},
    {"ticker": "ENB",  "name": "Enbridge",             "weight": 2.60,  "div_yield": 7.0,  "alert_drop": 3.0},
    {"ticker": "T",    "name": "AT&T",                 "weight": 2.55,  "div_yield": 5.0,  "alert_drop": 3.0},
    {"ticker": "LGEN.L","name": "Legal & General",     "weight": 10.83, "div_yield": 9.0,  "alert_drop": 3.0},
]

PORTFOLIO_VALUE = 34328  # EUR

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def get_quote(ticker):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=10)
        d = r.json()
        if d and d.get("c") and d["c"] > 0:
            return {"price": d["c"], "change_pct": d["dp"], "change": d["d"]}
    except:
        pass
    return None

def morning_report():
    """Rytinė portfelio apžvalga"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"🌅 <b>Portfelio apžvalga</b>\n📅 {now}\n"]
    
    total_pnl = 0
    alerts = []
    
    for p in PORTFOLIO:
        q = get_quote(p["ticker"])
        if q:
            pct = q["change_pct"] or 0
            pos_value = PORTFOLIO_VALUE * p["weight"] / 100
            pnl = pos_value * pct / 100
            total_pnl += pnl
            
            emoji = "🟢" if pct >= 0 else "🔴"
            sign = "+" if pct >= 0 else ""
            lines.append(f"{emoji} <b>{p['name']}</b> ({p['ticker']})")
            lines.append(f"   ${q['price']:.2f} | {sign}{pct:.2f}% | {sign}€{pnl:.0f}")
            
            # Ispėjimas jei krenta per daug
            if pct <= -p["alert_drop"]:
                alerts.append(f"⚠️ {p['name']}: -{abs(pct):.1f}%")
    
    # Bendras P&L
    sign = "+" if total_pnl >= 0 else ""
    lines.append(f"\n💼 <b>Šiandienos P&L: {sign}€{total_pnl:.0f}</b>")
    
    # Ispėjimai
    if alerts:
        lines.append("\n🚨 <b>ĮSPĖJIMAI:</b>")
        lines.extend(alerts)
    
    send_telegram("\n".join(lines))

def check_alerts():
    """Tikrina įspėjimus per dieną"""
    alerts = []
    
    for p in PORTFOLIO:
        q = get_quote(p["ticker"])
        if q:
            pct = q["change_pct"] or 0
            if pct <= -p["alert_drop"]:
                alerts.append(
                    f"🚨 <b>{p['name']}</b> ({p['ticker']})\n"
                    f"   Kaina: ${q['price']:.2f}\n"
                    f"   Kritimas: -{abs(pct):.2f}%"
                )
    
    if alerts:
        msg = "⚠️ <b>PORTFELIO ĮSPĖJIMAI</b>\n\n" + "\n\n".join(alerts)
        send_telegram(msg)
    else:
        print("Nėra įspėjimų")

def weekly_summary():
    """Savaitės apžvalga penktadienį"""
    lines = ["📊 <b>Savaitės portfelio apžvalga</b>\n"]
    
    total_div = sum(p["weight"] / 100 * p["div_yield"] for p in PORTFOLIO)
    monthly = PORTFOLIO_VALUE * total_div / 100 / 12
    annual = PORTFOLIO_VALUE * total_div / 100
    
    lines.append(f"💰 Dividendų pajamingumas: <b>{total_div:.2f}%</b>")
    lines.append(f"📅 Mėnesio pajamos: <b>€{monthly:.0f}</b>")
    lines.append(f"📈 Metinės pajamos: <b>€{annual:.0f}</b>")
    lines.append(f"\n🏆 <b>Top dividendai:</b>")
    
    top = sorted(PORTFOLIO, key=lambda x: x["div_yield"], reverse=True)[:5]
    for p in top:
        lines.append(f"   • {p['name']}: {p['div_yield']}%")
    
    send_telegram("\n".join(lines))

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    
    if mode == "morning":
        morning_report()
    elif mode == "alert":
        check_alerts()
    elif mode == "weekly":
        weekly_summary()
    else:
        morning_report()
