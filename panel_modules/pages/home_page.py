"""
Home page component for the trading panel
"""
import tkinter as tk
from panel_modules.coingecko_price_fetcher import CoinGeckoPriceFetcher


class HomePage:
    """Handles the home page display"""
    
    def __init__(self, parent, colors, api, positions_manager, orders_manager):
        """
        Initialize home page
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
            api: API instance
            positions_manager: PositionsManager instance
            orders_manager: OrdersManager instance
        """
        self.parent = parent
        self.colors = colors
        self.api = api
        self.positions_manager = positions_manager
        self.orders_manager = orders_manager
        
        # Initialize CoinGecko price fetcher
        self.price_fetcher = CoinGeckoPriceFetcher()
        
        # Label references
        self.balance_label = None
        self.available_label = None
        self.in_positions_label = None
        self.unrealized_pnl_label = None
        self.btc_price_label = None
        self.btc_change_label = None
        self.btc_high_label = None
        self.btc_low_label = None
        self.btc_volume_label = None
        self.btc_mark_label = None
        
    def create_page(self):
        """Create the home page content"""
        # Left column
        left_col = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_live_ticker(left_col)
        self.create_account_summary(left_col)
        
        # Right column
        right_col = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_open_positions(right_col)
        self.create_recent_activity(right_col)
    
    def create_live_ticker(self, parent):
        """Create the live market price ticker"""
        ticker_frame = tk.Frame(parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        ticker_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(ticker_frame, text="═══ LIVE MARKET PRICE ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 11, 'bold')).pack(pady=10)
        
        # Selected pair display
        pair_display = tk.Frame(ticker_frame, bg=self.colors['bg_dark'])
        pair_display.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(pair_display, text="BTC/USDT", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 10)).pack(side=tk.LEFT, padx=10)
        
        # Price label (will be updated)
        self.btc_price_label = tk.Label(pair_display, text="Loading...", bg=self.colors['bg_dark'], 
                                       fg=self.colors['white'], font=('Courier', 20, 'bold'))
        self.btc_price_label.pack(side=tk.LEFT, padx=10)
        
        # Change label (will be updated)
        self.btc_change_label = tk.Label(pair_display, text="---%", bg=self.colors['bg_dark'], 
                                        fg=self.colors['gray'], font=('Courier', 12, 'bold'))
        self.btc_change_label.pack(side=tk.LEFT, padx=10)
        
        # Market stats
        stats_frame = tk.Frame(ticker_frame, bg=self.colors['bg_panel'])
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Row 1
        row1 = tk.Frame(stats_frame, bg=self.colors['bg_panel'])
        row1.pack(fill=tk.X, pady=2)
        
        col1 = tk.Frame(row1, bg=self.colors['bg_panel'])
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(col1, text="24H HIGH:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), anchor='w').pack(side=tk.LEFT, padx=5)
        self.btc_high_label = tk.Label(col1, text="--", bg=self.colors['bg_panel'], 
                                      fg=self.colors['gray'], font=('Courier', 9, 'bold'), anchor='e')
        self.btc_high_label.pack(side=tk.RIGHT, padx=5)
        
        col2 = tk.Frame(row1, bg=self.colors['bg_panel'])
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(col2, text="24H LOW:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), anchor='w').pack(side=tk.LEFT, padx=5)
        self.btc_low_label = tk.Label(col2, text="--", bg=self.colors['bg_panel'], 
                                     fg=self.colors['gray'], font=('Courier', 9, 'bold'), anchor='e')
        self.btc_low_label.pack(side=tk.RIGHT, padx=5)
        
        # Row 2
        row2 = tk.Frame(stats_frame, bg=self.colors['bg_panel'])
        row2.pack(fill=tk.X, pady=2)
        
        col3 = tk.Frame(row2, bg=self.colors['bg_panel'])
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(col3, text="24H VOL:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), anchor='w').pack(side=tk.LEFT, padx=5)
        self.btc_volume_label = tk.Label(col3, text="--", bg=self.colors['bg_panel'], 
                                        fg=self.colors['gray'], font=('Courier', 9, 'bold'), anchor='e')
        self.btc_volume_label.pack(side=tk.RIGHT, padx=5)
        
        col4 = tk.Frame(row2, bg=self.colors['bg_panel'])
        col4.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(col4, text="MARK PRICE:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), anchor='w').pack(side=tk.LEFT, padx=5)
        self.btc_mark_label = tk.Label(col4, text="--", bg=self.colors['bg_panel'], 
                                      fg=self.colors['yellow'], font=('Courier', 9, 'bold'), anchor='e')
        self.btc_mark_label.pack(side=tk.RIGHT, padx=5)
    
    def create_account_summary(self, parent):
        """Create the account summary display"""
        summary_frame = tk.Frame(parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(summary_frame, text="═══ ACCOUNT SUMMARY ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 11, 'bold')).pack(pady=10)
        
        # Balance display
        balance_box = tk.Frame(summary_frame, bg=self.colors['bg_dark'])
        balance_box.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        tk.Label(balance_box, text="TOTAL BALANCE", bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 9)).pack()
        self.balance_label = tk.Label(balance_box, text="$0.00", bg=self.colors['bg_dark'], 
                                      fg=self.colors['white'], font=('Courier', 18, 'bold'))
        self.balance_label.pack(pady=5)
        
        # Stats grid
        stats_grid = tk.Frame(summary_frame, bg=self.colors['bg_panel'])
        stats_grid.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Available
        row1 = tk.Frame(stats_grid, bg=self.colors['bg_panel'])
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="AVAILABLE:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), width=18, anchor='w').pack(side=tk.LEFT)
        self.available_label = tk.Label(row1, text="0.00 USDT", bg=self.colors['bg_panel'], 
                                       fg=self.colors['green'], font=('Courier', 10, 'bold'), anchor='e')
        self.available_label.pack(side=tk.RIGHT)
        
        # In Positions
        row2 = tk.Frame(stats_grid, bg=self.colors['bg_panel'])
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="IN POSITIONS:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), width=18, anchor='w').pack(side=tk.LEFT)
        self.in_positions_label = tk.Label(row2, text="0.00 USDT", bg=self.colors['bg_panel'], 
                                          fg=self.colors['white'], font=('Courier', 10, 'bold'), anchor='e')
        self.in_positions_label.pack(side=tk.RIGHT)
        
        # Unrealized PNL
        row3 = tk.Frame(stats_grid, bg=self.colors['bg_panel'])
        row3.pack(fill=tk.X, pady=3)
        tk.Label(row3, text="UNREALIZED PNL:", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9), width=18, anchor='w').pack(side=tk.LEFT)
        self.unrealized_pnl_label = tk.Label(row3, text="+0.00 USDT", bg=self.colors['bg_panel'], 
                                            fg=self.colors['green'], font=('Courier', 10, 'bold'), anchor='e')
        self.unrealized_pnl_label.pack(side=tk.RIGHT)
    
    def create_open_positions(self, parent):
        """Create the open positions display"""
        self.positions_manager.parent = parent
        self.positions_manager.create_positions_display()
        self.positions_manager.update_positions()
    
    def create_recent_activity(self, parent):
        """Create the recent activity display"""
        self.orders_manager.parent = parent
        self.orders_manager.create_orders_display()
        self.orders_manager.update_display()
    
    def update_data(self):
        """Update home page data"""
        # Update BTC price using CoinGecko
        try:
            ticker_data = self.price_fetcher.get_ticker_24h('BTC')
            
            if ticker_data:
                btc_price = ticker_data['price']
                
                # Update price label
                if self.btc_price_label and self.btc_price_label.winfo_exists():
                    price_str = f"${btc_price:,.2f}"
                    self.btc_price_label.config(text=price_str)
                
                # Update change percentage
                if self.btc_change_label and self.btc_change_label.winfo_exists():
                    price_change = ticker_data['price_change_pct']
                    change_color = self.colors['green'] if price_change > 0 else self.colors['red'] if price_change < 0 else self.colors['gray']
                    change_text = f"+{price_change:.2f}%" if price_change > 0 else f"{price_change:.2f}%"
                    self.btc_change_label.config(text=change_text, fg=change_color)
                
                # Update 24h high
                if self.btc_high_label and self.btc_high_label.winfo_exists():
                    self.btc_high_label.config(text=f"${ticker_data['high_24h']:,.2f}")
                
                # Update 24h low
                if self.btc_low_label and self.btc_low_label.winfo_exists():
                    self.btc_low_label.config(text=f"${ticker_data['low_24h']:,.2f}")
                
                # Update 24h volume
                if self.btc_volume_label and self.btc_volume_label.winfo_exists():
                    volume_billions = ticker_data['volume_24h'] / 1_000_000_000
                    self.btc_volume_label.config(text=f"${volume_billions:.2f}B")
                
                # Update mark price (same as current price for CoinGecko)
                if self.btc_mark_label and self.btc_mark_label.winfo_exists():
                    self.btc_mark_label.config(text=f"${btc_price:,.2f}")
            else:
                # If API call fails, show cached data or error
                if self.btc_change_label and self.btc_change_label.winfo_exists():
                    self.btc_change_label.config(text="ERROR", fg=self.colors['red'])
                    
        except Exception as e:
            print(f"Error updating BTC price from CoinGecko: {e}")
            if self.btc_change_label and self.btc_change_label.winfo_exists():
                self.btc_change_label.config(text="ERROR", fg=self.colors['red'])
        
        # Update account summary
        if self.api.connected:
            summary = self.api.get_account_summary()
            if summary:
                if self.balance_label and self.balance_label.winfo_exists():
                    self.balance_label.config(text=f"${summary['total_balance']:.2f}")
                
                if self.available_label and self.available_label.winfo_exists():
                    self.available_label.config(text=f"{summary['available']:.2f} USDT")
                
                if self.in_positions_label and self.in_positions_label.winfo_exists():
                    self.in_positions_label.config(text=f"{summary['in_positions']:.2f} USDT")
                
                if self.unrealized_pnl_label and self.unrealized_pnl_label.winfo_exists():
                    pnl = summary['unrealized_pnl']
                    pnl_color = self.colors['green'] if pnl > 0 else self.colors['red'] if pnl < 0 else self.colors['white']
                    pnl_text = f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}"
                    self.unrealized_pnl_label.config(text=f"{pnl_text} USDT", fg=pnl_color)
        
        # Update positions
        if self.positions_manager and hasattr(self.positions_manager, 'update_positions'):
            try:
                self.positions_manager.update_positions()
            except Exception as e:
                print(f"Error updating positions: {e}")
