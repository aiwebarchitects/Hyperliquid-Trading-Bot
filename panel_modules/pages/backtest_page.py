"""
Self-optimizing backtest page for testing trading signals with historical data
"""
import tkinter as tk
from tkinter import ttk
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import threading
import itertools
import json
import os
from config import TRADING_SETTINGS, BACKTEST_SETTINGS


class BacktestPage:
    """Self-optimizing backtest page for signal testing"""
    
    def __init__(self, parent, colors):
        """
        Initialize backtest page
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
        """
        self.parent = parent
        self.colors = colors
        self.running_backtest = False
        self.results = None
        
        # Load coins from trading settings
        self.coins = TRADING_SETTINGS.get('monitored_coins', ['BTC', 'ETH'])
        
        # Load backtest settings
        self.position_size_usd = BACKTEST_SETTINGS.get('position_size_usd', 100)
        self.time_ranges = BACKTEST_SETTINGS.get('time_ranges', {
            "24 Hours": 1440,
            "72 Hours": 4320,
            "7 Days": 10080
        })
        
        # Optimization ranges (will be loaded based on selected signal)
        self.optimization_ranges = {}
        self.current_interval = '1m'
        
        # Coin selection state
        self.coin_vars = {}
        
    def create_page(self):
        """Create the backtest page UI"""
        # Title
        title_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], 
                              relief=tk.SOLID, borderwidth=1)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(title_frame, text="═══ SELF-OPTIMIZING BACKTEST ═══", 
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 14, 'bold')).pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Configuration
        left_panel = tk.Frame(main_container, bg=self.colors['bg_panel'],
                             relief=tk.SOLID, borderwidth=1, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self._create_config_panel(left_panel)
        
        # Right panel - Results
        right_panel = tk.Frame(main_container, bg=self.colors['bg_panel'],
                              relief=tk.SOLID, borderwidth=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._create_results_panel(right_panel)
    
    def _create_config_panel(self, parent):
        """Create configuration panel"""
        tk.Label(parent, text="BACKTEST CONFIGURATION", bg=self.colors['bg_panel'],
                fg=self.colors['green'], font=('Courier', 11, 'bold')).pack(pady=15)
        
        # Run button at the top
        btn_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.run_btn = tk.Button(btn_frame, text="RUN OPTIMIZATION",
                                 bg=self.colors['green'], fg=self.colors['bg_dark'],
                                 font=('Courier', 11, 'bold'), cursor="hand2",
                                 command=self.run_backtest)
        self.run_btn.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = tk.Label(parent, text="Ready", bg=self.colors['bg_panel'],
                                     fg=self.colors['gray'], font=('Courier', 9))
        self.status_label.pack(pady=(0, 10))
        
        # Scrollable config area
        config_canvas = tk.Canvas(parent, bg=self.colors['bg_panel'], highlightthickness=0)
        config_scrollbar = tk.Scrollbar(parent, orient="vertical", command=config_canvas.yview)
        config_frame = tk.Frame(config_canvas, bg=self.colors['bg_panel'])
        
        config_frame.bind("<Configure>", 
                         lambda e: config_canvas.configure(scrollregion=config_canvas.bbox("all")))
        config_canvas.create_window((0, 0), window=config_frame, anchor="nw")
        config_canvas.configure(yscrollcommand=config_scrollbar.set)
        
        # Signal selection
        signal_frame = tk.Frame(config_frame, bg=self.colors['bg_panel'])
        signal_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(signal_frame, text="Signal:", bg=self.colors['bg_panel'],
                fg=self.colors['white'], font=('Courier', 10)).pack(anchor='w')
        
        self.signal_var = tk.StringVar(value="RSI 1min")
        signal_dropdown = ttk.Combobox(signal_frame, textvariable=self.signal_var,
                                      values=["RSI 1min", "RSI 5min", "RSI 1h", "RSI 4h", "SMA 5min", 
                                             "Range 24h Low", "Range 7days Low", "Scalping 1min", "MACD 15min"],
                                      state='readonly', font=('Courier', 10))
        signal_dropdown.pack(fill=tk.X, pady=5)
        signal_dropdown.bind('<<ComboboxSelected>>', self._on_signal_changed)
        
        # Time range selection
        timerange_frame = tk.Frame(config_frame, bg=self.colors['bg_panel'])
        timerange_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(timerange_frame, text="Time Range:", bg=self.colors['bg_panel'],
                fg=self.colors['white'], font=('Courier', 10)).pack(anchor='w')
        
        self.timerange_var = tk.StringVar(value="24 Hours")
        timerange_dropdown = ttk.Combobox(timerange_frame, textvariable=self.timerange_var,
                                         values=list(self.time_ranges.keys()),
                                         state='readonly', font=('Courier', 10))
        timerange_dropdown.pack(fill=tk.X, pady=5)
        
        # Position size
        size_frame = tk.Frame(config_frame, bg=self.colors['bg_panel'])
        size_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(size_frame, text="Position Size (USD):", bg=self.colors['bg_panel'],
                fg=self.colors['white'], font=('Courier', 10)).pack(anchor='w')
        
        self.position_size_var = tk.StringVar(value=str(self.position_size_usd))
        tk.Entry(size_frame, textvariable=self.position_size_var,
                bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 10), insertbackground=self.colors['white']).pack(fill=tk.X, pady=5)
        
        # Coin selection
        coins_frame = tk.Frame(config_frame, bg=self.colors['bg_panel'])
        coins_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(coins_frame, text="Coins to Test:", bg=self.colors['bg_panel'],
                fg=self.colors['white'], font=('Courier', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        # Select/Deselect all buttons
        btn_row = tk.Frame(coins_frame, bg=self.colors['bg_panel'])
        btn_row.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_row, text="Select All", bg=self.colors['bg_dark'], fg=self.colors['white'],
                 font=('Courier', 8), command=self._select_all_coins).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(btn_row, text="Deselect All", bg=self.colors['bg_dark'], fg=self.colors['white'],
                 font=('Courier', 8), command=self._deselect_all_coins).pack(side=tk.LEFT)
        
        # Coin checkboxes
        for coin in self.coins:
            var = tk.BooleanVar(value=True)  # All enabled by default
            self.coin_vars[coin] = var
            cb = tk.Checkbutton(coins_frame, text=coin, variable=var,
                               bg=self.colors['bg_panel'], fg=self.colors['white'],
                               selectcolor=self.colors['bg_dark'],
                               font=('Courier', 9), activebackground=self.colors['bg_panel'])
            cb.pack(anchor='w', pady=2)
        
        # Optimization info
        opt_frame = tk.Frame(config_frame, bg=self.colors['bg_panel'])
        opt_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(opt_frame, text="Optimization Parameters:", bg=self.colors['bg_panel'],
                fg=self.colors['white'], font=('Courier', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        # Optimization info labels (will be updated dynamically)
        self.opt_periods_label = tk.Label(opt_frame, text="", bg=self.colors['bg_panel'],
                fg=self.colors['gray'], font=('Courier', 8))
        self.opt_periods_label.pack(anchor='w', pady=1)
        
        self.opt_oversold_label = tk.Label(opt_frame, text="", bg=self.colors['bg_panel'],
                fg=self.colors['gray'], font=('Courier', 8))
        self.opt_oversold_label.pack(anchor='w', pady=1)
        
        self.opt_overbought_label = tk.Label(opt_frame, text="", bg=self.colors['bg_panel'],
                fg=self.colors['gray'], font=('Courier', 8))
        self.opt_overbought_label.pack(anchor='w', pady=1)
        
        self.opt_total_label = tk.Label(opt_frame, text="", bg=self.colors['bg_panel'],
                fg=self.colors['yellow'], font=('Courier', 8, 'bold'))
        self.opt_total_label.pack(anchor='w', pady=(5, 1))
        
        # Load initial optimization ranges
        self._on_signal_changed(None)
        
        config_canvas.pack(side="left", fill="both", expand=True)
        config_scrollbar.pack(side="right", fill="y")
    
    def _on_signal_changed(self, event):
        """Handle signal selection change"""
        signal = self.signal_var.get()
        
        # Map signal names to config keys
        signal_map = {
            "RSI 1min": "rsi_1min_optimization",
            "RSI 5min": "rsi_5min_optimization",
            "RSI 1h": "rsi_1h_optimization",
            "RSI 4h": "rsi_4h_optimization",
            "SMA 5min": "sma_5min_optimization",
            "Range 24h Low": "range_24h_low_optimization",
            "Range 7days Low": "range_7days_low_optimization",
            "Scalping 1min": "scalping_1min_optimization",
            "MACD 15min": "macd_15min_optimization"
        }
        
        config_key = signal_map.get(signal, "rsi_1min_optimization")
        self.optimization_ranges = BACKTEST_SETTINGS.get(config_key, {
            'period': [10, 12, 14, 16, 18, 20],
            'oversold': [25, 28, 30, 32, 35],
            'overbought': [65, 68, 70, 72, 75],
            'interval': '1m'
        })
        
        # Update current interval
        self.current_interval = self.optimization_ranges.get('interval', '1m')
        
        # Update optimization info labels based on signal type
        if signal == "SMA 5min":
            short_periods = self.optimization_ranges.get('short_period', [5, 8, 10, 12, 15])
            long_periods = self.optimization_ranges.get('long_period', [20, 25, 30, 35, 40])
            total_combinations = len(short_periods) * len(long_periods)
            
            self.opt_periods_label.config(text=f"Short SMA Periods: {short_periods}")
            self.opt_oversold_label.config(text=f"Long SMA Periods: {long_periods}")
            self.opt_overbought_label.config(text="")
            self.opt_total_label.config(text=f"Total: {total_combinations} combinations")
        elif signal in ["Range 24h Low", "Range 7days Low"]:
            long_offsets = self.optimization_ranges.get('long_offset', [-2.0, -1.5, -1.0, -0.5, 0.0])
            tolerances = self.optimization_ranges.get('tolerance', [1.0, 1.5, 2.0, 2.5, 3.0])
            total_combinations = len(long_offsets) * len(tolerances)
            
            self.opt_periods_label.config(text=f"Long Offset %: {long_offsets}")
            self.opt_oversold_label.config(text=f"Tolerance %: {tolerances}")
            self.opt_overbought_label.config(text="")
            self.opt_total_label.config(text=f"Total: {total_combinations} combinations")
        elif signal == "Scalping 1min":
            fast_emas = self.optimization_ranges.get('fast_ema', [3, 5, 8])
            slow_emas = self.optimization_ranges.get('slow_ema', [10, 13, 15, 20])
            rsi_periods = self.optimization_ranges.get('rsi_period', [5, 7, 9])
            rsi_oversold = self.optimization_ranges.get('rsi_oversold', [25, 30, 35])
            rsi_overbought = self.optimization_ranges.get('rsi_overbought', [65, 70, 75])
            vol_mults = self.optimization_ranges.get('volume_multiplier', [1.3, 1.5, 1.8, 2.0])
            total_combinations = len(fast_emas) * len(slow_emas) * len(rsi_periods) * len(rsi_oversold) * len(rsi_overbought) * len(vol_mults)
            
            self.opt_periods_label.config(text=f"Fast EMA: {fast_emas} | Slow EMA: {slow_emas}")
            self.opt_oversold_label.config(text=f"RSI Period: {rsi_periods} | Vol Mult: {vol_mults}")
            self.opt_overbought_label.config(text=f"RSI OS/OB: {rsi_oversold}/{rsi_overbought}")
            self.opt_total_label.config(text=f"Total: {total_combinations} combinations")
        elif signal == "MACD 15min":
            fast_periods = self.optimization_ranges.get('fast', [8, 10, 12, 14, 16])
            slow_periods = self.optimization_ranges.get('slow', [20, 23, 26, 29, 32])
            signal_periods = self.optimization_ranges.get('signal', [7, 8, 9, 10, 11])
            total_combinations = len(fast_periods) * len(slow_periods) * len(signal_periods)
            
            self.opt_periods_label.config(text=f"Fast EMA: {fast_periods}")
            self.opt_oversold_label.config(text=f"Slow EMA: {slow_periods}")
            self.opt_overbought_label.config(text=f"Signal Line: {signal_periods}")
            self.opt_total_label.config(text=f"Total: {total_combinations} combinations")
        else:
            # RSI signals
            periods = self.optimization_ranges.get('period', [10, 12, 14, 16, 18, 20])
            oversold = self.optimization_ranges.get('oversold', [25, 28, 30, 32, 35])
            overbought = self.optimization_ranges.get('overbought', [65, 68, 70, 72, 75])
            total_combinations = len(periods) * len(oversold) * len(overbought)
            
            self.opt_periods_label.config(text=f"RSI Periods: {periods}")
            self.opt_oversold_label.config(text=f"Oversold: {oversold}")
            self.opt_overbought_label.config(text=f"Overbought: {overbought}")
            self.opt_total_label.config(text=f"Total: {total_combinations} combinations")
    
    def _select_all_coins(self):
        """Select all coins"""
        for var in self.coin_vars.values():
            var.set(True)
    
    def _deselect_all_coins(self):
        """Deselect all coins"""
        for var in self.coin_vars.values():
            var.set(False)
    
    def _create_results_panel(self, parent):
        """Create results display panel"""
        tk.Label(parent, text="OPTIMIZATION RESULTS", bg=self.colors['bg_panel'],
                fg=self.colors['green'], font=('Courier', 11, 'bold')).pack(pady=15)
        
        # Results container with scrollbar
        results_container = tk.Frame(parent, bg=self.colors['bg_panel'])
        results_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        canvas = tk.Canvas(results_container, bg=self.colors['bg_panel'], highlightthickness=0)
        scrollbar = tk.Scrollbar(results_container, orient="vertical", command=canvas.yview)
        
        self.results_frame = tk.Frame(canvas, bg=self.colors['bg_panel'])
        self.results_frame.bind("<Configure>", 
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial message
        tk.Label(self.results_frame, 
                text="No optimization results yet.\nConfigure and run optimization to find best parameters.",
                bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 10)).pack(pady=50)
    
    def run_backtest(self):
        """Run the optimization in a separate thread"""
        if self.running_backtest:
            return
        
        # Get selected coins
        selected_coins = [coin for coin, var in self.coin_vars.items() if var.get()]
        if not selected_coins:
            self.status_label.config(text="Please select at least one coin", fg=self.colors['red'])
            return
        
        self.running_backtest = True
        self.run_btn.config(state='disabled', text="OPTIMIZING...")
        self.status_label.config(text="Starting optimization...", fg=self.colors['yellow'])
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._execute_optimization, args=(selected_coins,))
        thread.daemon = True
        thread.start()
    
    def _execute_optimization(self, selected_coins: List[str]):
        """Execute the self-optimizing backtest"""
        try:
            # Get parameters
            timerange_name = self.timerange_var.get()
            minutes = self.time_ranges[timerange_name]
            position_size = float(self.position_size_var.get())
            signal_type = self.signal_var.get()
            
            # Generate combinations based on signal type
            if signal_type == "SMA 5min":
                short_periods = self.optimization_ranges.get('short_period', [5, 8, 10, 12, 15])
                long_periods = self.optimization_ranges.get('long_period', [20, 25, 30, 35, 40])
                combinations = list(itertools.product(short_periods, long_periods))
            elif signal_type in ["Range 24h Low", "Range 7days Low"]:
                long_offsets = self.optimization_ranges.get('long_offset', [-2.0, -1.5, -1.0, -0.5, 0.0])
                tolerances = self.optimization_ranges.get('tolerance', [1.0, 1.5, 2.0, 2.5, 3.0])
                combinations = list(itertools.product(long_offsets, tolerances))
            elif signal_type == "Scalping 1min":
                fast_emas = self.optimization_ranges.get('fast_ema', [3, 5, 8])
                slow_emas = self.optimization_ranges.get('slow_ema', [10, 13, 15, 20])
                rsi_periods = self.optimization_ranges.get('rsi_period', [5, 7, 9])
                rsi_oversold = self.optimization_ranges.get('rsi_oversold', [25, 30, 35])
                rsi_overbought = self.optimization_ranges.get('rsi_overbought', [65, 70, 75])
                vol_mults = self.optimization_ranges.get('volume_multiplier', [1.3, 1.5, 1.8, 2.0])
                combinations = list(itertools.product(fast_emas, slow_emas, rsi_periods, 
                                                     rsi_oversold, rsi_overbought, vol_mults))
            elif signal_type == "MACD 15min":
                fast_periods = self.optimization_ranges.get('fast', [8, 10, 12, 14, 16])
                slow_periods = self.optimization_ranges.get('slow', [20, 23, 26, 29, 32])
                signal_periods = self.optimization_ranges.get('signal', [7, 8, 9, 10, 11])
                combinations = list(itertools.product(fast_periods, slow_periods, signal_periods))
            else:
                # RSI signals
                periods = self.optimization_ranges.get('period', [10, 12, 14, 16, 18, 20])
                oversold_values = self.optimization_ranges.get('oversold', [25, 28, 30, 32, 35])
                overbought_values = self.optimization_ranges.get('overbought', [65, 68, 70, 72, 75])
                combinations = list(itertools.product(periods, oversold_values, overbought_values))
            
            total_tests = len(selected_coins) * len(combinations)
            
            self.parent.after(0, lambda: self.status_label.config(
                text=f"Testing {total_tests} configurations..."))
            
            # Store all results
            all_results = []
            test_count = 0
            
            # Test each coin
            for coin in selected_coins:
                # Fetch historical data once per coin
                self.parent.after(0, lambda c=coin: self.status_label.config(
                    text=f"Fetching data for {c}..."))
                
                df = self._fetch_historical_data(coin, minutes)
                
                # Check if we have enough data based on signal type
                if signal_type == "SMA 5min":
                    max_period = max(self.optimization_ranges.get('long_period', [40]))
                elif signal_type in ["Range 24h Low", "Range 7days Low"]:
                    max_period = 50  # Range signals don't need much historical data
                else:
                    max_period = max(self.optimization_ranges.get('period', [20]))
                
                if df is None or len(df) < max_period + 1:
                    continue
                
                # Test all parameter combinations for this coin
                if signal_type == "SMA 5min":
                    for short_period, long_period in combinations:
                        test_count += 1
                        
                        self.parent.after(0, lambda tc=test_count, tt=total_tests: self.status_label.config(
                            text=f"Testing {tc}/{tt} configurations..."))
                        
                        # Run SMA backtest
                        result = self._run_sma_backtest(
                            df, coin, short_period, long_period, position_size
                        )
                        
                        if result:
                            all_results.append(result)
                elif signal_type in ["Range 24h Low", "Range 7days Low"]:
                    for long_offset, tolerance in combinations:
                        test_count += 1
                        
                        self.parent.after(0, lambda tc=test_count, tt=total_tests: self.status_label.config(
                            text=f"Testing {tc}/{tt} configurations..."))
                        
                        # Run range backtest
                        result = self._run_range_backtest(
                            df, coin, long_offset, tolerance, position_size
                        )
                        
                        if result:
                            all_results.append(result)
                elif signal_type == "Scalping 1min":
                    for fast_ema, slow_ema, rsi_period, rsi_os, rsi_ob, vol_mult in combinations:
                        test_count += 1
                        
                        self.parent.after(0, lambda tc=test_count, tt=total_tests: self.status_label.config(
                            text=f"Testing {tc}/{tt} configurations..."))
                        
                        # Run scalping backtest
                        result = self._run_scalping_backtest(
                            df, coin, fast_ema, slow_ema, rsi_period, rsi_os, rsi_ob, vol_mult, position_size
                        )
                        
                        if result:
                            all_results.append(result)
                elif signal_type == "MACD 15min":
                    for fast, slow, signal_period in combinations:
                        test_count += 1
                        
                        self.parent.after(0, lambda tc=test_count, tt=total_tests: self.status_label.config(
                            text=f"Testing {tc}/{tt} configurations..."))
                        
                        # Run MACD backtest
                        result = self._run_macd_backtest(
                            df, coin, fast, slow, signal_period, position_size
                        )
                        
                        if result:
                            all_results.append(result)
                else:
                    # RSI signals
                    for period, oversold, overbought in combinations:
                        test_count += 1
                        
                        self.parent.after(0, lambda tc=test_count, tt=total_tests: self.status_label.config(
                            text=f"Testing {tc}/{tt} configurations..."))
                        
                        # Run backtest with these parameters
                        result = self._run_single_backtest(
                            df, coin, period, oversold, overbought, position_size
                        )
                        
                        if result:
                            all_results.append(result)
            
            # Sort by total profit (descending)
            all_results.sort(key=lambda x: x['total_profit_usd'], reverse=True)
            
            # Save best results for each coin
            self._save_best_results(all_results, timerange_name, position_size)
            
            # Display results
            self.parent.after(0, lambda: self._display_optimization_results(
                all_results, timerange_name, position_size))
            self.parent.after(0, lambda: self.status_label.config(
                text=f"Optimization completed - Results saved to /results", fg=self.colors['green']))
            
        except Exception as e:
            error_msg = str(e)
            print(f"Optimization error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.parent.after(0, lambda msg=error_msg: self.status_label.config(
                text=f"Error: {msg}", fg=self.colors['red']))
        
        finally:
            self.running_backtest = False
            self.parent.after(0, lambda: self.run_btn.config(state='normal', text="RUN OPTIMIZATION"))
    
    def _run_single_backtest(self, df: pd.DataFrame, coin: str, period: int, 
                            oversold: int, overbought: int, position_size: float) -> Optional[Dict]:
        """Run a single backtest with specific parameters"""
        try:
            # Calculate RSI
            df_copy = df.copy()
            df_copy['rsi'] = self._calculate_rsi(df_copy['close'], period)
            
            # Generate signals
            signals = []
            for i in range(len(df_copy)):
                if pd.isna(df_copy.iloc[i]['rsi']):
                    continue
                
                rsi = df_copy.iloc[i]['rsi']
                if rsi <= oversold:
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': rsi,
                        'action': 'BUY'
                    })
                elif rsi >= overbought:
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': rsi,
                        'action': 'SELL'
                    })
            
            # Simulate trades
            trades = self._simulate_trades(signals, position_size)
            
            if not trades:
                return None
            
            # Calculate statistics
            winning_trades = [t for t in trades if t['profit_usd'] > 0]
            losing_trades = [t for t in trades if t['profit_usd'] <= 0]
            
            total_profit = sum(t['profit_usd'] for t in trades)
            win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
            
            return {
                'coin': coin,
                'period': period,
                'oversold': oversold,
                'overbought': overbought,
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'total_profit_usd': total_profit,
                'avg_profit': total_profit / len(trades) if trades else 0,
                'signals_generated': len(signals)
            }
            
        except Exception as e:
            print(f"Error in single backtest: {e}")
            return None
    
    def _fetch_historical_data(self, coin: str, minutes: int) -> Optional[pd.DataFrame]:
        """Fetch historical candles from Binance"""
        try:
            symbol = f"{coin}USDT"
            url = "https://api.binance.com/api/v3/klines"
            
            # Calculate how many candles we need based on interval and time range
            interval_minutes = {
                '1m': 1,
                '5m': 5,
                '15m': 15,
                '1h': 60,
                '4h': 240,
                '1d': 1440
            }
            
            candles_needed = minutes // interval_minutes.get(self.current_interval, 1)
            limit = min(candles_needed, 1000)  # Binance max is 1000
            
            # Calculate start time based on time range
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (minutes * 60 * 1000)
            
            params = {
                'symbol': symbol,
                'interval': self.current_interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"Error fetching data for {coin}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        deltas = prices.diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def _run_range_backtest(self, df: pd.DataFrame, coin: str, long_offset: float,
                           tolerance: float, position_size: float) -> Optional[Dict]:
        """Run a single range-based backtest"""
        try:
            # Calculate period low and high
            period_low = df['low'].min()
            period_high = df['high'].max()
            
            # Calculate buy range based on offset and tolerance
            buy_range_low = period_low * (1 + long_offset / 100)
            buy_range_high = period_low * (1 + long_offset / 100 + tolerance / 100)
            
            # Generate signals based on price entering/exiting range
            signals = []
            in_range = False
            
            for i in range(len(df)):
                current_price = df.iloc[i]['close']
                
                # Check if price enters buy range (BUY signal)
                if not in_range and buy_range_low <= current_price <= buy_range_high:
                    signals.append({
                        'timestamp': df.iloc[i]['timestamp'],
                        'price': current_price,
                        'rsi': 0,  # Placeholder
                        'action': 'BUY'
                    })
                    in_range = True
                
                # Check if price exits range above (SELL signal - take profit)
                elif in_range and current_price > buy_range_high:
                    signals.append({
                        'timestamp': df.iloc[i]['timestamp'],
                        'price': current_price,
                        'rsi': 0,  # Placeholder
                        'action': 'SELL'
                    })
                    in_range = False
                
                # Check if price exits range below (SELL signal - stop loss)
                elif in_range and current_price < buy_range_low:
                    signals.append({
                        'timestamp': df.iloc[i]['timestamp'],
                        'price': current_price,
                        'rsi': 0,  # Placeholder
                        'action': 'SELL'
                    })
                    in_range = False
            
            # Simulate trades
            trades = self._simulate_trades(signals, position_size)
            
            if not trades:
                return None
            
            # Calculate statistics
            winning_trades = [t for t in trades if t['profit_usd'] > 0]
            losing_trades = [t for t in trades if t['profit_usd'] <= 0]
            
            total_profit = sum(t['profit_usd'] for t in trades)
            win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
            
            # Return result with range-specific format (using 'period' for offset, 'oversold' for tolerance)
            return {
                'coin': coin,
                'period': long_offset,  # Store as 'period' for compatibility
                'oversold': tolerance,  # Store as 'oversold' for compatibility
                'overbought': 0,  # Not used for range
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'total_profit_usd': total_profit,
                'avg_profit': total_profit / len(trades) if trades else 0,
                'signals_generated': len(signals)
            }
            
        except Exception as e:
            print(f"Error in range backtest: {e}")
            return None
    
    def _run_sma_backtest(self, df: pd.DataFrame, coin: str, short_period: int,
                          long_period: int, position_size: float) -> Optional[Dict]:
        """Run a single SMA crossover backtest"""
        try:
            # Calculate SMAs
            df_copy = df.copy()
            df_copy['short_sma'] = self._calculate_sma(df_copy['close'], short_period)
            df_copy['long_sma'] = self._calculate_sma(df_copy['close'], long_period)
            
            # Generate signals based on SMA crossover
            signals = []
            for i in range(1, len(df_copy)):
                if pd.isna(df_copy.iloc[i]['short_sma']) or pd.isna(df_copy.iloc[i]['long_sma']):
                    continue
                
                curr_short = df_copy.iloc[i]['short_sma']
                curr_long = df_copy.iloc[i]['long_sma']
                prev_short = df_copy.iloc[i-1]['short_sma']
                prev_long = df_copy.iloc[i-1]['long_sma']
                
                # Bullish crossover: short crosses above long
                if prev_short <= prev_long and curr_short > curr_long:
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': 0,  # Placeholder for compatibility
                        'action': 'BUY'
                    })
                # Bearish crossover: short crosses below long
                elif prev_short >= prev_long and curr_short < curr_long:
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': 0,  # Placeholder for compatibility
                        'action': 'SELL'
                    })
            
            # Simulate trades
            trades = self._simulate_trades(signals, position_size)
            
            if not trades:
                return None
            
            # Calculate statistics
            winning_trades = [t for t in trades if t['profit_usd'] > 0]
            losing_trades = [t for t in trades if t['profit_usd'] <= 0]
            
            total_profit = sum(t['profit_usd'] for t in trades)
            win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
            
            # Return result with SMA-specific format (using 'period' for short, 'oversold' for long)
            return {
                'coin': coin,
                'period': short_period,  # Store as 'period' for compatibility
                'oversold': long_period,  # Store as 'oversold' for compatibility
                'overbought': 0,  # Not used for SMA
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'total_profit_usd': total_profit,
                'avg_profit': total_profit / len(trades) if trades else 0,
                'signals_generated': len(signals)
            }
            
        except Exception as e:
            print(f"Error in SMA backtest: {e}")
            return None
    
    def _run_scalping_backtest(self, df: pd.DataFrame, coin: str, fast_ema: int,
                               slow_ema: int, rsi_period: int, rsi_oversold: int,
                               rsi_overbought: int, volume_multiplier: float,
                               position_size: float) -> Optional[Dict]:
        """Run a single scalping backtest"""
        try:
            df_copy = df.copy()
            
            # Calculate indicators
            df_copy['fast_ema'] = df_copy['close'].ewm(span=fast_ema, adjust=False).mean()
            df_copy['slow_ema'] = df_copy['close'].ewm(span=slow_ema, adjust=False).mean()
            df_copy['rsi'] = self._calculate_rsi(df_copy['close'], rsi_period)
            
            # Calculate volume spike
            df_copy['avg_volume'] = df_copy['volume'].rolling(window=20).mean()
            df_copy['volume_spike'] = df_copy['volume'] > (df_copy['avg_volume'] * volume_multiplier)
            
            # Generate signals
            signals = []
            for i in range(1, len(df_copy)):
                if pd.isna(df_copy.iloc[i]['fast_ema']) or pd.isna(df_copy.iloc[i]['rsi']):
                    continue
                
                curr_fast = df_copy.iloc[i]['fast_ema']
                curr_slow = df_copy.iloc[i]['slow_ema']
                prev_fast = df_copy.iloc[i-1]['fast_ema']
                prev_slow = df_copy.iloc[i-1]['slow_ema']
                curr_rsi = df_copy.iloc[i]['rsi']
                vol_spike = df_copy.iloc[i]['volume_spike']
                
                # Bullish crossover
                if (prev_fast <= prev_slow and curr_fast > curr_slow and
                    curr_rsi > rsi_oversold and curr_rsi < rsi_overbought and vol_spike):
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': curr_rsi,
                        'action': 'BUY'
                    })
                
                # Bearish crossover
                elif (prev_fast >= prev_slow and curr_fast < curr_slow and
                      curr_rsi < rsi_overbought and curr_rsi > rsi_oversold and vol_spike):
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': curr_rsi,
                        'action': 'SELL'
                    })
            
            # Simulate trades
            trades = self._simulate_trades(signals, position_size)
            
            if not trades:
                return None
            
            # Calculate statistics
            winning_trades = [t for t in trades if t['profit_usd'] > 0]
            losing_trades = [t for t in trades if t['profit_usd'] <= 0]
            
            total_profit = sum(t['profit_usd'] for t in trades)
            win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
            
            # Return result (using 'period' for fast_ema, 'oversold' for slow_ema, 'overbought' for rsi_period)
            return {
                'coin': coin,
                'period': fast_ema,
                'oversold': slow_ema,
                'overbought': rsi_period,
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'total_profit_usd': total_profit,
                'avg_profit': total_profit / len(trades) if trades else 0,
                'signals_generated': len(signals)
            }
            
        except Exception as e:
            print(f"Error in scalping backtest: {e}")
            return None
    
    def _run_macd_backtest(self, df: pd.DataFrame, coin: str, fast: int,
                           slow: int, signal_period: int, position_size: float) -> Optional[Dict]:
        """Run a single MACD backtest"""
        try:
            df_copy = df.copy()
            
            # Calculate MACD
            ema_fast = df_copy['close'].ewm(span=fast, adjust=False).mean()
            ema_slow = df_copy['close'].ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            histogram = macd_line - signal_line
            
            # Generate signals based on histogram crossover
            signals = []
            for i in range(1, len(df_copy)):
                if pd.isna(histogram.iloc[i]) or pd.isna(histogram.iloc[i-1]):
                    continue
                
                curr_hist = histogram.iloc[i]
                prev_hist = histogram.iloc[i-1]
                
                # Bullish crossover: histogram crosses above zero
                if prev_hist <= 0 and curr_hist > 0:
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': 0,  # Placeholder for compatibility
                        'action': 'BUY'
                    })
                # Bearish crossover: histogram crosses below zero
                elif prev_hist >= 0 and curr_hist < 0:
                    signals.append({
                        'timestamp': df_copy.iloc[i]['timestamp'],
                        'price': df_copy.iloc[i]['close'],
                        'rsi': 0,  # Placeholder for compatibility
                        'action': 'SELL'
                    })
            
            # Simulate trades
            trades = self._simulate_trades(signals, position_size)
            
            if not trades:
                return None
            
            # Calculate statistics
            winning_trades = [t for t in trades if t['profit_usd'] > 0]
            losing_trades = [t for t in trades if t['profit_usd'] <= 0]
            
            total_profit = sum(t['profit_usd'] for t in trades)
            win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
            
            # Return result (using 'period' for fast, 'oversold' for slow, 'overbought' for signal)
            return {
                'coin': coin,
                'period': fast,
                'oversold': slow,
                'overbought': signal_period,
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'total_profit_usd': total_profit,
                'avg_profit': total_profit / len(trades) if trades else 0,
                'signals_generated': len(signals)
            }
            
        except Exception as e:
            print(f"Error in MACD backtest: {e}")
            return None
    
    def _save_best_results(self, all_results: List[Dict], timerange: str, position_size: float):
        """Save best results for each coin to results folder"""
        try:
            # Create results directory if it doesn't exist
            results_dir = "results"
            os.makedirs(results_dir, exist_ok=True)
            
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Group results by coin and get best for each
            coins_best = {}
            for result in all_results:
                coin = result['coin']
                if coin not in coins_best:
                    coins_best[coin] = result
            
            # Get signal name for filename
            signal_name_map = {
                "RSI 1min": "rsi-1min",
                "RSI 5min": "rsi-5min",
                "RSI 1h": "rsi-1h",
                "RSI 4h": "rsi-4h",
                "SMA 5min": "sma-5min",
                "Range 24h Low": "range-24h-low",
                "Range 7days Low": "range-7days-low",
                "Scalping 1min": "scalping-1min",
                "MACD 15min": "macd-15min"
            }
            signal_name = signal_name_map.get(self.signal_var.get(), "rsi-1min")
            
            # Save each coin's best result
            for coin, best_result in coins_best.items():
                # Create filename: coin_signal_timestamp.json
                filename = f"{coin}_{signal_name}_{timestamp}.json"
                filepath = os.path.join(results_dir, filename)
                
                # Prepare data to save
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
                
                # Save to file
                with open(filepath, 'w') as f:
                    json.dump(save_data, f, indent=2)
                
                print(f"Saved best result for {coin} to {filepath}")
            
            print(f"Saved {len(coins_best)} coin configurations to {results_dir}/")
            
        except Exception as e:
            print(f"Error saving results: {e}")
            import traceback
            traceback.print_exc()
    
    def _simulate_trades(self, signals: List[Dict], position_size: float) -> List[Dict]:
        """Simulate trades based on signals with USD position size"""
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
    
    def _display_optimization_results(self, results: List[Dict], timerange: str, position_size: float):
        """Display optimization results - showing best configuration per coin"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not results:
            tk.Label(self.results_frame, text="No profitable configurations found",
                    bg=self.colors['bg_panel'], fg=self.colors['red'],
                    font=('Courier', 10)).pack(pady=50)
            return
        
        # Group results by coin and get best for each
        coins_best = {}
        for result in results:
            coin = result['coin']
            if coin not in coins_best or result['total_profit_usd'] > coins_best[coin]['total_profit_usd']:
                coins_best[coin] = result
        
        # Convert to list and sort by profit
        best_per_coin = list(coins_best.values())
        best_per_coin.sort(key=lambda x: x['total_profit_usd'], reverse=True)
        
        # Header
        header = tk.Frame(self.results_frame, bg=self.colors['bg_dark'])
        header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(header, text=f"Optimization Results - {timerange} - ${position_size} per trade",
                bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 11, 'bold')).pack()
        
        # Best overall result highlight
        best = best_per_coin[0]
        best_frame = tk.Frame(self.results_frame, bg=self.colors['green'], relief=tk.SOLID, borderwidth=2)
        best_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(best_frame, text="🏆 BEST OVERALL CONFIGURATION", bg=self.colors['green'],
                fg=self.colors['bg_dark'], font=('Courier', 10, 'bold')).pack(pady=5)
        
        best_info = tk.Frame(best_frame, bg=self.colors['bg_dark'])
        best_info.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(best_info, 
                text=f"{best['coin']} | Period: {best['period']} | Oversold: {best['oversold']} | Overbought: {best['overbought']}",
                bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 9, 'bold')).pack()
        
        tk.Label(best_info,
                text=f"Profit: ${best['total_profit_usd']:.2f} | Win Rate: {best['win_rate']:.1f}% | Trades: {best['total_trades']}",
                bg=self.colors['bg_dark'], fg=self.colors['green'],
                font=('Courier', 9, 'bold')).pack()
        
        # Best configuration per coin
        tk.Label(self.results_frame, text=f"═══ BEST CONFIGURATION PER COIN ({len(best_per_coin)} coins) ═══",
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 10, 'bold')).pack(pady=(20, 10))
        
        # Results table header
        header_row = tk.Frame(self.results_frame, bg=self.colors['bg_dark'])
        header_row.pack(fill=tk.X, padx=10, pady=2)
        
        tk.Label(header_row, text="Rank", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=5, anchor='w').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="Coin", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=6, anchor='w').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="Period", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=7, anchor='w').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="OS", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="OB", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="Profit", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=10, anchor='e').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="Win%", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=7, anchor='e').pack(side=tk.LEFT, padx=2)
        tk.Label(header_row, text="Trades", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 8, 'bold'), width=7, anchor='e').pack(side=tk.LEFT, padx=2)
        
        # Display best result for each coin
        for i, result in enumerate(best_per_coin):
            self._create_result_row(self.results_frame, result, i + 1)
    
    def _create_result_row(self, parent, result: Dict, rank: int):
        """Create a result row"""
        row = tk.Frame(parent, bg=self.colors['bg_dark'] if rank % 2 == 0 else self.colors['bg_panel'])
        row.pack(fill=tk.X, padx=10, pady=1)
        
        # Rank
        rank_color = self.colors['green'] if rank <= 3 else self.colors['white']
        tk.Label(row, text=f"#{rank}", bg=row['bg'], fg=rank_color,
                font=('Courier', 8, 'bold'), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Coin
        tk.Label(row, text=result['coin'], bg=row['bg'], fg=self.colors['white'],
                font=('Courier', 8), width=6, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Period
        tk.Label(row, text=str(result['period']), bg=row['bg'], fg=self.colors['white'],
                font=('Courier', 8), width=7, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Oversold
        tk.Label(row, text=str(result['oversold']), bg=row['bg'], fg=self.colors['white'],
                font=('Courier', 8), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Overbought
        tk.Label(row, text=str(result['overbought']), bg=row['bg'], fg=self.colors['white'],
                font=('Courier', 8), width=4, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Profit
        profit_color = self.colors['green'] if result['total_profit_usd'] > 0 else self.colors['red']
        profit_text = f"+${result['total_profit_usd']:.2f}" if result['total_profit_usd'] > 0 else f"${result['total_profit_usd']:.2f}"
        tk.Label(row, text=profit_text, bg=row['bg'], fg=profit_color,
                font=('Courier', 8, 'bold'), width=10, anchor='e').pack(side=tk.LEFT, padx=2)
        
        # Win rate
        wr_color = self.colors['green'] if result['win_rate'] >= 50 else self.colors['red']
        tk.Label(row, text=f"{result['win_rate']:.1f}%", bg=row['bg'], fg=wr_color,
                font=('Courier', 8), width=7, anchor='e').pack(side=tk.LEFT, padx=2)
        
        # Trades
        tk.Label(row, text=str(result['total_trades']), bg=row['bg'], fg=self.colors['white'],
                font=('Courier', 8), width=7, anchor='e').pack(side=tk.LEFT, padx=2)
