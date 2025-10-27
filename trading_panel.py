#!/usr/bin/env python3
"""
Automated Trading Bot Panel - Terminal Style
Monitoring and display only, no manual trading
MODULAR VERSION with real API integration
"""

import tkinter as tk
from datetime import datetime
from panel_modules import (
    PositionsManager, OrdersManager, HyperliquidAPI, 
    NavigationBar, HeaderComponent, BotStatusComponent, StatusBar,
    HomePage, SettingsPage, APISettingsPage
)
from panel_modules.pages.debug_page import DebugPage
from panel_modules.pages.backtest_page import BacktestPage
from panel_modules.signals_display import SignalsDisplay
from panel_modules.position_monitor import PositionMonitor
from core.trading_bot import TradingBot
from utils.logger import setup_logger, get_logger
from config import SYSTEM_SETTINGS, TRADING_SETTINGS

# Setup logging
setup_logger(
    log_level=SYSTEM_SETTINGS.get('log_level', 'INFO'),
    log_file=SYSTEM_SETTINGS.get('log_file', 'logs/trading_bot.log')
)

logger = get_logger(__name__)


class TradingBotPanel:
    """Main trading bot panel application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Automated Trading Bot - LIVE")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0a')
        
        # Color scheme
        self.colors = {
            'bg_dark': '#0a0a0a',
            'bg_panel': '#1a1a1a',
            'green': '#00ff41',
            'red': '#ff0040',
            'white': '#ffffff',
            'gray': '#888888',
            'yellow': '#ffff00',
            'blue': '#00bfff'
        }
        
        # Initialize API
        print("Initializing Hyperliquid API...")
        self.api = HyperliquidAPI()
        self.api.connect()
        
        # Initialize trading bot (not started yet)
        self.trading_bot = None
        self.bot_running = False
        
        # Current page tracking
        self.current_page = "home"
        self.main_content_frame = None
        self.content_container = None
        
        # Page instances
        self.home_page = None
        self.settings_page = None
        self.signals_display = None
        self.position_monitor = None
        
        # Initialize managers (will be recreated per page to avoid conflicts)
        self.orders_manager = OrdersManager(None, self.colors, self.api)
        
        # Create UI components
        self._create_ui()
        
        # Start auto-update
        self.update_data()
        
    def _create_ui(self):
        """Create all UI components"""
        # Navigation
        self.navigation = NavigationBar(self.root, self.colors, self.switch_page)
        self.navigation.create_navigation()
        
        # Header
        self.header = HeaderComponent(self.root, self.colors)
        self.header.create_header()
        
        # Bot Status
        self.bot_status = BotStatusComponent(self.root, self.colors, self.toggle_bot)
        self.bot_status.create_bot_status()
        
        # Content Container
        self.content_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Status Bar
        self.status_bar = StatusBar(self.root, self.colors, self.api)
        self.status_bar.create_status_bar()
        
        # Load initial page
        self.switch_page("home")
    
    def switch_page(self, page):
        """Switch between different pages"""
        self.current_page = page
        
        # Clear current content
        if self.main_content_frame:
            self.main_content_frame.destroy()
        
        # Create new content frame
        self.main_content_frame = tk.Frame(self.content_container, bg=self.colors['bg_dark'])
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create page content
        if page == "home":
            self._create_home_page()
        elif page == "signals":
            self._create_signals_page()
        elif page == "positions":
            self._create_positions_page()
        elif page == "monitor":
            self._create_monitor_page()
        elif page == "history":
            self._create_history_page()
        elif page == "backtest":
            self._create_backtest_page()
        elif page == "api settings":
            self._create_api_settings_page()
        elif page == "settings":
            self._create_settings_page()
        elif page == "debug":
            self._create_debug_page()
        
        print(f"Switched to page: {page}")
    
    def _create_home_page(self):
        """Create home page"""
        # Create fresh positions manager for home page
        positions_manager = PositionsManager(self.main_content_frame, self.colors, self.api.info, self.api.address)
        self.home_page = HomePage(self.main_content_frame, self.colors, self.api, 
                                  positions_manager, self.orders_manager)
        self.home_page.create_page()
    
    def _create_signals_page(self):
        """Create signals page"""
        if not self.signals_display:
            # First time - create new instance with API for position checking
            self.signals_display = SignalsDisplay(self.main_content_frame, self.colors, self.api)
            self.signals_display.create_signals_display()
            self.signals_display.check_signals()
        else:
            # Returning to page - recreate UI in new frame
            self.signals_display.parent = self.main_content_frame
            # Clear signal_labels to force rebuild
            self.signals_display.signal_labels = {}
            # Recreate UI
            self.signals_display.create_signals_display()
            # Force immediate update
            self.signals_display.check_signals()
    
    def _create_positions_page(self):
        """Create positions page"""
        # Create fresh positions manager for positions page
        positions_manager = PositionsManager(self.main_content_frame, self.colors, self.api.info, self.api.address)
        positions_manager.create_positions_display()
        positions_manager.update_positions()
        # Store reference for updates
        self.positions_page_manager = positions_manager
    
    def _create_monitor_page(self):
        """Create position monitor page"""
        # Use the REAL position manager from the trading bot if it exists
        print(f"DEBUG MONITOR: bot_running={self.bot_running}, trading_bot={self.trading_bot is not None}")
        if self.trading_bot:
            print(f"DEBUG MONITOR: has position_manager={hasattr(self.trading_bot, 'position_manager')}")
        
        if self.bot_running and self.trading_bot and hasattr(self.trading_bot, 'position_manager'):
            # Use the actual position manager that's tracking states
            position_mgr = self.trading_bot.position_manager
            print(f"DEBUG MONITOR: Using REAL position manager with {len(position_mgr.position_states)} tracked states")
        else:
            # Bot not running - create wrapper WITH state tracking
            print("DEBUG MONITOR: Bot not running, creating wrapper with state tracking")
            import json
            import os
            from datetime import datetime
            
            class PositionManagerWrapper:
                def __init__(self, api, settings):
                    self.api = api
                    self.settings = settings
                    self.position_states_file = "position_states.json"
                    self.position_states = self._load_position_states()
                
                def _load_position_states(self):
                    if os.path.exists(self.position_states_file):
                        try:
                            with open(self.position_states_file, 'r') as f:
                                return json.load(f)
                        except:
                            return {}
                    return {}
                
                def _save_position_states(self):
                    try:
                        with open(self.position_states_file, 'w') as f:
                            json.dump(self.position_states, f, indent=2)
                    except Exception as e:
                        print(f"Error saving states: {e}")
                
                def _update_position_state(self, coin, profit_pct):
                    if coin not in self.position_states:
                        self.position_states[coin] = {
                            'highest_pnl_pct': profit_pct,
                            'trailing_stop_activated': False,
                            'first_seen': datetime.now().isoformat(),
                            'last_updated': datetime.now().isoformat()
                        }
                    else:
                        current_highest = self.position_states[coin].get('highest_pnl_pct', profit_pct)
                        if profit_pct > current_highest:
                            self.position_states[coin]['highest_pnl_pct'] = profit_pct
                        self.position_states[coin]['last_updated'] = datetime.now().isoformat()
                    self._save_position_states()
                
                def get_all_positions(self):
                    try:
                        user_state = self.api.info.user_state(self.api.address)
                        asset_positions = user_state.get('assetPositions', [])
                        
                        result = []
                        open_coins = []
                        
                        for pos_data in asset_positions:
                            position = pos_data.get('position', {})
                            size = float(position.get('szi', 0) or 0)
                            if abs(size) > 0:
                                coin = position.get('coin')
                                open_coins.append(coin)
                                
                                # Calculate profit %
                                profit_pct = float(position.get('returnOnEquity', 0)) * 100
                                
                                # Update state
                                self._update_position_state(coin, profit_pct)
                                
                                # Get state
                                state = self.position_states.get(coin, {})
                                
                                result.append({
                                    'position': position,
                                    'state': state.copy()
                                })
                        
                        # Cleanup closed positions
                        closed_coins = [c for c in self.position_states.keys() if c not in open_coins]
                        for coin in closed_coins:
                            del self.position_states[coin]
                        if closed_coins:
                            self._save_position_states()
                        
                        return result
                    except Exception as e:
                        print(f"Error getting positions: {e}")
                        import traceback
                        traceback.print_exc()
                        return []
            
            position_mgr = PositionManagerWrapper(self.api, TRADING_SETTINGS)
            print(f"DEBUG MONITOR: Created wrapper with {len(position_mgr.position_states)} tracked states")
        
        self.position_monitor = PositionMonitor(self.main_content_frame, self.colors, position_mgr)
        self.position_monitor.create_monitor_display()
    
    def _create_history_page(self):
        """Create history page"""
        from datetime import datetime
        
        summary = self.api.get_today_trades_summary()
        
        # Analytics section
        analytics_frame = tk.Frame(self.main_content_frame, bg=self.colors['bg_dark'])
        analytics_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_frame = tk.Frame(analytics_frame, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(title_frame, text="═══ TODAY'S TRADING ANALYTICS ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 12, 'bold')).pack(pady=10)
        
        if summary:
            self._create_analytics_stats(analytics_frame, summary)
        
        # Trades list
        self._create_trades_list(self.main_content_frame, summary)
    
    def _create_analytics_stats(self, parent, summary):
        """Create analytics statistics display"""
        stats_container = tk.Frame(parent, bg=self.colors['bg_dark'])
        stats_container.pack(fill=tk.X)
        
        # Row 1: PNL, Trades, Win Rate
        row1 = tk.Frame(stats_container, bg=self.colors['bg_dark'])
        row1.pack(fill=tk.X, pady=2)
        
        # Total PNL
        pnl_frame = tk.Frame(row1, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        pnl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        tk.Label(pnl_frame, text="TOTAL PNL", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9)).pack(pady=(10, 2))
        pnl = summary['total_pnl']
        pnl_color = self.colors['green'] if pnl > 0 else self.colors['red'] if pnl < 0 else self.colors['white']
        pnl_text = f"+${pnl:.2f}" if pnl > 0 else f"${pnl:.2f}"
        tk.Label(pnl_frame, text=pnl_text, bg=self.colors['bg_panel'], fg=pnl_color,
                font=('Courier', 14, 'bold')).pack(pady=(0, 10))
        
        # Total Trades
        trades_frame = tk.Frame(row1, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        trades_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(trades_frame, text="TOTAL TRADES", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9)).pack(pady=(10, 2))
        tk.Label(trades_frame, text=str(summary['total_trades']), bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 14, 'bold')).pack(pady=(0, 10))
        
        # Win Rate
        winrate_frame = tk.Frame(row1, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        winrate_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        tk.Label(winrate_frame, text="WIN RATE", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9)).pack(pady=(10, 2))
        win_rate = summary['win_rate']
        wr_color = self.colors['green'] if win_rate >= 50 else self.colors['red']
        tk.Label(winrate_frame, text=f"{win_rate:.1f}%", bg=self.colors['bg_panel'], fg=wr_color,
                font=('Courier', 14, 'bold')).pack(pady=(0, 10))
        
        # Row 2: Volume, Wins, Losses
        row2 = tk.Frame(stats_container, bg=self.colors['bg_dark'])
        row2.pack(fill=tk.X, pady=2)
        
        # Volume
        vol_frame = tk.Frame(row2, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        vol_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        tk.Label(vol_frame, text="VOLUME", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9)).pack(pady=(10, 2))
        tk.Label(vol_frame, text=f"${summary['total_volume']:,.0f}", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 12, 'bold')).pack(pady=(0, 10))
        
        # Wins
        win_frame = tk.Frame(row2, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        win_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(win_frame, text="WINS", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9)).pack(pady=(10, 2))
        tk.Label(win_frame, text=str(summary['winning_trades']), bg=self.colors['bg_panel'], 
                fg=self.colors['green'], font=('Courier', 12, 'bold')).pack(pady=(0, 10))
        
        # Losses
        loss_frame = tk.Frame(row2, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        loss_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        tk.Label(loss_frame, text="LOSSES", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 9)).pack(pady=(10, 2))
        tk.Label(loss_frame, text=str(summary['losing_trades']), bg=self.colors['bg_panel'], 
                fg=self.colors['red'], font=('Courier', 12, 'bold')).pack(pady=(0, 10))
    
    def _create_trades_list(self, parent, summary):
        """Create scrollable trades list"""
        from datetime import datetime
        
        trades_frame = tk.Frame(parent, bg=self.colors['bg_panel'], relief=tk.SOLID, borderwidth=1)
        trades_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(trades_frame, text="═══ TODAY'S TRADES ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 11, 'bold')).pack(pady=10)
        
        canvas = tk.Canvas(trades_frame, bg=self.colors['bg_panel'], highlightthickness=0)
        scrollbar = tk.Scrollbar(trades_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_panel'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        if summary and summary['trades']:
            for trade in summary['trades']:
                self._create_trade_row(scrollable_frame, trade)
        else:
            tk.Label(scrollable_frame, text="No trades today", bg=self.colors['bg_panel'], 
                    fg=self.colors['gray'], font=('Courier', 10)).pack(pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_trade_row(self, parent, trade):
        """Create a single trade row"""
        from datetime import datetime
        
        trade_row = tk.Frame(parent, bg=self.colors['bg_dark'])
        trade_row.pack(fill=tk.X, padx=10, pady=3)
        
        # Time
        timestamp = int(trade.get('time', 0)) / 1000
        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        tk.Label(trade_row, text=time_str, bg=self.colors['bg_dark'], fg=self.colors['gray'],
                font=('Courier', 9), width=10, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Coin
        coin = trade.get('coin', 'N/A')
        tk.Label(trade_row, text=coin, bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 9, 'bold'), width=8, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Side
        side = trade.get('side', 'N/A')
        side_color = self.colors['green'] if side == 'B' else self.colors['red']
        side_text = "BUY" if side == 'B' else "SELL"
        tk.Label(trade_row, text=side_text, bg=self.colors['bg_dark'], fg=side_color,
                font=('Courier', 9, 'bold'), width=6, anchor='w').pack(side=tk.LEFT, padx=2)
        
        # Size
        size = abs(float(trade.get('sz', 0)))
        tk.Label(trade_row, text=f"{size:.4f}", bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 9), width=12, anchor='e').pack(side=tk.LEFT, padx=2)
        
        # Price
        price = float(trade.get('px', 0))
        tk.Label(trade_row, text=f"@{price:,.2f}", bg=self.colors['bg_dark'], fg=self.colors['white'],
                font=('Courier', 9), width=12, anchor='e').pack(side=tk.LEFT, padx=2)
        
        # PNL
        closed_pnl = float(trade.get('closedPnl', 0) or 0)
        if closed_pnl != 0:
            pnl_color = self.colors['green'] if closed_pnl > 0 else self.colors['red']
            pnl_text = f"+${closed_pnl:.2f}" if closed_pnl > 0 else f"${closed_pnl:.2f}"
            tk.Label(trade_row, text=pnl_text, bg=self.colors['bg_dark'], fg=pnl_color,
                    font=('Courier', 9, 'bold'), width=12, anchor='e').pack(side=tk.LEFT, padx=2)
    
    def _create_analytics_page(self):
        """Create analytics page"""
        placeholder = tk.Frame(self.main_content_frame, bg=self.colors['bg_panel'], 
                              relief=tk.SOLID, borderwidth=1)
        placeholder.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(placeholder, text="═══ ANALYTICS & PERFORMANCE ═══", bg=self.colors['bg_panel'], 
                fg=self.colors['white'], font=('Courier', 14, 'bold')).pack(pady=20)
        tk.Label(placeholder, text="Coming Soon...", bg=self.colors['bg_panel'], fg=self.colors['gray'],
                font=('Courier', 12)).pack(pady=10)
    
    def _create_api_settings_page(self):
        """Create API settings page"""
        api_settings_page = APISettingsPage(self.main_content_frame, self.colors)
        api_settings_page.create_page()
    
    def _create_settings_page(self):
        """Create settings page"""
        self.settings_page = SettingsPage(self.main_content_frame, self.colors)
        self.settings_page.create_page()
    
    def _create_backtest_page(self):
        """Create backtest page"""
        backtest_page = BacktestPage(self.main_content_frame, self.colors)
        backtest_page.create_page()
    
    def _create_debug_page(self):
        """Create debug settings page"""
        debug_page = DebugPage(self.main_content_frame, self.colors)
        debug_page.create_page()
    
    def toggle_bot(self):
        """Start or stop the trading bot"""
        if not self.bot_running:
            try:
                print("=" * 60)
                print("STARTING TRADING BOT...")
                print("=" * 60)
                logger.info("Starting trading bot from panel...")
                
                self.trading_bot = TradingBot(execute_orders=True)
                self.trading_bot.start()
                self.bot_running = True
                
                self.bot_status.update_bot_status(True)
                self.status_bar.update_bot_status(True)
                
                print("✓ Trading bot started successfully")
                logger.info("Trading bot started successfully")
                
            except Exception as e:
                import traceback
                print("=" * 60)
                print("ERROR STARTING BOT:")
                print("=" * 60)
                traceback.print_exc()
                logger.error(f"Failed to start bot: {e}", exc_info=True)
        else:
            try:
                logger.info("Stopping trading bot from panel...")
                if self.trading_bot:
                    self.trading_bot.stop()
                    self.trading_bot = None
                self.bot_running = False
                
                self.bot_status.update_bot_status(False)
                self.status_bar.update_bot_status(False)
                logger.info("Trading bot stopped successfully")
                
            except Exception as e:
                logger.error(f"Failed to stop bot: {e}")
    
    def update_data(self):
        """Update data periodically"""
        # Update signals if on signals page - ALWAYS update when on signals page
        if self.current_page == "signals" and self.signals_display:
            try:
                # Call check_signals every cycle (2 seconds)
                # The SignalsDisplay class handles its own update intervals per signal
                self.signals_display.check_signals()
            except Exception as e:
                print(f"Error updating signals: {e}")
        
        # Update position monitor if on monitor page
        if self.current_page == "monitor":
            if self.position_monitor:
                try:
                    self.position_monitor.update_monitor()
                except Exception as e:
                    print(f"Error updating position monitor: {e}")
        
        # Update home page if active
        if self.current_page == "home" and self.home_page:
            try:
                self.home_page.update_data()
            except Exception as e:
                print(f"Error updating home page: {e}")
        
        # Update positions on positions page
        if self.current_page == "positions" and hasattr(self, 'positions_page_manager'):
            try:
                self.positions_page_manager.update_positions()
            except Exception as e:
                print(f"Error updating positions: {e}")
        
        # Update bot status components
        self.bot_status.update_uptime()
        
        # Update position count
        if self.api.connected:
            positions = self.api.get_positions()
            max_positions = TRADING_SETTINGS.get('max_positions', 10)
            self.bot_status.update_positions_count(len(positions), max_positions)
        
        # Schedule next update
        self.root.after(2000, self.update_data)


def main():
    root = tk.Tk()
    app = TradingBotPanel(root)
    root.mainloop()


if __name__ == "__main__":
    main()
