"""
Debug Settings Page - Control debugging features (Tkinter version)
"""

import tkinter as tk
from config.debug_settings import get_all_debug_settings, set_debug_setting


class DebugPage:
    """Debug settings page for controlling console output"""
    
    def __init__(self, parent, colors):
        """
        Initialize debug page
        
        Args:
            parent: Parent tkinter widget
            colors: Dictionary of color scheme
        """
        self.parent = parent
        self.colors = colors
        self.debug_vars = {}
    
    def create_page(self):
        """Create the debug settings page"""
        # Title
        title_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(title_frame, text="═══ DEBUG SETTINGS ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 14, 'bold')).pack(pady=15)
        
        # Description
        desc_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(desc_frame, text="Control console output and debugging features", 
                bg=self.colors['bg_panel'], fg=self.colors['gray'], 
                font=('Courier', 10)).pack(pady=10)
        
        # Settings container
        settings_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get current debug settings
        debug_settings = get_all_debug_settings()
        
        # Position Check Debug Section
        self._create_section_header(settings_frame, "📊 Position Monitoring")
        
        # Position check debug toggle
        position_frame = tk.Frame(settings_frame, bg=self.colors['bg_dark'])
        position_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.debug_vars['position_check_debug'] = tk.BooleanVar(
            value=debug_settings.get('position_check_debug', False)
        )
        
        position_check = tk.Checkbutton(
            position_frame,
            text="Enable Position Check Debug Output",
            variable=self.debug_vars['position_check_debug'],
            bg=self.colors['bg_dark'],
            fg=self.colors['white'],
            selectcolor=self.colors['bg_panel'],
            activebackground=self.colors['bg_dark'],
            activeforeground=self.colors['green'],
            font=('Courier', 10, 'bold'),
            command=lambda: self._toggle_debug('position_check_debug')
        )
        position_check.pack(anchor='w')
        
        # Description
        desc_label = tk.Label(
            position_frame,
            text="Show detailed position check info in console:\n"
                 "• Entry/current prices\n"
                 "• Position size and unrealized PnL\n"
                 "• Current profit percentage\n"
                 "• Highest PnL percentage reached\n"
                 "• Stop-loss and take-profit targets\n"
                 "• Hold/SL/TP decision",
            bg=self.colors['bg_dark'],
            fg=self.colors['gray'],
            font=('Courier', 9),
            justify=tk.LEFT
        )
        desc_label.pack(anchor='w', padx=20, pady=(5, 0))
        
        # Current Status Section
        self._create_section_header(settings_frame, "Current Debug Status")
        
        status_frame = tk.Frame(settings_frame, bg=self.colors['bg_dark'])
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Status display
        status_text = "ON" if debug_settings.get('position_check_debug') else "OFF"
        status_color = self.colors['green'] if debug_settings.get('position_check_debug') else self.colors['red']
        
        tk.Label(
            status_frame,
            text=f"Position Check Debug: {status_text}",
            bg=self.colors['bg_dark'],
            fg=status_color,
            font=('Courier', 11, 'bold')
        ).pack(anchor='w')
        
        # Info Section
        self._create_section_header(settings_frame, "ℹ️ Information")
        
        info_frame = tk.Frame(settings_frame, bg=self.colors['bg_dark'])
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = (
            "Debug output appears in the terminal/console where you started\n"
            "the trading panel, not in this web interface.\n\n"
            "When position check debug is enabled, you'll see detailed output\n"
            "every time the bot checks positions (every 3 seconds by default)."
        )
        
        tk.Label(
            info_frame,
            text=info_text,
            bg=self.colors['bg_dark'],
            fg=self.colors['blue'],
            font=('Courier', 9),
            justify=tk.LEFT
        ).pack(anchor='w')
        
        # Future Options Section
        self._create_section_header(settings_frame, "🔮 Future Debug Options")
        
        future_frame = tk.Frame(settings_frame, bg=self.colors['bg_dark'])
        future_frame.pack(fill=tk.X, padx=20, pady=10)
        
        future_text = (
            "Additional debug options will be added here:\n"
            "• Signal generation debug\n"
            "• API request/response debug\n"
            "• Order execution debug\n"
            "• And more..."
        )
        
        tk.Label(
            future_frame,
            text=future_text,
            bg=self.colors['bg_dark'],
            fg=self.colors['gray'],
            font=('Courier', 9),
            justify=tk.LEFT
        ).pack(anchor='w')
    
    def _create_section_header(self, parent, text):
        """Create a section header"""
        header_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        header_frame.pack(fill=tk.X, padx=10, pady=(15, 5))
        
        tk.Label(
            header_frame,
            text=text,
            bg=self.colors['bg_panel'],
            fg=self.colors['white'],
            font=('Courier', 11, 'bold')
        ).pack(anchor='w', padx=10, pady=5)
    
    def _toggle_debug(self, setting_key):
        """Toggle a debug setting"""
        new_value = self.debug_vars[setting_key].get()
        
        if set_debug_setting(setting_key, new_value):
            status = "enabled" if new_value else "disabled"
            print(f"✅ {setting_key} {status}")
        else:
            print(f"❌ Failed to update {setting_key}")
