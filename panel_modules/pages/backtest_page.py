"""
Self-optimizing backtest page for testing trading signals with historical data
Refactored for modularity - uses helper modules for cleaner code organization
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional, Dict, List
import threading
import itertools
from config import TRADING_SETTINGS, BACKTEST_SETTINGS

# Import modular components
from panel_modules.backtest_data_fetcher import fetch_historical_data
from panel_modules.backtest_strategies import (
    run_rsi_backtest, run_sma_backtest, run_range_backtest,
    run_scalping_backtest, run_macd_backtest
)
from panel_modules.backtest_results import save_best_results, group_best_results_by_coin
from panel_modules.backtest_ui_components import (
    create_result_row, create_results_header, create_best_overall_highlight
)


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
                                             "Range 24h Low", "Range 7days Low", "Scalping 1min", "MACD 15min",
                                             "Support/Resistance 1H"],
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
            var = tk.BooleanVar(value=True)
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
        
        # Optimization info labels
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
            "MACD 15min": "macd_15min_optimization",
            "Support/Resistance 1H": "support_resistance_1h_optimization"
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
        
        # Update optimization info labels
        self._update_optimization_labels(signal)
    
    def _update_optimization_labels(self, signal: str):
        """Update optimization parameter labels based on signal type"""
        if signal == "SMA 5min":
            short_periods = self.optimization_ranges.get('short_period', [5, 8, 10, 12, 15])
            long_periods = self.optimization_ranges.get('long_period', [20, 25, 30, 35, 40])
            total = len(short_periods) * len(long_periods)
            
            self.opt_periods_label.config(text=f"Short SMA Periods: {short_periods}")
            self.opt_oversold_label.config(text=f"Long SMA Periods: {long_periods}")
            self.opt_overbought_label.config(text="")
            self.opt_total_label.config(text=f"Total: {total} combinations")
        elif signal in ["Range 24h Low", "Range 7days Low"]:
            long_offsets = self.optimization_ranges.get('long_offset', [-2.0, -1.5, -1.0, -0.5, 0.0])
            tolerances = self.optimization_ranges.get('tolerance', [1.0, 1.5, 2.0, 2.5, 3.0])
            total = len(long_offsets) * len(tolerances)
            
            self.opt_periods_label.config(text=f"Long Offset %: {long_offsets}")
            self.opt_oversold_label.config(text=f"Tolerance %: {tolerances}")
            self.opt_overbought_label.config(text="")
            self.opt_total_label.config(text=f"Total: {total} combinations")
        elif signal == "Scalping 1min":
            fast_emas = self.optimization_ranges.get('fast_ema', [3, 5, 8])
            slow_emas = self.optimization_ranges.get('slow_ema', [10, 13, 15, 20])
            rsi_periods = self.optimization_ranges.get('rsi_period', [5, 7, 9])
            rsi_oversold = self.optimization_ranges.get('rsi_oversold', [25, 30, 35])
            rsi_overbought = self.optimization_ranges.get('rsi_overbought', [65, 70, 75])
            vol_mults = self.optimization_ranges.get('volume_multiplier', [1.3, 1.5, 1.8, 2.0])
            total = len(fast_emas) * len(slow_emas) * len(rsi_periods) * len(rsi_oversold) * len(rsi_overbought) * len(vol_mults)
            
            self.opt_periods_label.config(text=f"Fast EMA: {fast_emas} | Slow EMA: {slow_emas}")
            self.opt_oversold_label.config(text=f"RSI Period: {rsi_periods} | Vol Mult: {vol_mults}")
            self.opt_overbought_label.config(text=f"RSI OS/OB: {rsi_oversold}/{rsi_overbought}")
            self.opt_total_label.config(text=f"Total: {total} combinations")
        elif signal == "MACD 15min":
            fast_periods = self.optimization_ranges.get('fast', [8, 10, 12, 14, 16])
            slow_periods = self.optimization_ranges.get('slow', [20, 23, 26, 29, 32])
            signal_periods = self.optimization_ranges.get('signal', [7, 8, 9, 10, 11])
            total = len(fast_periods) * len(slow_periods) * len(signal_periods)
            
            self.opt_periods_label.config(text=f"Fast EMA: {fast_periods}")
            self.opt_oversold_label.config(text=f"Slow EMA: {slow_periods}")
            self.opt_overbought_label.config(text=f"Signal Line: {signal_periods}")
            self.opt_total_label.config(text=f"Total: {total} combinations")
        else:
            # RSI signals
            periods = self.optimization_ranges.get('period', [10, 12, 14, 16, 18, 20])
            oversold = self.optimization_ranges.get('oversold', [25, 28, 30, 32, 35])
            overbought = self.optimization_ranges.get('overbought', [65, 68, 70, 72, 75])
            total = len(periods) * len(oversold) * len(overbought)
            
            self.opt_periods_label.config(text=f"RSI Periods: {periods}")
            self.opt_oversold_label.config(text=f"Oversold: {oversold}")
            self.opt_overbought_label.config(text=f"Overbought: {overbought}")
            self.opt_total_label.config(text=f"Total: {total} combinations")
    
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
            
            # Generate combinations and run tests
            all_results = self._run_all_tests(selected_coins, signal_type, minutes, position_size)
            
            # Sort by total profit
            all_results.sort(key=lambda x: x['total_profit_usd'], reverse=True)
            
            # Get signal name for saving
            signal_name = self._get_signal_filename(signal_type)
            
            # Save best results
            save_best_results(all_results, signal_name, timerange_name, position_size)
            
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
    
    def _run_all_tests(self, selected_coins: List[str], signal_type: str, 
                       minutes: int, position_size: float) -> List[Dict]:
        """Run all backtest combinations"""
        all_results = []
        combinations = self._generate_combinations(signal_type)
        total_tests = len(selected_coins) * len(combinations)
        test_count = 0
        
        for coin in selected_coins:
            self.parent.after(0, lambda c=coin: self.status_label.config(
                text=f"Fetching data for {c}..."))
            
            df = fetch_historical_data(coin, minutes, self.current_interval)
            
            if df is None or len(df) < self._get_min_data_length(signal_type):
                continue
            
            # Test all combinations for this coin
            for combo in combinations:
                test_count += 1
                self.parent.after(0, lambda tc=test_count, tt=total_tests: self.status_label.config(
                    text=f"Testing {tc}/{tt} configurations..."))
                
                result = self._run_strategy_backtest(df, coin, signal_type, combo, position_size)
                if result:
                    all_results.append(result)
        
        return all_results
    
    def _generate_combinations(self, signal_type: str) -> List:
        """Generate parameter combinations based on signal type"""
        if signal_type == "SMA 5min":
            short = self.optimization_ranges.get('short_period', [5, 8, 10, 12, 15])
            long = self.optimization_ranges.get('long_period', [20, 25, 30, 35, 40])
            return list(itertools.product(short, long))
        elif signal_type in ["Range 24h Low", "Range 7days Low"]:
            offsets = self.optimization_ranges.get('long_offset', [-2.0, -1.5, -1.0, -0.5, 0.0])
            tolerances = self.optimization_ranges.get('tolerance', [1.0, 1.5, 2.0, 2.5, 3.0])
            return list(itertools.product(offsets, tolerances))
        elif signal_type == "Scalping 1min":
            fast = self.optimization_ranges.get('fast_ema', [3, 5, 8])
            slow = self.optimization_ranges.get('slow_ema', [10, 13, 15, 20])
            rsi_p = self.optimization_ranges.get('rsi_period', [5, 7, 9])
            rsi_os = self.optimization_ranges.get('rsi_oversold', [25, 30, 35])
            rsi_ob = self.optimization_ranges.get('rsi_overbought', [65, 70, 75])
            vol = self.optimization_ranges.get('volume_multiplier', [1.3, 1.5, 1.8, 2.0])
            return list(itertools.product(fast, slow, rsi_p, rsi_os, rsi_ob, vol))
        elif signal_type == "MACD 15min":
            fast = self.optimization_ranges.get('fast', [8, 10, 12, 14, 16])
            slow = self.optimization_ranges.get('slow', [20, 23, 26, 29, 32])
            signal = self.optimization_ranges.get('signal', [7, 8, 9, 10, 11])
            return list(itertools.product(fast, slow, signal))
        else:
            # RSI signals
            periods = self.optimization_ranges.get('period', [10, 12, 14, 16, 18, 20])
            oversold = self.optimization_ranges.get('oversold', [25, 28, 30, 32, 35])
            overbought = self.optimization_ranges.get('overbought', [65, 68, 70, 72, 75])
            return list(itertools.product(periods, oversold, overbought))
    
    def _run_strategy_backtest(self, df: pd.DataFrame, coin: str, signal_type: str,
                               combo: tuple, position_size: float) -> Optional[Dict]:
        """Run backtest for specific strategy and parameters"""
        if signal_type == "SMA 5min":
            return run_sma_backtest(df, coin, combo[0], combo[1], position_size)
        elif signal_type in ["Range 24h Low", "Range 7days Low"]:
            return run_range_backtest(df, coin, combo[0], combo[1], position_size)
        elif signal_type == "Scalping 1min":
            return run_scalping_backtest(df, coin, combo[0], combo[1], combo[2], 
                                        combo[3], combo[4], combo[5], position_size)
        elif signal_type == "MACD 15min":
            return run_macd_backtest(df, coin, combo[0], combo[1], combo[2], position_size)
        else:
            # RSI signals
            return run_rsi_backtest(df, coin, combo[0], combo[1], combo[2], position_size)
    
    def _get_min_data_length(self, signal_type: str) -> int:
        """Get minimum data length required for signal type"""
        if signal_type == "SMA 5min":
            return max(self.optimization_ranges.get('long_period', [40]))
        elif signal_type in ["Range 24h Low", "Range 7days Low"]:
            return 50
        else:
            return max(self.optimization_ranges.get('period', [20]))
    
    def _get_signal_filename(self, signal_type: str) -> str:
        """Get filename-friendly signal name"""
        signal_map = {
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
        return signal_map.get(signal_type, "rsi-1min")
    
    def _display_optimization_results(self, results: List[Dict], timerange: str, position_size: float):
        """Display optimization results"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not results:
            tk.Label(self.results_frame, text="No profitable configurations found",
                    bg=self.colors['bg_panel'], fg=self.colors['red'],
                    font=('Courier', 10)).pack(pady=50)
            return
        
        # Get best results per coin
        best_per_coin = group_best_results_by_coin(results)
        
        # Header
        header = tk.Frame(self.results_frame, bg=self.colors['bg_dark'])
        header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(header, text=f"Optimization Results - {timerange} - ${position_size} per trade",
                bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 11, 'bold')).pack()
        
        # Best overall highlight
        create_best_overall_highlight(self.results_frame, best_per_coin[0], self.colors)
        
        # Best per coin section
        tk.Label(self.results_frame, text=f"═══ BEST CONFIGURATION PER COIN ({len(best_per_coin)} coins) ═══",
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 10, 'bold')).pack(pady=(20, 10))
        
        # Results table
        create_results_header(self.results_frame, self.colors)
        
        for i, result in enumerate(best_per_coin):
            create_result_row(self.results_frame, result, i + 1, self.colors)
