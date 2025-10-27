"""
Header and status components for the trading panel
"""
import tkinter as tk
from datetime import datetime
import pytz


class HeaderComponent:
    """Handles the header display with title and time"""
    
    def __init__(self, parent, colors):
        """
        Initialize header component
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
        """
        self.parent = parent
        self.colors = colors
        self.time_label = None
        
    def create_header(self):
        """Create the header with title and time display"""
        header_frame = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title = tk.Label(header_frame, text="⬤ AUTOMATED TRADING BOT v0.1", 
                        bg=self.colors['bg_dark'], fg=self.colors['green'],
                        font=('Courier', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Time display container
        time_container = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        time_container.pack(side=tk.RIGHT)
        
        # Store time label reference for updates
        self.time_label = tk.Label(time_container, 
                             text="",
                             bg=self.colors['bg_dark'], fg=self.colors['white'],
                             font=('Courier', 10))
        self.time_label.pack()
        
        # Start time updates
        self.update_time_display()
    
    def update_time_display(self):
        """Update time display with CET and US Eastern time"""
        try:
            # Get current time in CET
            cet_tz = pytz.timezone('Europe/Paris')  # CET/CEST
            cet_time = datetime.now(cet_tz)
            
            # Get current time in US Eastern
            us_tz = pytz.timezone('America/New_York')  # EST/EDT
            us_time = datetime.now(us_tz)
            
            # Format the display
            time_text = f"LIVE | CET: {cet_time.strftime('%Y-%m-%d %H:%M:%S')} | US: {us_time.strftime('%H:%M:%S %Z')}"
            
            if self.time_label and self.time_label.winfo_exists():
                self.time_label.config(text=time_text)
        except Exception as e:
            print(f"Error updating time display: {e}")
            # Fallback to simple display
            if self.time_label and self.time_label.winfo_exists():
                self.time_label.config(text=f"LIVE | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Schedule next update (every second)
        if self.time_label and self.time_label.winfo_exists():
            self.parent.after(1000, self.update_time_display)


class BotStatusComponent:
    """Handles the bot status display and controls"""
    
    def __init__(self, parent, colors, toggle_callback):
        """
        Initialize bot status component
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
            toggle_callback: Function to call when toggling bot
        """
        self.parent = parent
        self.colors = colors
        self.toggle_callback = toggle_callback
        self.bot_status_label = None
        self.bot_control_btn = None
        self.uptime_label = None
        self.positions_count_label = None
        self.start_time = datetime.now()
        
    def create_bot_status(self):
        """Create the bot status display"""
        status_container = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        status_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Bot Status with START/STOP button
        bot_frame = tk.Frame(status_container, bg=self.colors['bg_panel'], 
                            relief=tk.SOLID, borderwidth=1)
        bot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(bot_frame, text="BOT STATUS", bg=self.colors['bg_panel'], 
                fg=self.colors['gray'], font=('Courier', 9)).pack(pady=(5, 2))
        
        self.bot_status_label = tk.Label(bot_frame, text="● STOPPED", 
                                         bg=self.colors['bg_panel'], fg=self.colors['red'],
                                         font=('Courier', 12, 'bold'))
        self.bot_status_label.pack(pady=(0, 5))
        
        # Start/Stop button
        self.bot_control_btn = tk.Button(bot_frame, text="START BOT", 
                                         command=self.toggle_callback,
                                         bg=self.colors['green'], fg=self.colors['bg_dark'],
                                         font=('Courier', 9, 'bold'),
                                         cursor="hand2", relief=tk.RAISED)
        self.bot_control_btn.pack(pady=(0, 10))
        
        # Strategy
        strat_frame = tk.Frame(status_container, bg=self.colors['bg_panel'], 
                              relief=tk.SOLID, borderwidth=1)
        strat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(strat_frame, text="STRATEGY", bg=self.colors['bg_panel'], 
                fg=self.colors['gray'], font=('Courier', 9)).pack(pady=(10, 2))
        tk.Label(strat_frame, text="MULTI-ALGO", bg=self.colors['bg_panel'], 
                fg=self.colors['blue'], font=('Courier', 12, 'bold')).pack(pady=(0, 10))
        
        # Uptime
        uptime_frame = tk.Frame(status_container, bg=self.colors['bg_panel'], 
                               relief=tk.SOLID, borderwidth=1)
        uptime_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(uptime_frame, text="UPTIME", bg=self.colors['bg_panel'], 
                fg=self.colors['gray'], font=('Courier', 9)).pack(pady=(10, 2))
        self.uptime_label = tk.Label(uptime_frame, text="0h 0m 0s", 
                                     bg=self.colors['bg_panel'], fg=self.colors['white'],
                                     font=('Courier', 12, 'bold'))
        self.uptime_label.pack(pady=(0, 10))
        
        # Total Trades
        trades_frame = tk.Frame(status_container, bg=self.colors['bg_panel'], 
                               relief=tk.SOLID, borderwidth=1)
        trades_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(trades_frame, text="OPEN POSITIONS", bg=self.colors['bg_panel'], 
                fg=self.colors['gray'], font=('Courier', 9)).pack(pady=(10, 2))
        self.positions_count_label = tk.Label(trades_frame, text="0/10", 
                                             bg=self.colors['bg_panel'], fg=self.colors['white'],
                                             font=('Courier', 14, 'bold'))
        self.positions_count_label.pack(pady=(0, 10))
    
    def update_bot_status(self, running):
        """Update bot status display"""
        if running:
            self.bot_status_label.config(text="● RUNNING", fg=self.colors['green'])
            self.bot_control_btn.config(text="STOP BOT", bg=self.colors['red'])
        else:
            self.bot_status_label.config(text="● STOPPED", fg=self.colors['red'])
            self.bot_control_btn.config(text="START BOT", bg=self.colors['green'])
    
    def update_uptime(self):
        """Update uptime display"""
        if self.uptime_label and self.uptime_label.winfo_exists():
            uptime = datetime.now() - self.start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            seconds = int(uptime.total_seconds() % 60)
            self.uptime_label.config(text=f"{hours}h {minutes}m {seconds}s")
    
    def update_positions_count(self, count, max_count):
        """Update positions count display"""
        if self.positions_count_label and self.positions_count_label.winfo_exists():
            self.positions_count_label.config(text=f"{count}/{max_count}")


class StatusBar:
    """Handles the bottom status bar"""
    
    def __init__(self, parent, colors, api):
        """
        Initialize status bar
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
            api: API instance for connection status
        """
        self.parent = parent
        self.colors = colors
        self.api = api
        self.status_label = None
        self.bot_running = False
        
    def create_status_bar(self):
        """Create the bottom status bar"""
        status_frame = tk.Frame(self.parent, bg=self.colors['green'], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Bot status label (will be updated with real status)
        self.status_label = tk.Label(status_frame, text="● BOT STOPPED", 
                                     bg=self.colors['green'], 
                                     fg=self.colors['bg_dark'], 
                                     font=('Courier', 9, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Exchange link label
        exchange_label = tk.Label(status_frame, text="EXCHANGE: HYPERLIQUID", 
                                 bg=self.colors['green'], 
                                 fg=self.colors['bg_dark'], 
                                 font=('Courier', 9, 'underline'),
                                 cursor="hand2")
        exchange_label.pack(side=tk.RIGHT, padx=10)
        exchange_label.bind("<Button-1>", lambda e: self._open_exchange_link())
    
    def _open_exchange_link(self):
        """Open Hyperliquid exchange with bonus link"""
        import webbrowser
        webbrowser.open("https://app.hyperliquid.xyz/join/BONUS500")
    
    def update_bot_status(self, running):
        """Update the bot status display with real status"""
        if self.status_label and self.status_label.winfo_exists():
            self.bot_running = running
            if running:
                self.status_label.config(text="● BOT RUNNING")
            else:
                self.status_label.config(text="● BOT STOPPED")
