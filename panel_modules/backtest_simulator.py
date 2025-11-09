"""
Trade simulation utilities for backtesting
"""
from typing import List, Dict, Optional


def simulate_trades(signals: List[Dict], position_size: float) -> List[Dict]:
    """
    Simulate trades based on signals with USD position size
    
    Args:
        signals: List of signal dictionaries with 'action', 'price', 'timestamp', 'rsi'
        position_size: Position size in USD
        
    Returns:
        List of completed trades with P&L
    """
    trades = []
    position = None
    
    for signal in signals:
        if signal['action'] == 'BUY' and position is None:
            # Open long position
            position = {
                'entry_time': signal['timestamp'],
                'entry_price': signal['price'],
                'entry_rsi': signal['rsi'],
                'size_usd': position_size
            }
        
        elif signal['action'] == 'SELL' and position is not None:
            # Close position
            pnl_pct = ((signal['price'] - position['entry_price']) / position['entry_price']) * 100
            profit_usd = (pnl_pct / 100) * position['size_usd']
            
            trades.append({
                'entry_time': position['entry_time'],
                'entry_price': position['entry_price'],
                'exit_time': signal['timestamp'],
                'exit_price': signal['price'],
                'pnl_pct': pnl_pct,
                'profit_usd': profit_usd
            })
            
            position = None
    
    return trades


def calculate_trade_statistics(trades: List[Dict]) -> Optional[Dict]:
    """
    Calculate statistics from completed trades
    
    Args:
        trades: List of completed trades
        
    Returns:
        Dictionary with trade statistics or None if no trades
    """
    if not trades:
        return None
    
    winning_trades = [t for t in trades if t['profit_usd'] > 0]
    losing_trades = [t for t in trades if t['profit_usd'] <= 0]
    
    total_profit = sum(t['profit_usd'] for t in trades)
    win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
    avg_profit = total_profit / len(trades) if trades else 0
    
    return {
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_profit_usd': total_profit,
        'avg_profit': avg_profit
    }
