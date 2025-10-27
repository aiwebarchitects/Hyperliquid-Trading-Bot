"""
Position Monitor Module - Real-time position monitoring with detailed state tracking.
Shows trailing stop status, exit condition distances, and position health.
"""

import tkinter as tk
from typing import Dict, List, Optional
from datetime import datetime


class PositionMonitor:
    """
    Position Monitor for detailed position tracking and debugging.
    Shows real-time position states, trailing stops, and exit conditions.
    """
    
    def __init__(self, parent, colors: Dict, position_manager):
        """
        Initialize Position Monitor.
        
        Args:
            parent: Parent tkinter frame
            colors: Color scheme dictionary
            position_manager: Position manager instance from managers/position_manager.py
        """
        self.parent = parent
        self.colors = colors
        self.position_manager = position_manager
        
        # UI elements
        self.table_frame = None
        self.position_rows = {}  # Store label references by coin
        self.no_positions_label = None
    
    def create_monitor_display(self):
        """Create the position monitor UI"""
        # Title
        title_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], 
                              relief=tk.SOLID, borderwidth=1)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="═══ POSITION MONITOR - REAL-TIME TRACKING ═══",
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 12, 'bold')).pack(pady=10)
        
        # Table container
        table_container = tk.Frame(self.parent, bg=self.colors['bg_panel'],
                                  relief=tk.SOLID, borderwidth=1)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Table header
        header_frame = tk.Frame(table_container, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X, padx=2, pady=2)
        
        headers = [
            ("COIN", 8),
            ("TYPE", 6),
            ("ENTRY", 10),
            ("CURRENT", 10),
            ("SIZE", 10),
            ("PNL %", 8),
            ("PNL $", 10),
            ("HIGHEST", 8),
            ("TO SL", 8),
            ("TO TP", 8),
            ("TRAILING", 12)
        ]
        
        for header, width in headers:
            tk.Label(header_frame, text=header, bg=self.colors['bg_dark'],
                    fg=self.colors['yellow'], font=('Courier', 9, 'bold'),
                    width=width, anchor='center').pack(side=tk.LEFT, padx=1)
        
        # Table rows container
        self.table_frame = tk.Frame(table_container, bg=self.colors['bg_panel'])
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Initial update
        self.update_monitor()
    
    def update_monitor(self):
        """Update the position monitor display"""
        # Get all positions with state info
        positions = self.position_manager.get_all_positions()
        
        if not positions:
            # Show no positions message
            if not self.no_positions_label:
                # Clear any existing position rows
                for coin in list(self.position_rows.keys()):
                    self._remove_position_row(coin)
                
                # Create no positions message
                no_pos_frame = tk.Frame(self.table_frame, bg=self.colors['bg_panel'])
                no_pos_frame.pack(fill=tk.BOTH, expand=True)
                
                self.no_positions_label = tk.Label(no_pos_frame, text="No open positions to monitor",
                        bg=self.colors['bg_panel'], fg=self.colors['gray'],
                        font=('Courier', 12))
                self.no_positions_label.pack(pady=50)
            return
        
        # Remove no positions message if it exists
        if self.no_positions_label:
            self.no_positions_label.master.destroy()
            self.no_positions_label = None
        
        # Get current coins
        current_coins = {pos['position'].get('coin') for pos in positions}
        
        # Remove rows for positions that no longer exist
        for coin in list(self.position_rows.keys()):
            if coin not in current_coins:
                self._remove_position_row(coin)
        
        # Update or create rows for each position
        for pos_data in positions:
            coin = pos_data['position'].get('coin')
            if coin in self.position_rows:
                self._update_position_row(coin, pos_data)
            else:
                self._create_position_row(pos_data)
    
    def _create_position_row(self, pos_data: Dict):
        """
        Create a table row for a single position.
        
        Args:
            pos_data: Dictionary with 'position' and 'state' keys
        """
        position = pos_data.get('position', {})
        coin = position.get('coin', 'N/A')
        size = float(position.get('szi', 0))
        
        # Determine row color
        row_bg = self.colors['bg_dark']
        
        # Create row
        row = tk.Frame(self.table_frame, bg=row_bg)
        row.pack(fill=tk.X, pady=1)
        
        # Create labels and store references
        labels = {}
        
        # Coin (static)
        labels['coin'] = tk.Label(row, text=coin, bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9, 'bold'), width=8, anchor='center')
        labels['coin'].pack(side=tk.LEFT, padx=1)
        
        # Type (static)
        type_color = self.colors['green'] if size > 0 else self.colors['red']
        position_type = "LONG" if size > 0 else "SHORT"
        labels['type'] = tk.Label(row, text=position_type, bg=row_bg, fg=type_color,
                font=('Courier', 9, 'bold'), width=6, anchor='center')
        labels['type'].pack(side=tk.LEFT, padx=1)
        
        # Entry (static)
        labels['entry'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9), width=10, anchor='center')
        labels['entry'].pack(side=tk.LEFT, padx=1)
        
        # Current (dynamic)
        labels['current'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9), width=10, anchor='center')
        labels['current'].pack(side=tk.LEFT, padx=1)
        
        # Size (static)
        labels['size'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9), width=10, anchor='center')
        labels['size'].pack(side=tk.LEFT, padx=1)
        
        # PNL % (dynamic)
        labels['pnl_pct'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9, 'bold'), width=8, anchor='center')
        labels['pnl_pct'].pack(side=tk.LEFT, padx=1)
        
        # PNL $ (dynamic)
        labels['pnl_usd'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9, 'bold'), width=10, anchor='center')
        labels['pnl_usd'].pack(side=tk.LEFT, padx=1)
        
        # Highest (dynamic)
        labels['highest'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['yellow'],
                font=('Courier', 9), width=8, anchor='center')
        labels['highest'].pack(side=tk.LEFT, padx=1)
        
        # To SL (dynamic)
        labels['to_sl'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9), width=8, anchor='center')
        labels['to_sl'].pack(side=tk.LEFT, padx=1)
        
        # To TP (dynamic)
        labels['to_tp'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['white'],
                font=('Courier', 9), width=8, anchor='center')
        labels['to_tp'].pack(side=tk.LEFT, padx=1)
        
        # Trailing (dynamic)
        labels['trailing'] = tk.Label(row, text="", bg=row_bg, fg=self.colors['gray'],
                font=('Courier', 9), width=12, anchor='center')
        labels['trailing'].pack(side=tk.LEFT, padx=1)
        
        # Store references
        self.position_rows[coin] = {
            'row': row,
            'labels': labels
        }
        
        # Initial update
        self._update_position_row(coin, pos_data)
    
    def _update_position_row(self, coin: str, pos_data: Dict):
        """
        Update an existing position row with new data.
        
        Args:
            coin: Coin symbol
            pos_data: Dictionary with 'position' and 'state' keys
        """
        if coin not in self.position_rows:
            return
        
        labels = self.position_rows[coin]['labels']
        row = self.position_rows[coin]['row']
        
        position = pos_data.get('position', {})
        state = pos_data.get('state', {})
        
        # Extract position data - handle both API format and direct format
        entry_price = float(position.get('entryPx', position.get('entry_price', 0)))
        size = float(position.get('szi', position.get('size', 0)))
        unrealized_pnl = float(position.get('unrealizedPnl', position.get('unrealized_pnl', 0)))
        
        # Get REAL PNL percentage - handle both API formats
        pnl_pct = float(position.get('returnOnEquity', 0)) * 100
        if pnl_pct == 0:
            pnl_pct = float(position.get('profit_pct', 0))
        
        # Get current price for display
        current_price = float(position.get('current_price', 0))
        if not current_price:
            current_price = self.position_manager.api.get_current_price(coin)
        if not current_price:
            current_price = entry_price
        
        # Get state info - CRITICAL: highest_pnl_pct should ALWAYS exist in state
        # The position_manager ensures this in get_all_positions()
        # If it's missing, something is wrong - use current pnl as emergency fallback
        # but this should NEVER happen in normal operation
        highest_pnl_pct = state.get('highest_pnl_pct')
        if highest_pnl_pct is None:
            print(f"⚠️ WARNING: {coin} has no highest_pnl_pct in state! Using current PnL as emergency fallback.")
            highest_pnl_pct = pnl_pct
        
        # CRITICAL: Highest can ONLY go UP, never down!
        # If current PnL is higher than stored highest, update it
        # (This shouldn't happen here as position_manager handles it, but safety check)
        if pnl_pct > highest_pnl_pct:
            print(f"⚠️ WARNING: {coin} current PnL ({pnl_pct:.2f}%) > stored highest ({highest_pnl_pct:.2f}%)!")
            print(f"   This should be handled by position_manager, not here!")
            highest_pnl_pct = pnl_pct
        
        trailing_active = state.get('trailing_stop_activated', False)
        
        # DEBUG: Print what we're displaying
        print(f"📊 {coin}: Current PnL={pnl_pct:.2f}%, Highest={highest_pnl_pct:.2f}%, Trailing={trailing_active}")
        
        # Get settings
        settings = self.position_manager.settings
        sl_pct = settings['stop_loss_percent']
        tp_pct = settings['take_profit_percent']
        trailing_distance = settings['trailing_stop_percent']
        
        # FIXED stop loss and take profit levels (not distances!)
        fixed_sl_level = -sl_pct  # Always negative
        fixed_tp_level = tp_pct   # Always positive
        
        # Update row background color
        if pnl_pct > 0:
            row_bg = self.colors['bg_dark']
        else:
            row_bg = '#1a0a0a'
        row.config(bg=row_bg)
        for label in labels.values():
            label.config(bg=row_bg)
        
        # Update labels
        labels['entry'].config(text=f"${entry_price:,.2f}")
        labels['current'].config(text=f"${current_price:,.2f}")
        labels['size'].config(text=f"{abs(size):.4f}")
        
        # PNL %
        pnl_color = self.colors['green'] if pnl_pct > 0 else self.colors['red']
        pnl_text = f"+{pnl_pct:.2f}%" if pnl_pct > 0 else f"{pnl_pct:.2f}%"
        labels['pnl_pct'].config(text=pnl_text, fg=pnl_color)
        
        # PNL $
        pnl_usd_text = f"+${unrealized_pnl:.2f}" if unrealized_pnl > 0 else f"${unrealized_pnl:.2f}"
        labels['pnl_usd'].config(text=pnl_usd_text, fg=pnl_color)
        
        # Highest
        labels['highest'].config(text=f"{highest_pnl_pct:.2f}%")
        
        # TO SL - Show FIXED stop loss level
        sl_color = self.colors['red'] if pnl_pct <= fixed_sl_level else self.colors['white']
        labels['to_sl'].config(text=f"{fixed_sl_level:.2f}%", fg=sl_color)
        
        # TO TP - Show FIXED take profit level (or trailing if active)
        if trailing_active:
            trailing_tp_level = highest_pnl_pct - trailing_distance
            tp_color = self.colors['green'] if pnl_pct <= trailing_tp_level else self.colors['white']
            labels['to_tp'].config(text=f"{trailing_tp_level:.2f}%", fg=tp_color)
        else:
            tp_color = self.colors['green'] if pnl_pct >= fixed_tp_level else self.colors['white']
            labels['to_tp'].config(text=f"{fixed_tp_level:.2f}%", fg=tp_color)
        
        # Trailing
        if trailing_active:
            trailing_stop_level = highest_pnl_pct - trailing_distance
            trailing_text = f"✓ {trailing_stop_level:.2f}%"
            trailing_color = self.colors['green']
        else:
            trailing_text = "INACTIVE"
            trailing_color = self.colors['gray']
        labels['trailing'].config(text=trailing_text, fg=trailing_color)
    
    def _remove_position_row(self, coin: str):
        """
        Remove a position row.
        
        Args:
            coin: Coin symbol
        """
        if coin in self.position_rows:
            self.position_rows[coin]['row'].destroy()
            del self.position_rows[coin]
