"""
Results management for backtesting
"""
import os
import json
from datetime import datetime
from typing import List, Dict


def save_best_results(all_results: List[Dict], signal_name: str, 
                     timerange: str, position_size: float) -> None:
    """
    Save best results for each coin to results folder
    
    Args:
        all_results: List of all backtest results
        signal_name: Name of the signal being tested
        timerange: Time range tested
        position_size: Position size in USD
    """
    try:
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Group results by coin and get best for each
        coins_best = {}
        for result in all_results:
            coin = result['coin']
            if coin not in coins_best:
                coins_best[coin] = result
        
        # Save each coin's best result
        for coin, best_result in coins_best.items():
            filename = f"{coin}_{signal_name}_{timestamp}.json"
            filepath = os.path.join(results_dir, filename)
            
            save_data = {
                'coin': coin,
                'signal': signal_name,
                'timestamp': timestamp,
                'backtest_date': datetime.now().isoformat(),
                'timerange': timerange,
                'position_size_usd': position_size,
                'best_parameters': {
                    'period': best_result['period'],
                    'oversold': best_result['oversold'],
                    'overbought': best_result['overbought']
                },
                'performance': {
                    'total_profit_usd': best_result['total_profit_usd'],
                    'total_trades': best_result['total_trades'],
                    'winning_trades': best_result['winning_trades'],
                    'losing_trades': best_result['losing_trades'],
                    'win_rate': best_result['win_rate'],
                    'avg_profit': best_result['avg_profit'],
                    'signals_generated': best_result['signals_generated']
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"Saved best result for {coin} to {filepath}")
        
        print(f"Saved {len(coins_best)} coin configurations to {results_dir}/")
        
    except Exception as e:
        print(f"Error saving results: {e}")
        import traceback
        traceback.print_exc()


def group_best_results_by_coin(results: List[Dict]) -> List[Dict]:
    """
    Group results by coin and return best for each
    
    Args:
        results: List of all backtest results
        
    Returns:
        List of best results per coin, sorted by profit
    """
    coins_best = {}
    for result in results:
        coin = result['coin']
        if coin not in coins_best or result['total_profit_usd'] > coins_best[coin]['total_profit_usd']:
            coins_best[coin] = result
    
    best_per_coin = list(coins_best.values())
    best_per_coin.sort(key=lambda x: x['total_profit_usd'], reverse=True)
    
    return best_per_coin
