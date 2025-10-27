"""
API Utils - Handles Hyperliquid API connection and data fetching
"""

import json
import os
import sys

try:
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    import eth_account
    from eth_account.signers.local import LocalAccount
    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    print("Warning: Hyperliquid SDK not installed")


class HyperliquidAPI:
    """Handles Hyperliquid API connections and data fetching"""
    
    def __init__(self, config_path=None):
        self.info = None
        self.exchange = None
        self.address = None
        self.account = None
        self.connected = False
        
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.json')
        self.config_path = config_path
    
    def connect(self):
        """Connect to Hyperliquid API"""
        if not HYPERLIQUID_AVAILABLE:
            print("Hyperliquid SDK not available")
            return False
        
        try:
            # Load config
            with open(self.config_path) as f:
                config = json.load(f)
            
            # Check if credentials are set (detect first-time user)
            secret_key = config.get("secret_key", "")
            account_address = config.get("account_address", "")
            
            # Detect placeholder/invalid credentials
            is_first_time = (
                not secret_key or 
                secret_key.startswith("YOUR_") or 
                secret_key.startswith("your_") or
                secret_key == "PASTE_YOUR_SECRET_KEY_HERE" or
                len(secret_key) < 60
            )
            
            if is_first_time:
                self._show_welcome_message()
                self.connected = False
                return False
            
            # Setup account
            self.account: LocalAccount = eth_account.Account.from_key(config["secret_key"])
            self.address = config["account_address"]
            if self.address == "":
                self.address = self.account.address
            
            print(f"Connecting to Hyperliquid with account: {self.address}")
            
            # Initialize Info and Exchange
            self.info = Info(base_url=None, skip_ws=False)
            self.exchange = Exchange(self.account, base_url=None, account_address=self.address)
            
            # Verify connection
            user_state = self.info.user_state(self.address)
            margin_summary = user_state["marginSummary"]
            account_value = float(margin_summary["accountValue"])
            
            print(f"✓ Connected! Account value: ${account_value:.2f}")
            
            self.connected = True
            return True
            
        except ValueError as e:
            # This catches "Non-hexadecimal digit found" and similar errors
            if "hexadecimal" in str(e).lower() or "invalid" in str(e).lower():
                self._show_welcome_message()
            else:
                print(f"✗ Failed to connect: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            self.connected = False
            return False
    
    def _show_welcome_message(self):
        """Show welcome message for first-time users"""
        print("\n" + "="*80)
        print("🎉 WELCOME TO AUTO TRADING BOT v0.1 🎉")
        print("="*80)
        print("\n⚠️  It looks like you haven't set up your API credentials yet!\n")
        print("📋 To get started, please follow these steps:\n")
        print("   1. Sign up for Hyperliquid:")
        print("      👉 https://app.hyperliquid.xyz/join/BONUS500\n")
        print("   2. Create your API credentials:")
        print("      👉 https://app.hyperliquid.xyz/API\n")
        print("   3. Fund your account with USDC before starting the bot\n")
        print("   4. Add your credentials using ONE of these methods:\n")
        print("      METHOD A - Edit config file manually:")
        print("      • Open: config/api_config.json")
        print("      • Add your 'secret_key' and 'account_address'\n")
        print("      METHOD B - Use the web interface:")
        print("      • The panel will start in a moment")
        print("      • Go to the 'API Settings' tab")
        print("      • Enter your credentials and click 'Save'\n")
        print("="*80)
        print("💡 TIP: The panel will continue to load so you can configure it via the UI")
        print("="*80 + "\n")
    
    def get_account_value(self):
        """Get total account value"""
        if not self.connected or not self.info:
            return 0.0
        
        try:
            user_state = self.info.user_state(self.address)
            margin_summary = user_state["marginSummary"]
            return float(margin_summary["accountValue"])
        except Exception as e:
            print(f"Error getting account value: {e}")
            return 0.0
    
    def get_positions(self):
        """Get all open positions"""
        if not self.connected or not self.info:
            return []
        
        try:
            user_state = self.info.user_state(self.address)
            all_mids = self.info.all_mids()
            
            positions = []
            
            for pos in user_state.get("assetPositions", []):
                position = pos.get("position", {})
                coin = position.get("coin")
                
                if coin:
                    size = float(position.get("szi", 0) or 0)
                    
                    if abs(size) > 0:
                        entry_price = float(position.get("entryPx", 0) or 0)
                        current_price = float(all_mids.get(coin, 0) or 0)
                        pnl = float(position.get("unrealizedPnl", 0) or 0)
                        
                        positions.append({
                            'coin': coin,
                            'size': size,
                            'entry_price': entry_price,
                            'current_price': current_price,
                            'pnl': pnl,
                            'side': "LONG" if size > 0 else "SHORT"
                        })
            
            return positions
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_account_summary(self):
        """Get account summary with balance, PNL, etc."""
        if not self.connected or not self.info:
            return None
        
        try:
            user_state = self.info.user_state(self.address)
            margin_summary = user_state["marginSummary"]
            all_mids = self.info.all_mids()
            
            total_balance = float(margin_summary["accountValue"])
            total_margin_used = float(margin_summary["totalMarginUsed"])
            available_balance = total_balance - total_margin_used
            
            # Calculate total unrealized PNL and position value
            total_pnl = 0.0
            total_position_value = 0.0
            
            for pos in user_state.get("assetPositions", []):
                position = pos.get("position", {})
                coin = position.get("coin")
                
                if coin:
                    size = abs(float(position.get("szi", 0) or 0))
                    if size > 0:
                        current_price = float(all_mids.get(coin, 0) or 0)
                        position_value = size * current_price
                        total_position_value += position_value
                        
                        pnl = float(position.get("unrealizedPnl", 0) or 0)
                        total_pnl += pnl
            
            return {
                'total_balance': total_balance,
                'available': available_balance,
                'in_positions': total_position_value,
                'unrealized_pnl': total_pnl
            }
            
        except Exception as e:
            print(f"Error getting account summary: {e}")
            return None
    
    def get_current_price(self, coin):
        """Get current price for a coin"""
        if not self.connected or not self.info:
            return 0.0
        
        try:
            all_mids = self.info.all_mids()
            return float(all_mids.get(coin, 0) or 0)
        except Exception as e:
            print(f"Error getting price for {coin}: {e}")
            return 0.0
    
    def get_user_fills(self, limit=100):
        """Get user's recent fills/trades"""
        if not self.connected or not self.info:
            return []
        
        try:
            fills = self.info.user_fills(self.address)
            # Limit the results
            return fills[:limit] if fills else []
        except Exception as e:
            print(f"Error getting user fills: {e}")
            return []
    
    def get_today_trades_summary(self):
        """Get summary of today's trades"""
        if not self.connected or not self.info:
            return None
        
        try:
            from datetime import datetime, timezone
            
            fills = self.get_user_fills(limit=1000)
            
            # Get today's start timestamp (midnight UTC)
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_ms = int(today_start.timestamp() * 1000)
            
            # Filter today's trades
            today_trades = []
            total_pnl = 0.0
            total_volume = 0.0
            winning_trades = 0
            losing_trades = 0
            
            for fill in fills:
                timestamp = int(fill.get('time', 0))
                if timestamp >= today_start_ms:
                    today_trades.append(fill)
                    
                    # Calculate PNL if it's a closing trade
                    closed_pnl = float(fill.get('closedPnl', 0) or 0)
                    if closed_pnl != 0:
                        total_pnl += closed_pnl
                        if closed_pnl > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                    
                    # Calculate volume
                    px = float(fill.get('px', 0) or 0)
                    sz = abs(float(fill.get('sz', 0) or 0))
                    total_volume += px * sz
            
            win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
            
            return {
                'total_trades': len(today_trades),
                'total_pnl': total_pnl,
                'total_volume': total_volume,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'trades': today_trades
            }
            
        except Exception as e:
            print(f"Error getting today's trades summary: {e}")
            return None
