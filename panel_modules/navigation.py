"""
Navigation bar component for the trading panel
"""
import tkinter as tk


class NavigationBar:
    """Handles the navigation bar and page switching"""
    
    def __init__(self, parent, colors, switch_callback):
        """
        Initialize navigation bar
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
            switch_callback: Function to call when switching pages
        """
        self.parent = parent
        self.colors = colors
        self.switch_callback = switch_callback
        self.nav_buttons = {}
        self.current_page = "home"
        
    def create_navigation(self):
        """Create the navigation bar"""
        nav_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], height=50)
        nav_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        nav_frame.pack_propagate(False)
        
        nav_items = ["HOME", "SIGNALS", "POSITIONS", "MONITOR", "HISTORY", "BACKTEST", "API SETTINGS", "SETTINGS", "DEBUG"]
        
        for i, item in enumerate(nav_items):
            btn_bg = self.colors['green'] if i == 0 else self.colors['bg_panel']
            btn_fg = self.colors['bg_dark'] if i == 0 else self.colors['white']
            
            btn = tk.Label(nav_frame, text=item, bg=btn_bg, fg=btn_fg,
                          font=('Courier', 10, 'bold'), padx=20, pady=10, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Button-1>", lambda e, page=item.lower(): self.switch_page(page))
            self.nav_buttons[item.lower()] = btn
    
    def switch_page(self, page):
        """
        Switch to a different page
        
        Args:
            page: Page name to switch to
        """
        self.current_page = page
        
        # Update button colors
        for nav_page, btn in self.nav_buttons.items():
            if nav_page == page:
                btn.config(bg=self.colors['green'], fg=self.colors['bg_dark'])
            else:
                btn.config(bg=self.colors['bg_panel'], fg=self.colors['white'])
        
        # Call the switch callback
        self.switch_callback(page)
