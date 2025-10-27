"""
Trading Bot Core Engine - Main orchestrator.
Coordinates signal generators, order manager, and position manager.
"""

import time
import threading
from datetime import datetime
from typing import List, Dict
from signals import (
    RSI5MinSignalGenerator, 
    RSI1MinSignalGenerator, 
    RSI1HSignalGenerator,
    RSI4HSignalGenerator,
    SMA5MinSignalGenerator,
    Range7DaysLowSignalGenerator,
    Range24HLowSignalGenerator,
    MACD15MinSignalGenerator
)
from managers import OrderManager, PositionManager
from utils.api_client import APIClient
from utils.logger import get_logger
from config import SYSTEM_SETTINGS, TRADING_SETTINGS
from config.signal_settings import SIGNAL_GENERATOR_SETTINGS

logger = get_logger(__name__)


class TradingBot:
    """
    Main trading bot orchestrator.
    
    Coordinates:
    - Signal generators (algorithms)
    - Order manager (execution)
    - Position manager (monitoring)
    """
    
    def __init__(self, execute_orders: bool = False):
        """
        Initialize Trading Bot.
        
        Args:
            execute_orders: If True, execute orders. If False, only monitor signals.
        """
        self.execute_orders = execute_orders
        self.running = False
        self.signal_thread: threading.Thread = None
        
        # Initialize API client
        logger.info("Initializing API client...")
        self.api = APIClient()
        self.api.connect()
        
        # Initialize managers
        logger.info("Initializing managers...")
        self.order_manager = OrderManager(self.api)
        self.position_manager = PositionManager(self.api)
        
        # Initialize signal generators
        logger.info("Initializing signal generators...")
        self.signal_generators = self._init_signal_generators()
        
        # Track last check time for each signal generator
        self.last_check_times = {gen.name: 0 for gen in self.signal_generators}
        
        # Get monitored coins from settings
        self.monitored_coins = TRADING_SETTINGS['monitored_coins']
        
        logger.info(f"TradingBot initialized (execute_orders={execute_orders})")
        logger.info(f"Monitoring {len(self.monitored_coins)} coins: {', '.join(self.monitored_coins)}")
        logger.info(f"Active signal generators: {len(self.signal_generators)}")
        
        # Log signal check intervals
        intervals = SYSTEM_SETTINGS['signal_check_intervals']
        logger.info("Signal check intervals:")
        for gen in self.signal_generators:
            interval = intervals.get(gen.name, 60)
            logger.info(f"  - {gen.name}: every {interval}s ({interval/60:.1f} min)")
    
    def _init_signal_generators(self) -> List:
        """
        Initialize enabled signal generators only.
        
        Returns:
            List of enabled signal generator instances
        """
        generators = []
        
        # RSI 1-minute (default parameters from backtesting)
        if SIGNAL_GENERATOR_SETTINGS['rsi_1min']['enabled']:
            generators.append(RSI1MinSignalGenerator(period=14, oversold=30, overbought=70))
            logger.info("  ✓ RSI 1-Minute signal generator enabled")
        
        # RSI 5-minute (default parameters from backtesting)
        if SIGNAL_GENERATOR_SETTINGS['rsi_5min']['enabled']:
            generators.append(RSI5MinSignalGenerator(period=14, oversold=30, overbought=70))
            logger.info("  ✓ RSI 5-Minute signal generator enabled")
        
        # RSI 1-hour (default parameters from backtesting)
        if SIGNAL_GENERATOR_SETTINGS['rsi_1h']['enabled']:
            generators.append(RSI1HSignalGenerator(period=14, oversold=30, overbought=70))
            logger.info("  ✓ RSI 1-Hour signal generator enabled")
        
        # RSI 4-hour (default parameters from backtesting)
        if SIGNAL_GENERATOR_SETTINGS['rsi_4h']['enabled']:
            generators.append(RSI4HSignalGenerator(period=14, oversold=30, overbought=70))
            logger.info("  ✓ RSI 4-Hour signal generator enabled")
        
        # SMA 5-minute (default parameters from backtesting)
        if SIGNAL_GENERATOR_SETTINGS['sma_5min']['enabled']:
            generators.append(SMA5MinSignalGenerator(short_period=10, long_period=20))
            logger.info("  ✓ SMA 5-Minute signal generator enabled")
        
        # 7 Days Low Range (buy when price is near 7-day low)
        if SIGNAL_GENERATOR_SETTINGS['range_7days_low']['enabled']:
            generators.append(Range7DaysLowSignalGenerator(long_offset_percent=-1.0, tolerance_percent=2.0))
            logger.info("  ✓ 7-Day Low Range signal generator enabled")
        
        # 24 Hours Low Range (buy when price is near 24h low)
        if SIGNAL_GENERATOR_SETTINGS['range_24h_low']['enabled']:
            generators.append(Range24HLowSignalGenerator(long_offset_percent=-1.0, tolerance_percent=2.0))
            logger.info("  ✓ 24-Hour Low Range signal generator enabled")
        
        # MACD 15-minute (default parameters from backtesting)
        if SIGNAL_GENERATOR_SETTINGS['macd_15min']['enabled']:
            generators.append(MACD15MinSignalGenerator(fast=12, slow=26, signal=9))
            logger.info("  ✓ MACD 15-Minute signal generator enabled")
        
        if not generators:
            logger.warning("  ⚠️  No signal generators enabled! Check config/signal_settings.py")
        
        return generators
    
    def start(self):
        """Start the trading bot."""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        logger.info("=" * 60)
        logger.info("STARTING TRADING BOT")
        logger.info("=" * 60)
        
        if self.execute_orders:
            logger.warning("⚠️  ORDER EXECUTION ENABLED - LIVE TRADING MODE")
        else:
            logger.info("📊 SIGNAL MONITORING MODE - No orders will be executed")
        
        self.running = True
        
        # Start position monitoring with configured interval
        if self.execute_orders:
            position_interval = SYSTEM_SETTINGS['position_check_interval']
            self.position_manager.start_monitoring(interval=position_interval)
        
        # Start signal generation loop
        self.signal_thread = threading.Thread(target=self._signal_loop, daemon=True)
        self.signal_thread.start()
        
        logger.info("Trading bot started successfully")
    
    def stop(self):
        """Stop the trading bot."""
        if not self.running:
            return
        
        logger.info("=" * 60)
        logger.info("STOPPING TRADING BOT")
        logger.info("=" * 60)
        
        self.running = False
        
        # Stop position monitoring
        self.position_manager.stop_monitoring()
        
        # Wait for signal thread
        if self.signal_thread:
            self.signal_thread.join(timeout=10)
        
        # Disconnect API
        self.api.disconnect()
        
        logger.info("Trading bot stopped")
    
    def _signal_loop(self):
        """
        Main signal generation loop with smart per-timeframe checking.
        Runs in background thread.
        """
        # Use shortest interval as base loop interval (1 minute)
        base_interval = 60  # Check every minute
        
        logger.info(f"Signal loop started (base interval={base_interval}s)")
        logger.info("Smart timeframe-based checking enabled")
        
        while self.running:
            try:
                self._check_signals()
                time.sleep(base_interval)
            except Exception as e:
                logger.error(f"Error in signal loop: {e}")
                time.sleep(base_interval)
    
    def _check_signals(self):
        """Check signals for all monitored coins with smart timeframe-based intervals."""
        current_time = time.time()
        intervals = SYSTEM_SETTINGS['signal_check_intervals']
        
        # Determine which generators should run this cycle
        generators_to_run = []
        for generator in self.signal_generators:
            interval = intervals.get(generator.name, 60)
            last_check = self.last_check_times[generator.name]
            
            if current_time - last_check >= interval:
                generators_to_run.append(generator)
                self.last_check_times[generator.name] = current_time
        
        if not generators_to_run:
            return  # No generators need to run this cycle
        
        logger.info("-" * 60)
        logger.info(f"Checking signals at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Active generators: {', '.join([g.name for g in generators_to_run])}")
        
        for coin in self.monitored_coins:
            try:
                self._check_coin_signals(coin, generators_to_run)
            except Exception as e:
                logger.error(f"Error checking signals for {coin}: {e}")
    
    def _check_coin_signals(self, coin: str, generators_to_run: List):
        """
        Check signals for a specific coin from specified generators.
        
        Args:
            coin: Coin symbol
            generators_to_run: List of generators to check this cycle
        """
        signals = []
        
        # Generate signals from specified generators only
        for generator in generators_to_run:
            try:
                signal = generator.generate_signal(coin)
                if signal and signal.action != "HOLD":
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal from {generator.name} for {coin}: {e}")
        
        # Process signals
        if signals:
            logger.info(f"\n{coin}: {len(signals)} signal(s) generated")
            
            for signal in signals:
                logger.info(f"  └─ {signal}")
                
                # Execute order if enabled
                if self.execute_orders:
                    executed = self.order_manager.process_signal(signal)
                    if executed:
                        logger.info(f"     ✓ Order executed")
                    else:
                        logger.info(f"     ✗ Order not executed (validation failed)")
                else:
                    logger.info(f"     📊 Signal logged (execution disabled)")
    
    def get_status(self) -> Dict:
        """
        Get current bot status.
        
        Returns:
            Status dictionary
        """
        order_stats = self.order_manager.get_stats()
        position_stats = self.position_manager.get_stats()
        
        return {
            'running': self.running,
            'execute_orders': self.execute_orders,
            'monitored_coins': len(self.monitored_coins),
            'signal_generators': len(self.signal_generators),
            'order_manager': order_stats,
            'position_manager': position_stats
        }
    
    def emergency_stop(self):
        """Emergency stop - close all positions and stop bot."""
        logger.warning("=" * 60)
        logger.warning("EMERGENCY STOP INITIATED")
        logger.warning("=" * 60)
        
        # Close all positions
        self.position_manager.force_close_all()
        
        # Stop bot
        self.stop()
        
        logger.warning("Emergency stop completed")
