"""
Position Manager - Real-time position monitoring and exit management.
SIMPLIFIED VERSION - No trailing stops, just fixed SL/TP
"""

import threading
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from utils.api_client import APIClient
from utils.logger import get_logger
from config import TRADING_SETTINGS
from config.debug_settings import get_debug_setting

logger = get_logger(__name__)


class PositionManager:
    """
    Manages position monitoring and exit logic.
    
    SIMPLIFIED LOGIC:
    - Fixed stop-loss at entry - X%
    - Fixed take-profit at entry + X%
    - NO TRAILING STOPS (removed for clarity)
    - Tracks highest PnL% for each position
    """
    
    def __init__(self, api_client: APIClient):
        """
        Initialize Position Manager.
        
        Args:
            api_client: API client for exchange operations
        """
        self.api = api_client
        self.settings = TRADING_SETTINGS
        
        # Position state tracking (highest values, etc.)
        self.position_states_file = "position_states.json"
        self.position_states: Dict[str, Dict] = self._load_position_states()
        
        # Monitoring control
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        logger.info("PositionManager initialized (SIMPLIFIED - NO TRAILING)")
        logger.info(f"Stop Loss: {self.settings['stop_loss_percent']}%")
        logger.info(f"Take Profit: {self.settings['take_profit_percent']}%")
        logger.info(f"Position states loaded: {len(self.position_states)} positions")
    
    def _load_position_states(self) -> Dict[str, Dict]:
        """
        Load position states from JSON file.
        
        Returns:
            Dictionary of position states by coin
        """
        if os.path.exists(self.position_states_file):
            try:
                with open(self.position_states_file, 'r') as f:
                    states = json.load(f)
                    logger.info(f"Loaded position states for {len(states)} positions")
                    return states
            except Exception as e:
                logger.error(f"Error loading position states: {e}")
                return {}
        return {}
    
    def _save_position_states(self):
        """Save position states to JSON file."""
        try:
            with open(self.position_states_file, 'w') as f:
                json.dump(self.position_states, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving position states: {e}")
    
    def _update_position_state(self, coin: str, profit_pct: float):
        """
        Update position state tracking (highest PnL%, etc.).
        
        Args:
            coin: Coin symbol
            profit_pct: Current profit percentage
        """
        # Initialize state if new position
        if coin not in self.position_states:
            self.position_states[coin] = {
                'highest_pnl_pct': profit_pct,
                'trailing_stop_activated': False,
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            logger.info(f"New position state created for {coin}: {profit_pct:.2f}%")
        else:
            # Update highest PnL if current is higher
            current_highest = self.position_states[coin].get('highest_pnl_pct', profit_pct)
            if profit_pct > current_highest:
                self.position_states[coin]['highest_pnl_pct'] = profit_pct
                logger.info(f"New highest PnL for {coin}: {profit_pct:.2f}% (was {current_highest:.2f}%)")
            
            self.position_states[coin]['last_updated'] = datetime.now().isoformat()
        
        # Save to file after each update
        self._save_position_states()
    
    def _cleanup_closed_positions(self, open_coins: List[str]):
        """
        Remove states for positions that are no longer open.
        
        Args:
            open_coins: List of currently open coin symbols
        """
        closed_coins = [coin for coin in self.position_states.keys() if coin not in open_coins]
        
        if closed_coins:
            for coin in closed_coins:
                logger.info(f"Removing state for closed position: {coin}")
                del self.position_states[coin]
            
            # Save after cleanup
            self._save_position_states()
    
    def start_monitoring(self, interval: int = 2):
        """
        Start position monitoring in background thread.
        
        Args:
            interval: Update interval in seconds (default: 2)
        """
        if self.monitoring:
            logger.warning("Position monitoring already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Position monitoring started (interval={interval}s)")
    
    def stop_monitoring(self):
        """Stop position monitoring."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Position monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """
        Main monitoring loop (runs in background thread).
        
        Args:
            interval: Update interval in seconds
        """
        while self.monitoring:
            try:
                self._check_positions()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(interval)
    
    def _check_positions(self):
        """Check all open positions and handle exits."""
        try:
            # Get positions from API (returns dict: {coin: position_data})
            positions = self.api.get_positions()
            
            if not positions:
                # Clean up all states if no positions
                if self.position_states:
                    self._cleanup_closed_positions([])
                return
            
            # Clean up states for closed positions
            self._cleanup_closed_positions(list(positions.keys()))
            
            # Check each position
            for coin, position_data in positions.items():
                # Update position state (track highest PnL)
                profit_pct = position_data.get('profit_pct', 0)
                self._update_position_state(coin, profit_pct)
                
                # Check exit conditions
                should_exit, reason = self._check_exit_conditions(coin, position_data)
                
                if should_exit:
                    logger.info(f"🔴 EXIT SIGNAL: {coin} - {reason}")
                    self._close_position(coin, reason)
                
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
            import traceback
            traceback.print_exc()
    
    def _check_exit_conditions(self, coin: str, position: Dict) -> tuple[bool, str]:
        """
        Check if position should be exited.
        SIMPLIFIED: Only fixed SL/TP, no trailing.
        
        Args:
            coin: Coin symbol
            position: Position data from API
            
        Returns:
            Tuple of (should_exit, reason)
        """
        try:
            # Extract position data
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            size = position.get('size', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            profit_pct = position.get('profit_pct', 0)  # This is ROE% from API
            
            # Get settings
            sl_pct = self.settings['stop_loss_percent']
            tp_pct = self.settings['take_profit_percent']
            
            # Get highest PnL from state
            highest_pnl = self.position_states.get(coin, {}).get('highest_pnl_pct', profit_pct)
            
            # DEBUG LOGGING (controlled by debug settings)
            if get_debug_setting('position_check_debug'):
                print(f"\n{'='*70}")
                print(f"🔍 POSITION CHECK: {coin}")
                print(f"{'='*70}")
                print(f"  Entry Price:      ${entry_price:.2f}")
                print(f"  Current Price:    ${current_price:.2f}")
                print(f"  Position Size:    {size}")
                print(f"  Unrealized PnL:   ${unrealized_pnl:.2f}")
                print(f"  Profit %:         {profit_pct:.2f}%")
                print(f"  Highest PnL %:    {highest_pnl:.2f}%")
                print(f"")
                print(f"  Stop Loss Target: <=-{sl_pct}%")
                print(f"  Take Profit Target: >={tp_pct}%")
                print(f"")
            
            # Check STOP LOSS (profit <= -X%)
            if profit_pct <= -sl_pct:
                reason = f"STOP LOSS HIT: {profit_pct:.2f}% <= -{sl_pct}% (PnL: ${unrealized_pnl:.2f})"
                if get_debug_setting('position_check_debug'):
                    print(f"  ❌ {reason}")
                    print(f"{'='*70}\n")
                return True, reason
            
            # Check TAKE PROFIT (profit >= +X%)
            if profit_pct >= tp_pct:
                reason = f"TAKE PROFIT HIT: {profit_pct:.2f}% >= {tp_pct}% (PnL: ${unrealized_pnl:.2f})"
                if get_debug_setting('position_check_debug'):
                    print(f"  ✅ {reason}")
                    print(f"{'='*70}\n")
                return True, reason
            
            # No exit condition met
            if get_debug_setting('position_check_debug'):
                print(f"  ⏳ HOLDING - Profit: {profit_pct:.2f}% (need {tp_pct}% for TP or <=-{sl_pct}% for SL)")
                print(f"{'='*70}\n")
            return False, ""
            
        except Exception as e:
            logger.error(f"Error checking exit conditions for {coin}: {e}")
            import traceback
            traceback.print_exc()
            return False, ""
    
    def _close_position(self, coin: str, reason: str):
        """
        Close a position.
        
        Args:
            coin: Coin symbol
            reason: Reason for closing
        """
        try:
            print(f"\n{'='*70}")
            print(f"🔴 CLOSING POSITION: {coin}")
            print(f"   Reason: {reason}")
            print(f"{'='*70}\n")
            
            result = self.api.close_position(coin)
            
            if result and result.get('status') == 'ok':
                print(f"\n{'='*70}")
                print(f"✅ POSITION CLOSED SUCCESSFULLY: {coin}")
                print(f"   Filled: {result.get('filled_size')} @ ${result.get('avg_price')}")
                print(f"{'='*70}\n")
                logger.info(f"Position closed successfully: {coin}")
                
                # Remove state for closed position
                if coin in self.position_states:
                    del self.position_states[coin]
                    self._save_position_states()
            else:
                print(f"\n{'='*70}")
                print(f"❌ FAILED TO CLOSE POSITION: {coin}")
                print(f"   Result: {result}")
                print(f"{'='*70}\n")
                logger.error(f"Failed to close position: {result}")
                
        except Exception as e:
            logger.error(f"Error closing position for {coin}: {e}")
            import traceback
            traceback.print_exc()
    
    def get_position_status(self, coin: str) -> Optional[Dict]:
        """
        Get current status of a position.
        
        Args:
            coin: Coin symbol
            
        Returns:
            Position status dict or None
        """
        try:
            positions = self.api.get_positions()
            return positions.get(coin)
            
        except Exception as e:
            logger.error(f"Error getting position status: {e}")
            return None
    
    def get_all_positions(self) -> List[Dict]:
        """
        Get all open positions with state information.
        
        Returns:
            List of dicts with 'position' and 'state' keys
        """
        try:
            positions = self.api.get_positions()
            
            result = []
            for coin, position_data in positions.items():
                profit_pct = position_data.get('profit_pct', 0)
                
                # CRITICAL: Ensure state exists for this position
                # If state doesn't exist, create it NOW with current profit as highest
                if coin not in self.position_states:
                    self._update_position_state(coin, profit_pct)
                else:
                    # IMPORTANT: Also update existing state to track highest
                    # This ensures the monitor always gets the latest highest value
                    self._update_position_state(coin, profit_pct)
                
                # Get state for this position (now guaranteed to exist and updated)
                # Make a COPY to avoid reference issues
                state = self.position_states.get(coin, {})
                
                # DEBUG: Check what we're returning (controlled by debug settings)
                if get_debug_setting('position_check_debug'):
                    print(f"🔧 get_all_positions() for {coin}:")
                    print(f"   State in memory: {self.position_states.get(coin)}")
                    print(f"   State being returned: {state}")
                
                # Add coin symbol to position data so monitor can display it
                position_data['coin'] = coin
                
                result.append({
                    'position': position_data,
                    'state': state.copy()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all positions: {e}")
            return []
    
    def force_close_all(self):
        """Emergency: Close all positions."""
        try:
            logger.warning("🚨 FORCE CLOSING ALL POSITIONS 🚨")
            
            positions = self.api.get_positions()
            
            for coin in positions.keys():
                self._close_position(coin, "EMERGENCY CLOSE")
            
            logger.info("All positions closed")
            
        except Exception as e:
            logger.error(f"Error force closing positions: {e}")
    
    def get_positions_to_sell(self) -> List[tuple[str, str]]:
        """
        Get list of positions that should be sold based on exit conditions.
        Useful for batch checking without auto-closing.
        
        Returns:
            List of tuples (coin, reason)
        """
        positions_to_sell = []
        
        try:
            positions = self.api.get_positions()
            
            for coin, position_data in positions.items():
                should_exit, reason = self._check_exit_conditions(coin, position_data)
                if should_exit:
                    positions_to_sell.append((coin, reason))
            
        except Exception as e:
            logger.error(f"Error getting positions to sell: {e}")
        
        return positions_to_sell
    
    def get_stats(self) -> Dict:
        """
        Get position manager statistics.
        
        Returns:
            Dictionary with stats
        """
        positions = self.get_all_positions()
        
        total_unrealized_pnl = sum(
            p.get('position', {}).get('unrealized_pnl', 0)
            for p in positions
        )
        
        return {
            'total_positions': len(positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'monitoring': self.monitoring,
            'tracked_states': len(self.position_states)
        }
