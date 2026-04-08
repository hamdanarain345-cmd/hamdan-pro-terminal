import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_option_menu import option_menu
from datetime import datetime, timezone, timedelta
import math
import time
import os
import random 

# --- TWILIO SMS SETUP ---
try:
    from twilio.rest import Client
    TWILIO_INSTALLED = True
    # Yahan Streamlit ke 'Secrets' use kiye hain taake password safe rahay
    TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
    TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
except Exception as e:
    TWILIO_INSTALLED = False

TWILIO_SENDER_NUMBER = '+15186349627'
MY_PHONE_NUMBERS = ['+923136538984', '+923153745987']

def send_sms_alert(coin, signal, price):
    if not TWILIO_INSTALLED: return
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        for number in MY_PHONE_NUMBERS:
            client.messages.create(body=f"🚨 HAMDAN PRO ALERT: {coin} - {signal} Setup Confirmed! Entry Price: {price}", from_=TWILIO_SENDER_NUMBER, to=number)
    except Exception as e: pass

# --- 1. Page Configuration & Custom CSS ---
st.set_page_config(page_title="Hamdan Pro Terminal", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# --- PERMANENT STORAGE SYSTEM ---
TRADE_FILE = "live_trades_journal.csv"
BACKTEST_FILE = "backtest_reports_journal.csv"
LEARNING_FILE = "learning_journal.csv"

def load_saved_data(filename):
    if os.path.exists(filename): return pd.read_csv(filename).to_dict('records')
    return []

def save_permanent_data(data_list, filename):
    if len(data_list) > 0: pd.DataFrame(data_list).to_csv(filename, index=False)

if 'trade_history' not in st.session_state: st.session_state['trade_history'] = load_saved_data(TRADE_FILE)
if 'backtest_history' not in st.session_state: st.session_state['backtest_history'] = load_saved_data(BACKTEST_FILE)
if 'learning_history' not in st.session_state: st.session_state['learning_history'] = load_saved_data(LEARNING_FILE)

st.markdown("""
    <style>
    .main {background-color: #0b0e14;}
    h1, h2, h3, h4, h5 {color: #EAECEF;}
    div[data-testid="stMetricValue"] {color: #EAECEF;} 
    .signal-box {background-color: #2B3139; padding: 25px; border-radius: 12px; text-align: center; margin-top: 20px; border: 2px solid #3b424d;}
    .trade-card {background-color: #1a1e23; padding: 15px; border-radius: 8px; text-align: left; margin-top: 15px; border-left: 5px solid #0ECB81;}
    .recommendation-box {background-color: #1E2329; padding: 15px; border-radius: 10px; border: 1px solid #3b424d; margin-bottom: 20px;}
    .news-card {background-color: #1E2329; padding: 20px; border-radius: 10px; border-left: 5px solid #F3BA2F; margin-bottom: 15px;}
    .lesson-card {background-color: #1a1e23; padding: 20px; border-radius: 10px; border-left: 5px solid #0ECB81; margin-bottom: 15px;}
    .book-card {background-color: #1E2329; padding: 20px; border-radius: 10px; border-left: 5px solid #F6465D; margin-bottom: 15px;}
    .pattern-card {background-color: #1E2329; padding: 15px; border-radius: 8px; border: 1px solid #3b424d; margin-bottom: 15px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

HEADERS = {'User-Agent': 'Mozilla/5.0'}

PRO_LISTS = {
    "👑 Titans (Most Stable)": ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'],
    "🚀 Layer-1/2 (Smooth Trend)": ['SUIUSDT', 'APTUSDT', 'SEIUSDT', 'INJUSDT', 'AVAXUSDT', 'NEARUSDT', 'FTMUSDT', 'ARBUSDT', 'OPUSDT', 'POLUSDT', 'TIAUSDT', 'ADAUSDT', 'DOTUSDT'],
    "🤖 AI (High Vol)": ['TAOUSDT', 'FETUSDT', 'RNDRUSDT', 'ARKMUSDT', 'AGIXUSDT', 'WLDUSDT', 'OCEANUSDT'],
    "🏦 DeFi (Tech Moves)": ['LINKUSDT', 'UNIUSDT', 'AAVEUSDT', 'RUNEUSDT', 'MKRUSDT', 'SNXUSDT', 'LDOUSDT'],
    "🐕 Memes (High Risk)": ['DOGEUSDT', 'PEPEUSDT', 'WIFUSDT', 'FLOKIUSDT', 'BONKUSDT', 'BOMEUSDT', 'SHIBUSDT']
}

def get_coin_category(symbol):
    for cat, coins in PRO_LISTS.items():
        if symbol in coins: return cat
    return "⚪ Normal / Unverified"

# --- Data Functions ---
@st.cache_data(ttl=60)
def fetch_gold_silver():
    try:
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        silver = yf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
        return float(gold), float(silver)
    except: return 0.0, 0.0

@st.cache_data(ttl=60)
def fetch_fear_and_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()
        return int(res['data'][0]['value']), res['data'][0]['value_classification']
    except: return 50, "Neutral"

@st.cache_data(ttl=60)
def fetch_all_crypto():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", headers=HEADERS, timeout=10).json()
        df = pd.DataFrame(res)[['symbol', 'lastPrice', 'priceChangePercent', 'volume']]
        df.columns = ['Pair', 'Price (USD)', '24h Change (%)', 'Volume']
        for col in ['Price (USD)', '24h Change (%)', 'Volume']: df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna()
    except: return pd.DataFrame()

def get_retail_whale_limit(symbol): return 10000 if symbol in ['BTCUSDT', 'ETHUSDT'] else 500 if symbol in ['PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT'] else 2000

# --- Indicators ---
def calculate_rsi(prices_series, period=14):
    if len(prices_series) < period: return 50
    deltas = prices_series.diff(); gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean(); rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(prices_series, period=50): return prices_series.ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']; high_close = (df['high'] - df['close'].shift()).abs(); low_close = (df['low'] - df['close'].shift()).abs()
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(window=period).mean().iloc[-1]

def fmt_p(price): return f"${price:,.8f}" if price < 0.01 else f"${price:,.4f}"

def get_market_session_pkt():
    hour = (datetime.now(timezone.utc) + timedelta(hours=5)).hour
    if 5 <= hour < 12: return "Tokyo Open 🇯🇵 (Low Volatility)"
    elif 12 <= hour < 17: return "London Open 🇬🇧 (Medium Volatility)"
    elif 17 <= hour < 21: return "London + NY Overlap 🇬🇧🇺🇸 (MAX VOLATILITY - Golden Hours)"
    elif 21 <= hour < 2: return "New York Open 🇺🇸 (High Volatility)"
    else: return "Sydney/Asian 🇦🇺 (Dead Zone)"

def fetch_klines_safe(symbol, interval, limit):
    try:
        res = requests.get(f"https://api.mexc.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}", timeout=5).json()
        if not isinstance(res, list) or len(res) == 0: return None
        df_raw = pd.DataFrame(res)
        return pd.DataFrame({'time': df_raw.iloc[:, 0].astype(float), 'open': df_raw.iloc[:, 1].astype(float), 'high': df_raw.iloc[:, 2].astype(float), 'low': df_raw.iloc[:, 3].astype(float), 'close': df_raw.iloc[:, 4].astype(float)})
    except: return None

def fetch_deep_history(symbol, interval='15m', loops=36):
    all_data = []; end_time = None
    for _ in range(loops):
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit=1000"
        if end_time: url += f"&endTime={end_time}"
        try:
            res = requests.get(url, timeout=5).json()
            if not res or not isinstance(res, list) or 'code' in res: break
            all_data.append(pd.DataFrame(res)); end_time = int(pd.DataFrame(res).iloc[0, 0]) - 1; time.sleep(0.1) 
        except: break
    if not all_data: return None
    combined = pd.concat(all_data).drop_duplicates(subset=[0]).sort_values(by=0).reset_index(drop=True)
    return pd.DataFrame({'time': combined.iloc[:, 0].astype(float), 'open': combined.iloc[:, 1].astype(float), 'high': combined.iloc[:, 2].astype(float), 'low': combined.iloc[:, 3].astype(float), 'close': combined.iloc[:, 4].astype(float)})

@st.cache_data(ttl=60) 
def pro_intraday_analyzer(symbol):
    whale_limit_usd = get_retail_whale_limit(symbol); trades_url = f"https://api.mexc.com/api/v3/trades?symbol={symbol.upper()}&limit=1000"
    try:
        t_res = requests.get(trades_url, timeout=5).json()
        buy_vol, sell_vol, b_count, s_count = 0, 0, 0, 0
        if isinstance(t_res, list):
            for t in t_res:
                val = float(t['price']) * float(t['qty'])
                if val >= whale_limit_usd:
                    if t['isBuyerMaker']: sell_vol += val; s_count += 1
                    else: buy_vol += val; b_count += 1
        df_4h = fetch_klines_safe(symbol, '4h', 60); df_15m = fetch_klines_safe(symbol, '15m', 100); df_5m = fetch_klines_safe(symbol, '5m', 60)
        if df_4h is None or df_15m is None or df_5m is None: return None, "Kline Error"

        ema_50_4h = calculate_ema(df_4h['close'], 50).iloc[-2]; trend_4h = "UP" if df_4h['close'].iloc[-2] > ema_50_4h else "DOWN"
        rsi_15m = calculate_rsi(df_15m['close']).iloc[-2]; ema_50_15m = calculate_ema(df_15m['close'], 50).iloc[-2]
        atr_15m = calculate_atr(df_15m); trend_15m = "UP" if df_15m['close'].iloc[-2] > ema_50_15m else "DOWN"
        rsi_5m = calculate_rsi(df_5m['close']).iloc[-2]

        total_vol = buy_vol + sell_vol; buy_pct = (buy_vol / total_vol * 100) if total_vol > 0 else 50
        current_price = df_15m['close'].iloc[-1] 
        whale_status = "🐋 WHALE PUMP" if buy_pct >= 60 else "🐋 WHALE DUMP" if buy_pct <= 40 else "🐟 RETAIL NOISE"
        
        score = 0; signal_type = "NONE"
        if trend_4h == "UP" and trend_15m == "UP" and buy_pct >= 60 and 40 <= rsi_15m <= 65 and rsi_5m > 40: score = 100; signal_type = "LONG"
        elif trend_4h == "DOWN" and trend_15m == "DOWN" and buy_pct <= 40 and 35 <= rsi_15m <= 60 and rsi_5m < 60: score = -100; signal_type = "SHORT"
        
        return {"symbol": symbol, "buy_pct": buy_pct, "rsi_15m": rsi_15m, "price": current_price, "trend_4h": trend_4h, "trend_15m": trend_15m, "atr": atr_15m, "score": score, "signal": signal_type, "whale_status": whale_status}, None
    except Exception as e: return None, f"API Fetch Error: {str(e)}"

@st.cache_data(ttl=600)
def run_pro_backtest(symbol, capital, risk_pct, target_rr, loops=36):
    df = fetch_deep_history(symbol, '15m', loops) 
    if df is None: return None
    df['ema50'] = calculate_ema(df['close'], 50); df['rsi'] = calculate_rsi(df['close']); df['atr'] = calculate_atr(df)
    df['pkt_time'] = pd.to_datetime(df['time'], unit='ms') + pd.Timedelta(hours=5)
    df['hour'] = df['pkt_time'].dt.hour; df['day_of_week'] = df['pkt_time'].dt.day_name()
    
    wins_5to9, losses_5to9, pnl_5to9 = 0, 0, 0.0
    wins_other, losses_other, pnl_other = 0, 0, 0.0
    hour_perf = {h: {'wins': 0, 'losses': 0} for h in range(24)}; day_perf = {d: {'wins': 0, 'losses': 0} for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    risk_usd = capital * (risk_pct / 100)
    
    for i in range(50, len(df)-8):
        c_close, ema, rsi, atr = df['close'].iloc[i], df['ema50'].iloc[i], df['rsi'].iloc[i], df['atr'].iloc[i]
        c_hour, c_day = df['hour'].iloc[i], df['day_of_week'].iloc[i]
        is_golden = (17 <= c_hour <= 21); win_det, loss_det, pnl_chg = False, False, 0
        sl_dist = 1.5 * atr; tp_dist = sl_dist * target_rr
        
        if c_close > ema and 45 <= rsi <= 60: 
            tp, sl = c_close + tp_dist, c_close - sl_dist
            f_high, f_low = df['high'].iloc[i+1:i+8].max(), df['low'].iloc[i+1:i+8].min()
            if f_high >= tp: win_det = True; pnl_chg = (risk_usd * target_rr)
            elif f_low <= sl: loss_det = True; pnl_chg = -risk_usd
        elif c_close < ema and 40 <= rsi <= 55: 
            tp, sl = c_close - tp_dist, c_close + sl_dist
            f_low, f_high = df['low'].iloc[i+1:i+8].min(), df['high'].iloc[i+1:i+8].max()
            if f_low <= tp: win_det = True; pnl_chg = (risk_usd * target_rr)
            elif f_high >= sl: loss_det = True; pnl_chg = -risk_usd
        
        if win_det:
            hour_perf[c_hour]['wins'] += 1; day_perf[c_day]['wins'] += 1
            if is_golden: wins_5to9 += 1; pnl_5to9 += pnl_chg
            else: wins_other += 1; pnl_other += pnl_chg
        elif loss_det:
            hour_perf[c_hour]['losses'] += 1; day_perf[c_day]['losses'] += 1
            if is_golden: losses_5to9 += 1; pnl_5to9 += pnl_chg
            else: losses_other += 1; pnl_other += pnl_chg

    best_hr, best_w_rate = 0, 0
    for h, s in hour_perf.items():
        t = s['wins'] + s['losses']
        if t > 5 and (s['wins']/t*100) > best_w_rate: best_w_rate = (s['wins']/t*100); best_hr = h

    best_d, best_d_rate = "None", 0
    for d, s in day_perf.items():
        t = s['wins'] + s['losses']
        if t > 5 and (s['wins']/t*100) > best_d_rate: best_d_rate = (s['wins']/t*100); best_d = d
                
    return {"golden": {"wins": wins_5to9, "losses": losses_5to9, "pnl": pnl_5to9}, "other": {"wins": wins_other, "losses": losses_other, "pnl": pnl_other}, "best_hour": best_hr, "best_win_rate": best_w_rate, "best_day": best_d, "best_day_win_rate": best_d_rate, "total_candles_analyzed": len(df), "risk_amt": risk_usd, "reward_amt": risk_usd * target_rr}

def color_change(val): return 'color: #0ECB81; font-weight: bold;' if val > 0 else 'color: #F6465D; font-weight: bold;' if val < 0 else 'color: white;'
def highlight_recommendation(val): return 'background-color: rgba(243, 186, 47, 0.2); font-weight: bold; color: #F3BA2F;' if "🔥" in str(val) else ''

# --- 4. Navigation Bar ---
selected = option_menu(
    menu_title=None, 
    options=["Market", "⚡ Screener", "🎯 Engine", "🧪 Backtester", "📈 Pattern Book", "🧠 Pro Academy", "📓 Journal"], 
    icons=["house", "search", "bullseye", "database", "bar-chart-line", "book", "journal-bookmark"], 
    menu_icon="cast", default_index=4, orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#1E2329"},
        "icon": {"color": "#F3BA2F", "font-size": "14px"}, 
        "nav-link": {"color": "white", "font-size": "13px", "text-align": "center", "margin":"0px"},
        "nav-link-selected": {"background-color": "#F3BA2F", "color": "black", "font-weight": "bold"},
    }
)

# --- 5. Pages Logic ---
if selected == "Market":
    st.title("📊 Global Market Overview")
    gold_price, silver_price = fetch_gold_silver()
    fng_value, fng_class = fetch_fear_and_greed()
    market_df = fetch_all_crypto()
    fng_color = "#F6465D" if fng_value < 45 else "#0ECB81" if fng_value > 55 else "#F3BA2F"
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f"<h3 style='text-align: center; color: {fng_color};'>{fng_value}/100</h3><p style='text-align: center;'>Sentiment: {fng_class}</p>", unsafe_allow_html=True)
    col2.metric("🥇 Gold", fmt_p(gold_price))
    col3.metric("🥈 Silver", fmt_p(silver_price))
    if not market_df.empty: col4.metric("🟠 Bitcoin (BTC)", fmt_p(market_df[market_df['Pair'] == 'BTCUSDT']['Price (USD)'].values[0]))

elif selected == "⚡ Screener":
    st.title("⚡ AI Smart Coin Screener")
    market_df = fetch_all_crypto()
    if not market_df.empty:
        ignore_list = ['USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT']
        df_filtered = market_df[market_df['Pair'].str.endswith('USDT') & (~market_df['Pair'].isin(ignore_list))].copy()
        df_filtered['Category'] = df_filtered['Pair'].apply(get_coin_category)
        def get_rec(row): return "🔥 Best for Today" if row['Category'] != "⚪ Normal / Unverified" and row['Volume'] > 50000000 else "✅ Stable Choice" if row['Category'] != "⚪ Normal / Unverified" else "⚠️ Avoid / Risky"
        df_filtered['AI Recommendation'] = df_filtered.apply(get_rec, axis=1)
        df_filtered = df_filtered.sort_values(by='Volume', ascending=False)
        c1, c2 = st.columns([1, 2])
        with c1: view_filter = st.radio("Display Filter:", ["Top 50 Pro Coins (Safe)", "All Market Coins (Risky)"])
        display_df = df_filtered[df_filtered['Category'] != "⚪ Normal / Unverified"] if view_filter == "Top 50 Pro Coins (Safe)" else df_filtered
        st.dataframe(display_df[['Pair', 'Price (USD)', '24h Change (%)', 'Volume', 'Category', 'AI Recommendation']].style.map(color_change, subset=['24h Change (%)']).map(highlight_recommendation, subset=['AI Recommendation']).format({'Price (USD)': '${:,.6f}', '24h Change (%)': '{:,.2f}%', 'Volume': '{:,.0f}'}), use_container_width=True, height=700, hide_index=True)

elif selected == "🎯 Engine":
    st.title("🎯 Stable Multi-Timeframe Trade Planner")
    current_session = get_market_session_pkt()
    st.markdown(f"<div style='text-align:center; padding: 10px; background-color:#1E2329; border-radius:10px; border-bottom: 3px solid #0ECB81;'>🌍 Current Market Status: <b>{current_session}</b></div><br>", unsafe_allow_html=True)
    
    st.subheader("📡 Quick Engine (Top 8 High-Volume Coins)")
    market_df = fetch_all_crypto()
    top_watch_list = ["BTCUSDT", "ETHUSDT", "SUIUSDT", "SOLUSDT", "PEPEUSDT", "WIFUSDT", "DOGEUSDT", "XRPUSDT"]
    if not market_df.empty:
        ignore_list = ['USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT']
        top_watch_list = market_df[market_df['Pair'].str.endswith('USDT') & (~market_df['Pair'].isin(ignore_list))].sort_values(by='Volume', ascending=False).head(8)['Pair'].tolist()
    
    scan_cols = st.columns(4)
    best_coin_found = None
    for i, symbol in enumerate(top_watch_list):
        data, err = pro_intraday_analyzer(symbol) 
        if data:
            box_color = "#0ECB81" if data['score'] == 100 else "#F6465D" if data['score'] == -100 else "#3b424d"
            signal_text = "🟢 BUY SETUP" if data['score'] == 100 else "🔴 SELL SETUP" if data['score'] == -100 else "⚪ WAITING"
            whale_color = "#F3BA2F" if "PUMP" in data['whale_status'] or "DUMP" in data['whale_status'] else "#848E9C"
            if data['score'] in [100, -100] and best_coin_found is None: best_coin_found = symbol
            with scan_cols[i % 4]:
                st.markdown(f"""<div class="recommendation-box" style="border-left: 4px solid {box_color};"><h5 style="margin:0;">{symbol}</h5><p style="margin:0; font-size: 14px;">Price: {fmt_p(data['price'])}</p><p style="margin:0; font-size: 12px; color: #848E9C;">4H Trend: <b>{data['trend_4h']}</b></p><p style="margin:0; font-size: 11px; font-weight: bold; color: {whale_color};">{data['whale_status']}</p><hr style="margin: 5px 0; border-color: #3b424d;"><p style="margin:0; font-size: 12px; font-weight: bold; color: {box_color};">{signal_text}</p></div>""", unsafe_allow_html=True)
                
    st.markdown("---")
    st.subheader("⚙️ Apni Trade Set Karein")
    all_pro_coins = sorted(list(set([coin for coins in PRO_LISTS.values() for coin in coins])))
    default_idx = all_pro_coins.index(best_coin_found) if best_coin_found and best_coin_found in all_pro_coins else all_pro_coins.index("SUIUSDT") if "SUIUSDT" in all_pro_coins else 0
    c1, c2, c3 = st.columns(3)
    with c1: target_coin = st.selectbox("Select Safe Coin:", all_pro_coins, index=default_idx)
    with c2: user_capital = st.number_input("Aapka Total Capital ($)", min_value=10.0, value=100.0, step=10.0)
    with c3: risk_pct = st.slider("Risk Per Trade (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
    
    if st.button("🚀 Analyze Setup & Save to Journal", type="primary"):
        with st.spinner(f"Running Strict Confluence Analysis for {target_coin}..."):
            data, error = pro_intraday_analyzer(target_coin)
            if error: st.error("⚠️ Data fetch error: " + error)
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Live Price", fmt_p(data['price']))
                m2.metric("📈 4H & 15m Trend", f"4H: {data['trend_4h']} | 15m: {data['trend_15m']}", delta_color="normal" if data['trend_4h'] == "UP" else "inverse")
                m3.metric("📊 Stable 15m RSI", f"{data['rsi_15m']:.1f}")
                m4.metric(f"{data['whale_status']}", f"{data['buy_pct']:.1f}% Buy", delta_color="normal" if data['buy_pct'] > 50 else "inverse")

                buy_pct, trend_4h, rsi_15m, price, atr = data['buy_pct'], data['trend_4h'], data['rsi_15m'], data['price'], data['atr']
                risk_amount_usd = user_capital * (risk_pct / 100); signal_type = data['signal']
                
                if signal_type == "LONG": box_color = "#0ECB81"; signal_msg = "🚀 CONFIRMED LONG"; send_sms_alert(target_coin, "LONG", fmt_p(price))
                elif signal_type == "SHORT": box_color = "#F6465D"; signal_msg = "📉 CONFIRMED SHORT"; send_sms_alert(target_coin, "SHORT", fmt_p(price))
                else: box_color = "#3b424d"; signal_msg = "⚖️ NO TRADE (Intezar karein)"

                st.markdown(f"<div class='signal-box' style='border-color: {box_color};'><h3 style='color: {box_color};'>{signal_msg}</h3></div>", unsafe_allow_html=True)
                sl_price, tp1_price = "-", "-"
                if signal_type != "NONE":
                    sl_price = price - (1.5 * atr) if signal_type == "LONG" else price + (1.5 * atr)
                    tp1_price = price + (3.0 * atr) if signal_type == "LONG" else price - (3.0 * atr)
                    sl_dist = max(abs(price - sl_price) / price, 0.001); pos_size = risk_amount_usd / sl_dist; lev = min(max(math.ceil(1.0 / (sl_dist * 1.5)), 1), 20); margin = pos_size / lev
                    st.markdown(f"""<div class="trade-card" style="border-left-color: {box_color};"><h4 style="color: {box_color};">🎯 Confirmed Trade Plan</h4><div style="display: flex; justify-content: space-between; margin-top: 15px;"><div><p style="color: #848E9C; margin:0;">Entry</p><h3>{fmt_p(price)}</h3></div><div><p style="color: #F6465D; margin:0;">Stop Loss</p><h3>{fmt_p(sl_price)}</h3></div><div><p style="color: #0ECB81; margin:0;">Target</p><h3>{fmt_p(tp1_price)}</h3></div></div><hr style="border-color: #3b424d;"><ul><li><b>Position Size:</b> ${pos_size:,.2f}</li><li><b>Leverage:</b> {lev}x</li><li><b>Margin Used:</b> ${margin:,.2f}</li></ul></div>""", unsafe_allow_html=True)

                now_pkt = (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%d %I:%M %p")
                st.session_state['trade_history'].append({"Date & Time (PKT)": now_pkt, "Coin": target_coin, "Whale Driver": data['whale_status'], "15m RSI": round(rsi_15m, 1), "Signal": signal_type, "Entry": f"${price:.6f}", "Stop Loss": f"${sl_price:.6f}" if sl_price != "-" else "-", "Target": f"${tp1_price:.6f}" if tp1_price != "-" else "-"})
                save_permanent_data(st.session_state['trade_history'], TRADE_FILE)
                st.info("✅ Trade saved to Journal!")

elif selected == "🧪 Backtester":
    st.title("🧪 Time-Filtered Backtester (1-Year Data)")
    all_pro_coins = sorted(list(set([coin for coins in PRO_LISTS.values() for coin in coins])))
    c1, c2, c3, c4 = st.columns(4)
    with c1: bt_coin = st.selectbox("Test Pro Coin:", all_pro_coins, index=0)
    with c2: bt_cap = st.number_input("Starting Capital ($)", value=100.0)
    with c3: bt_risk = st.number_input("Risk Per Trade (%)", value=2.0)
    with c4: bt_rr = st.number_input("Target R:R (e.g. 2.0)", value=2.0, step=0.5, min_value=1.0)

    if st.button("🔄 Run Deep Analysis", type="primary"):
        with st.spinner(f"Extracting Historical data for {bt_coin}..."):
            res = run_pro_backtest(bt_coin, bt_cap, bt_risk, bt_rr, loops=36) 
            if res:
                st.success(f"Analyzed {res['total_candles_analyzed']} candles")
                st.subheader("🌟 Golden Hours (5 PM to 9 PM PKT)")
                g_tot = res['golden']['wins'] + res['golden']['losses']; g_win = (res['golden']['wins']/g_tot*100) if g_tot > 0 else 0
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Trades", g_tot); c2.metric("Win Rate", f"{g_win:.1f}%"); c3.metric("Net PnL", f"${res['golden']['pnl']:.2f}")
                st.info(f"💡 Best Time: **{res['best_hour']:02d}:00 PKT** | Best Day: **{res['best_day']}**")
                bt_log = {"Date": (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"), "Coin": bt_coin, "R:R": f"1:{bt_rr}", "Candles": res['total_candles_analyzed'], "Gold Trades": g_tot, "Gold WinRate": f"{g_win:.1f}%", "Gold PnL": f"${res['golden']['pnl']:.2f}", "Best Hr": f"{res['best_hour']:02d}:00", "Best Day": res['best_day']}
                st.session_state['backtest_history'].append(bt_log)
                save_permanent_data(st.session_state['backtest_history'], BACKTEST_FILE)

# --- NAYA TAB: PATTERN BOOK (TA & FA) ---
elif selected == "📈 Pattern Book":
    st.title("📈 Technical & Fundamental Analysis Guide")
    st.markdown("Is section mein aap chart patterns aur fundamental news ki basic logic dekh sakte hain. Aap in tasweeron ko yaad kar ke live market mein apply kar sakte hain.")

    t1, t2, t3 = st.tabs(["📊 Chart Patterns", "🕯️ Candlesticks", "🏢 Fundamental Analysis"])
    
    with t1:
        st.subheader("Classic Chart Patterns (Technical Analysis)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="pattern-card">
                <img src="https://dummyimage.com/400x200/2B3139/0ECB81&text=Bull+Flag+Pattern" width="100%" style="border-radius: 8px;">
                <h4 style="color: #0ECB81; margin-top:10px;">1. Bull Flag (Tezi Ka Nishan)</h4>
                <p style="font-size: 14px; text-align: left;">Market achanak pump hoti hai (Pole), phir thora neechay rest karti hai (Flag). Jab flag ki upper line break ho, toh dobara waisa hi pump aata hai.</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="pattern-card">
                <img src="https://dummyimage.com/400x200/2B3139/F6465D&text=Head+%26+Shoulders" width="100%" style="border-radius: 8px;">
                <h4 style="color: #F6465D; margin-top:10px;">3. Head and Shoulders (Girawat)</h4>
                <p style="font-size: 14px; text-align: left;">Price 3 peaks banati hai. Darmiyan wali peak sab se unchi (Head) aur side wali choti (Shoulders). Jab neckline tootti hai, market crash karti hai.</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="pattern-card">
                <img src="https://dummyimage.com/400x200/2B3139/0ECB81&text=Double+Bottom+(W)" width="100%" style="border-radius: 8px;">
                <h4 style="color: #0ECB81; margin-top:10px;">2. Double Bottom (W-Pattern)</h4>
                <p style="font-size: 14px; text-align: left;">Girne ke baad market 2 dafa same support se upar uthti hai aur 'W' ki shakal banati hai. Yeh ek strong Buy signal hota hai.</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="pattern-card">
                <img src="https://dummyimage.com/400x200/2B3139/F3BA2F&text=Symmetrical+Triangle" width="100%" style="border-radius: 8px;">
                <h4 style="color: #F3BA2F; margin-top:10px;">4. Symmetrical Triangle</h4>
                <p style="font-size: 14px; text-align: left;">Price ek choti range mein phans jati hai (Higher Lows & Lower Highs). Jis taraf breakout ho, trade usi taraf li jati hai.</p>
            </div>
            """, unsafe_allow_html=True)

    with t2:
        st.subheader("Candlestick Patterns (Price Action)")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("""<div class="pattern-card"><h4 style="color: #0ECB81;">Hammer (Hathora)</h4><p style="text-align: left;">Neechay ki taraf ek lambi wick hoti hai aur upar choti body. Iska matlab hai neechay se buyers ne pressure dala hai. Trend Reversal signal.</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="pattern-card"><h4 style="color: #0ECB81;">Bullish Engulfing</h4><p style="text-align: left;">Pehli choti red candle hoti hai, aur agli bari green candle pehli wali ko poora 'kha' (engulf) jati hai. Strong buying signal.</p></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown("""<div class="pattern-card"><h4 style="color: #F6465D;">Shooting Star</h4><p style="text-align: left;">Upar ki taraf lambi wick aur neechay choti body. Matlab sellers ne price ko reject kar diya hai. Strong sell signal.</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="pattern-card"><h4 style="color: #F3BA2F;">Doji</h4><p style="text-align: left;">Body bilkul patli line jaisi hoti hai aur dono taraf wicks. Iska matlab hai market confuse hai ke upar jana hai ya neechay.</p></div>""", unsafe_allow_html=True)

    with t3:
        st.subheader("Fundamental Analysis (News Data)")
        st.markdown("""
        <div class="news-card">
            <h4>🔴 US CPI Data (Inflation)</h4>
            <p><b>Impact:</b> EXTREME VOLATILITY | <b>When:</b> Har mahine (12-15 date) - <b>5:30 PM PKT</b>.</p>
            <hr><b>🔥 Rule:</b> Inflation (Mehgai) data agar expectation se ziyada aye, toh US Dollar strong hota hai aur Crypto girti hai.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="news-card">
            <h4>🔴 FOMC Meeting & Interest Rates</h4>
            <p><b>Impact:</b> MARKET CHANGER | <b>When:</b> Har 6 haftay baad Wed ko - <b>11:00 PM PKT</b>.</p>
            <hr><b>🔥 Rule:</b> Agar Federal Reserve Interest Rate (Sood ki sharah) barhaye, toh market girti hai. Agar Rate kam kare (Cut), toh market PUMP hoti hai.
        </div>
        """, unsafe_allow_html=True)

elif selected == "🧠 Pro Academy":
    st.title("🧠 Pro Trading Academy")
    tab1, tab2, tab3 = st.tabs(["📚 12 Master Books", "💡 Daily AI Lessons", "📂 My Notes"])
    with tab1:
        st.markdown("Top trading books ki asaan Roman Urdu summary:")
        books = [
            {"title": "1. Trading in the Zone", "author": "Mark Douglas", "desc": "Mindset trading ka 80% hissa hai, strategy sirf 20%."},
            {"title": "2. Market Wizards", "author": "Jack D. Schwager", "desc": "Bare log kis tarah sochte hain jab unhe nuksan hota hai."},
            {"title": "3. Volume Price Analysis", "author": "Anna Coulling", "desc": "Whales ko track karne ka wahid tareeqa Volume hai."}
        ]
        for book in books:
            st.markdown(f"""<div class="book-card"><h4 style="margin-top: 0; color: #F6465D;">{book['title']}</h4><p style="color: #848E9C; font-size: 13px; font-weight: bold;">Author: {book['author']}</p><p style="font-size: 14px; margin-bottom: 0;">{book['desc']}</p></div>""", unsafe_allow_html=True)
    with tab2:
        all_lessons = ["Risk management is everything.", "Don't trade the news directly.", "Trend is your friend until it bends."]
        random.seed(datetime.now().date().toordinal())
        todays_lessons = random.sample(all_lessons, min(3, len(all_lessons)))
        for i, lesson in enumerate(todays_lessons, 1):
            st.markdown(f"""<div class="lesson-card"><h4 style="color: #0ECB81; margin-top: 0;">Insight {i}:</h4><p style="font-size: 16px; margin-bottom: 0;">{lesson}</p></div>""", unsafe_allow_html=True)
            if st.button(f"✅ Save to My Brain (Lesson {i})", key=f"save_lesson_{i}"):
                save_time = (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%d %I:%M %p")
                st.session_state['learning_history'].append({"Date Saved": save_time, "Lesson": lesson})
                save_permanent_data(st.session_state['learning_history'], LEARNING_FILE)
                st.success("✅ Lesson saved!")
    with tab3:
        if len(st.session_state['learning_history']) > 0:
            st.dataframe(pd.DataFrame(st.session_state['learning_history']), use_container_width=True)
            csv_learn = pd.DataFrame(st.session_state['learning_history']).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Notes", data=csv_learn, file_name="Hamdan_Learning.csv", mime="text/csv")
        else: st.warning("Koi lesson save nahi kiya.")

elif selected == "📓 Journal":
    st.title("📓 My Trading Journal")
    st.subheader("1. Live Trade History")
    if len(st.session_state['trade_history']) > 0: st.dataframe(pd.DataFrame(st.session_state['trade_history']), use_container_width=True)
    else: st.warning("Abhi tak koi live trade data save nahi hua.")
    st.markdown("---")
    st.subheader("2. Backtest Reports")
    if len(st.session_state['backtest_history']) > 0: st.dataframe(pd.DataFrame(st.session_state['backtest_history']), use_container_width=True)
    else: st.warning("Abhi tak koi backtest run nahi kiya gaya.")
    st.markdown("---")
    if st.button("🗑️ Clear ALL Data"):
        st.session_state['trade_history'] = []; st.session_state['backtest_history'] = []; st.session_state['learning_history'] = []
        for f in [TRADE_FILE, BACKTEST_FILE, LEARNING_FILE]: 
            if os.path.exists(f): os.remove(f)
        st.rerun()

   # Final Mobile Update