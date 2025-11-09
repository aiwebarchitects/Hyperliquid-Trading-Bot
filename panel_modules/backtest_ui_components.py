"""
UI components for backtest results display
"""
import tkinter as tk
from typing import Dict, List


def create_result_row(parent, result: Dict, rank: int, colors: Dict) -> None:
    """
    Create a result row in the UI
    
    Args:
        parent: Parent tkinter widget
        result: Result dictionary
        rank: Rank number
        colors: Color scheme dictionary
    """
    row = tk.Frame(parent, bg=colors['bg_dark'] if rank % 2 == 0 else colors['bg_panel'])
    row.pack(fill=tk.X, padx=10, pady=1)
    
    # Rank
    rank_color = colors['green'] if rank <= 3 else colors['white']
    tk.Label(row, text=f"#{rank}", bg=row['bg'], fg=rank_color,
            font=('Courier', 8, 'bold'), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
    
    # Coin
    tk.Label(row, text=result['coin'], bg=row['bg'], fg=colors['white'],
            font=('Courier', 8), width=6, anchor='w').pack(side=tk.LEFT, padx=2)
    
    # Period
    tk.Label(row, text=str(result['period']), bg=row['bg'], fg=colors['white'],
            font=('Courier', 8), width=7, anchor='w').pack(side=tk.LEFT, padx=2)
    
    # Oversold
    tk.Label(row, text=str(result['oversold']), bg=row['bg'], fg=colors['white'],
            font=('Courier', 8), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
    
    # Overbought
    tk.Label(row, text=str(result['overbought']), bg=row['bg'], fg=colors['white'],
            font=('Courier', 8), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
    
    # Profit
    profit_color = colors['green'] if result['total_profit_usd'] > 0 else colors['red']
    profit_text = f"+${result['total_profit_usd']:.2f}" if result['total_profit_usd'] > 0 else f"${result['total_profit_usd']:.2f}"
    tk.Label(row, text=profit_text, bg=row['bg'], fg=profit_color,
            font=('Courier', 8, 'bold'), width=10, anchor='e').pack(side=tk.LEFT, padx=2)
    
    # Win rate
    wr_color = colors['green'] if result['win_rate'] >= 50 else colors['red']
    tk.Label(row, text=f"{result['win_rate']:.1f}%", bg=row['bg'], fg=wr_color,
            font=('Courier', 8), width=7, anchor='e').pack(side=tk.LEFT, padx=2)
    
    # Trades
    tk.Label(row, text=str(result['total_trades']), bg=row['bg'], fg=colors['white'],
            font=('Courier', 8), width=7, anchor='e').pack(side=tk.LEFT, padx=2)


def create_results_header(parent, colors: Dict) -> None:
    """
    Create results table header
    
    Args:
        parent: Parent tkinter widget
        colors: Color scheme dictionary
    """
    header_row = tk.Frame(parent, bg=colors['bg_dark'])
    header_row.pack(fill=tk.X, padx=10, pady=2)
    
    tk.Label(header_row, text="Rank", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=5, anchor='w').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="Coin", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=6, anchor='w').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="Period", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=7, anchor='w').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="OS", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="OB", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="Profit", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=10, anchor='e').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="Win%", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=7, anchor='e').pack(side=tk.LEFT, padx=2)
    tk.Label(header_row, text="Trades", bg=colors['bg_dark'], fg=colors['gray'],
            font=('Courier', 8, 'bold'), width=7, anchor='e').pack(side=tk.LEFT, padx=2)


def create_best_overall_highlight(parent, best: Dict, colors: Dict) -> None:
    """
    Create best overall configuration highlight
    
    Args:
        parent: Parent tkinter widget
        best: Best result dictionary
        colors: Color scheme dictionary
    """
    best_frame = tk.Frame(parent, bg=colors['green'], relief=tk.SOLID, borderwidth=2)
    best_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(best_frame, text="🏆 BEST OVERALL CONFIGURATION", bg=colors['green'],
            fg=colors['bg_dark'], font=('Courier', 10, 'bold')).pack(pady=5)
    
    best_info = tk.Frame(best_frame, bg=colors['bg_dark'])
    best_info.pack(fill=tk.X, padx=5, pady=5)
    
    tk.Label(best_info, 
            text=f"{best['coin']} | Period: {best['period']} | Oversold: {best['oversold']} | Overbought: {best['overbought']}",
            bg=colors['bg_dark'], fg=colors['white'],
            font=('Courier', 9, 'bold')).pack()
    
    tk.Label(best_info,
            text=f"Profit: ${best['total_profit_usd']:.2f} | Win Rate: {best['win_rate']:.1f}% | Trades: {best['total_trades']}",
            bg=colors['bg_dark'], fg=colors['green'],
            font=('Courier', 9, 'bold')).pack()
