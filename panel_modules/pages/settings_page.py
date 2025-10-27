"""
Settings page component for the trading panel
"""
import tkinter as tk
import os


class SettingsPage:
    """Handles the settings page display and functionality"""
    
    def __init__(self, parent, colors):
        """
        Initialize settings page
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
        """
        self.parent = parent
        self.colors = colors
        
        # Setting variables
        self.max_positions_var = None
        self.position_size_var = None
        self.stop_loss_var = None
        self.take_profit_var = None
        self.trailing_stop_var = None
        self.trailing_activation_var = None
        self.min_profit_var = None
        self.signal_strength_var = None
        self.new_coin_entry = None
        self.coins_list_frame = None
        self.settings_status_label = None
        
    def create_page(self):
        """Create the settings page content"""
        from config import TRADING_SETTINGS
        
        # Settings container
        settings_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], 
                                 relief=tk.SOLID, borderwidth=1)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(settings_frame, text="═══ TRADING SETTINGS ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 14, 'bold')).pack(pady=15)
        
        # Scrollable content
        canvas = tk.Canvas(settings_frame, bg=self.colors['bg_panel'], highlightthickness=0)
        scrollbar = tk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_panel'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create grid layout for settings sections
        # Row 1: Position Management and Risk Management side by side
        row1_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_panel'])
        row1_frame.pack(fill=tk.X, padx=10, pady=5)
        
        position_container = tk.Frame(row1_frame, bg=self.colors['bg_panel'])
        position_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_position_management_section(position_container, TRADING_SETTINGS)
        
        risk_container = tk.Frame(row1_frame, bg=self.colors['bg_panel'])
        risk_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_risk_management_section(risk_container, TRADING_SETTINGS)
        
        # Row 2: Signal Generators and Monitored Coins side by side
        row2_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_panel'])
        row2_frame.pack(fill=tk.X, padx=10, pady=5)
        
        signals_container = tk.Frame(row2_frame, bg=self.colors['bg_panel'])
        signals_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_signal_generators_section(signals_container)
        
        coins_container = tk.Frame(row2_frame, bg=self.colors['bg_panel'])
        coins_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_monitored_coins_section(coins_container, TRADING_SETTINGS)
        
        # Row 3: Save button (full width)
        self._create_save_button(scrollable_frame)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_position_management_section(self, parent, settings):
        """Create position management settings section"""
        position_section = tk.Frame(parent, bg=self.colors['bg_dark'], 
                                   relief=tk.SOLID, borderwidth=1)
        position_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(position_section, text="POSITION MANAGEMENT", bg=self.colors['bg_dark'], 
                fg=self.colors['green'], font=('Courier', 12, 'bold')).pack(pady=10)
        
        # Max Positions
        max_pos_frame = tk.Frame(position_section, bg=self.colors['bg_dark'])
        max_pos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(max_pos_frame, text="Max Positions:", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.max_positions_var = tk.StringVar(value=str(settings.get('max_positions', 10)))
        max_pos_entry = tk.Entry(max_pos_frame, textvariable=self.max_positions_var,
                                bg=self.colors['bg_panel'], fg=self.colors['white'], 
                                font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        max_pos_entry.pack(side=tk.LEFT, padx=5)
        
        # Position Size
        pos_size_frame = tk.Frame(position_section, bg=self.colors['bg_dark'])
        pos_size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(pos_size_frame, text="Position Size (USD):", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.position_size_var = tk.StringVar(value=str(settings.get('position_size_usd', 20)))
        pos_size_entry = tk.Entry(pos_size_frame, textvariable=self.position_size_var,
                                  bg=self.colors['bg_panel'], fg=self.colors['white'], 
                                  font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        pos_size_entry.pack(side=tk.LEFT, padx=5)
    
    def _create_risk_management_section(self, parent, settings):
        """Create risk management settings section"""
        risk_section = tk.Frame(parent, bg=self.colors['bg_dark'], 
                               relief=tk.SOLID, borderwidth=1)
        risk_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(risk_section, text="RISK MANAGEMENT", bg=self.colors['bg_dark'], 
                fg=self.colors['green'], font=('Courier', 12, 'bold')).pack(pady=10)
        
        # Stop Loss
        sl_frame = tk.Frame(risk_section, bg=self.colors['bg_dark'])
        sl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(sl_frame, text="Stop Loss (%):", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.stop_loss_var = tk.StringVar(value=str(settings.get('stop_loss_percent', 2.20)))
        sl_entry = tk.Entry(sl_frame, textvariable=self.stop_loss_var,
                           bg=self.colors['bg_panel'], fg=self.colors['white'], 
                           font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        sl_entry.pack(side=tk.LEFT, padx=5)
        
        # Take Profit
        tp_frame = tk.Frame(risk_section, bg=self.colors['bg_dark'])
        tp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(tp_frame, text="Take Profit (%):", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.take_profit_var = tk.StringVar(value=str(settings.get('take_profit_percent', 0.62)))
        tp_entry = tk.Entry(tp_frame, textvariable=self.take_profit_var,
                           bg=self.colors['bg_panel'], fg=self.colors['white'], 
                           font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        tp_entry.pack(side=tk.LEFT, padx=5)
        
        # Trailing Stop
        trail_frame = tk.Frame(risk_section, bg=self.colors['bg_dark'])
        trail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(trail_frame, text="Trailing Stop (%):", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.trailing_stop_var = tk.StringVar(value=str(settings.get('trailing_stop_percent', 0.20)))
        trail_entry = tk.Entry(trail_frame, textvariable=self.trailing_stop_var,
                              bg=self.colors['bg_panel'], fg=self.colors['white'], 
                              font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        trail_entry.pack(side=tk.LEFT, padx=5)
        
        # Trailing Activation
        trail_act_frame = tk.Frame(risk_section, bg=self.colors['bg_dark'])
        trail_act_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(trail_act_frame, text="Trailing Activation (%):", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.trailing_activation_var = tk.StringVar(value=str(settings.get('trailing_stop_activation', 0.30)))
        trail_act_entry = tk.Entry(trail_act_frame, textvariable=self.trailing_activation_var,
                                   bg=self.colors['bg_panel'], fg=self.colors['white'], 
                                   font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        trail_act_entry.pack(side=tk.LEFT, padx=5)
        
        # Min Profit to Sell
        min_profit_frame = tk.Frame(risk_section, bg=self.colors['bg_dark'])
        min_profit_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(min_profit_frame, text="Min Profit to Sell:", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.min_profit_var = tk.StringVar(value=str(settings.get('min_profit_to_sell', 0.03)))
        min_profit_entry = tk.Entry(min_profit_frame, textvariable=self.min_profit_var,
                                    bg=self.colors['bg_panel'], fg=self.colors['white'], 
                                    font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        min_profit_entry.pack(side=tk.LEFT, padx=5)
        
        # Min Signal Strength
        signal_str_frame = tk.Frame(risk_section, bg=self.colors['bg_dark'])
        signal_str_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(signal_str_frame, text="Min Signal Strength:", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10), width=25, anchor='w').pack(side=tk.LEFT, padx=5)
        
        self.signal_strength_var = tk.StringVar(value=str(settings.get('min_signal_strength', 0.80)))
        signal_str_entry = tk.Entry(signal_str_frame, textvariable=self.signal_strength_var,
                                    bg=self.colors['bg_panel'], fg=self.colors['white'], 
                                    font=('Courier', 10), width=10, insertbackground=self.colors['white'])
        signal_str_entry.pack(side=tk.LEFT, padx=5)
    
    def _create_signal_generators_section(self, parent):
        """Create signal generators enable/disable section"""
        from config.signal_settings import SIGNAL_GENERATOR_SETTINGS
        
        signals_section = tk.Frame(parent, bg=self.colors['bg_dark'], 
                                  relief=tk.SOLID, borderwidth=1)
        signals_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(signals_section, text="SIGNAL GENERATORS", bg=self.colors['bg_dark'], 
                fg=self.colors['green'], font=('Courier', 12, 'bold')).pack(pady=10)
        
        tk.Label(signals_section, text="Enable/Disable signal generators on startup", 
                bg=self.colors['bg_dark'], fg=self.colors['gray'], 
                font=('Courier', 9)).pack(pady=(0, 10))
        
        # Store signal checkboxes
        self.signal_vars = {}
        
        # Create checkbox for each signal
        for signal_id, signal_info in SIGNAL_GENERATOR_SETTINGS.items():
            signal_frame = tk.Frame(signals_section, bg=self.colors['bg_dark'])
            signal_frame.pack(fill=tk.X, padx=10, pady=3)
            
            # Checkbox variable
            var = tk.BooleanVar(value=signal_info['enabled'])
            self.signal_vars[signal_id] = var
            
            # Checkbox
            checkbox = tk.Checkbutton(
                signal_frame,
                text=signal_info['name'],
                variable=var,
                bg=self.colors['bg_dark'],
                fg=self.colors['white'],
                selectcolor=self.colors['bg_panel'],
                activebackground=self.colors['bg_dark'],
                activeforeground=self.colors['green'],
                font=('Courier', 10),
                cursor="hand2"
            )
            checkbox.pack(side=tk.LEFT, padx=5)
            
            # Status indicator
            status_label = tk.Label(
                signal_frame,
                text="● ENABLED" if signal_info['enabled'] else "○ DISABLED",
                bg=self.colors['bg_dark'],
                fg=self.colors['green'] if signal_info['enabled'] else self.colors['gray'],
                font=('Courier', 9)
            )
            status_label.pack(side=tk.LEFT, padx=10)
            
            # Update status label when checkbox changes
            def update_status(label=status_label, v=var):
                if v.get():
                    label.config(text="● ENABLED", fg=self.colors['green'])
                else:
                    label.config(text="○ DISABLED", fg=self.colors['gray'])
            
            var.trace('w', lambda *args, u=update_status: u())
    
    def _create_monitored_coins_section(self, parent, settings):
        """Create monitored coins settings section"""
        coins_section = tk.Frame(parent, bg=self.colors['bg_dark'], 
                                relief=tk.SOLID, borderwidth=1)
        coins_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(coins_section, text="MONITORED COINS", bg=self.colors['bg_dark'], 
                fg=self.colors['green'], font=('Courier', 12, 'bold')).pack(pady=10)
        
        # Current coins display
        current_coins = settings.get('monitored_coins', [])
        
        coins_display_frame = tk.Frame(coins_section, bg=self.colors['bg_dark'])
        coins_display_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(coins_display_frame, text="Current Coins:", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10)).pack(anchor='w', pady=5)
        
        # Coins list with remove buttons
        self.coins_list_frame = tk.Frame(coins_display_frame, bg=self.colors['bg_dark'])
        self.coins_list_frame.pack(fill=tk.X, pady=5)
        
        self._update_coins_display(current_coins)
        
        # Add coin section
        add_coin_frame = tk.Frame(coins_section, bg=self.colors['bg_dark'])
        add_coin_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(add_coin_frame, text="Add New Coin:", bg=self.colors['bg_dark'], 
                fg=self.colors['gray'], font=('Courier', 10)).pack(side=tk.LEFT, padx=5)
        
        self.new_coin_entry = tk.Entry(add_coin_frame, bg=self.colors['bg_panel'], 
                                       fg=self.colors['white'], font=('Courier', 10), 
                                       width=10, insertbackground=self.colors['white'])
        self.new_coin_entry.pack(side=tk.LEFT, padx=5)
        
        add_btn = tk.Button(add_coin_frame, text="ADD", command=self._add_coin,
                           bg=self.colors['green'], fg=self.colors['bg_dark'], 
                           font=('Courier', 9, 'bold'), cursor="hand2", relief=tk.RAISED)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Info label
        tk.Label(coins_section, text="Enter coin symbol (e.g., BTC, ETH, SOL)", 
                bg=self.colors['bg_dark'], fg=self.colors['gray'], 
                font=('Courier', 8)).pack(pady=5)
    
    def _create_save_button(self, parent):
        """Create save button section"""
        save_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        save_frame.pack(fill=tk.X, padx=20, pady=20)
        
        save_btn = tk.Button(save_frame, text="💾 SAVE SETTINGS", command=self._save_settings,
                            bg=self.colors['blue'], fg=self.colors['white'], 
                            font=('Courier', 12, 'bold'), cursor="hand2", 
                            relief=tk.RAISED, padx=20, pady=10)
        save_btn.pack()
        
        self.settings_status_label = tk.Label(save_frame, text="", bg=self.colors['bg_panel'], 
                                              fg=self.colors['green'], font=('Courier', 10))
        self.settings_status_label.pack(pady=10)
    
    def _update_coins_display(self, coins):
        """Update the display of monitored coins"""
        # Clear existing display
        for widget in self.coins_list_frame.winfo_children():
            widget.destroy()
        
        # Display each coin with remove button
        for coin in coins:
            coin_row = tk.Frame(self.coins_list_frame, bg=self.colors['bg_panel'], 
                               relief=tk.SOLID, borderwidth=1)
            coin_row.pack(fill=tk.X, pady=2)
            
            tk.Label(coin_row, text=coin, bg=self.colors['bg_panel'], fg=self.colors['white'],
                    font=('Courier', 10, 'bold'), width=10).pack(side=tk.LEFT, padx=10, pady=5)
            
            remove_btn = tk.Button(coin_row, text="✖ REMOVE", 
                                   command=lambda c=coin: self._remove_coin(c),
                                   bg=self.colors['red'], fg=self.colors['white'], 
                                   font=('Courier', 8, 'bold'), cursor="hand2", relief=tk.RAISED)
            remove_btn.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _add_coin(self):
        """Add a new coin to the monitored list"""
        new_coin = self.new_coin_entry.get().strip().upper()
        
        if not new_coin:
            self.settings_status_label.config(text="⚠ Please enter a coin symbol", 
                                             fg=self.colors['red'])
            return
        
        from config import TRADING_SETTINGS
        current_coins = TRADING_SETTINGS.get('monitored_coins', [])
        
        if new_coin in current_coins:
            self.settings_status_label.config(text=f"⚠ {new_coin} is already in the list", 
                                             fg=self.colors['red'])
            return
        
        # Add coin to list
        current_coins.append(new_coin)
        TRADING_SETTINGS['monitored_coins'] = current_coins
        
        # Update display
        self._update_coins_display(current_coins)
        
        # Clear entry
        self.new_coin_entry.delete(0, tk.END)
        
        # Show status
        self.settings_status_label.config(text=f"✓ {new_coin} added (click SAVE to persist)", 
                                         fg=self.colors['green'])
    
    def _remove_coin(self, coin):
        """Remove a coin from the monitored list"""
        from config import TRADING_SETTINGS
        current_coins = TRADING_SETTINGS.get('monitored_coins', [])
        
        if coin in current_coins:
            current_coins.remove(coin)
            TRADING_SETTINGS['monitored_coins'] = current_coins
            
            # Update display
            self._update_coins_display(current_coins)
            
            # Show status
            self.settings_status_label.config(text=f"✓ {coin} removed (click SAVE to persist)", 
                                             fg=self.colors['green'])
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            from config import TRADING_SETTINGS, SIGNAL_SETTINGS
            from config.signal_settings import SIGNAL_GENERATOR_SETTINGS
            
            # Update TRADING_SETTINGS with values from input fields
            try:
                TRADING_SETTINGS['max_positions'] = int(self.max_positions_var.get())
                TRADING_SETTINGS['position_size_usd'] = int(self.position_size_var.get())
                TRADING_SETTINGS['stop_loss_percent'] = float(self.stop_loss_var.get())
                TRADING_SETTINGS['take_profit_percent'] = float(self.take_profit_var.get())
                TRADING_SETTINGS['trailing_stop_percent'] = float(self.trailing_stop_var.get())
                TRADING_SETTINGS['trailing_stop_activation'] = float(self.trailing_activation_var.get())
                TRADING_SETTINGS['min_profit_to_sell'] = float(self.min_profit_var.get())
                TRADING_SETTINGS['min_signal_strength'] = float(self.signal_strength_var.get())
            except ValueError as e:
                self.settings_status_label.config(text=f"✖ Invalid number format: {str(e)}", 
                                                 fg=self.colors['red'])
                return
            
            # Update signal generator settings
            for signal_id, var in self.signal_vars.items():
                SIGNAL_GENERATOR_SETTINGS[signal_id]['enabled'] = var.get()
            
            # Read current file
            settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                        'config', 'trading_settings.py')
            
            # Create new content
            content = '''"""
Trading-specific settings for the bot.
Based on DEV_PLAN.md requirements only.
"""

TRADING_SETTINGS = {
    # Position Management (from DEV_PLAN)
    'max_positions': %d,              # Maximum concurrent positions
    'position_size_usd': %d,         # Default position size
    
    # Risk Management (from DEV_PLAN)
    'stop_loss_percent': %.2f,         # Stop loss percentage (FIXED - never trails)
    'take_profit_percent': %.2f,       # Take profit percentage fixed profit doesnt make sense.
    'trailing_stop_percent': %.2f,     # Trailing stop distance from peak  is deactived
    'trailing_stop_activation': %.2f,  # Profit %% to activate trailing stop not working. on monitor it always says inactive.
    'min_profit_to_sell': %.2f,       # Minimum profit to consider selling
    'min_signal_strength': %.2f,       # Minimum signal strength to execute (0.0-1.0)
    
    # Market Data (from DEV_PLAN)
    'timeframe': '%s',                # Default timeframe
    'monitored_coins': %s,              # Coins to trade
    
    # Exchange (from DEV_PLAN)
    'exchange': '%s',
    'testnet': %s,
}

# Signal Generator Settings each coin will use its own settings from backtest results. same for stop loss and take profit.
SIGNAL_SETTINGS = {
    # RSI Settings
    'rsi': {
        'period': %d,
        'oversold': %d,
        'overbought': %d,
    },
    
    # SMA Settings
    'sma': {
        'short_period': %d,
        'long_period': %d,
    },
}''' % (
                TRADING_SETTINGS['max_positions'],
                TRADING_SETTINGS['position_size_usd'],
                TRADING_SETTINGS['stop_loss_percent'],
                TRADING_SETTINGS['take_profit_percent'],
                TRADING_SETTINGS['trailing_stop_percent'],
                TRADING_SETTINGS['trailing_stop_activation'],
                TRADING_SETTINGS['min_profit_to_sell'],
                TRADING_SETTINGS['min_signal_strength'],
                TRADING_SETTINGS['timeframe'],
                TRADING_SETTINGS['monitored_coins'],
                TRADING_SETTINGS['exchange'],
                TRADING_SETTINGS['testnet'],
                SIGNAL_SETTINGS['rsi']['period'],
                SIGNAL_SETTINGS['rsi']['oversold'],
                SIGNAL_SETTINGS['rsi']['overbought'],
                SIGNAL_SETTINGS['sma']['short_period'],
                SIGNAL_SETTINGS['sma']['long_period']
            )
            
            # Write trading settings to file
            with open(settings_file, 'w') as f:
                f.write(content)
            
            # Save signal generator settings
            signal_settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                               'config', 'signal_settings.py')
            
            signal_content = '''"""
Signal Generator Settings Configuration
Controls which signal generators are enabled by default on startup
"""

# Signal Generator Enable/Disable Settings
SIGNAL_GENERATOR_SETTINGS = {
'''
            for signal_id, signal_info in SIGNAL_GENERATOR_SETTINGS.items():
                signal_content += f"    '{signal_id}': {{\n"
                signal_content += f"        'enabled': {signal_info['enabled']},\n"
                signal_content += f"        'name': '{signal_info['name']}'\n"
                signal_content += "    },\n"
            
            signal_content += "}"
            
            with open(signal_settings_file, 'w') as f:
                f.write(signal_content)
            
            self.settings_status_label.config(
                text="✓ Settings saved successfully! Restart bot to apply changes.", 
                fg=self.colors['green']
            )
            
            print("=" * 60)
            print("SETTINGS SAVED SUCCESSFULLY")
            print("=" * 60)
            print(f"Monitored Coins: {TRADING_SETTINGS['monitored_coins']}")
            print(f"Signal Generators:")
            for signal_id, signal_info in SIGNAL_GENERATOR_SETTINGS.items():
                status = "ENABLED" if signal_info['enabled'] else "DISABLED"
                print(f"  - {signal_info['name']}: {status}")
            print("=" * 60)
            print("⚠ RESTART THE BOT to apply changes")
            print("=" * 60)
            
        except Exception as e:
            self.settings_status_label.config(text=f"✖ Error saving: {str(e)}", 
                                             fg=self.colors['red'])
            print(f"Error saving settings: {e}")
            import traceback
            traceback.print_exc()
