"""
Signals Display Module for Trading Panel
Shows real-time signals from all generators with enable/disable controls
IMPROVED VERSION with independent signal updates and comprehensive debugging
"""

import tkinter as tk
from datetime import datetime
from typing import Dict, List
from signals import RSI5MinSignalGenerator, RSI1MinSignalGenerator, RSI1HSignalGenerator, RSI4HSignalGenerator, SMA5MinSignalGenerator, Range7DaysLowSignalGenerator, Range24HLowSignalGenerator, Scalping1MinSignalGenerator, MACD15MinSignalGenerator
from config import TRADING_SETTINGS, SIGNAL_SETTINGS
from config.signal_settings import SIGNAL_GENERATOR_SETTINGS
from utils.logger import get_logger
import os
import threading
import time

# Setup signals logger
logger = get_logger(__name__)

# Create signals log file
signals_log_path = 'logs/signals_log.txt'
os.makedirs('logs', exist_ok=True)

# Log file settings
MAX_LOG_LINES = 1000  # Keep only last 1000 lines
LOG_CLEANUP_INTERVAL = 100  # Clean up every 100 writes


class SignalsDisplay:
    """Manages signals display and generator controls in the panel."""
    
    def __init__(self, parent_frame, colors, api=None):
        """
        Initialize Signals Display.
        
        Args:
            parent_frame: Parent tkinter frame
            colors: Color scheme dictionary
            api: API client for checking positions (optional)
        """
        self.parent = parent_frame
        self.colors = colors
        self.api = api
        
        # Log file management
        self.log_write_counter = 0
        
        # Track open positions (updated every minute)
        self.open_positions = set()
        self.last_position_check = 0
        self.position_check_interval = 60  # Check positions every 60 seconds
        
        # Load signal settings
        rsi_settings = SIGNAL_SETTINGS['rsi']
        sma_settings = SIGNAL_SETTINGS['sma']
        
        # Signal generators with enable/disable state (loaded from config)
        self.generators = {
            'rsi_5min': {
                'instance': RSI5MinSignalGenerator(
                    period=rsi_settings['period'],
                    oversold=rsi_settings['oversold'],
                    overbought=rsi_settings['overbought']
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['rsi_5min']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['rsi_5min']['name'],
                'last_signals': [],
                'update_interval': 60  # Update every 60 seconds (5min data doesn't change that fast)
            },
            'rsi_1min': {
                'instance': RSI1MinSignalGenerator(
                    period=rsi_settings['period'],
                    oversold=rsi_settings['oversold'],
                    overbought=rsi_settings['overbought']
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['rsi_1min']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['rsi_1min']['name'],
                'last_signals': [],
                'update_interval': 30  # Update every 30 seconds
            },
            'rsi_1h': {
                'instance': RSI1HSignalGenerator(
                    period=rsi_settings['period'],
                    oversold=rsi_settings['oversold'],
                    overbought=rsi_settings['overbought']
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['rsi_1h']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['rsi_1h']['name'],
                'last_signals': [],
                'update_interval': 300  # Update every 5 minutes (1h data doesn't change often)
            },
            'rsi_4h': {
                'instance': RSI4HSignalGenerator(
                    period=rsi_settings['period'],
                    oversold=rsi_settings['oversold'],
                    overbought=rsi_settings['overbought']
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['rsi_4h']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['rsi_4h']['name'],
                'last_signals': [],
                'update_interval': 600  # Update every 10 minutes (4h data changes slowly)
            },
            'sma_5min': {
                'instance': SMA5MinSignalGenerator(
                    short_period=sma_settings['short_period'],
                    long_period=sma_settings['long_period']
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['sma_5min']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['sma_5min']['name'],
                'last_signals': [],
                'update_interval': 60  # Update every 60 seconds
            },
            'range_7days_low': {
                'instance': Range7DaysLowSignalGenerator(
                    long_offset_percent=-1.0,
                    tolerance_percent=2.0
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['range_7days_low']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['range_7days_low']['name'],
                'last_signals': [],
                'update_interval': 120  # Update every 2 minutes (7-day range doesn't change fast)
            },
            'range_24h_low': {
                'instance': Range24HLowSignalGenerator(
                    long_offset_percent=-1.0,
                    tolerance_percent=2.0
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['range_24h_low']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['range_24h_low']['name'],
                'last_signals': [],
                'update_interval': 90  # Update every 90 seconds (24h range changes more frequently than 7d)
            },
            'scalping_1min': {
                'instance': Scalping1MinSignalGenerator(
                    fast_ema=5,
                    slow_ema=13,
                    rsi_period=7,
                    rsi_oversold=30,
                    rsi_overbought=70,
                    volume_multiplier=1.5
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['scalping_1min']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['scalping_1min']['name'],
                'last_signals': [],
                'update_interval': 30  # Update every 30 seconds (1min scalping needs frequent updates)
            },
            'macd_15min': {
                'instance': MACD15MinSignalGenerator(
                    fast=12,
                    slow=26,
                    signal=9
                ),
                'enabled': SIGNAL_GENERATOR_SETTINGS['macd_15min']['enabled'],
                'name': SIGNAL_GENERATOR_SETTINGS['macd_15min']['name'],
                'last_signals': [],
                'update_interval': 90  # Update every 90 seconds (15min data changes every 15 minutes)
            }
        }
        
        # Track last update time per generator per coin
        self.last_update_times = {}  # {gen_id: {coin: timestamp}}
        for gen_id in self.generators.keys():
            self.last_update_times[gen_id] = {}
        
        # Monitored coins from settings
        self.monitored_coins = TRADING_SETTINGS['monitored_coins']
        
        # UI elements
        self.signals_frame = None
        self.control_buttons = {}
        self.signal_labels = {}  # Store label references for updates
        self.last_update_label = None
        self.debug_label = None
        
        # Threading control
        self.update_threads = {}  # Track active update threads
        self.stop_updates = False
    
    def create_signals_display(self):
        """Create the signals display page."""
        # Main container
        main_frame = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top: Generator controls
        self._create_generator_controls(main_frame)
        
        # Bottom: Signals feed
        self._create_signals_feed(main_frame)
        
        return main_frame
    
    def _create_generator_controls(self, parent):
        """Create signal generator enable/disable controls."""
        control_frame = tk.Frame(parent, bg=self.colors['bg_panel'], 
                                relief=tk.SOLID, borderwidth=1)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(control_frame, text="═══ SIGNAL GENERATORS ═══", 
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 11, 'bold')).pack(pady=10)
        
        # Trading settings info
        settings_info = tk.Frame(control_frame, bg=self.colors['bg_dark'])
        settings_info.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(settings_info, text="Trading Settings:", bg=self.colors['bg_dark'],
                fg=self.colors['yellow'], font=('Courier', 9, 'bold')).pack(anchor='w')
        
        settings_text = (
            f"Position Size: ${TRADING_SETTINGS['position_size_usd']} | "
            f"Stop Loss: {TRADING_SETTINGS['stop_loss_percent']}% | "
            f"Take Profit: {TRADING_SETTINGS['take_profit_percent']}% | "
            f"Max Positions: {TRADING_SETTINGS['max_positions']}"
        )
        tk.Label(settings_info, text=settings_text, bg=self.colors['bg_dark'],
                fg=self.colors['white'], font=('Courier', 8)).pack(anchor='w', pady=2)
        
        # Generator toggles
        toggles_container = tk.Frame(control_frame, bg=self.colors['bg_panel'])
        toggles_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        for gen_id, gen_data in self.generators.items():
            self._create_generator_toggle(toggles_container, gen_id, gen_data)
    
    def _create_generator_toggle(self, parent, gen_id, gen_data):
        """Create a single generator toggle."""
        row = tk.Frame(parent, bg=self.colors['bg_dark'])
        row.pack(fill=tk.X, pady=3)
        
        # Generator name
        tk.Label(row, text=gen_data['name'], bg=self.colors['bg_dark'], 
                fg=self.colors['white'], font=('Courier', 10, 'bold'),
                width=20, anchor='w').pack(side=tk.LEFT, padx=5)
        
        # Generator parameters (thresholds)
        instance = gen_data['instance']
        params_text = ""
        if hasattr(instance, 'oversold') and hasattr(instance, 'overbought'):
            params_text = f"BUY≤{instance.oversold} | SELL≥{instance.overbought}"
        elif hasattr(instance, 'short_period') and hasattr(instance, 'long_period'):
            params_text = f"SMA {instance.short_period}/{instance.long_period}"
        
        if params_text:
            tk.Label(row, text=params_text, bg=self.colors['bg_dark'],
                    fg=self.colors['blue'], font=('Courier', 8),
                    width=20, anchor='w').pack(side=tk.LEFT, padx=5)
        
        # Update interval info
        interval_text = f"Updates: {gen_data['update_interval']}s"
        tk.Label(row, text=interval_text, bg=self.colors['bg_dark'],
                fg=self.colors['gray'], font=('Courier', 8),
                width=15, anchor='w').pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        status_color = self.colors['green'] if gen_data['enabled'] else self.colors['red']
        status_text = "● ENABLED" if gen_data['enabled'] else "● DISABLED"
        status_label = tk.Label(row, text=status_text, bg=self.colors['bg_dark'],
                               fg=status_color, font=('Courier', 9, 'bold'),
                               width=12, anchor='w')
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Toggle button
        btn_text = "Disable" if gen_data['enabled'] else "Enable"
        btn_color = self.colors['red'] if gen_data['enabled'] else self.colors['green']
        
        toggle_btn = tk.Label(row, text=btn_text, bg=btn_color, 
                             fg=self.colors['bg_dark'], font=('Courier', 9, 'bold'),
                             padx=10, pady=5, cursor="hand2")
        toggle_btn.pack(side=tk.LEFT, padx=5)
        toggle_btn.bind("<Button-1>", 
                       lambda e, gid=gen_id: self._toggle_generator(gid))
        
        # Store references
        self.control_buttons[gen_id] = {
            'status_label': status_label,
            'toggle_btn': toggle_btn
        }
    
    def _toggle_generator(self, gen_id):
        """Toggle a signal generator on/off."""
        gen_data = self.generators[gen_id]
        gen_data['enabled'] = not gen_data['enabled']
        
        # Update UI
        controls = self.control_buttons[gen_id]
        
        if gen_data['enabled']:
            controls['status_label'].config(text="● ENABLED", fg=self.colors['green'])
            controls['toggle_btn'].config(text="Disable", bg=self.colors['red'])
            self._log_debug(f"Generator {gen_data['name']} ENABLED")
        else:
            controls['status_label'].config(text="● DISABLED", fg=self.colors['red'])
            controls['toggle_btn'].config(text="Enable", bg=self.colors['green'])
            self._log_debug(f"Generator {gen_data['name']} DISABLED")
        
        print(f"{gen_data['name']}: {'ENABLED' if gen_data['enabled'] else 'DISABLED'}")
    
    def _create_signals_feed(self, parent):
        """Create the signals feed display."""
        feed_frame = tk.Frame(parent, bg=self.colors['bg_panel'], 
                             relief=tk.SOLID, borderwidth=1)
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Header with refresh button
        header_frame = tk.Frame(feed_frame, bg=self.colors['bg_panel'])
        header_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(header_frame, text="═══ LIVE SIGNALS FEED ═══", 
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 11, 'bold')).pack(side=tk.LEFT, padx=10)
        
        # Debug info label
        self.debug_label = tk.Label(header_frame, text="", 
                                    bg=self.colors['bg_panel'], fg=self.colors['yellow'],
                                    font=('Courier', 8))
        self.debug_label.pack(side=tk.LEFT, padx=10)
        
        # Refresh button
        refresh_btn = tk.Label(header_frame, text="🔄 REFRESH ALL", 
                              bg=self.colors['blue'], fg=self.colors['bg_dark'],
                              font=('Courier', 10, 'bold'), padx=15, pady=5, cursor="hand2")
        refresh_btn.pack(side=tk.RIGHT, padx=10)
        refresh_btn.bind("<Button-1>", lambda e: self.force_refresh_all())
        
        # Scrollable signals list
        canvas = tk.Canvas(feed_frame, bg=self.colors['bg_panel'], highlightthickness=0)
        scrollbar = tk.Scrollbar(feed_frame, orient="vertical", command=canvas.yview)
        self.signals_frame = tk.Frame(canvas, bg=self.colors['bg_panel'])
        
        self.signals_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.signals_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _update_open_positions(self):
        """Update list of coins with open positions (called every minute)."""
        if not self.api:
            return
        
        current_time = time.time()
        if current_time - self.last_position_check < self.position_check_interval:
            return  # Not time to check yet
        
        try:
            positions = self.api.get_positions()
            # get_positions() returns a dict {coin: position_data}
            if isinstance(positions, dict):
                self.open_positions = set(positions.keys())
            elif isinstance(positions, list):
                # If it's a list, extract coin names
                self.open_positions = set(pos.get('coin', '') for pos in positions if pos.get('coin'))
            else:
                self.open_positions = set()
            
            self.last_position_check = current_time
            
            if self.open_positions:
                self._log_debug(f"Open positions: {', '.join(self.open_positions)}")
        except Exception as e:
            self._log_debug(f"Error checking positions: {e}")
    
    def check_signals(self):
        """Check signals from all enabled generators - with independent updates per signal."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Update open positions list (every minute)
        self._update_open_positions()
        
        # If first time, build the UI structure AND force initial update
        first_time = not self.signal_labels
        if first_time:
            self._log_debug("Building initial signals structure...")
            self._build_signals_structure()
        
        # Update timestamp
        if self.last_update_label and self.last_update_label.winfo_exists():
            self.last_update_label.config(text=f"Last Check: {timestamp}")
        
        # Update each signal independently based on its update interval
        current_time = time.time()
        updates_triggered = 0
        skipped_has_position = 0
        
        for gen_id, gen_data in self.generators.items():
            if not gen_data['enabled']:
                # Show disabled state for disabled generators
                for coin in self.monitored_coins:
                    if coin in self.signal_labels and gen_id in self.signal_labels[coin]:
                        labels = self.signal_labels[coin][gen_id]
                        if labels['action'].winfo_exists():
                            labels['action'].config(text="OFF", fg=self.colors['gray'])
                            labels['strength'].config(text="--")
                            labels['metadata'].config(text="Disabled")
                continue
            
            for coin in self.monitored_coins:
                # Skip if we already have a position for this coin
                if coin in self.open_positions:
                    if coin in self.signal_labels and gen_id in self.signal_labels[coin]:
                        labels = self.signal_labels[coin][gen_id]
                        if labels['action'].winfo_exists():
                            labels['action'].config(text="POS", fg=self.colors['yellow'])
                            labels['strength'].config(text="--")
                            labels['metadata'].config(text="Has open position")
                    skipped_has_position += 1
                    continue
                
                # Check if this signal needs updating
                last_update = self.last_update_times[gen_id].get(coin, 0)
                time_since_update = current_time - last_update
                
                # Force update on first time OR if interval has passed
                if first_time or time_since_update >= gen_data['update_interval']:
                    # Trigger independent update for this signal
                    self._update_signal_async(gen_id, coin)
                    updates_triggered += 1
        
        if skipped_has_position > 0:
            self._log_debug(f"Check complete. Triggered {updates_triggered} updates, skipped {skipped_has_position} (has position)")
        else:
            self._log_debug(f"Check complete. Triggered {updates_triggered} signal updates.")
    
    def force_refresh_all(self):
        """Force refresh all signals immediately."""
        self._log_debug("FORCE REFRESH: Updating all signals now...")
        
        # Reset all update times to force immediate update
        for gen_id in self.last_update_times:
            self.last_update_times[gen_id] = {}
        
        # Trigger check which will now update everything
        self.check_signals()
    
    def _update_signal_async(self, gen_id, coin):
        """Update a single signal asynchronously in a separate thread."""
        thread_key = f"{gen_id}_{coin}"
        
        # Don't start a new thread if one is already running for this signal
        if thread_key in self.update_threads and self.update_threads[thread_key].is_alive():
            self._log_debug(f"Skipping {gen_id} for {coin} - update already in progress")
            return
        
        # Start update thread
        thread = threading.Thread(
            target=self._update_single_signal,
            args=(gen_id, coin),
            daemon=True
        )
        self.update_threads[thread_key] = thread
        thread.start()
        
        self._log_debug(f"Started async update: {gen_id} for {coin}")
    
    def _update_single_signal(self, gen_id, coin):
        """Update a single signal (runs in separate thread)."""
        start_time = time.time()
        gen_data = self.generators[gen_id]
        
        try:
            # Show loading state
            self._set_signal_loading(gen_id, coin)
            
            # Generate signal
            signal = gen_data['instance'].generate_signal(coin)
            
            # Calculate how long it took
            duration = time.time() - start_time
            
            # Update UI with result (must use after() for thread safety)
            self.parent.after(0, lambda: self._update_signal_ui(gen_id, coin, signal, duration))
            
            # Update last update time
            self.last_update_times[gen_id][coin] = time.time()
            
            self._log_debug(f"✓ {gen_data['name']} for {coin} completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # Show error in UI
            self.parent.after(0, lambda: self._set_signal_error(gen_id, coin, error_msg))
            
            self._log_debug(f"✗ {gen_data['name']} for {coin} FAILED after {duration:.2f}s: {error_msg}")
            logger.error(f"Error updating {gen_data['name']} for {coin}: {e}", exc_info=True)
    
    def _set_signal_loading(self, gen_id, coin):
        """Set signal to loading state (thread-safe)."""
        def update_ui():
            if coin not in self.signal_labels or gen_id not in self.signal_labels[coin]:
                return
            
            labels = self.signal_labels[coin][gen_id]
            if labels['action'].winfo_exists():
                labels['action'].config(text="⏳", fg=self.colors['yellow'])
                labels['strength'].config(text="Loading...")
                labels['metadata'].config(text="Fetching data...")
        
        self.parent.after(0, update_ui)
    
    def _set_signal_error(self, gen_id, coin, error_msg):
        """Set signal to error state."""
        if coin not in self.signal_labels or gen_id not in self.signal_labels[coin]:
            return
        
        labels = self.signal_labels[coin][gen_id]
        if labels['action'].winfo_exists():
            labels['action'].config(text="ERR", fg=self.colors['red'])
            labels['strength'].config(text="--")
            labels['metadata'].config(text=error_msg[:40])
    
    def _update_signal_ui(self, gen_id, coin, signal, duration):
        """Update signal UI with result."""
        # DEBUG: Log what we received
        self._log_debug(f"UI UPDATE: {gen_id} {coin} signal={signal} duration={duration:.2f}s")
        
        if coin not in self.signal_labels or gen_id not in self.signal_labels[coin]:
            self._log_debug(f"UI UPDATE SKIPPED: Labels don't exist (page was switched)")
            return
        
        gen_data = self.generators[gen_id]
        labels = self.signal_labels[coin][gen_id]
        
        # Check if widget still exists (might have been destroyed if page was switched)
        try:
            if not labels['action'].winfo_exists():
                self._log_debug(f"UI UPDATE SKIPPED: Widget destroyed (page was switched)")
                return
        except:
            # Widget was destroyed
            self._log_debug(f"UI UPDATE SKIPPED: Widget destroyed (page was switched)")
            return
        
        if signal:
            self._log_debug(f"UI UPDATE: Signal exists - {signal.action} strength={signal.strength}")
            
            # Log signal to file
            self._log_signal(coin, gen_data['name'], signal, duration)
            
            # Update action
            if signal.action == "BUY":
                action_color = self.colors['green']
            elif signal.action == "SELL":
                action_color = self.colors['red']
            else:  # HOLD
                action_color = self.colors['white']
            labels['action'].config(text=signal.action, fg=action_color)
            
            # Update strength
            strength_text = f"Str: {signal.strength:.2f}"
            labels['strength'].config(text=strength_text)
            
            # Update metadata with duration
            metadata_text = ""
            if 'fast_ema' in signal.metadata and 'slow_ema' in signal.metadata:
                # Scalping signal
                metadata_text = f"EMA: {signal.metadata['fast_ema']:.6f}/{signal.metadata['slow_ema']:.6f} | RSI: {signal.metadata['rsi']:.1f}"
                if signal.metadata.get('volume_spike'):
                    metadata_text += " | VOL⚡"
            elif 'rsi' in signal.metadata:
                metadata_text = f"RSI: {signal.metadata['rsi']}"
            elif 'short_sma' in signal.metadata:
                metadata_text = f"SMA: {signal.metadata['short_sma']:.2f}/{signal.metadata['long_sma']:.2f}"
            elif '7days_low' in signal.metadata:
                metadata_text = f"Price: ${signal.metadata['current_price']:.6f} | Range: ${signal.metadata['buy_range_low']:.6f}-${signal.metadata['buy_range_high']:.6f}"
            elif '24h_low' in signal.metadata:
                metadata_text = f"Price: ${signal.metadata['current_price']:.6f} | Range: ${signal.metadata['buy_range_low']:.6f}-${signal.metadata['buy_range_high']:.6f}"
            elif 'macd' in signal.metadata and 'histogram' in signal.metadata:
                # MACD signal
                metadata_text = f"MACD: {signal.metadata['macd']:.6f} | Signal: {signal.metadata['signal']:.6f} | Hist: {signal.metadata['histogram']:.6f}"
            
            metadata_text += f" ({duration:.1f}s)"
            labels['metadata'].config(text=metadata_text)
            
            self._log_debug(f"UI UPDATE SUCCESS: {gen_id} {coin} displayed as {signal.action}")
        else:
            # No signal returned
            self._log_debug(f"UI UPDATE: No signal returned for {gen_id} {coin}")
            labels['action'].config(text="--", fg=self.colors['gray'])
            labels['strength'].config(text="--")
            labels['metadata'].config(text=f"No data ({duration:.1f}s)")
    
    def _build_signals_structure(self):
        """Build the initial signals display structure (only once)."""
        # Clear any existing widgets
        for widget in self.signals_frame.winfo_children():
            widget.destroy()
        
        self.signal_labels = {}
        
        # Header with timestamp
        header = tk.Frame(self.signals_frame, bg=self.colors['bg_dark'])
        header.pack(fill=tk.X, padx=10, pady=5)
        self.last_update_label = tk.Label(header, text="Last Check: --:--:--", 
                bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 9))
        self.last_update_label.pack()
        
        # Create structure for each coin
        for coin in self.monitored_coins:
            self._create_coin_structure(coin)
        
        self._log_debug(f"Built structure for {len(self.monitored_coins)} coins")
    
    def _create_coin_structure(self, coin):
        """Create the UI structure for a coin's signals (only once)."""
        # Coin header
        coin_frame = tk.Frame(self.signals_frame, bg=self.colors['bg_dark'])
        coin_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(coin_frame, text=f"▼ {coin}", bg=self.colors['bg_dark'],
                fg=self.colors['white'], font=('Courier', 10, 'bold'),
                anchor='w').pack(fill=tk.X)
        
        # Create rows for each generator
        self.signal_labels[coin] = {}
        
        for gen_id, gen_data in self.generators.items():
            sig_row = tk.Frame(self.signals_frame, bg=self.colors['bg_panel'])
            sig_row.pack(fill=tk.X, padx=20, pady=2)
            
            # Generator name (static)
            tk.Label(sig_row, text=gen_data['name'], bg=self.colors['bg_panel'],
                    fg=self.colors['gray'], font=('Courier', 9),
                    width=15, anchor='w').pack(side=tk.LEFT, padx=2)
            
            # Action label (will be updated)
            action_label = tk.Label(sig_row, text="--", bg=self.colors['bg_panel'],
                    fg=self.colors['white'], font=('Courier', 9, 'bold'),
                    width=6, anchor='w')
            action_label.pack(side=tk.LEFT, padx=2)
            
            # Strength label (will be updated)
            strength_label = tk.Label(sig_row, text="--", bg=self.colors['bg_panel'],
                    fg=self.colors['white'], font=('Courier', 9),
                    width=15, anchor='w')
            strength_label.pack(side=tk.LEFT, padx=2)
            
            # Metadata label (will be updated)
            metadata_label = tk.Label(sig_row, text="Waiting for update...", bg=self.colors['bg_panel'],
                    fg=self.colors['blue'], font=('Courier', 9),
                    anchor='w')
            metadata_label.pack(side=tk.LEFT, padx=2)
            
            # Store label references
            self.signal_labels[coin][gen_id] = {
                'action': action_label,
                'strength': strength_label,
                'metadata': metadata_label
            }
    
    def _log_signal(self, coin, generator_name, signal, duration):
        """Log signal to signals_log.txt file with automatic rotation."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format metadata
            metadata_str = ""
            if 'fast_ema' in signal.metadata and 'slow_ema' in signal.metadata:
                # Scalping signal
                vol_spike = "VOL⚡" if signal.metadata.get('volume_spike') else ""
                metadata_str = f"EMA={signal.metadata['fast_ema']:.6f}/{signal.metadata['slow_ema']:.6f} RSI={signal.metadata['rsi']:.1f} {vol_spike}".strip()
            elif 'rsi' in signal.metadata:
                metadata_str = f"RSI={signal.metadata['rsi']}"
            elif 'short_sma' in signal.metadata:
                metadata_str = f"SMA={signal.metadata['short_sma']:.2f}/{signal.metadata['long_sma']:.2f}"
            elif '7days_low' in signal.metadata:
                metadata_str = f"Price=${signal.metadata['current_price']:.6f} Range=${signal.metadata['buy_range_low']:.6f}-${signal.metadata['buy_range_high']:.6f}"
            elif '24h_low' in signal.metadata:
                metadata_str = f"Price=${signal.metadata['current_price']:.6f} Range=${signal.metadata['buy_range_low']:.6f}-${signal.metadata['buy_range_high']:.6f}"
            elif 'macd' in signal.metadata and 'histogram' in signal.metadata:
                # MACD signal
                metadata_str = f"MACD={signal.metadata['macd']:.6f} Signal={signal.metadata['signal']:.6f} Hist={signal.metadata['histogram']:.6f}"
            
            # Create log entry with duration
            log_entry = f"[{timestamp}] {coin:6} | {generator_name:15} | {signal.action:4} | Strength={signal.strength:.2f} | {metadata_str} | Duration={duration:.2f}s\n"
            
            # Append to log file
            with open(signals_log_path, 'a') as f:
                f.write(log_entry)
            
            # Increment write counter and check if cleanup needed
            self.log_write_counter += 1
            if self.log_write_counter >= LOG_CLEANUP_INTERVAL:
                self._cleanup_log_file()
                self.log_write_counter = 0
            
            # Also log to main logger if action is BUY or SELL
            if signal.action in ['BUY', 'SELL']:
                logger.info(f"SIGNAL: {coin} {signal.action} from {generator_name} (strength={signal.strength:.2f}, duration={duration:.2f}s)")
                
        except Exception as e:
            print(f"Error logging signal: {e}")
    
    def _log_debug(self, message):
        """Log debug message and update debug label."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {message}"
        
        # Print to console
        print(f"[SIGNALS DEBUG] {full_msg}")
        
        # Update debug label if it exists
        if self.debug_label and self.debug_label.winfo_exists():
            self.debug_label.config(text=message[:60])
        
        # Log to file (debug messages don't count toward cleanup counter)
        try:
            with open(signals_log_path, 'a') as f:
                f.write(f"DEBUG: {full_msg}\n")
        except:
            pass
    
    def _cleanup_log_file(self):
        """Keep only the last MAX_LOG_LINES in the log file."""
        try:
            if not os.path.exists(signals_log_path):
                return
            
            # Read all lines
            with open(signals_log_path, 'r') as f:
                lines = f.readlines()
            
            # If file is too large, keep only the last MAX_LOG_LINES
            if len(lines) > MAX_LOG_LINES:
                # Keep last MAX_LOG_LINES
                lines = lines[-MAX_LOG_LINES:]
                
                # Write back
                with open(signals_log_path, 'w') as f:
                    f.writelines(lines)
                
                print(f"[SIGNALS DEBUG] Log file cleaned up - kept last {MAX_LOG_LINES} lines")
                
        except Exception as e:
            print(f"Error cleaning up log file: {e}")
    
    def get_enabled_generators(self):
        """Get list of enabled generator instances."""
        return [
            gen_data['instance'] 
            for gen_data in self.generators.values() 
            if gen_data['enabled']
        ]
    
    def cleanup(self):
        """Cleanup when switching away from signals page."""
        self.stop_updates = True
        self._log_debug("Signals display cleanup initiated")
