"""
Orders Module - Handles order display and management
"""

import tkinter as tk
from datetime import datetime


class OrdersManager:
    """Manages order display and tracking"""
    
    def __init__(self, parent_frame, colors, api=None):
        self.parent = parent_frame
        self.colors = colors
        self.orders = []
        self.api = api
        
    def create_orders_display(self):
        """Create the recent activity/orders display panel"""
        activity_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], 
                                 relief=tk.SOLID, borderwidth=1)
        activity_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(activity_frame, text="═══ RECENT ACTIVITY ═══", 
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 11, 'bold')).pack(pady=10)
        
        # Container for activity rows
        self.activity_container = tk.Frame(activity_frame, bg=self.colors['bg_panel'])
        self.activity_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        return activity_frame
    
    def add_order(self, time, action, pair, details):
        """Add an order to the activity log"""
        order = {
            'time': time,
            'action': action,
            'pair': pair,
            'details': details,
            'color': self.colors['green'] if action == "BUY" else self.colors['red']
        }
        self.orders.insert(0, order)  # Add to beginning
        
        # Keep only last 20 orders
        if len(self.orders) > 20:
            self.orders = self.orders[:20]
        
        self.update_display()
    
    def update_display(self):
        """Update the orders display with last 10 trades from API"""
        # Clear existing
        for widget in self.activity_container.winfo_children():
            widget.destroy()
        
        # Try to get real trades from API
        if self.api and hasattr(self.api, 'get_user_fills'):
            try:
                fills = self.api.get_user_fills(limit=10)  # Get last 10 trades
                
                if fills:
                    for fill in fills:
                        activity_row = tk.Frame(self.activity_container, bg=self.colors['bg_dark'])
                        activity_row.pack(fill=tk.X, pady=2)
                        
                        # Time
                        timestamp = int(fill.get('time', 0)) / 1000
                        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                        tk.Label(activity_row, text=time_str, bg=self.colors['bg_dark'], 
                                fg=self.colors['gray'], font=('Courier', 8), 
                                width=9, anchor='w').pack(side=tk.LEFT, padx=2)
                        
                        # Action (Buy/Sell)
                        side = fill.get('side', 'N/A')
                        action = "BUY" if side == 'B' else "SELL"
                        color = self.colors['green'] if side == 'B' else self.colors['red']
                        tk.Label(activity_row, text=action, bg=self.colors['bg_dark'], 
                                fg=color, font=('Courier', 8, 'bold'), 
                                width=5, anchor='w').pack(side=tk.LEFT, padx=2)
                        
                        # Coin
                        coin = fill.get('coin', 'N/A')
                        tk.Label(activity_row, text=coin, bg=self.colors['bg_dark'], 
                                fg=self.colors['white'], font=('Courier', 8, 'bold'), 
                                width=7, anchor='w').pack(side=tk.LEFT, padx=2)
                        
                        # Size
                        size = abs(float(fill.get('sz', 0)))
                        tk.Label(activity_row, text=f"{size:.4f}", bg=self.colors['bg_dark'], 
                                fg=self.colors['white'], font=('Courier', 8), 
                                width=10, anchor='e').pack(side=tk.LEFT, padx=2)
                        
                        # Price
                        price = float(fill.get('px', 0))
                        tk.Label(activity_row, text=f"@{price:,.2f}", bg=self.colors['bg_dark'], 
                                fg=self.colors['white'], font=('Courier', 8), 
                                width=11, anchor='e').pack(side=tk.LEFT, padx=2)
                        
                        # P&L (if closed position)
                        closed_pnl = float(fill.get('closedPnl', 0) or 0)
                        if closed_pnl != 0:
                            pnl_color = self.colors['green'] if closed_pnl > 0 else self.colors['red']
                            pnl_text = f"+${closed_pnl:.2f}" if closed_pnl > 0 else f"${closed_pnl:.2f}"
                            tk.Label(activity_row, text=pnl_text, bg=self.colors['bg_dark'], 
                                    fg=pnl_color, font=('Courier', 8, 'bold'), 
                                    width=10, anchor='e').pack(side=tk.LEFT, padx=2)
                        else:
                            # Empty space for alignment
                            tk.Label(activity_row, text="", bg=self.colors['bg_dark'], 
                                    width=10).pack(side=tk.LEFT, padx=2)
                    return
            except Exception as e:
                print(f"Error fetching recent trades: {e}")
        
        # Fallback to demo data if API not available or no trades
        self._show_demo_orders()
    
    def _show_demo_orders(self):
        """Show demo orders with enhanced details"""
        demo_orders = [
            ("14:32:15", "BUY", "BTC", "0.0250", "43,240.00", "+12.50", self.colors['green']),
            ("14:28:42", "SELL", "ETH", "1.5000", "2,287.00", "-5.20", self.colors['red']),
            ("14:25:11", "BUY", "XRP", "500.0000", "0.6234", "+8.75", self.colors['green']),
            ("14:19:33", "SELL", "SOL", "5.0000", "98.50", "+15.30", self.colors['green']),
            ("14:15:20", "BUY", "BNB", "2.5000", "312.00", "", self.colors['green']),
            ("14:12:08", "SELL", "BTC", "0.0180", "43,180.00", "-3.40", self.colors['red']),
            ("14:08:45", "BUY", "ETH", "2.0000", "2,275.00", "+22.10", self.colors['green']),
            ("14:05:22", "SELL", "XRP", "800.0000", "0.6198", "+6.85", self.colors['green'])
        ]
        
        for time, action, coin, size, price, pnl, color in demo_orders:
            activity_row = tk.Frame(self.activity_container, bg=self.colors['bg_dark'])
            activity_row.pack(fill=tk.X, pady=2)
            
            # Time
            tk.Label(activity_row, text=time, bg=self.colors['bg_dark'], 
                    fg=self.colors['gray'], font=('Courier', 8), 
                    width=9, anchor='w').pack(side=tk.LEFT, padx=2)
            
            # Action
            tk.Label(activity_row, text=action, bg=self.colors['bg_dark'], 
                    fg=color, font=('Courier', 8, 'bold'), 
                    width=5, anchor='w').pack(side=tk.LEFT, padx=2)
            
            # Coin
            tk.Label(activity_row, text=coin, bg=self.colors['bg_dark'], 
                    fg=self.colors['white'], font=('Courier', 8, 'bold'), 
                    width=7, anchor='w').pack(side=tk.LEFT, padx=2)
            
            # Size
            tk.Label(activity_row, text=size, bg=self.colors['bg_dark'], 
                    fg=self.colors['white'], font=('Courier', 8), 
                    width=10, anchor='e').pack(side=tk.LEFT, padx=2)
            
            # Price
            tk.Label(activity_row, text=f"@{price}", bg=self.colors['bg_dark'], 
                    fg=self.colors['white'], font=('Courier', 8), 
                    width=11, anchor='e').pack(side=tk.LEFT, padx=2)
            
            # P&L
            if pnl:
                pnl_color = self.colors['green'] if pnl.startswith('+') else self.colors['red']
                tk.Label(activity_row, text=f"${pnl}", bg=self.colors['bg_dark'], 
                        fg=pnl_color, font=('Courier', 8, 'bold'), 
                        width=10, anchor='e').pack(side=tk.LEFT, padx=2)
            else:
                tk.Label(activity_row, text="", bg=self.colors['bg_dark'], 
                        width=10).pack(side=tk.LEFT, padx=2)
