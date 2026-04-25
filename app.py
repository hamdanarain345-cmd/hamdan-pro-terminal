
import streamlit as st
import pandas as pd
import requests
from streamlit_option_menu import option_menu
from datetime import datetime, timezone, timedelta
import math
import time
import os
import random 
import xml.etree.ElementTree as ET 

# --- TWILIO SMS SETUP ---
try:
    from twilio.rest import Client
    TWILIO_INSTALLED = True
    TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")
except Exception as e:
    TWILIO_INSTALLED = False

TWILIO_SENDER_NUMBER = '+15186349627'
MY_PHONE_NUMBERS = ['+923136538984', '+923153745987']

def send_sms_alert(coin, signal, price):
    if not TWILIO_INSTALLED or not TWILIO_ACCOUNT_SID: return
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        for number in MY_PHONE_NUMBERS:
            client.messages.create(body=f"🚨 HAMDAN PRO ALERT: {coin} - SMC {signal} Setup! Entry Zone: {price}", from_=TWILIO_SENDER_NUMBER, to=number)
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
if 'sent_alerts' not in st.session_state: st.session_state['sent_alerts'] = []

st.markdown("""
    <style>
    .main {background-color: #0b0e14;}
    h1, h2, h3, h4, h5 {color: #EAECEF;}
    div[data-testid="stMetricValue"] {color: #EAECEF;} 
    .signal-box {background-color: #2B3139; padding: 25px; border-radius: 12px; text-align: center; margin-top: 20px; border: 2px solid #3b424d;}
    .trade-card {background-color: #1a1e23; padding: 15px; border-radius: 8px; text-align: left; margin-top: 15px; border-left: 5px solid #0ECB81;}
    .recommendation-box {background-color: #1E2329; padding: 15px; border-radius: 10px; border: 1px solid #3b424d; margin-bottom: 20px;}
    .news-card {background-color: #1E2329; padding: 20px; border-radius: 10px; border-left: 5px solid #5C82FF; margin-bottom: 15px;}
    .lesson-card {background-color: #1a1e23; padding: 20px; border-radius: 10px; border-left: 5px solid #0ECB81; margin-bottom: 15px;}
    .book-card {background-color: #1E2329; padding: 20px; border-radius: 10px; border-left: 5px solid #F6465D; margin-bottom: 15px;}
    .pattern-card {background-color: #1E2329; padding: 15px; border-radius: 8px; border: 1px solid #3b424d; margin-bottom: 15px; text-align: center;}
    .ict-box {background-color: #1E2329; padding: 25px; border-radius: 12px; border: 1px solid #F3BA2F; margin-bottom: 25px;}
    
    @media (max-width: 768px) {
        .pattern-card, .book-card, .lesson-card, .ict-box, .news-card { padding: 15px; }
        h1 {font-size: 24px;}
        h2 {font-size: 20px;}
    }
    </style>
    """, unsafe_allow_html=True)

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# --- NEW: Dynamic Coin Categorization Logic ---
def assign_coin_category(symbol):
    s = symbol.upper()
    if s in ['BTCUSDT', 'ETHUSDT']: return "👑 Titan / Digital Gold"
    elif s in ['SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'APTUSDT', 'SUIUSDT', 'ADAUSDT', 'DOTUSDT', 'FTMUSDT', 'SEIUSDT', 'INJUSDT']: return "🚀 Layer-1 Smart Contract"
    elif s in ['ARBUSDT', 'OPUSDT', 'POLUSDT', 'MATICUSDT']: return "⛓️ Layer-2 Scaling"
    elif s in ['TAOUSDT', 'FETUSDT', 'RNDRUSDT', 'ARKMUSDT', 'AGIXUSDT', 'WLDUSDT']: return "🤖 AI & Big Data"
    elif s in ['LINKUSDT', 'UNIUSDT', 'AAVEUSDT', 'MKRUSDT', 'SNXUSDT', 'RUNEUSDT']: return "🏦 DeFi (Decentralized Finance)"
    elif s in ['DOGEUSDT', 'PEPEUSDT', 'WIFUSDT', 'SHIBUSDT', 'BONKUSDT', 'FLOKIUSDT', 'BOMEUSDT']: return "🐕 Meme Coin (High Risk)"
    elif s in ['XRPUSDT', 'TRXUSDT', 'XLMUSDT']: return "💸 Cross-Border Payment"
    elif s in ['SANDUSDT', 'MANAUSDT', 'GALAUSDT', 'AXSUSDT', 'IMXUSDT']: return "🎮 Gaming & Metaverse"
    elif s in ['STXUSDT', 'FILUSDT', 'ICPUSDT', 'ROSEUSDT']: return "🛠️ Utility & Infrastructure"
    return "⚪ General Altcoin"

def format_volume(vol):
    try:
        v = float(vol)
        if v >= 1e9: return f"${v/1e9:.3f}B"
        elif v >= 1e6: return f"${v/1e6:.3f}M"
        elif v >= 1e3: return f"${v/1e3:.2f}K"
        return f"${v:.2f}"
    except: return vol

@st.cache_data(ttl=20) 
def fetch_gold_silver():
    try:
        g_res = requests.get("https://contract.mexc.com/api/v1/contract/ticker?symbol=GOLD_USDT", timeout=5).json()
        s_res = requests.get("https://contract.mexc.com/api/v1/contract/ticker?symbol=SILVER_USDT", timeout=5).json()
        g_price = float(g_res.get('data', {}).get('lastPrice', 0))
        s_price = float(s_res.get('data', {}).get('lastPrice', 0))
        return g_price, s_price
    except: return 0.0, 0.0

@st.cache_data(ttl=60)
def fetch_fear_and_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()
        return int(res['data'][0]['value']), res['data'][0]['value_classification']
    except: return 50, "Neutral"

# --- NEW: Dynamic Fetching of Top Liquid Coins ---
@st.cache_data(ttl=60)
def fetch_all_crypto():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", headers=HEADERS, timeout=10).json()
        df = pd.DataFrame(res)
        
        # Calculate strict Quote Volume
        df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
        df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
        df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
        
        # Filter: Only USDT pairs, ignoring stablecoins/fiat
        ignore_list = ['USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT']
        df = df[df['symbol'].str.endswith('USDT') & (~df['symbol'].isin(ignore_list))]
        
        # Format the dataframe
        df = df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']]
        df.columns = ['Pair', 'Price (USD)', '24h Change (%)', 'Volume (USDT)']
        
        # Sort by highest 24h volume and drop NaNs
        df = df.sort_values(by='Volume (USDT)', ascending=False).dropna()
        
        # Assign purpose/category dynamically
        df['Category (Maqsad)'] = df['Pair'].apply(assign_coin_category)
        
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def generate_correlation_matrix():
    coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT']
    data = {}
    try:
        for coin in coins:
            url = f"https://api.binance.com/api/v3/klines?symbol={coin}&interval=1h&limit=100"
            res = requests.get(url, timeout=5).json()
            if isinstance(res, list) and len(res) > 0:
                closes = [float(candle[4]) for candle in res]
                data[coin.replace('USDT', '')] = closes
        if data:
            df = pd.DataFrame(data)
            return df.corr()
    except: return None
    return None

@st.cache_data(ttl=1800)
def fetch_live_news():
    news_items = []
    try:
        url = "https://cointelegraph.com/rss" 
        req = requests.get(url, headers=HEADERS, timeout=5)
        root = ET.fromstring(req.content)
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            pubDate = item.find('pubDate').text
            news_items.append({"title": title, "date": pubDate[:-15]})
    except Exception as e:
        news_items.append({"title": "News API thori der ke liye band hai.", "date": ""})
    return news_items

def get_retail_whale_limit(symbol): return 10000 if symbol in ['BTCUSDT', 'ETHUSDT'] else 500 if symbol in ['PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'BONKUSDT'] else 2000

def calculate_rsi(prices_series, period=14):
    if len(prices_series) < period: return pd.Series([50]*len(prices_series))
    deltas = prices_series.diff(); gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean(); rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(prices_series, period=50): return prices_series.ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']; high_close = (df['high'] - df['close'].shift()).abs(); low_close = (df['low'] - df['close'].shift()).abs()
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(window=period).mean()

def fmt_p(price): return f"${price:,.8f}" if price < 0.01 else f"${price:,.4f}"

def get_market_session_pkt():
    hour = (datetime.now(timezone.utc) + timedelta(hours=5)).hour
    if 5 <= hour < 12: return "Tokyo Open 🇯🇵 (Kam Volatility)"
    elif 12 <= hour < 17: return "London Open 🇬🇧 (Darmiyani Volatility)"
    elif 17 <= hour < 21: return "London + NY Overlap 🇬🇧🇺🇸 (SAB SE ZYADA VOLATILITY - Golden Hours)"
    elif 21 <= hour < 2: return "New York Open 🇺🇸 (Zyada Volatility)"
    else: return "Sydney/Asian 🇦🇺 (Dead Zone - Trade Na Karein)"

def fetch_klines_safe(symbol, interval, limit):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=5).json()
        if not isinstance(res, list) or len(res) == 0: return None
        df_raw = pd.DataFrame(res)
        return pd.DataFrame({
            'time': df_raw.iloc[:, 0].astype(float), 
            'open': df_raw.iloc[:, 1].astype(float), 
            'high': df_raw.iloc[:, 2].astype(float), 
            'low': df_raw.iloc[:, 3].astype(float), 
            'close': df_raw.iloc[:, 4].astype(float),
            'volume': df_raw.iloc[:, 5].astype(float)
        })
    except: return None

@st.cache_data(ttl=10) 
def get_ict_smc_strict_signal():
    # Only monitoring top highly liquid coins for strict setups
    top_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'SUIUSDT', 'LINKUSDT']
    valid_setups = []
    
    fng_val, _ = fetch_fear_and_greed()
    macro_fund_bias = "BULLISH" if fng_val > 55 else "BEARISH" if fng_val < 45 else "NEUTRAL"
    
    hour = (datetime.now(timezone.utc) + timedelta(hours=5)).hour
    is_active_session = 12 <= hour <= 23 
    
    for coin in top_coins:
        df_4h = fetch_klines_safe(coin, '4h', 50) 
        df_15m = fetch_klines_safe(coin, '15m', 100) 
        if df_4h is None or df_15m is None: continue
        
        close_price = df_15m['close'].iloc[-1]
        atr = calculate_atr(df_15m).iloc[-1]
        
        df_15m['vol_ma20'] = df_15m['volume'].rolling(window=20).mean()
        curr_vol_ma = df_15m['vol_ma20'].iloc[-1]
        
        recent_4h_high = df_4h['high'].max()
        recent_4h_low = df_4h['low'].min()
        tech_trend = "BULLISH" if (close_price - recent_4h_low) > (recent_4h_high - close_price) else "BEARISH"
        
        if macro_fund_bias != "NEUTRAL" and tech_trend != macro_fund_bias:
            continue 
            
        swing_high = df_15m['high'].max()
        swing_low = df_15m['low'].min()
        eq = (swing_high + swing_low) / 2
        
        signal = None
        if tech_trend == "BULLISH" and close_price <= eq and is_active_session: 
            for i in range(len(df_15m)-3, 10, -1):
                fvg_gap = df_15m['low'].iloc[i+1] - df_15m['high'].iloc[i-1]
                if fvg_gap > 0:
                    ob_idx = i-1
                    fvg_candle_vol = df_15m['volume'].iloc[i] 
                    if fvg_candle_vol > df_15m['vol_ma20'].iloc[i] * 1.2: 
                        if df_15m['close'].iloc[ob_idx] < df_15m['open'].iloc[ob_idx]: 
                            ob_high = df_15m['high'].iloc[ob_idx]
                            ob_low = df_15m['low'].iloc[ob_idx]
                            
                            if close_price > ob_low: 
                                dist = (close_price - ob_high) / ob_high
                                last_3_vol_avg = df_15m['volume'].iloc[-3:].mean()
                                
                                if last_3_vol_avg < curr_vol_ma:
                                    if -0.005 <= dist <= 0.015: 
                                        signal = "LONG 🟢"
                                        entry = ob_high
                                        sl = ob_low - (atr * 0.5)
                                        tp = entry + ((entry - sl) * 3) 
                                        reason = f"<b>STRICT WHALE SMC:</b><br>1. <b>Trend Align:</b> 4H+News is Bullish.<br>2. <b>Volume Matrix:</b> High Vol on FVG breakout, Low Vol on Pullback.<br>3. <b>Setup:</b> Tapping FVG + Order Block at {fmt_p(entry)}."
                                        status = "🟢 ACTIVE (OB + Vol Confirmed)" if dist <= 0 else "🟡 WAITING (OB Tap)"
                                        color = "#0ECB81" if dist <= 0 else "#F3BA2F"
                                        valid_setups.append({"coin": coin, "signal": signal, "entry": entry, "sl": sl, "tp": tp, "reason": reason, "status": status, "color": color})
                                        break

        elif tech_trend == "BEARISH" and close_price >= eq and is_active_session: 
            for i in range(len(df_15m)-3, 10, -1):
                fvg_gap = df_15m['low'].iloc[i-1] - df_15m['high'].iloc[i+1]
                if fvg_gap > 0:
                    ob_idx = i-1
                    fvg_candle_vol = df_15m['volume'].iloc[i] 
                    if fvg_candle_vol > df_15m['vol_ma20'].iloc[i] * 1.2: 
                        if df_15m['close'].iloc[ob_idx] > df_15m['open'].iloc[ob_idx]: 
                            ob_high = df_15m['high'].iloc[ob_idx]
                            ob_low = df_15m['low'].iloc[ob_idx]
                            
                            if close_price < ob_high:
                                dist = (ob_low - close_price) / ob_low
                                last_3_vol_avg = df_15m['volume'].iloc[-3:].mean()
                                
                                if last_3_vol_avg < curr_vol_ma:
                                    if -0.005 <= dist <= 0.015: 
                                        signal = "SHORT 🔴"
                                        entry = ob_low
                                        sl = ob_high + (atr * 0.5)
                                        tp = entry - ((sl - entry) * 3)
                                        reason = f"<b>STRICT WHALE SMC:</b><br>1. <b>Trend Align:</b> 4H+News is Bearish.<br>2. <b>Volume Matrix:</b> High Vol on FVG dump, Low Vol on Pullback.<br>3. <b>Setup:</b> Tapping FVG + Order Block at {fmt_p(entry)}."
                                        status = "🔴 ACTIVE (OB + Vol Confirmed)" if dist <= 0 else "🟡 WAITING (OB Tap)"
                                        color = "#F6465D" if dist <= 0 else "#F3BA2F"
                                        valid_setups.append({"coin": coin, "signal": signal, "entry": entry, "sl": sl, "tp": tp, "reason": reason, "status": status, "color": color})
                                        break
                            
    return valid_setups

# --- NEW: Dynamic Screener Engine (Volume + Whales) ---
@st.cache_data(ttl=15) 
def pro_dynamic_analyzer(symbol):
    whale_limit_usd = get_retail_whale_limit(symbol)
    trades_url = f"https://api.mexc.com/api/v3/trades?symbol={symbol.upper()}&limit=1000"
    try:
        t_res = requests.get(trades_url, timeout=5).json()
        buy_vol, sell_vol = 0, 0
        if isinstance(t_res, list):
            for t in t_res:
                val = float(t['price']) * float(t['qty'])
                if val >= whale_limit_usd:
                    if t['isBuyerMaker']: sell_vol += val
                    else: buy_vol += val
                    
        df_4h = fetch_klines_safe(symbol, '4h', 60)
        df_15m = fetch_klines_safe(symbol, '15m', 100)
        if df_4h is None or df_15m is None: return None, "Kline Error"

        ema_50_4h = calculate_ema(df_4h['close'], 50).iloc[-1]
        trend_4h = "UP" if df_4h['close'].iloc[-1] > ema_50_4h else "DOWN"
        
        rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
        ema_50_15m = calculate_ema(df_15m['close'], 50).iloc[-1]
        atr_15m = calculate_atr(df_15m).iloc[-1]
        trend_15m = "UP" if df_15m['close'].iloc[-1] > ema_50_15m else "DOWN"

        total_vol = buy_vol + sell_vol
        buy_pct = (buy_vol / total_vol * 100) if total_vol > 0 else 50
        current_price = df_15m['close'].iloc[-1] 
        
        whale_status = "🐋 HEAVY BUYING" if buy_pct >= 65 else "🐋 HEAVY SELLING" if buy_pct <= 35 else "🐟 RETAIL NOISE"
        
        hour = (datetime.now(timezone.utc) + timedelta(hours=5)).hour
        is_active_session = 12 <= hour <= 21

        score = 0
        signal_type = "NONE"
        
        if is_active_session:
            if trend_4h == "UP" and trend_15m == "UP" and buy_pct >= 65 and 40 <= rsi_15m <= 65: 
                score = 100; signal_type = "LONG"
            elif trend_4h == "DOWN" and trend_15m == "DOWN" and buy_pct <= 35 and 35 <= rsi_15m <= 60: 
                score = -100; signal_type = "SHORT"
        
        return {"symbol": symbol, "buy_pct": buy_pct, "rsi_15m": rsi_15m, "price": current_price, "trend_4h": trend_4h, "trend_15m": trend_15m, "atr": atr_15m, "score": score, "signal": signal_type, "whale_status": whale_status}, None
    except Exception as e: return None, f"API Fetch Error: {str(e)}"

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

@st.cache_data(ttl=600)
def run_pro_backtest(symbol, capital, risk_pct, target_rr, loops=36):
    df = fetch_deep_history(symbol, '15m', loops) 
    if df is None or len(df) < 500: return None
    
    df['ema200'] = calculate_ema(df['close'], 200)
    df['atr'] = calculate_atr(df, 14)
    df['pkt_time'] = pd.to_datetime(df['time'], unit='ms') + pd.Timedelta(hours=5)
    df['hour'] = df['pkt_time'].dt.hour
    df['day_of_week'] = df['pkt_time'].dt.day_name()
    
    closes = df['close'].values
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    ema200 = df['ema200'].values
    atrs = df['atr'].values
    hours = df['hour'].values
    days = df['day_of_week'].values

    wins_golden, losses_golden, pnl_golden = 0, 0, 0.0
    wins_other, losses_other, pnl_other = 0, 0, 0.0
    hour_perf = {h: {'wins': 0, 'losses': 0} for h in range(24)}
    day_perf = {d: {'wins': 0, 'losses': 0} for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}

    risk_usd = capital * (risk_pct / 100)

    in_trade, trade_type, sl, tp, entry_price, trade_hour, trade_day, is_golden = False, "", 0.0, 0.0, 0.0, 0, "", False

    for i in range(200, len(df) - 1):
        if in_trade:
            win, loss = False, False
            if trade_type == "LONG":
                if lows[i] <= sl: loss = True
                elif highs[i] >= tp: win = True
            elif trade_type == "SHORT":
                if highs[i] >= sl: loss = True
                elif lows[i] <= tp: win = True

            if win or loss:
                pnl_chg = (risk_usd * target_rr) if win else -risk_usd
                hour_perf[trade_hour]['wins' if win else 'losses'] += 1
                day_perf[trade_day]['wins' if win else 'losses'] += 1

                if is_golden:
                    if win: wins_golden += 1
                    else: losses_golden += 1
                    pnl_golden += pnl_chg
                else:
                    if win: wins_other += 1
                    else: losses_other += 1
                    pnl_other += pnl_chg
                in_trade = False
            continue

        c_close, c_ema200 = closes[i], ema200[i]

        if not in_trade:
            if c_close > c_ema200: 
                min_low_5 = min(lows[i-5:i])
                if lows[i-1] <= min_low_5 and closes[i] > opens[i] and closes[i] > highs[i-1]:
                    in_trade, trade_type, entry_price = True, "LONG", closes[i]
                    sl = lows[i-1] - (atrs[i] * 0.5)
                    dist = max(entry_price - sl, atrs[i] * 0.5) 
                    tp = entry_price + (dist * target_rr)
                    
            elif c_close < c_ema200: 
                max_high_5 = max(highs[i-5:i])
                if highs[i-1] >= max_high_5 and closes[i] < opens[i] and closes[i] < lows[i-1]:
                    in_trade, trade_type, entry_price = True, "SHORT", closes[i]
                    sl = highs[i-1] + (atrs[i] * 0.5)
                    dist = max(sl - entry_price, atrs[i] * 0.5)
                    tp = entry_price - (dist * target_rr)

        if in_trade:
            trade_hour, trade_day = hours[i], days[i]
            is_golden = (16 <= trade_hour <= 21) 

    best_hr, best_w_rate = 0, 0
    for h, s in hour_perf.items():
        t = s['wins'] + s['losses']
        if t > 10 and (s['wins']/t*100) > best_w_rate:
            best_w_rate = (s['wins']/t*100); best_hr = h

    best_d, best_d_rate = "None", 0
    for d, s in day_perf.items():
        t = s['wins'] + s['losses']
        if t > 10 and (s['wins']/t*100) > best_d_rate:
            best_d_rate = (s['wins']/t*100); best_d = d

    return {
        "golden": {"wins": wins_golden, "losses": losses_golden, "pnl": pnl_golden},
        "other": {"wins": wins_other, "losses": losses_other, "pnl": pnl_other},
        "best_hour": best_hr, "best_win_rate": best_w_rate,
        "best_day": best_d, "best_day_win_rate": best_d_rate,
        "total_candles_analyzed": len(df), "risk_amt": risk_usd, "reward_amt": risk_usd * target_rr
    }

def color_change(val): return 'color: #0ECB81; font-weight: bold;' if val > 0 else 'color: #F6465D; font-weight: bold;' if val < 0 else 'color: white;'
def highlight_recommendation(val): return 'background-color: rgba(243, 186, 47, 0.2); font-weight: bold; color: #F3BA2F;' if "🔥" in str(val) or "⚡" in str(val) or "🐋" in str(val) else ''

# --- Navigation Bar ---
selected = option_menu(
    menu_title=None, 
    options=["Market", "📰 Fundamentals", "⚡ Screener", "🎯 Engine", "🧪 Backtester", "📈 Pattern Book", "🧠 Pro Academy", "📓 Journal"], 
    icons=["house", "globe", "search", "bullseye", "database", "bar-chart-line", "book", "journal-bookmark"], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#1E2329"},
        "icon": {"color": "#F3BA2F", "font-size": "14px"}, 
        "nav-link": {"color": "white", "font-size": "12px", "text-align": "center", "margin":"0px"},
        "nav-link-selected": {"background-color": "#F3BA2F", "color": "black", "font-weight": "bold"},
    }
)

# --- Pages Logic ---
if selected == "Market":
    st.title("📊 Dunya Ka Market Overview")
    gold_price, silver_price = fetch_gold_silver()
    fng_value, fng_class = fetch_fear_and_greed()
    
    st.warning("⚠️ **Risk Warning:** Koi bhi trade 100% pass nahi hoti. Whales order blocks ko sweep kar ke fail karwate hain. Hamesha sirf account ka 2% risk karein.")
    
    fng_color = "#F6465D" if fng_value < 45 else "#0ECB81" if fng_value > 55 else "#F3BA2F"
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f"<h3 style='text-align: center; color: {fng_color};'>{fng_value}/100</h3><p style='text-align: center;'>Jazbaat: {fng_class}</p>", unsafe_allow_html=True)
    
    g_text = fmt_p(gold_price) if gold_price > 0 else "Data Unavailable"
    s_text = fmt_p(silver_price) if silver_price > 0 else "Data Unavailable"
    
    col2.metric("🥇 Gold (MEXC)", g_text)
    col3.metric("🥈 Silver (MEXC)", s_text)
    
    # Safely fetch BTC price for the top dashboard
    market_df = fetch_all_crypto()
    if not market_df.empty and 'BTCUSDT' in market_df['Pair'].values:
        btc_price = market_df[market_df['Pair'] == 'BTCUSDT']['Price (USD)'].values[0]
        col4.metric("🟠 Bitcoin (BTC)", fmt_p(btc_price))
    else:
        col4.metric("🟠 Bitcoin (BTC)", "Loading...")

    st.markdown("---")
    st.subheader("🤖 SMC + 4 Whale Volume Metrics (ULTRA STRICT)")
    smc_setups = get_ict_smc_strict_signal()
    
    if smc_setups and len(smc_setups) > 0:
        for smc_signal in smc_setups[:3]: 
            st.markdown(f"""
            <div class="ict-box">
                <h3 style="color: #F3BA2F; margin-top: 0;">{smc_signal['coin']} - {smc_signal['signal']}</h3>
                <h5 style="color: {smc_signal['color']};">{smc_signal['status']}</h5>
                <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                    <div><p style="color: #848E9C; margin:0;">Entry Zone</p><h4>{fmt_p(smc_signal['entry'])}</h4></div>
                    <div><p style="color: #F6465D; margin:0;">Stop Loss</p><h4>{fmt_p(smc_signal['sl'])}</h4></div>
                    <div><p style="color: #0ECB81; margin:0;">Target</p><h4>{fmt_p(smc_signal['tp'])}</h4></div>
                </div>
                <hr style="border-color: #3b424d;">
                <p style="font-size: 15px;">{smc_signal['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            alert_key = f"{smc_signal['coin']}_{smc_signal['signal']}_{smc_signal['entry']}"
            if alert_key not in st.session_state['sent_alerts']:
                send_sms_alert(smc_signal['coin'], smc_signal['signal'], fmt_p(smc_signal['entry']))
                st.session_state['sent_alerts'].append(alert_key)
    else:
        st.info("⚠️ Market mein abhi koi Whale Volume + OB ka proper mix nahi ban raha. Volume rules reject kar rahe hain. Zabardasti ki trade loss degi, wait karein.")

elif selected == "📰 Fundamentals":
    st.title("🌐 Macro Data & Market Correlations")
    t1, t2 = st.tabs(["🔗 Crypto Correlation Matrix", "📰 Live News"])
    
    with t1:
        st.subheader("Live 1H Correlation Matrix (Top Coins)")
        with st.spinner("Binance Orderbooks se data calculate ho raha hai..."):
            corr_df = generate_correlation_matrix()
            if corr_df is not None:
                def highlight_corr(val):
                    if val >= 0.8: return 'background-color: #0ECB81; color: black; font-weight: bold;'
                    elif val <= -0.5: return 'background-color: #F6465D; color: white; font-weight: bold;'
                    elif val >= 0.5: return 'background-color: rgba(14, 203, 129, 0.3); color: white;'
                    return 'color: #848E9C;'
                st.dataframe(corr_df.style.map(highlight_corr).format("{:.2f}"), use_container_width=True, height=400)
            else:
                st.error("Data fetch karne mein masla aaya.")
                
    with t2:
        st.subheader("Latest Crypto News")
        news_data = fetch_live_news()
        if news_data:
            for n in news_data:
                st.markdown(f"""
                <div class="news-card">
                    <h5 style="color: #5C82FF; margin-top:0;">{n['title']}</h5>
                    <p style="color: #848E9C; font-size: 12px; margin:0;">🗓️ Waqt: {n['date']}</p>
                </div>
                """, unsafe_allow_html=True)

# --- NEW: Dynamic Screener Tab ---
elif selected == "⚡ Screener":
    st.title("⚡ Dynamic Top Volume Screener")
    st.markdown("Yeh screener directly live orderbooks se sab se high volume wale coins uthata hai aur check karta hai ke Whales kahan paisa daal rahi hain.")
    
    with st.spinner("Fetching top 150 high volume coins globally..."):
        market_df = fetch_all_crypto()
        
    if not market_df.empty:
        # We only want to analyze top 20 to avoid rate limits on MEXC API
        top_coins_list = market_df.head(20)['Pair'].tolist()
        
        st.write("Analyzing Whale Orderflow for the top 20 most liquid coins...")
        progress_bar = st.progress(0)
        
        results = []
        for i, coin in enumerate(top_coins_list):
            data, err = pro_dynamic_analyzer(coin)
            if data:
                # Merge Whale data with Market data
                coin_market_data = market_df[market_df['Pair'] == coin].iloc[0]
                results.append({
                    "Coin": coin,
                    "Category (Maqsad)": coin_market_data['Category (Maqsad)'],
                    "Price": fmt_p(data['price']),
                    "24h Vol": format_volume(coin_market_data['Volume (USDT)']),
                    "Trend (4H/15m)": f"{data['trend_4h']} / {data['trend_15m']}",
                    "Whale Activity": data['whale_status'],
                    "AI Action": "🟢 LONG (Session)" if data['signal'] == "LONG" else "🔴 SHORT (Session)" if data['signal'] == "SHORT" else "⚪ Neutral"
                })
            progress_bar.progress((i + 1) / len(top_coins_list))
            
        if results:
            res_df = pd.DataFrame(results)
            st.dataframe(
                res_df.style.map(highlight_recommendation, subset=['AI Action', 'Whale Activity']),
                use_container_width=True, hide_index=True
            )
            st.info("💡 **Note:** 'Category (Maqsad)' batata hai ke coin kis use-case (jaise AI, DeFi, Gaming) ke liye banaya gaya tha. Whales aksar specific categories ko ek sath pump karti hain.")

# --- NEW: Dynamic Engine Tab ---
elif selected == "🎯 Engine":
    st.title("🎯 Whale-Driven Trade Engine")
    current_session = get_market_session_pkt()
    st.markdown(f"<div style='text-align:center; padding: 10px; background-color:#1E2329; border-radius:10px; border-bottom: 3px solid #0ECB81;'>🌍 Current Market Status: <b>{current_session}</b></div><br>", unsafe_allow_html=True)
    
    st.subheader("⚙️ Live Coin Selection")
    st.markdown("Ab list fix nahi hai. Jo coin market mein sab se zyada trade ho raha hai (Highest Volume), engine sirf unhi par analysis karega.")
    
    market_df = fetch_all_crypto()
    if not market_df.empty:
        # Get dynamic top 50 coins for the dropdown
        dynamic_coin_list = market_df.head(50)['Pair'].tolist()
    else:
        dynamic_coin_list = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'] # Fallback
        
    c1, c2, c3 = st.columns(3)
    with c1: target_coin = st.selectbox("Select High-Volume Coin:", dynamic_coin_list, index=0)
    with c2: user_capital = st.number_input("Aapka Total Capital ($)", min_value=10.0, value=100.0, step=10.0)
    with c3: risk_pct = st.slider("Risk Per Trade (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
    
    if st.button("🚀 Analyze Setup & Save to Journal", type="primary"):
        with st.spinner(f"{target_coin} ka live orderbook Whale Data nikal raha hai..."):
            data, error = pro_dynamic_analyzer(target_coin)
            if error: st.error("⚠️ Data fetch error: " + error)
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Live Qeemat", fmt_p(data['price']))
                m2.metric("📈 4H & 15m Trend", f"4H: {data['trend_4h']} | 15m: {data['trend_15m']}", delta_color="normal" if data['trend_4h'] == "UP" else "inverse")
                m3.metric("📊 Stable 15m RSI", f"{data['rsi_15m']:.1f}")
                m4.metric(f"{data['whale_status']}", f"{data['buy_pct']:.1f}% Buy", delta_color="normal" if data['buy_pct'] > 50 else "inverse")

                buy_pct, trend_4h, rsi_15m, price, atr = data['buy_pct'], data['trend_4h'], data['rsi_15m'], data['price'], data['atr']
                risk_amount_usd = user_capital * (risk_pct / 100); signal_type = data['signal']
                
                if "LONG" in signal_type: box_color = "#0ECB81"; signal_msg = f"🚀 CONFIRMED {signal_type}"; send_sms_alert(target_coin, signal_type, fmt_p(price))
                elif "SHORT" in signal_type: box_color = "#F6465D"; signal_msg = f"📉 CONFIRMED {signal_type}"; send_sms_alert(target_coin, signal_type, fmt_p(price))
                else: box_color = "#3b424d"; signal_msg = "⚖️ KOI TRADE NAHI (Intezar karein)"

                st.markdown(f"<div class='signal-box' style='border-color: {box_color};'><h3 style='color: {box_color};'>{signal_msg}</h3></div>", unsafe_allow_html=True)
                sl_price, tp1_price = "-", "-"
                if signal_type != "NONE":
                    sl_price = price - (1.5 * atr) if "LONG" in signal_type else price + (1.5 * atr)
                    tp1_price = price + (3.0 * atr) if "LONG" in signal_type else price - (3.0 * atr)
                    sl_dist = max(abs(price - sl_price) / price, 0.001); pos_size = risk_amount_usd / sl_dist; lev = min(max(math.ceil(1.0 / (sl_dist * 1.5)), 1), 20); margin = pos_size / lev
                    st.markdown(f"""<div class="trade-card" style="border-left-color: {box_color};"><h4 style="color: {box_color};">🎯 Confirmed Trade Plan</h4><div style="display: flex; justify-content: space-between; margin-top: 15px;"><div><p style="color: #848E9C; margin:0;">Entry</p><h3>{fmt_p(price)}</h3></div><div><p style="color: #F6465D; margin:0;">Stop Loss</p><h3>{fmt_p(sl_price)}</h3></div><div><p style="color: #0ECB81; margin:0;">Target</p><h3>{fmt_p(tp1_price)}</h3></div></div><hr style="border-color: #3b424d;"><ul><li><b>Position Size:</b> ${pos_size:,.2f}</li><li><b>Leverage:</b> {lev}x</li><li><b>Margin Used:</b> ${margin:,.2f}</li></ul></div>""", unsafe_allow_html=True)

                now_pkt = (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%d %I:%M %p")
                st.session_state['trade_history'].append({"Date & Time (PKT)": now_pkt, "Coin": target_coin, "Whale Driver": data['whale_status'], "15m RSI": round(rsi_15m, 1), "Signal": signal_type, "Entry": f"${price:.6f}", "Stop Loss": f"${sl_price:.6f}" if sl_price != "-" else "-", "Target": f"${tp1_price:.6f}" if tp1_price != "-" else "-"})
                save_permanent_data(st.session_state['trade_history'], TRADE_FILE)
                st.info("✅ Trade Journal mein save ho gayi!")

elif selected == "🧪 Backtester":
    st.title("🧪 1-Year Deep SMC Backtester")
    st.markdown("Yeh system **1 saal (36,000 candles)** ka live data nikal kar us par **ICT Liquidity Sweep + Order Block** ki mechanical strategy test karta hai.")
    
    market_df = fetch_all_crypto()
    dynamic_coin_list = market_df.head(50)['Pair'].tolist() if not market_df.empty else ['BTCUSDT']
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: bt_coin = st.selectbox("Coin Select Karein:", dynamic_coin_list, index=0)
    with c2: bt_cap = st.number_input("Starting Capital ($)", value=100.0)
    with c3: bt_risk = st.number_input("Risk Per Trade (%)", value=2.0)
    with c4: bt_rr = st.number_input("Target R:R (e.g. 2.0)", value=2.0, step=0.5, min_value=1.0)

    if st.button("🔄 1-Year SMC Backtest Shuru Karein", type="primary"):
        with st.spinner(f"⏳ {bt_coin} ka 1 saal ka data (36,000+ candles) load aur analyze ho raha hai... (Approx 15-20 seconds)"):
            res = run_pro_backtest(bt_coin, bt_cap, bt_risk, bt_rr, loops=36) 
            if res:
                st.success(f"✅ {res['total_candles_analyzed']} candles analyze ho gayin! (Pura 1 Saal Ka Data)")
                
                st.markdown("### 📊 Section 1: Golden Hours (Shaam 4 se Raat 9 Baje PKT)")
                st.markdown("SMC strategy aam tor par London-NY overlap mein sab se achi chalti hai. Yahan uska 1 saal ka result dekhein:")
                
                g_tot = res['golden']['wins'] + res['golden']['losses']
                g_win = (res['golden']['wins']/g_tot*100) if g_tot > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Golden Hours Trades", g_tot)
                col2.metric("Win Rate (4 PM - 9 PM)", f"{g_win:.1f}%")
                col3.metric("Net Profit / Loss ($)", f"${res['golden']['pnl']:.2f}")

                st.markdown("### 🏆 Section 2: Pura Saal - Best Day & Best Time")
                st.markdown("Is section se aapko pata chalega ke is coin ko exactly kis din aur kis time trade karna sab se zyada safe hai.")
                
                b1, b2 = st.columns(2)
                with b1:
                    st.info(f"📅 **Sab Se Best Din:** {res['best_day']} \n\n (Win Rate: {res['best_day_win_rate']:.1f}%)")
                with b2:
                    st.info(f"⏰ **Sab Se Best Time:** {res['best_hour']:02d}:00 PKT \n\n (Win Rate: {res['best_win_rate']:.1f}%)")

                st.markdown("---")
                st.markdown("🧠 **Strategy Explained:** \n- **Macro Trend:** 200 EMA ke sath trend align hona zaroori hai.\n- **Entry:** Price pichli 5 candles ka low/high sweep (hunt) kare, aur foran ek Order Block (Engulfing) banaye.\n- **Exit:** Aapka diya gaya 1:2 R:R strict follow hoga.")

                bt_log = {"Date": (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"), "Coin": bt_coin, "R:R": f"1:{bt_rr}", "Candles": res['total_candles_analyzed'], "Gold Trades": g_tot, "Gold WinRate": f"{g_win:.1f}%", "Gold PnL": f"${res['golden']['pnl']:.2f}", "Best Hr": f"{res['best_hour']:02d}:00", "Best Day": res['best_day']}
                st.session_state['backtest_history'].append(bt_log)
                save_permanent_data(st.session_state['backtest_history'], BACKTEST_FILE)

elif selected == "📈 Pattern Book":
    st.title("📈 Technical & Fundamental Guide")
    t1, t2, t3 = st.tabs(["📊 Chart Patterns", "🕯️ Candlesticks", "🏢 Fundamental News"])
    with t1:
        st.subheader("Classic Chart Patterns (Technical)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""<div class="pattern-card"><img src="https://dummyimage.com/400x200/2B3139/0ECB81&text=Bull+Flag+Pattern" width="100%" style="border-radius: 8px;"><h4 style="color: #0ECB81; margin-top:10px;">1. Bull Flag (Tezi)</h4></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="pattern-card"><img src="https://dummyimage.com/400x200/2B3139/F6465D&text=Head+%26+Shoulders" width="100%" style="border-radius: 8px;"><h4 style="color: #F6465D; margin-top:10px;">3. Head and Shoulders (Girawat)</h4></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="pattern-card"><img src="https://dummyimage.com/400x200/2B3139/F6465D&text=Bear+Flag+Pattern" width="100%" style="border-radius: 8px;"><h4 style="color: #F6465D; margin-top:10px;">2. Bear Flag (Mandi)</h4></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="pattern-card"><img src="https://dummyimage.com/400x200/2B3139/0ECB81&text=Double+Bottom+(W)" width="100%" style="border-radius: 8px;"><h4 style="color: #0ECB81; margin-top:10px;">4. Double Bottom (W-Pattern)</h4></div>""", unsafe_allow_html=True)
    with t2:
        st.subheader("Candlestick Patterns")
        c3, c4 = st.columns(2)
        with c3: st.markdown("""<div class="pattern-card"><h4 style="color: #0ECB81;">Hammer (Hathora)</h4></div>""", unsafe_allow_html=True)
        with c4: st.markdown("""<div class="pattern-card"><h4 style="color: #F6465D;">Shooting Star</h4></div>""", unsafe_allow_html=True)
    with t3:
        st.subheader("Fundamental Events")
        st.markdown("""<div class="news-card"><h4>🔴 US CPI Data (Mehgai)</h4></div>""", unsafe_allow_html=True)

elif selected == "🧠 Pro Academy":
    st.title("🧠 Elite Trader Academy")
    tab1, tab2 = st.tabs(["📚 Top Books & Links", "💡 Daily Tips"])
    with tab1:
        books = [
            {"title": "1. Trading in the Zone", "author": "Mark Douglas", "url": "https://www.amazon.com/Trading-Zone-Confidence-Discipline-Attitude/dp/0735201447"},
            {"title": "2. Volume Price Analysis", "author": "Anna Coulling", "url": "https://www.amazon.com/Complete-Guide-Volume-Price-Analysis/dp/1491249390"}
        ]
        c1, c2 = st.columns(2)
        for i, book in enumerate(books):
            col = c1 if i % 2 == 0 else c2
            with col:
                st.markdown(f"""<div class="book-card"><h4 style="margin-top: 0; color: #F6465D;">{book['title']}</h4><p style="color: #848E9C; font-size: 13px; font-weight: bold;">{book['author']}</p><a href="{book['url']}" target="_blank" style="color: #5C82FF; text-decoration: none; font-size: 14px; font-weight:bold;">👉 Book Dekhein</a></div>""", unsafe_allow_html=True)
    with tab2:
        st.markdown("### 🎲 Aaj Ke Golden Rules:")
        st.markdown("""<div class="lesson-card"><h4 style="color: #0ECB81; margin-top: 0;">Rule 1:</h4><p style="font-size: 16px; margin-bottom: 0;">Stop Loss ko kabhi move na karein.</p></div>""", unsafe_allow_html=True)

elif selected == "📓 Journal":
    st.title("📓 Mera Trading Journal")
    st.subheader("1. Live Trade History")
    if len(st.session_state['trade_history']) > 0: st.dataframe(pd.DataFrame(st.session_state['trade_history']), use_container_width=True)
    else: st.warning("Abhi tak koi live trade save nahi hui.")
    st.markdown("---")
    st.subheader("2. Backtest Reports")
    if len(st.session_state['backtest_history']) > 0: st.dataframe(pd.DataFrame(st.session_state['backtest_history']), use_container_width=True)
    else: st.warning("Abhi tak koi backtest save nahi hua.")
    st.markdown("---")
    if st.button("🗑️ Sab Kuch Clear Karein"):
        st.session_state['trade_history'] = []; st.session_state['backtest_history'] = []; st.session_state['learning_history'] = []
        for f in [TRADE_FILE, BACKTEST_FILE, LEARNING_FILE]: 
            if os.path.exists(f): os.remove(f)
        st.rerun()
