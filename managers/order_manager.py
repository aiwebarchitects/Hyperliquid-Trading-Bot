"""
Order Manager - Central order execution and validation system.
Handles signal processing, risk validation, and order execution.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from core.signal import Signal
from utils.api_client import APIClient
from utils.logger import get_logger
from config import TRADING_SETTINGS

logger = get_logger(__name__)


class OrderManager:
    """
    Manages order execution with validation and risk management.
    
    Responsibilities:
    - Receive signals from algorithms
    - Validate trading conditions (position limits, duplicates, balance)
    - Execute orders on exchange
    - Set stop-loss and take-profit orders
    - Track order history and cooldowns
    """
    
    def __init__(self, api_client: APIClient):
        """
        Initialize Order Manager.
        
        Args:
            api_client: API client for exchange operations
        """
        self.api = api_client
        self.settings = TRADING_SETTINGS
        
        # Track cooldowns per coin (coin -> last order timestamp)
        self.cooldowns: Dict[str, datetime] = {}
        
        # Track daily trade counts
        self.daily_trades: Dict[str, int] = {}  # coin -> count
        self.total_daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        logger.info("OrderManager initialized")
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily trade counters if it's a new day."""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_trades.clear()
            self.total_daily_trades = 0
            self.last_reset_date = current_date
            logger.info("Daily trade counters reset")
    
    def _check_position_limit(self) -> bool:
        """
        Check if we can open a new position.
        
        Returns:
            True if under position limit, False otherwise
        """
        try:
            # get_positions() returns {coin: position_data} dict
            positions = self.api.get_positions()
            current_positions = len(positions)
            max_positions = self.settings['max_positions']
            
            if current_positions >= max_positions:
                logger.warning(f"Position limit reached: {current_positions}/{max_positions}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking position limit: {e}")
            return False
    
    def _check_duplicate_position(self, coin: str) -> bool:
        """
        Check if we already have a position for this coin.
        
        Args:
            coin: Coin symbol
            
        Returns:
            True if no duplicate, False if position exists
        """
        try:
            # get_positions() returns {coin: position_data} dict
            positions = self.api.get_positions()
            
            # Check if coin exists in positions dict
            if coin in positions:
                logger.warning(f"Position already exists for {coin}: size={positions[coin].get('size', 0)}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking duplicate position: {e}")
            return False
    
    def _check_cooldown(self, coin: str) -> bool:
        """
        Check if coin is in cooldown period.
        
        Args:
            coin: Coin symbol
            
        Returns:
            True if not in cooldown, False if still cooling down
        """
        if coin not in self.cooldowns:
            return True
        
        cooldown_period = self.settings.get('cooldown_period', 300)  # Default 5 minutes
        elapsed = (datetime.now() - self.cooldowns[coin]).total_seconds()
        
        if elapsed < cooldown_period:
            remaining = int(cooldown_period - elapsed)
            logger.info(f"{coin} in cooldown: {remaining}s remaining")
            return False
        
        return True
    
    def _check_balance(self, position_size: float) -> bool:
        """
        Check if we have sufficient balance.
        
        Args:
            position_size: Size of position in USD
            
        Returns:
            True if sufficient balance, False otherwise
        """
        try:
            balance_info = self.api.get_account_balance()
            
            # DEBUG: Print to console
            print("=" * 60)
            print("BALANCE CHECK DEBUG:")
            print(f"Full balance_info: {balance_info}")
            print(f"API connected: {self.api.connected}")
            print(f"API address: {self.api.address}")
            print("=" * 60)
            
            available = float(balance_info.get('withdrawable', 0))
            total = float(balance_info.get('total', 0))
            
            print(f"Balance check: Total=${total:.2f}, Available=${available:.2f}, Required=${position_size:.2f}")
            
            if available < position_size:
                logger.warning(f"Insufficient balance: ${available:.2f} < ${position_size:.2f}")
                return False
            
            print(f"✓ Sufficient balance for ${position_size:.2f} order")
            return True
            
        except Exception as e:
            print(f"ERROR in balance check: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error checking balance: {e}")
            return False
    
    def process_signal(self, signal: Signal) -> bool:
        """
        Process a trading signal and execute if valid.
        
        IMPORTANT: Order Manager only opens NEW positions.
        Position Manager handles closing existing positions via SL/TP/Trailing.
        
        Args:
            signal: Trading signal to process
            
        Returns:
            True if order executed, False otherwise
        """
        try:
            # Reset daily counters if needed
            self._reset_daily_counters_if_needed()
            
            # Only process BUY/SELL signals
            if signal.action == "HOLD":
                return False
            
            # Check signal strength
            min_strength = self.settings.get('min_signal_strength', 0.7)
            if not signal.is_actionable(min_strength):
                logger.info(f"Signal too weak: {signal.strength:.2f} < {min_strength}")
                return False
            
            # CRITICAL: Check if position already exists
            # If position exists, Position Manager handles it (SL/TP/Trailing)
            # Order Manager only opens NEW positions
            if not self._check_duplicate_position(signal.coin):
                logger.info(f"Position already exists for {signal.coin} - Position Manager will handle exits")
                return False
            
            # Check position limit
            if not self._check_position_limit():
                return False
            
            # Check cooldown
            if not self._check_cooldown(signal.coin):
                return False
            
            # Check balance
            position_size = self.settings['position_size_usd']
            if not self._check_balance(position_size):
                return False
            
            # Execute order
            success = self._execute_order(signal)
            
            if success:
                # Update cooldown
                self.cooldowns[signal.coin] = datetime.now()
                
                # Update daily counters
                self.daily_trades[signal.coin] = self.daily_trades.get(signal.coin, 0) + 1
                self.total_daily_trades += 1
                
                logger.info(f"Order executed: {signal}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return False
    
    def _execute_order(self, signal: Signal) -> bool:
        """
        Execute the actual order on the exchange.
        
        Args:
            signal: Trading signal
            
        Returns:
            True if successful, False otherwise
        """
        try:
            coin = signal.coin
            action = signal.action
            position_size_usd = self.settings['position_size_usd']
            
            # Get current price
            current_price = self.api.get_current_price(coin)
            if not current_price:
                logger.error(f"Could not get price for {coin}")
                return False
            
            # Calculate size in coin units
            raw_size = position_size_usd / current_price
            
            # Round size to avoid "float_to_wire causes rounding" error
            # Hyperliquid requires specific decimal precision
            # Round to 5 significant figures to be safe
            size = round(raw_size, 5)
            
            # Determine side for API
            side = "buy" if action == "BUY" else "sell"
            
            # Place market order
            logger.info(f"Placing {side} order: {coin} size={size} (raw={raw_size}) @ ${current_price:.2f}")
            result = self.api.place_market_order(coin, side, size)
            
            if result and result.get('status') == 'ok':
                logger.info(f"Order successful: {result}")
                
                # Set stop-loss and take-profit
                self._set_stop_loss_take_profit(coin, current_price, side)
                
                return True
            else:
                logger.error(f"Order failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return False
    
    def _set_stop_loss_take_profit(self, coin: str, entry_price: float, side: str):
        """
        Set stop-loss and take-profit orders.
        
        Args:
            coin: Coin symbol
            entry_price: Entry price
            side: "buy" or "sell"
        """
        try:
            sl_pct = self.settings['stop_loss_percent'] / 100
            tp_pct = self.settings['take_profit_percent'] / 100
            
            if side == "buy":
                # Long position
                stop_loss_price = entry_price * (1 - sl_pct)
                take_profit_price = entry_price * (1 + tp_pct)
            else:
                # Short position
                stop_loss_price = entry_price * (1 + sl_pct)
                take_profit_price = entry_price * (1 - tp_pct)
            
            logger.info(f"SL/TP for {coin}: SL=${stop_loss_price:.2f}, TP=${take_profit_price:.2f}")
            
            # Note: Actual SL/TP order placement would go here
            # This depends on exchange API capabilities
            # For now, Position Manager will handle exits
            
        except Exception as e:
            logger.error(f"Error setting SL/TP: {e}")
    
    def get_stats(self) -> Dict:
        """
        Get order manager statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            'total_daily_trades': self.total_daily_trades,
            'trades_by_coin': dict(self.daily_trades),
            'coins_in_cooldown': len([c for c, t in self.cooldowns.items() 
                                     if (datetime.now() - t).total_seconds() < 300])
        }
