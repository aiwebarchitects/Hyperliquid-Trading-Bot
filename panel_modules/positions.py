"""
Positions Module - Handles position display and management
"""

import tkinter as tk
from datetime import datetime


class PositionsManager:
    """Manages position display and data fetching"""
    
    def __init__(self, parent_frame, colors, info=None, address=None):
        self.parent = parent_frame
        self.colors = colors
        self.info = info
        self.address = address
        self.positions = {}
        self.position_labels = {}  # Store label references to avoid recreating
        self.last_positions_count = 0
        
    def create_positions_display(self):
        """Create the positions display panel"""
        positions_frame = tk.Frame(self.parent, bg=self.colors['bg_panel'], 
                                  relief=tk.SOLID, borderwidth=1)
        positions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tk.Label(positions_frame, text="═══ OPEN POSITIONS ═══", 
                bg=self.colors['bg_panel'], fg=self.colors['white'],
                font=('Courier', 11, 'bold')).pack(pady=10)
        
        # Headers - Two rows for better organization
        header_container = tk.Frame(positions_frame, bg=self.colors['bg_dark'])
        header_container.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Row 1: Basic info
        header_row1 = tk.Frame(header_container, bg=self.colors['bg_dark'])
        header_row1.pack(fill=tk.X)
        
        headers_row1 = [("PAIR", 10), ("SIDE", 6), ("SIZE", 10), ("ENTRY", 10), 
                       ("CURRENT", 10), ("PNL $", 10), ("ROI%", 8)]
        
        for header, width in headers_row1:
            tk.Label(header_row1, text=header, bg=self.colors['bg_dark'], 
                    fg=self.colors['gray'], font=('Courier', 8, 'bold'), 
                    width=width).pack(side=tk.LEFT, padx=1)
        
        # Row 2: Advanced info
        header_row2 = tk.Frame(header_container, bg=self.colors['bg_dark'])
        header_row2.pack(fill=tk.X, pady=(2, 0))
        
        headers_row2 = [("LEVERAGE", 10), ("MARGIN", 10), ("LIQ.PRICE", 10), 
                       ("FUNDING", 10), ("VALUE", 10), ("RETURN", 10), ("TIME", 8)]
        
        for header, width in headers_row2:
            tk.Label(header_row2, text=header, bg=self.colors['bg_dark'], 
                    fg=self.colors['gray'], font=('Courier', 8, 'bold'), 
                    width=width).pack(side=tk.LEFT, padx=1)
        
        # Container for position rows
        self.positions_container = tk.Frame(positions_frame, bg=self.colors['bg_panel'])
        self.positions_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(positions_frame, text="", bg=self.colors['bg_panel']).pack(pady=5)
        
        return positions_frame
    
    def update_positions(self):
        """Fetch and update positions from API"""
        if not self.info or not self.address:
            return
        
        try:
            
            # Fetch real positions
            user_state = self.info.user_state(self.address)
            all_mids = self.info.all_mids()
            
            positions_data = []
            
            for pos in user_state.get("assetPositions", []):
                position = pos.get("position", {})
                coin = position.get("coin")
                
                if coin:
                    size = float(position.get("szi", 0) or 0)
                    
                    if abs(size) > 0:
                        entry_price = float(position.get("entryPx", 0) or 0)
                        current_price = float(all_mids.get(coin, 0) or 0)
                        pnl = float(position.get("unrealizedPnl", 0) or 0)
                        
                        # Calculate additional metrics
                        leverage = float(position.get("leverage", {}).get("value", 1) or 1)
                        margin_used = float(position.get("marginUsed", 0) or 0)
                        liquidation_px = float(position.get("liquidationPx", 0) or 0)
                        position_value = abs(size) * current_price
                        
                        # Calculate ROI%
                        if entry_price > 0:
                            if size > 0:  # LONG
                                roi = ((current_price - entry_price) / entry_price) * 100 * leverage
                            else:  # SHORT
                                roi = ((entry_price - current_price) / entry_price) * 100 * leverage
                        else:
                            roi = 0
                        
                        # Get cumulative funding
                        cumulative_funding = float(position.get("cumFunding", {}).get("allTime", 0) or 0)
                        
                        # Calculate return on margin
                        return_on_margin = (pnl / margin_used * 100) if margin_used > 0 else 0
                        
                        # Get position timestamp (use current time as fallback)
                        pos_time = position.get("positionValue", {})
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        side = "LONG" if size > 0 else "SHORT"
                        
                        positions_data.append({
                            'pair': f"{coin}",
                            'side': side,
                            'size': f"{abs(size):.4f}",
                            'entry': f"{entry_price:.2f}",
                            'current': f"{current_price:.2f}",
                            'pnl': f"{pnl:+.2f}",
                            'roi': f"{roi:+.2f}%",
                            'leverage': f"{leverage:.1f}x",
                            'margin': f"${margin_used:.2f}",
                            'liq_price': f"{liquidation_px:.2f}" if liquidation_px > 0 else "N/A",
                            'funding': f"{cumulative_funding:+.4f}",
                            'value': f"${position_value:.2f}",
                            'return': f"{return_on_margin:+.1f}%",
                            'time': timestamp,
                            'pnl_color': self.colors['green'] if pnl > 0 else self.colors['red'],
                            'roi_color': self.colors['green'] if roi > 0 else self.colors['red'],
                            'return_color': self.colors['green'] if return_on_margin > 0 else self.colors['red'],
                            'funding_color': self.colors['green'] if cumulative_funding > 0 else self.colors['red']
                        })
            
            self._display_positions(positions_data)
            
        except Exception as e:
            print(f"Error fetching positions: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_positions(self, positions_data):
        """Display positions in the UI - updates existing labels to avoid blinking"""
        # Check if we need to rebuild (position count changed)
        if len(positions_data) != self.last_positions_count:
            self.last_positions_count = len(positions_data)
            self.position_labels = {}
            
            # Clear and rebuild
            for widget in self.positions_container.winfo_children():
                widget.destroy()
            
            if not positions_data:
                tk.Label(self.positions_container, text="No open positions", 
                        bg=self.colors['bg_panel'], fg=self.colors['gray'],
                        font=('Courier', 9)).pack(pady=10)
                return
            
            # Create new position rows with label references
            for i, pos in enumerate(positions_data):
                # Main container for this position (with border)
                pos_container = tk.Frame(self.positions_container, bg=self.colors['bg_dark'], 
                                        relief=tk.SOLID, borderwidth=1)
                pos_container.pack(fill=tk.X, pady=3)
                
                # Row 1: Basic info
                pos_frame1 = tk.Frame(pos_container, bg=self.colors['bg_dark'])
                pos_frame1.pack(fill=tk.X, padx=2, pady=2)
                
                pair_label = tk.Label(pos_frame1, text=pos['pair'], bg=self.colors['bg_dark'], 
                        fg=self.colors['white'], font=('Courier', 9, 'bold'), width=10)
                pair_label.pack(side=tk.LEFT, padx=1)
                
                side_color = self.colors['green'] if pos['side'] == "LONG" else self.colors['red']
                side_label = tk.Label(pos_frame1, text=pos['side'], bg=self.colors['bg_dark'], 
                        fg=side_color, font=('Courier', 9, 'bold'), width=6)
                side_label.pack(side=tk.LEFT, padx=1)
                
                size_label = tk.Label(pos_frame1, text=pos['size'], bg=self.colors['bg_dark'], 
                        fg=self.colors['white'], font=('Courier', 9), width=10)
                size_label.pack(side=tk.LEFT, padx=1)
                
                entry_label = tk.Label(pos_frame1, text=pos['entry'], bg=self.colors['bg_dark'], 
                        fg=self.colors['white'], font=('Courier', 9), width=10)
                entry_label.pack(side=tk.LEFT, padx=1)
                
                current_label = tk.Label(pos_frame1, text=pos['current'], bg=self.colors['bg_dark'], 
                        fg=self.colors['yellow'], font=('Courier', 9, 'bold'), width=10)
                current_label.pack(side=tk.LEFT, padx=1)
                
                pnl_label = tk.Label(pos_frame1, text=pos['pnl'], bg=self.colors['bg_dark'], 
                        fg=pos['pnl_color'], font=('Courier', 9, 'bold'), width=10)
                pnl_label.pack(side=tk.LEFT, padx=1)
                
                roi_label = tk.Label(pos_frame1, text=pos['roi'], bg=self.colors['bg_dark'], 
                        fg=pos['roi_color'], font=('Courier', 9, 'bold'), width=8)
                roi_label.pack(side=tk.LEFT, padx=1)
                
                # Row 2: Advanced info
                pos_frame2 = tk.Frame(pos_container, bg=self.colors['bg_dark'])
                pos_frame2.pack(fill=tk.X, padx=2, pady=(0, 2))
                
                leverage_label = tk.Label(pos_frame2, text=pos['leverage'], bg=self.colors['bg_dark'], 
                        fg=self.colors['blue'], font=('Courier', 9), width=10)
                leverage_label.pack(side=tk.LEFT, padx=1)
                
                margin_label = tk.Label(pos_frame2, text=pos['margin'], bg=self.colors['bg_dark'], 
                        fg=self.colors['white'], font=('Courier', 9), width=10)
                margin_label.pack(side=tk.LEFT, padx=1)
                
                liq_label = tk.Label(pos_frame2, text=pos['liq_price'], bg=self.colors['bg_dark'], 
                        fg=self.colors['red'], font=('Courier', 9), width=10)
                liq_label.pack(side=tk.LEFT, padx=1)
                
                funding_label = tk.Label(pos_frame2, text=pos['funding'], bg=self.colors['bg_dark'], 
                        fg=pos['funding_color'], font=('Courier', 9), width=10)
                funding_label.pack(side=tk.LEFT, padx=1)
                
                value_label = tk.Label(pos_frame2, text=pos['value'], bg=self.colors['bg_dark'], 
                        fg=self.colors['white'], font=('Courier', 9), width=10)
                value_label.pack(side=tk.LEFT, padx=1)
                
                return_label = tk.Label(pos_frame2, text=pos['return'], bg=self.colors['bg_dark'], 
                        fg=pos['return_color'], font=('Courier', 9, 'bold'), width=10)
                return_label.pack(side=tk.LEFT, padx=1)
                
                time_label = tk.Label(pos_frame2, text=pos['time'], bg=self.colors['bg_dark'], 
                        fg=self.colors['gray'], font=('Courier', 9), width=8)
                time_label.pack(side=tk.LEFT, padx=1)
                
                # Store label references
                self.position_labels[i] = {
                    'pair': pair_label,
                    'side': side_label,
                    'size': size_label,
                    'entry': entry_label,
                    'current': current_label,
                    'pnl': pnl_label,
                    'roi': roi_label,
                    'leverage': leverage_label,
                    'margin': margin_label,
                    'liq_price': liq_label,
                    'funding': funding_label,
                    'value': value_label,
                    'return': return_label,
                    'time': time_label
                }
        else:
            # Just update existing labels (no blinking!)
            for i, pos in enumerate(positions_data):
                if i in self.position_labels:
                    labels = self.position_labels[i]
                    
                    # Update dynamic values
                    labels['current'].config(text=pos['current'])
                    labels['pnl'].config(text=pos['pnl'], fg=pos['pnl_color'])
                    labels['roi'].config(text=pos['roi'], fg=pos['roi_color'])
                    labels['value'].config(text=pos['value'])
                    labels['return'].config(text=pos['return'], fg=pos['return_color'])
                    labels['funding'].config(text=pos['funding'], fg=pos['funding_color'])
                    labels['time'].config(text=pos['time'])
                    
                    # Update size if it changed
                    if labels['size'].cget('text') != pos['size']:
                        labels['size'].config(text=pos['size'])
