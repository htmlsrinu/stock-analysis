import json
import os
import sys
import datetime
import traceback

# List of space-related companies with tickers, categories, and full names
STOCK_SECTOR_INFO = {
    'RKLB': {'name': 'Rocket Lab USA, Inc.', 'category': 'Pure Play'},
    'LUNR': {'name': 'Intuitive Machines, Inc.', 'category': 'Pure Play'},
    'ASTS': {'name': 'AST SpaceMobile, Inc.', 'category': 'Pure Play'},
    'SPCE': {'name': 'Virgin Galactic Holdings, Inc.', 'category': 'Pure Play'},
    'PL': {'name': 'Planet Labs PBC', 'category': 'Pure Play'},
    'SPIR': {'name': 'Spire Global, Inc.', 'category': 'Pure Play'},
    'RDW': {'name': 'Redwire Corporation', 'category': 'Pure Play'},
    'BKSY': {'name': 'BlackSky Technology Inc.', 'category': 'Pure Play'},
    'SATL': {'name': 'Satellogic Inc.', 'category': 'Pure Play'},
    'SIDU': {'name': 'Sidus Space, Inc.', 'category': 'Pure Play'},
    'IRDM': {'name': 'Iridium Communications Inc.', 'category': 'Pure Play'},
    'VSAT': {'name': 'Viasat, Inc.', 'category': 'Pure Play'},
    'GSAT': {'name': 'Globalstar, Inc.', 'category': 'Pure Play'},
    'ASTC': {'name': 'Astrotech Corporation', 'category': 'Pure Play'},
    'PWRL': {'name': 'Powerlaw Corp. (SpaceX Proxy)', 'category': 'Pure Play'},
    
    'LMT': {'name': 'Lockheed Martin Corporation', 'category': 'Defense Giant'},
    'NOC': {'name': 'Northrop Grumman Corporation', 'category': 'Defense Giant'},
    'BA': {'name': 'The Boeing Company', 'category': 'Defense Giant'},
    'RTX': {'name': 'RTX Corporation', 'category': 'Defense Giant'},
    'LHX': {'name': 'L3Harris Technologies, Inc.', 'category': 'Defense Giant'},
    
    'HWM': {'name': 'Howmet Aerospace Inc.', 'category': 'Aerospace Supplier'},
    'HEI': {'name': 'HEICO Corporation', 'category': 'Aerospace Supplier'},
    'HXL': {'name': 'Hexcel Corporation', 'category': 'Aerospace Supplier'}
}

def main():
    print("Starting Space Stock Technical Analysis script...")
    
    # Try importing required packages, exit if they aren't ready
    try:
        import pandas as pd
        import numpy as np
        import yfinance as yf
    except ImportError:
        print("ERROR: Required packages (pandas, numpy, yfinance) are not installed or are still installing in the background.")
        sys.exit(1)
        
    print(f"Libraries imported successfully. Ticker count: {len(STOCK_SECTOR_INFO)}")
    
    results = {}
    last_trading_day_str = None
    
    for ticker, info in STOCK_SECTOR_INFO.items():
        print(f"Fetching data for {ticker} ({info['name']})...")
        try:
            # Download 300 days of daily data to have plenty of historical cushion for 200 SMA and ADX
            stock = yf.Ticker(ticker)
            df = stock.history(period="18mo")
            
            if df.empty or len(df) < 50:
                print(f"  WARNING: Insufficient or empty data returned for {ticker}. Skipping.")
                continue
                
            print(f"  Downloaded {len(df)} rows. Calculating indicators...")
            
            # 1. Clean & compute indicators
            df = df.sort_index()
            
            # Store price metrics
            close = df['Close']
            high = df['High']
            low = df['Low']
            
            # Simple metrics
            df['Daily_Return'] = df['Close'].pct_change() * 100
            
            # Relative Strength Index (RSI - 14 Days)
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            
            # Wilder's Smoothing for RSI
            roll_gain = gain.ewm(alpha=1/14, adjust=False).mean()
            roll_loss = loss.ewm(alpha=1/14, adjust=False).mean()
            rs = roll_gain / (roll_loss + 1e-9)
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD (12, 26, 9)
            df['EMA12'] = close.ewm(span=12, adjust=False).mean()
            df['EMA26'] = close.ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            df['MACD_Hist_prev'] = df['MACD_Hist'].shift(1)
            
            # Bollinger Bands (20, 2)
            df['BB_Middle'] = close.rolling(window=20).mean()
            df['BB_Std'] = close.rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
            df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])
            
            # Stochastic Oscillator (14, 3)
            low_14 = low.rolling(window=14).min()
            high_14 = high.rolling(window=14).max()
            # Avoid division by zero
            denom = high_14 - low_14 + 1e-9
            df['Stoch_K'] = 100 * ((close - low_14) / denom)
            df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
            df['Stoch_K_prev'] = df['Stoch_K'].shift(1)
            df['Stoch_D_prev'] = df['Stoch_D'].shift(1)
            
            # EMA/SMA Trend Lines
            df['EMA9'] = close.ewm(span=9, adjust=False).mean()
            df['EMA21'] = close.ewm(span=21, adjust=False).mean()
            df['SMA50'] = close.rolling(window=50).mean()
            df['SMA200'] = close.rolling(window=200).mean()
            
            # ADX (Average Directional Index - 14)
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            up_move = high.diff()
            down_move = -low.diff()
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
            
            atr = tr.ewm(alpha=1/14, adjust=False).mean()
            plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / (atr + 1e-9)
            minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / (atr + 1e-9)
            
            dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
            adx = dx.ewm(alpha=1/14, adjust=False).mean()
            
            df['ATR'] = atr
            df['Plus_DI'] = plus_di
            df['Minus_DI'] = minus_di
            df['ADX'] = adx
            
            # 2. Get last trading day data
            last_row = df.iloc[-1]
            last_idx = df.index[-1]
            
            # Set global last trading day string (e.g. "2026-05-15")
            if last_trading_day_str is None:
                last_trading_day_str = last_idx.strftime('%Y-%m-%d')
                
            # Current price details
            curr_price = float(last_row['Close'])
            prev_price = float(df['Close'].iloc[-2]) if len(df) >= 2 else curr_price
            price_change = curr_price - prev_price
            price_change_pct = float(last_row['Daily_Return']) if not pd.isna(last_row['Daily_Return']) else 0.0
            
            # 3. Scoring Engine
            scores = {}
            explanations = {}
            
            # RSI Analysis
            rsi_val = float(last_row['RSI'])
            if pd.isna(rsi_val):
                scores['RSI'] = 0.0
                explanations['RSI'] = "No RSI data available."
            elif rsi_val < 30:
                scores['RSI'] = 1.0
                explanations['RSI'] = f"Oversold ({rsi_val:.1f}). Strong bounce potential."
            elif rsi_val < 40:
                scores['RSI'] = 0.5
                explanations['RSI'] = f"Near support ({rsi_val:.1f}). Moderate buying momentum."
            elif rsi_val > 70:
                scores['RSI'] = -1.0
                explanations['RSI'] = f"Overbought ({rsi_val:.1f}). High risk of fatigue and correction."
            elif rsi_val > 60:
                scores['RSI'] = -0.5
                explanations['RSI'] = f"Near resistance ({rsi_val:.1f}). Overextended short-term."
            else:
                scores['RSI'] = 0.0
                explanations['RSI'] = f"Neutral RSI ({rsi_val:.1f}). Stable trading."
                
            # MACD Analysis
            macd_val = float(last_row['MACD'])
            macd_sig = float(last_row['MACD_Signal'])
            macd_hist = float(last_row['MACD_Hist'])
            macd_hist_prev = float(last_row['MACD_Hist_prev']) if not pd.isna(last_row['MACD_Hist_prev']) else 0.0
            
            if pd.isna(macd_val) or pd.isna(macd_sig):
                scores['MACD'] = 0.0
                explanations['MACD'] = "No MACD data available."
            else:
                if macd_val > macd_sig:
                    if macd_hist > macd_hist_prev:
                        scores['MACD'] = 1.0
                        explanations['MACD'] = f"Bullish MACD crossover, positive momentum expanding (Hist: {macd_hist:.3f})."
                    else:
                        scores['MACD'] = 0.5
                        explanations['MACD'] = f"Bullish MACD crossover, but momentum tapering (Hist: {macd_hist:.3f})."
                else:
                    if macd_hist < macd_hist_prev:
                        scores['MACD'] = -1.0
                        explanations['MACD'] = f"Bearish MACD crossover, negative momentum expanding (Hist: {macd_hist:.3f})."
                    else:
                        scores['MACD'] = -0.5
                        explanations['MACD'] = f"Bearish MACD crossover, but contraction slowing (Hist: {macd_hist:.3f})."

            # Bollinger Bands Analysis
            bb_mid = float(last_row['BB_Middle'])
            bb_up = float(last_row['BB_Upper'])
            bb_low = float(last_row['BB_Lower'])
            
            if pd.isna(bb_up) or pd.isna(bb_low):
                scores['Bollinger'] = 0.0
                explanations['Bollinger'] = "No Bollinger Band data."
            else:
                if curr_price <= bb_low * 1.01:
                    scores['Bollinger'] = 1.0
                    explanations['Bollinger'] = f"Price at lower Bollinger Band (${curr_price:.2f} <= Lower: ${bb_low:.2f}). Severe discount."
                elif curr_price >= bb_up * 0.99:
                    scores['Bollinger'] = -1.0
                    explanations['Bollinger'] = f"Price at upper Bollinger Band (${curr_price:.2f} >= Upper: ${bb_up:.2f}). Overextended premium."
                elif curr_price < bb_mid:
                    scores['Bollinger'] = 0.2
                    explanations['Bollinger'] = f"Trading in lower channel (${curr_price:.2f} < Mid: ${bb_mid:.2f}), approaching support."
                else:
                    scores['Bollinger'] = -0.2
                    explanations['Bollinger'] = f"Trading in upper channel (${curr_price:.2f} > Mid: ${bb_mid:.2f}), approaching resistance."

            # Stochastic Oscillator Analysis
            stoch_k = float(last_row['Stoch_K'])
            stoch_d = float(last_row['Stoch_D'])
            stoch_k_prev = float(last_row['Stoch_K_prev']) if not pd.isna(last_row['Stoch_K_prev']) else 0.0
            stoch_d_prev = float(last_row['Stoch_D_prev']) if not pd.isna(last_row['Stoch_D_prev']) else 0.0
            
            if pd.isna(stoch_k) or pd.isna(stoch_d):
                scores['Stochastic'] = 0.0
                explanations['Stochastic'] = "No Stochastic data."
            else:
                if stoch_k < 20:
                    if stoch_k > stoch_d and stoch_k_prev <= stoch_d_prev:
                        scores['Stochastic'] = 1.0
                        explanations['Stochastic'] = f"Bullish Stochastic crossover in oversold territory (K: {stoch_k:.1f} > D: {stoch_d:.1f})."
                    else:
                        scores['Stochastic'] = 0.5
                        explanations['Stochastic'] = f"Oversold territory (%K: {stoch_k:.1f}). Buying pressure forming."
                elif stoch_k > 80:
                    if stoch_k < stoch_d and stoch_k_prev >= stoch_d_prev:
                        scores['Stochastic'] = -1.0
                        explanations['Stochastic'] = f"Bearish Stochastic crossover in overbought territory (K: {stoch_k:.1f} < D: {stoch_d:.1f})."
                    else:
                        scores['Stochastic'] = -0.5
                        explanations['Stochastic'] = f"Overbought territory (%K: {stoch_k:.1f}). Selling pressure forming."
                else:
                    if stoch_k > stoch_d and stoch_k_prev <= stoch_d_prev:
                        scores['Stochastic'] = 0.3
                        explanations['Stochastic'] = f"Bullish crossover in neutral zone (%K: {stoch_k:.1f})."
                    elif stoch_k < stoch_d and stoch_k_prev >= stoch_d_prev:
                        scores['Stochastic'] = -0.3
                        explanations['Stochastic'] = f"Bearish crossover in neutral zone (%K: {stoch_k:.1f})."
                    else:
                        scores['Stochastic'] = 0.0
                        explanations['Stochastic'] = f"Stochastic neutral (%K: {stoch_k:.1f})."

            # EMA Crossover & SMA Trends
            ema9 = float(last_row['EMA9'])
            ema21 = float(last_row['EMA21'])
            sma50 = float(last_row['SMA50']) if not pd.isna(last_row['SMA50']) else curr_price
            sma200 = float(last_row['SMA200']) if not pd.isna(last_row['SMA200']) else curr_price
            
            if pd.isna(ema9) or pd.isna(ema21):
                scores['EMA'] = 0.0
                explanations['EMA'] = "No EMA trend data."
            else:
                if ema9 > ema21:
                    if curr_price > ema9 and curr_price > sma50:
                        scores['EMA'] = 1.0
                        explanations['EMA'] = f"Strong short-term bullish trend: EMA9 (${ema9:.2f}) > EMA21 (${ema21:.2f}), Price above 50 SMA."
                    else:
                        scores['EMA'] = 0.5
                        explanations['EMA'] = f"Moderate bullish trend: EMA9 (${ema9:.2f}) > EMA21 (${ema21:.2f})."
                else:
                    if curr_price < ema9 and curr_price < sma50:
                        scores['EMA'] = -1.0
                        explanations['EMA'] = f"Strong short-term bearish trend: EMA9 (${ema9:.2f}) < EMA21 (${ema21:.2f}), Price below 50 SMA."
                    else:
                        scores['EMA'] = -0.5
                        explanations['EMA'] = f"Moderate bearish trend: EMA9 (${ema9:.2f}) < EMA21 (${ema21:.2f})."

            # ADX Trend Strength Analysis
            adx_val = float(last_row['ADX'])
            plus_di_val = float(last_row['Plus_DI'])
            minus_di_val = float(last_row['Minus_DI'])
            
            if pd.isna(adx_val) or pd.isna(plus_di_val) or pd.isna(minus_di_val):
                scores['ADX'] = 0.0
                explanations['ADX'] = "No trend strength data."
            else:
                if adx_val > 25:
                    if plus_di_val > minus_di_val:
                        scores['ADX'] = 1.0
                        explanations['ADX'] = f"Strong bullish trend active (ADX: {adx_val:.1f}, +DI > -DI)."
                    else:
                        scores['ADX'] = -1.0
                        explanations['ADX'] = f"Strong bearish trend active (ADX: {adx_val:.1f}, -DI > +DI)."
                else:
                    scores['ADX'] = 0.0
                    explanations['ADX'] = f"Weak or rangebound trend (ADX: {adx_val:.1f} < 25)."

            # Calculate composite score & consensus signal
            valid_scores = [v for v in scores.values() if not pd.isna(v)]
            comp_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
            
            if comp_score >= 0.35:
                consensus_signal = "BUY"
            elif comp_score <= -0.35:
                consensus_signal = "SELL"
            else:
                consensus_signal = "HOLD"
                
            # Calculate volatility-based Targets and Stop Loss
            atr_val = float(last_row['ATR']) if not pd.isna(last_row['ATR']) else (curr_price * 0.03)
            if atr_val <= 0:
                atr_val = curr_price * 0.03
                
            if consensus_signal == "SELL":
                # For SELL, targets are on the downside and stop loss is above
                st_target = curr_price - (1.5 * atr_val)
                mt_target = curr_price - (3.0 * atr_val)
                lt_target = curr_price - (6.0 * atr_val)
                stop_loss = curr_price + (2.0 * atr_val)
            else:
                # For BUY/HOLD, targets are on the upside and stop loss is below
                st_target = curr_price + (1.5 * atr_val)
                mt_target = curr_price + (3.0 * atr_val)
                lt_target = curr_price + (6.0 * atr_val)
                stop_loss = curr_price - (2.0 * atr_val)
                
            st_target = max(0.01, round(st_target, 2))
            mt_target = max(0.01, round(mt_target, 2))
            lt_target = max(0.01, round(lt_target, 2))
            stop_loss = max(0.01, round(stop_loss, 2))
            
            # --- New Apex Shorts Calculations ---
            # Fetch Ticker metadata (Info and News) safely
            try:
                ticker_info = stock.info
            except Exception:
                ticker_info = {}
                
            short_percent = float(ticker_info.get('shortPercentOfFloat', 0.0)) if ticker_info.get('shortPercentOfFloat') is not None else 0.0
            inst_percent = float(ticker_info.get('heldPercentInstitutions', 0.0)) if ticker_info.get('heldPercentInstitutions') is not None else 0.0
            shares_short = int(ticker_info.get('sharesShort', 0)) if ticker_info.get('sharesShort') is not None else 0
            days_to_cover = float(ticker_info.get('shortRatio', 0.0)) if ticker_info.get('shortRatio') is not None else 0.0
            
            # Short Squeeze Potential Evaluation
            squeeze_risk = "LOW"
            if short_percent >= 0.15 or days_to_cover >= 5:
                squeeze_risk = "HIGH"
            elif short_percent >= 0.08 or days_to_cover >= 3:
                squeeze_risk = "MODERATE"
                
            # Institutional / Large Investor Support
            inst_support = "LOW"
            if inst_percent >= 0.50:
                inst_support = "HIGH"
            elif inst_percent >= 0.25:
                inst_support = "MODERATE"
                
            # Determine if any Big Company / Insider is backing
            major_backing = "None Identified"
            if inst_percent >= 0.40:
                major_backing = "Significant Institutional Support"
            if ticker in ['RKLB', 'LUNR', 'ASTS', 'SPCE', 'RDW']:
                major_backing = "NASA / SpaceX / Industry Partners"
                
            # Fetch latest news headline
            news_headline = "No recent headlines."
            has_big_news = "NO - Quiet Session"
            try:
                news_items = stock.news
                if news_items and len(news_items) > 0:
                    news_headline = news_items[0].get('content', {}).get('title', "No headline available.")
                    has_big_news = "YES - Catalyst Active"
            except Exception:
                pass
                
            # Volatility-based Short Exit Target (Mean Reversion Cover Target) & Stop Loss
            cover_price = min(bb_mid, curr_price - (2.0 * atr_val))
            short_sl = curr_price + (1.5 * atr_val)
            
            cover_price = max(0.01, round(cover_price, 2))
            short_sl = max(0.01, round(short_sl, 2))
            # -------------------------------------
                
            # 4. Save historical chart data (past 60 trading days) for drawing charts
            hist_df = df.tail(60)
            history_data = []
            for date_idx, r in hist_df.iterrows():
                history_data.append({
                    'date': date_idx.strftime('%m-%d'),
                    'close': float(r['Close']),
                    'volume': int(r['Volume']),
                    'rsi': float(r['RSI']) if not pd.isna(r['RSI']) else None,
                    'macd': float(r['MACD']) if not pd.isna(r['MACD']) else None,
                    'macd_signal': float(r['MACD_Signal']) if not pd.isna(r['MACD_Signal']) else None,
                    'bb_upper': float(r['BB_Upper']) if not pd.isna(r['BB_Upper']) else None,
                    'bb_lower': float(r['BB_Lower']) if not pd.isna(r['BB_Lower']) else None,
                    'bb_middle': float(r['BB_Middle']) if not pd.isna(r['BB_Middle']) else None,
                    'stoch_k': float(r['Stoch_K']) if not pd.isna(r['Stoch_K']) else None,
                    'stoch_d': float(r['Stoch_D']) if not pd.isna(r['Stoch_D']) else None
                })
                
            # Compile final asset details
            results[ticker] = {
                'ticker': ticker,
                'name': info['name'],
                'category': info['category'],
                'price': curr_price,
                'change': price_change,
                'changePercent': price_change_pct,
                'high': float(last_row['High']),
                'low': float(last_row['Low']),
                'open': float(last_row['Open']),
                'volume': int(last_row['Volume']),
                'compositeScore': comp_score,
                'signal': consensus_signal,
                'targets': {
                    'shortTerm': st_target,
                    'mediumTerm': mt_target,
                    'longTerm': lt_target,
                    'stopLoss': stop_loss
                },
                'shortAnalysis': {
                    'shortPercent': round(short_percent * 100, 2),
                    'sharesShort': shares_short,
                    'daysToCover': days_to_cover,
                    'squeezeRisk': squeeze_risk,
                    'instPercent': round(inst_percent * 100, 2),
                    'instSupport': inst_support,
                    'majorBacking': major_backing,
                    'hasBigNews': has_big_news,
                    'latestHeadline': news_headline,
                    'recommendedCover': cover_price,
                    'shortStopLoss': short_sl,
                    'percentAboveBB': round(((curr_price / bb_up) - 1.0) * 100, 1) if bb_up > 0 else 0.0
                },
                'indicators': {
                    'RSI': {'value': rsi_val, 'score': scores['RSI'], 'explanation': explanations['RSI']},
                    'MACD': {'value': macd_val, 'signal': macd_sig, 'score': scores['MACD'], 'explanation': explanations['MACD']},
                    'Bollinger': {'upper': bb_up, 'lower': bb_low, 'middle': bb_mid, 'score': scores['Bollinger'], 'explanation': explanations['Bollinger']},
                    'Stochastic': {'k': stoch_k, 'd': stoch_d, 'score': scores['Stochastic'], 'explanation': explanations['Stochastic']},
                    'EMA': {'ema9': ema9, 'ema21': ema21, 'score': scores['EMA'], 'explanation': explanations['EMA']},
                    'ADX': {'value': adx_val, 'plus_di': plus_di_val, 'minus_di': minus_di_val, 'score': scores['ADX'], 'explanation': explanations['ADX']}
                },
                'history': history_data
            }
            
            print(f"  -> SUCCESS! Price: ${curr_price:.2f} | Change: {price_change_pct:+.2f}% | Consensus: {consensus_signal} (Score: {comp_score:.2f})")
            
        except Exception as e:
            print(f"  -> ERROR analyzing {ticker}: {e}")
            traceback.print_exc()

    # 5. Output data as a clean JavaScript file
    output_filename = "data.js"
    payload = {
        'lastUpdated': last_trading_day_str or datetime.datetime.now().strftime('%Y-%m-%d'),
        'stocks': results
    }
    
    js_content = f"window.STOCK_DATA = {json.dumps(payload, indent=2)};"
    
    with open(output_filename, 'w') as f:
        f.write(js_content)
        
    print(f"\nAnalysis completed successfully! Results written to '{output_filename}'.")
    
if __name__ == '__main__':
    main()
