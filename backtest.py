import json
import os
import sys

DATA_SPACE_FILE = "data.js"
DATA_QUANTUM_FILE = "data_quantum.js"
OUTPUT_PERF_FILE = "performance.js"

def load_dataset(filepath):
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx == -1 or end_idx == -1:
            return {}
        return json.loads(content[start_idx:end_idx+1])
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def run_backtest():
    space_data = load_dataset(DATA_SPACE_FILE)
    quantum_data = load_dataset(DATA_QUANTUM_FILE)
    
    all_stocks = []
    if space_data:
        for t, s in space_data.get('stocks', {}).items():
            s['sector'] = 'Space'
            all_stocks.append(s)
    if quantum_data:
        for t, s in quantum_data.get('stocks', {}).items():
            s['sector'] = 'Quantum'
            all_stocks.append(s)
            
    trades = []
    
    for stock in all_stocks:
        ticker = stock.get('ticker')
        sector = stock.get('sector')
        history = stock.get('history', [])
        
        if len(history) < 30:
            continue
            
        # We simulate trading over the middle segment of history (e.g. from index 10 to index len-10)
        # to allow enough technical context before and trading window after
        for i in range(10, len(history) - 10):
            day_data = history[i]
            close_price = day_data.get('close', 0.0)
            rsi = day_data.get('rsi', 50.0)
            bb_upper = day_data.get('bb_upper', 0.0)
            bb_lower = day_data.get('bb_lower', 0.0)
            bb_middle = day_data.get('bb_middle', 0.0)
            
            if not bb_upper or not bb_lower:
                continue
                
            entry_date = day_data.get('date')
            signal = None
            entry_price = close_price
            target = 0.0
            stop = 0.0
            
            # 1. Check for Buy setup (Mean reversion from lower Bollinger Band)
            if entry_price <= bb_lower or rsi <= 30.0:
                signal = 'BUY'
                target = bb_middle if bb_middle > entry_price else entry_price * 1.08
                stop = entry_price * 0.92
                
            # 2. Check for Short setup (Mean reversion from upper Bollinger Band)
            elif entry_price >= bb_upper or rsi >= 70.0:
                signal = 'SHORT'
                target = bb_middle if bb_middle < entry_price else entry_price * 0.92
                stop = entry_price * 1.08
                
            if signal:
                # To prevent overlapping trades of same signal on consecutive days, we skip if we recently opened one
                already_exists = False
                for t in trades:
                    if t['ticker'] == ticker and t['signal'] == signal and abs(history.index(day_data) - t['entry_index']) < 5:
                        already_exists = True
                        break
                if already_exists:
                    continue
                    
                # Track subsequent days to find trade resolution
                outcome = 'ACTIVE'
                exit_price = entry_price
                exit_date = 'Open Position'
                pnl = 0.0
                resolution_index = len(history) - 1
                
                for j in range(i + 1, len(history)):
                    chk_day = history[j]
                    high = chk_day.get('high', chk_day.get('close'))
                    low = chk_day.get('low', chk_day.get('close'))
                    close = chk_day.get('close')
                    
                    if signal == 'BUY':
                        # Check stop loss first (conservative approach)
                        if low <= stop:
                            outcome = 'LOSS'
                            exit_price = stop
                            exit_date = chk_day.get('date')
                            resolution_index = j
                            break
                        # Check target limit
                        elif high >= target:
                            outcome = 'WIN'
                            exit_price = target
                            exit_date = chk_day.get('date')
                            resolution_index = j
                            break
                    elif signal == 'SHORT':
                        # Check stop loss (short price rises)
                        if high >= stop:
                            outcome = 'LOSS'
                            exit_price = stop
                            exit_date = chk_day.get('date')
                            resolution_index = j
                            break
                        # Check cover target (short price drops)
                        elif low <= target:
                            outcome = 'WIN'
                            exit_price = target
                            exit_date = chk_day.get('date')
                            resolution_index = j
                            break
                            
                # Calculate return
                if signal == 'BUY':
                    if outcome == 'ACTIVE':
                        exit_price = history[-1].get('close')
                        exit_date = history[-1].get('date')
                    pnl = ((exit_price / entry_price) - 1.0) * 100
                elif signal == 'SHORT':
                    if outcome == 'ACTIVE':
                        exit_price = history[-1].get('close')
                        exit_date = history[-1].get('date')
                    pnl = (1.0 - (exit_price / entry_price)) * 100
                    
                trades.append({
                    'ticker': ticker,
                    'sector': sector,
                    'signal': signal,
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'target': target,
                    'stop': stop,
                    'exit_date': exit_date,
                    'exit_price': exit_price,
                    'outcome': outcome,
                    'pnl': pnl,
                    'entry_index': i,
                    'resolution_index': resolution_index
                })
                
    # Compile statistics
    closed_trades = [t for t in trades if t['outcome'] != 'ACTIVE']
    wins = [t for t in closed_trades if t['outcome'] == 'WIN']
    losses = [t for t in closed_trades if t['outcome'] == 'LOSS']
    
    total_trades = len(trades)
    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0.0
    avg_return = (sum(t['pnl'] for t in trades) / total_trades) if total_trades else 0.0
    
    # Calculate paper trading account performance (Starting Capital $100,000, risk $2,000 per trade)
    starting_capital = 100000.0
    net_pnl_dollars = 0.0
    for t in trades:
        # We allocate $10,000 paper capital per trade
        trade_allocation = 10000.0
        trade_profit = trade_allocation * (t['pnl'] / 100.0)
        net_pnl_dollars += trade_profit
        
    ending_capital = starting_capital + net_pnl_dollars
    net_return_pct = (net_pnl_dollars / starting_capital) * 100
    
    # Keep only a clean subset of trades to keep the database size fast and neat
    # Sort trades by entry date descending
    trades.sort(key=lambda x: x['entry_date'], reverse=True)
    
    perf_data = {
        "summary": {
            "totalTrades": total_trades,
            "closedTrades": len(closed_trades),
            "wins": len(wins),
            "losses": len(losses),
            "winRate": round(win_rate, 1),
            "avgReturn": round(avg_return, 2),
            "startingCapital": starting_capital,
            "endingCapital": round(ending_capital, 2),
            "netProfitDollars": round(net_pnl_dollars, 2),
            "netReturnPct": round(net_return_pct, 2)
        },
        "trades": trades[:50] # Top 50 most recent historical setups for display
    }
    
    with open(OUTPUT_PERF_FILE, 'w') as f:
        f.write(f"window.PERFORMANCE_DATA = {json.dumps(perf_data, indent=2)};\n")
        
    print(f"==================================================")
    print(f"        QUANTITATIVE BACKTEST COMPLETED           ")
    print(f"==================================================")
    print(f"Total Trades Tracked : {total_trades}")
    print(f"Win Rate             : {win_rate:.1f}%")
    print(f"Average P&L Return   : {avg_return:+.2f}%")
    print(f"Net Paper Profit     : ${net_pnl_dollars:,.2f} ({net_return_pct:+.2f}%)")
    print(f"Performance database written to '{OUTPUT_PERF_FILE}'.\n")

if __name__ == '__main__':
    run_backtest()
