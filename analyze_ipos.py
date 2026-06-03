import json
import os
import sys
import datetime
import traceback

IPO_INFO = {
    'CBRS': {'name': 'Cerebras Systems Inc.', 'ipo_price': 185.00, 'ipo_date': '2026-05-14'},
    'FRVO': {'name': 'Fervo Energy Company', 'ipo_price': 27.00, 'ipo_date': '2026-05-14'},
    'LCLN': {'name': 'Lincoln International, Inc.', 'ipo_price': 20.00, 'ipo_date': '2026-05-21'},
    'BXDC': {'name': 'Blackstone Digital Infrastructure Trust Inc.', 'ipo_price': 20.00, 'ipo_date': '2026-05-14'},
    'VIDA': {'name': 'VIDA Global Inc.', 'ipo_price': 4.00, 'ipo_date': '2026-05-15'},
    'HAWK': {'name': 'HawkEye 360, Inc.', 'ipo_price': 26.00, 'ipo_date': '2026-05-07'},
    'ODTX': {'name': 'Odyssey Therapeutics, Inc.', 'ipo_price': 18.00, 'ipo_date': '2026-05-08'},
    'SUJA': {'name': 'Suja Life, Inc.', 'ipo_price': 21.00, 'ipo_date': '2026-05-07'},
    'PWRL': {'name': 'Powerlaw Corp. (SpaceX Proxy)', 'ipo_price': 20.00, 'ipo_date': '2026-05-27'}
}

def main():
    print("Starting IPO Technical Analysis script...")
    
    try:
        import pandas as pd
        import numpy as np
        import yfinance as yf
    except ImportError:
        print("ERROR: Required packages (pandas, numpy, yfinance) are not installed.")
        sys.exit(1)
        
    results = {}
    last_trading_day_str = None
    
    for ticker, info in IPO_INFO.items():
        print(f"Fetching data for IPO {ticker} ({info['name']})...")
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3mo") # get all history since IPO
            
            if df.empty or len(df) < 2:
                print(f"  WARNING: Insufficient or empty data returned for {ticker}. Skipping.")
                continue
                
            df = df.sort_index()
            close = df['Close']
            high = df['High']
            low = df['Low']
            
            # Simple metrics
            df['Daily_Return'] = df['Close'].pct_change() * 100
            
            # Calculate 52-week equivalent metrics (since IPO is < 52 weeks, these are max/min since IPO)
            high_52w = float(high.max())
            low_52w = float(low.min())
            avg_volume = float(df['Volume'].mean())
            
            # Retrieve sector and news safely
            try:
                stock_info = stock.info
                sector = stock_info.get('sector', 'Technology' if ticker in ['CBRS', 'VIDA'] else 'Other')
            except Exception:
                sector = 'Technology' if ticker in ['CBRS', 'VIDA'] else 'Other'
                
            news_headline = "No recent headlines."
            try:
                news_items = stock.news
                if news_items and len(news_items) > 0:
                    news_headline = news_items[0].get('content', {}).get('title', news_items[0].get('title', "No headline available."))
            except Exception:
                pass
                
            # Adaptive Technical Scoring Engine
            n_days = len(df)
            scores = {}
            explanations = {}
            
            # 1. RSI (14 or shorter lookback if history is short)
            rsi_period = min(14, n_days - 1)
            if rsi_period >= 2:
                delta = close.diff()
                gain = delta.where(delta > 0, 0.0)
                loss = -delta.where(delta < 0, 0.0)
                roll_gain = gain.ewm(alpha=1/rsi_period, adjust=False).mean()
                roll_loss = loss.ewm(alpha=1/rsi_period, adjust=False).mean()
                rs = roll_gain / (roll_loss + 1e-9)
                df['RSI'] = 100 - (100 / (1 + rs))
                rsi_val = float(df['RSI'].iloc[-1])
                
                if rsi_val < 30:
                    scores['RSI'] = 1.0
                    explanations['RSI'] = f"Oversold RSI ({rsi_val:.1f}). Bounce potential."
                elif rsi_val < 40:
                    scores['RSI'] = 0.5
                    explanations['RSI'] = f"Near support RSI ({rsi_val:.1f})."
                elif rsi_val > 70:
                    scores['RSI'] = -1.0
                    explanations['RSI'] = f"Overbought RSI ({rsi_val:.1f}). Correction risk."
                elif rsi_val > 60:
                    scores['RSI'] = -0.5
                    explanations['RSI'] = f"Near resistance RSI ({rsi_val:.1f})."
                else:
                    scores['RSI'] = 0.0
                    explanations['RSI'] = f"Neutral RSI ({rsi_val:.1f})."
            else:
                scores['RSI'] = 0.0
                explanations['RSI'] = "Insufficient history for RSI."
                rsi_val = 50.0

            # 2. Bollinger Bands (Adaptive window)
            bb_window = min(20, n_days)
            if bb_window >= 2:
                df['BB_Middle'] = close.rolling(window=bb_window).mean()
                df['BB_Std'] = close.rolling(window=bb_window).std()
                df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
                df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])
                
                curr_price = float(close.iloc[-1])
                bb_mid = float(df['BB_Middle'].iloc[-1])
                bb_up = float(df['BB_Upper'].iloc[-1]) if not pd.isna(df['BB_Upper'].iloc[-1]) else curr_price * 1.05
                bb_low = float(df['BB_Lower'].iloc[-1]) if not pd.isna(df['BB_Lower'].iloc[-1]) else curr_price * 0.95
                
                if curr_price <= bb_low * 1.01:
                    scores['Bollinger'] = 1.0
                    explanations['Bollinger'] = "Price at lower Bollinger Band. Discounted price."
                elif curr_price >= bb_up * 0.99:
                    scores['Bollinger'] = -1.0
                    explanations['Bollinger'] = "Price at upper Bollinger Band. Overextended price."
                elif curr_price < bb_mid:
                    scores['Bollinger'] = 0.2
                    explanations['Bollinger'] = "Trading below middle band, near support."
                else:
                    scores['Bollinger'] = -0.2
                    explanations['Bollinger'] = "Trading above middle band, near resistance."
            else:
                scores['Bollinger'] = 0.0
                explanations['Bollinger'] = "Insufficient history for Bollinger Bands."
                bb_mid = curr_price = float(close.iloc[-1])
                bb_up = curr_price * 1.05
                bb_low = curr_price * 0.95

            # 3. MACD (Adaptive fast/slow spans)
            macd_fast = min(12, max(2, n_days // 4))
            macd_slow = min(26, max(3, n_days // 2))
            macd_signal = min(9, max(2, n_days // 6))
            
            if macd_slow > macd_fast and macd_fast >= 2:
                df['EMA_Fast'] = close.ewm(span=macd_fast, adjust=False).mean()
                df['EMA_Slow'] = close.ewm(span=macd_slow, adjust=False).mean()
                df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
                df['MACD_Sig'] = df['MACD'].ewm(span=macd_signal, adjust=False).mean()
                df['MACD_Hist'] = df['MACD'] - df['MACD_Sig']
                
                macd_val = float(df['MACD'].iloc[-1])
                macd_sig_val = float(df['MACD_Sig'].iloc[-1])
                macd_hist_val = float(df['MACD_Hist'].iloc[-1])
                
                if macd_val > macd_sig_val:
                    scores['MACD'] = 0.8
                    explanations['MACD'] = "Bullish MACD crossover."
                else:
                    scores['MACD'] = -0.8
                    explanations['MACD'] = "Bearish MACD crossover."
            else:
                scores['MACD'] = 0.0
                explanations['MACD'] = "Insufficient history for MACD."
                macd_val = 0.0
                macd_sig_val = 0.0
                macd_hist_val = 0.0

            # 4. Stochastic (Adaptive window)
            stoch_window = min(14, n_days)
            if stoch_window >= 2:
                low_st = low.rolling(window=stoch_window).min()
                high_st = high.rolling(window=stoch_window).max()
                denom = high_st - low_st + 1e-9
                df['Stoch_K'] = 100 * ((close - low_st) / denom)
                df['Stoch_D'] = df['Stoch_K'].rolling(window=min(3, n_days)).mean()
                
                stoch_k = float(df['Stoch_K'].iloc[-1])
                stoch_d = float(df['Stoch_D'].iloc[-1])
                
                if stoch_k < 20:
                    scores['Stochastic'] = 0.8
                    explanations['Stochastic'] = f"Oversold (%K: {stoch_k:.1f})."
                elif stoch_k > 80:
                    scores['Stochastic'] = -0.8
                    explanations['Stochastic'] = f"Overbought (%K: {stoch_k:.1f})."
                else:
                    scores['Stochastic'] = 0.0
                    explanations['Stochastic'] = "Stochastic neutral."
            else:
                scores['Stochastic'] = 0.0
                explanations['Stochastic'] = "Insufficient history for Stochastic."
                stoch_k = 50.0
                stoch_d = 50.0

            # 5. Trend (EMA crossover or simple price vs middle band)
            ema_fast_w = min(9, n_days)
            ema_slow_w = min(21, n_days)
            if ema_slow_w > ema_fast_w and ema_fast_w >= 2:
                df['EMA_Fast_Cross'] = close.ewm(span=ema_fast_w, adjust=False).mean()
                df['EMA_Slow_Cross'] = close.ewm(span=ema_slow_w, adjust=False).mean()
                ema_f = float(df['EMA_Fast_Cross'].iloc[-1])
                ema_s = float(df['EMA_Slow_Cross'].iloc[-1])
                
                if ema_f > ema_s:
                    scores['EMA'] = 0.6
                    explanations['EMA'] = "Bullish short-term EMA trend."
                else:
                    scores['EMA'] = -0.6
                    explanations['EMA'] = "Bearish short-term EMA trend."
            else:
                scores['EMA'] = 0.0
                explanations['EMA'] = "Insufficient history for EMA trend."

            # Calculate composite score & consensus signal
            valid_scores = [v for v in scores.values() if not pd.isna(v)]
            comp_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
            
            if comp_score >= 0.25:
                consensus_signal = "BUY"
            elif comp_score <= -0.25:
                consensus_signal = "SELL"
            else:
                consensus_signal = "HOLD"

            # Formulate history list for modal chart (max 60 days)
            history_data = []
            for date_idx, r in df.iterrows():
                history_data.append({
                    'date': date_idx.strftime('%m-%d'),
                    'close': float(r['Close']),
                    'volume': int(r['Volume']),
                    'rsi': float(r['RSI']) if 'RSI' in r and not pd.isna(r['RSI']) else None,
                    'macd': float(r['MACD']) if 'MACD' in r and not pd.isna(r['MACD']) else None,
                    'macd_signal': float(r['MACD_Sig']) if 'MACD_Sig' in r and not pd.isna(r['MACD_Sig']) else None,
                    'bb_upper': float(r['BB_Upper']) if 'BB_Upper' in r and not pd.isna(r['BB_Upper']) else None,
                    'bb_lower': float(r['BB_Lower']) if 'BB_Lower' in r and not pd.isna(r['BB_Lower']) else None,
                    'bb_middle': float(r['BB_Middle']) if 'BB_Middle' in r and not pd.isna(r['BB_Middle']) else None,
                    'stoch_k': float(r['Stoch_K']) if 'Stoch_K' in r and not pd.isna(r['Stoch_K']) else None,
                    'stoch_d': float(r['Stoch_D']) if 'Stoch_D' in r and not pd.isna(r['Stoch_D']) else None
                })

            # --- New Apex Shorts Calculations ---
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
            major_backing = "Significant Institutional Support" if inst_percent >= 0.40 else "None Identified"
            if ticker in ['CBRS', 'HAWK', 'PWRL']:
                major_backing = "Venture Backed / Strategic Partners"
                
            has_big_news = "YES - Catalyst Active" if news_headline != "No recent headlines." else "NO - Quiet Session"
            
            curr_price = float(close.iloc[-1])
            # Volatility approximation since ATR is not calculated, we use standard deviation or default to 3%
            sd_val = float(df['BB_Std'].iloc[-1]) if 'BB_Std' in df and not pd.isna(df['BB_Std'].iloc[-1]) else curr_price * 0.03
            if sd_val <= 0:
                sd_val = curr_price * 0.03
                
            # Volatility-based Short Exit Target (Mean Reversion Cover Target) & Stop Loss
            cover_price = min(bb_mid, curr_price - (2.0 * sd_val))
            short_sl = curr_price + (1.5 * sd_val)
            
            cover_price = max(0.01, round(cover_price, 2))
            short_sl = max(0.01, round(short_sl, 2))

            # Save result
            results[ticker] = {
                'ticker': ticker,
                'name': info['name'],
                'ipo_price': info['ipo_price'],
                'ipo_date': info['ipo_date'],
                'price': float(close.iloc[-1]),
                'change': float(close.iloc[-1] - close.iloc[-2]) if len(df) >= 2 else 0.0,
                'changePercent': float(df['Daily_Return'].iloc[-1]) if len(df) >= 2 and not pd.isna(df['Daily_Return'].iloc[-1]) else 0.0,
                'high_52w': high_52w,
                'low_52w': low_52w,
                'avg_volume': avg_volume,
                'sector': sector,
                'famous_news': news_headline,
                'compositeScore': comp_score,
                'signal': consensus_signal,
                'open': float(df['Open'].iloc[-1]),
                'high': float(df['High'].iloc[-1]),
                'low': float(df['Low'].iloc[-1]),
                'volume': int(df['Volume'].iloc[-1]),
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
                    'RSI': {'value': rsi_val, 'score': scores.get('RSI', 0.0), 'explanation': explanations.get('RSI', '')},
                    'MACD': {'value': macd_val, 'signal': macd_sig_val, 'score': scores.get('MACD', 0.0), 'explanation': explanations.get('MACD', '')},
                    'Bollinger': {'upper': bb_up, 'lower': bb_low, 'middle': bb_mid, 'score': scores.get('Bollinger', 0.0), 'explanation': explanations.get('Bollinger', '')},
                    'Stochastic': {'k': stoch_k, 'd': stoch_d, 'score': scores.get('Stochastic', 0.0), 'explanation': explanations.get('Stochastic', '')},
                    'EMA': {'ema9': float(df['EMA_Fast_Cross'].iloc[-1]) if 'EMA_Fast_Cross' in df else float(close.iloc[-1]), 
                            'ema21': float(df['EMA_Slow_Cross'].iloc[-1]) if 'EMA_Slow_Cross' in df else float(close.iloc[-1]), 
                            'score': scores.get('EMA', 0.0), 'explanation': explanations.get('EMA', '')},
                    'ADX': {'value': 0.0, 'plus_di': 0.0, 'minus_di': 0.0, 'score': 0.0, 'explanation': "Insufficient history for ADX"}
                },
                'history': history_data
            }
            
            # Setup last trading day
            if last_trading_day_str is None:
                last_trading_day_str = df.index[-1].strftime('%Y-%m-%d')
                
            print(f"  -> SUCCESS! Price: ${close.iloc[-1]:.2f} | IPO Price: ${info['ipo_price']} | Consensus: {consensus_signal}")
            
        except Exception as e:
            print(f"  -> ERROR analyzing {ticker}: {e}")
            traceback.print_exc()

    # Save to data_ipos.js
    output_filename = "data_ipos.js"
    payload = {
        'lastUpdated': last_trading_day_str or datetime.datetime.now().strftime('%Y-%m-%d'),
        'ipos': results
    }
    
    js_content = f"window.IPO_DATA = {json.dumps(payload, indent=2)};"
    
    with open(output_filename, 'w') as f:
        f.write(js_content)
        
    print(f"\nIPO analysis completed! Results written to '{output_filename}'.")

if __name__ == '__main__':
    main()
