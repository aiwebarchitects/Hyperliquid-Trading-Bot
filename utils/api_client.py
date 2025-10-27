"""
API Client - Handles exchange API interactions
Integrated with Hyperliquid SDK
"""

from typing import Dict, List, Optional
import time
import json
import os

try:
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    import eth_account
    from eth_account.signers.local import LocalAccount
    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    print("Warning: Hyperliquid SDK not installed. Install with: pip install hyperliquid-python-sdk")


class APIClient:
    """
    API Client for exchange interactions
    Integrated with Hyperliquid SDK
    """
    
    def __init__(self, config_path: str = None, testnet: bool = False):
        self.testnet = testnet
        self.connected = False
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
        
        # Hyperliquid components
        self.info = None
        self.exchange = None
        self.address = None
        self.account = None
        
        # Config path
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.json')
        self.config_path = config_path
    
    def connect(self):
        """Connect to the exchange API"""
        if not HYPERLIQUID_AVAILABLE:
            print("Hyperliquid SDK not available - running in demo mode")
            self.connected = False
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
            
            print(f"Connecting with account: {self.address}")
            
            # Initialize Info and Exchange
            base_url = None  # Use default
            self.info = Info(base_url, skip_ws=False)
            self.exchange = Exchange(self.account, base_url, account_address=self.address)
            
            # Verify connection
            user_state = self.info.user_state(self.address)
            margin_summary = user_state["marginSummary"]
            account_value = float(margin_summary["accountValue"])
            
            print(f"Connected! Account value: ${account_value:.2f}")
            
            self.connected = True
            return True
            
        except ValueError as e:
            # This catches "Non-hexadecimal digit found" and similar errors
            if "hexadecimal" in str(e).lower() or "invalid" in str(e).lower():
                self._show_welcome_message()
            else:
                print(f"Failed to connect to Hyperliquid: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"Failed to connect to Hyperliquid: {e}")
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
    
    def disconnect(self):
        """Disconnect from the exchange API"""
        self.connected = False
        self.info = None
        self.exchange = None
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_positions(self, address: str = None) -> Dict:
        """
        Get current positions
        
        Args:
            address: Wallet address (uses self.address if not provided)
            
        Returns:
            Dict of positions {coin: position_data}
        """
        if not self.connected or not self.info:
            return {}
        
        self._rate_limit()
        
        try:
            if address is None:
                address = self.address
            
            user_state = self.info.user_state(address)
            positions = {}
            
            # Get all mids for current prices
            all_mids = self.info.all_mids()
            
            for pos in user_state.get("assetPositions", []):
                position = pos.get("position", {})
                coin = position.get("coin")
                
                if coin:
                    size = float(position.get("szi", 0) or 0)
                    
                    if abs(size) > 0:
                        # Get ROE (Return on Equity) - this is the profit percentage
                        roe_str = position.get("returnOnEquity", "0")
                        roe_pct = float(roe_str) * 100 if roe_str else 0.0
                        
                        # Get current price
                        current_price = float(all_mids.get(coin, 0) or 0)
                        
                        positions[coin] = {
                            'size': size,
                            'entry_price': float(position.get("entryPx", 0) or 0),
                            'current_price': current_price,
                            'unrealized_pnl': float(position.get("unrealizedPnl", 0) or 0),
                            'liquidation_px': float(position.get("liquidationPx", 0) or 0),
                            'margin_used': float(position.get("marginUsed", 0) or 0),
                            'profit_pct': roe_pct,
                            'position_value': abs(size) * current_price
                        }
            
            return positions
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {}
    
    def get_market_data(self, coin: str, timeframe: str = '5m', limit: int = 100) -> List[Dict]:
        """
        Get market data (OHLCV candles)
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            
        Returns:
            List of candle data
        """
        self._rate_limit()
        # TODO: Implement actual API call
        return []
    
    def get_current_price(self, coin: str) -> Optional[float]:
        """
        Get current price for a coin
        
        Args:
            coin: Coin symbol
            
        Returns:
            Current price or None if not available
        """
        if not self.connected or not self.info:
            return None
        
        self._rate_limit()
        
        try:
            # Get all mid prices
            all_mids = self.info.all_mids()
            
            # Get price for specific coin
            price = all_mids.get(coin)
            
            if price is None:
                print(f"Warning: No price data available for {coin}")
                return None
            
            return float(price)
            
        except Exception as e:
            print(f"Error getting price for {coin}: {e}")
            return None
    
    def place_market_order(self, coin: str, side: str, size: float) -> Dict:
        """
        Place a market order using Hyperliquid Exchange API
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            side: 'buy' or 'sell'
            size: Order size in coin units (will be rounded to correct decimals)
            
        Returns:
            Order result dict with 'status' key
        """
        if not self.connected or not self.exchange:
            return {
                'status': 'error',
                'response': {'error': 'Not connected to exchange'}
            }
        
        self._rate_limit()
        
        try:
            # Get exchange metadata for proper size rounding
            meta = self.info.meta()
            sz_decimals = {}
            for asset_info in meta["universe"]:
                sz_decimals[asset_info["name"]] = asset_info["szDecimals"]
            
            # Check if coin exists in metadata
            if coin not in sz_decimals:
                return {
                    'status': 'error',
                    'response': {'error': f'Could not find szDecimals for {coin}'}
                }
            
            # Round size according to coin's szDecimals
            rounded_size = round(size, sz_decimals[coin])
            
            print(f"Size rounding: {size} -> {rounded_size} (decimals={sz_decimals[coin]})")
            
            # Convert side to boolean (True = buy, False = sell)
            is_buy = side.lower() == 'buy'
            
            # Place market order using exchange.market_open()
            # Signature: market_open(coin, is_buy, sz, px, slippage)
            # px=None for market order, slippage=0.01 (1%)
            result = self.exchange.market_open(coin, is_buy, rounded_size, None, 0.01)
            
            print(f"Market order result: {result}")
            
            # Check if order was successful
            if result and result.get('status') == 'ok':
                # Extract order details from response
                order_id = None
                filled_size = None
                avg_price = None
                
                for status in result.get('response', {}).get('data', {}).get('statuses', []):
                    if 'filled' in status:
                        filled = status['filled']
                        order_id = filled.get('oid')
                        filled_size = filled.get('totalSz')
                        avg_price = filled.get('avgPx')
                        break
                
                return {
                    'status': 'ok',
                    'response': result.get('response', {}),
                    'order_id': order_id,
                    'filled_size': filled_size,
                    'avg_price': avg_price
                }
            else:
                return {
                    'status': 'error',
                    'response': result
                }
                
        except Exception as e:
            print(f"Error placing market order: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'response': {'error': str(e)}
            }
    
    def place_limit_order(self, coin: str, side: str, size: float, price: float) -> Dict:
        """
        Place a limit order
        
        Args:
            coin: Coin symbol
            side: 'BUY' or 'SELL'
            size: Order size
            price: Limit price
            
        Returns:
            Order result
        """
        self._rate_limit()
        # TODO: Implement actual API call
        return {
            'success': False,
            'message': 'API not implemented yet',
            'order_id': None
        }
    
    def close_position(self, coin: str) -> Dict:
        """
        Close a position by placing a market order in the opposite direction
        
        Args:
            coin: Coin symbol
            
        Returns:
            Close result with 'status' key ('ok' or 'error')
        """
        if not self.connected or not self.exchange:
            print(f"❌ Cannot close {coin} - not connected to exchange")
            return {
                'status': 'error',
                'response': {'error': 'Not connected to exchange'}
            }
        
        self._rate_limit()
        
        try:
            # Get current position
            positions = self.get_positions()
            
            if coin not in positions:
                print(f"❌ No position found for {coin}")
                return {
                    'status': 'error',
                    'response': {'error': f'No position found for {coin}'}
                }
            
            position = positions[coin]
            size = position['size']
            
            print(f"\n{'='*60}")
            print(f"🔴 CLOSING POSITION: {coin}")
            print(f"  Current Size: {size}")
            print(f"  Entry Price: ${position['entry_price']:.2f}")
            print(f"  Current Price: ${position['current_price']:.2f}")
            print(f"  Unrealized PnL: ${position['unrealized_pnl']:.2f}")
            print(f"  Profit %: {position['profit_pct']:.2f}%")
            print(f"{'='*60}\n")
            
            # Determine side (opposite of current position)
            # If size > 0, we're LONG, so we need to SELL
            # If size < 0, we're SHORT, so we need to BUY
            is_buy = size < 0
            side = 'buy' if is_buy else 'sell'
            close_size = abs(size)
            
            print(f"Placing {side.upper()} market order for {close_size} {coin}...")
            
            # Place market order to close
            result = self.place_market_order(coin, side, close_size)
            
            if result.get('status') == 'ok':
                print(f"✅ Position closed successfully: {coin}")
                print(f"   Filled: {result.get('filled_size')} @ ${result.get('avg_price')}")
                return {
                    'status': 'ok',
                    'response': result.get('response', {}),
                    'filled_size': result.get('filled_size'),
                    'avg_price': result.get('avg_price')
                }
            else:
                print(f"❌ Failed to close position: {result}")
                return {
                    'status': 'error',
                    'response': result.get('response', {})
                }
                
        except Exception as e:
            print(f"❌ Error closing position for {coin}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'response': {'error': str(e)}
            }
    
    def get_account_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Balance information with 'withdrawable' key
        """
        if not self.connected or not self.info:
            return {
                'total': 0.0,
                'available': 0.0,
                'used': 0.0,
                'withdrawable': 0.0
            }
        
        self._rate_limit()
        
        try:
            user_state = self.info.user_state(self.address)
            margin_summary = user_state.get("marginSummary", {})
            
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            
            # Calculate REAL available balance
            # Available = Total - Used (margin locked in positions)
            available_for_trading = account_value - total_margin_used
            
            return {
                'total': account_value,
                'available': available_for_trading,
                'used': total_margin_used,
                'withdrawable': available_for_trading  # Use calculated value, not API's withdrawable
            }
            
        except Exception as e:
            print(f"Error getting account balance: {e}")
            return {
                'total': 0.0,
                'available': 0.0,
                'used': 0.0,
                'withdrawable': 0.0
            }
    
    def get_open_orders(self, coin: Optional[str] = None) -> List[Dict]:
        """
        Get open orders
        
        Args:
            coin: Optional coin filter
            
        Returns:
            List of open orders
        """
        self._rate_limit()
        # TODO: Implement actual API call
        return []
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancel result
        """
        self._rate_limit()
        # TODO: Implement actual API call
        return {
            'success': False,
            'message': 'API not implemented yet'
        }
    
    def cancel_all_orders(self, coin: Optional[str] = None) -> Dict:
        """
        Cancel all orders
        
        Args:
            coin: Optional coin filter
            
        Returns:
            Cancel result
        """
        self._rate_limit()
        # TODO: Implement actual API call
        return {
            'success': False,
            'message': 'API not implemented yet',
            'cancelled_count': 0
        }
