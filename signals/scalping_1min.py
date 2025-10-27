"""
Scalping 1-minute signal generator.
Uses EMA crossover, RSI, and volume spike detection for quick scalping trades.
"""

import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
from core.signal import Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class Scalping1MinSignalGenerator:
    """
    Scalping signal generator using 1-minute candles.
    
    Strategy:
    - Fast EMA (5) crosses Slow EMA (13) for trend direction
    - RSI (7) for momentum confirmation
    - Volume spike detection for entry timing
    - Designed for quick trades with tight stop losses
    """
    
    def __init__(self, fast_ema: int = 5, slow_ema: int = 13, 
                 rsi_period: int = 7, rsi_oversold: int = 30, 
                 rsi_overbought: int = 70, volume_multiplier: float = 1.5):
        """
        Initialize scalping signal generator.
        
        Args:
            fast_ema: Fast EMA period (default: 5)
            slow_ema: Slow EMA period (default: 13)
            rsi_period: RSI calculation period (default: 7)
            rsi_oversold: RSI oversold threshold (default: 30)
            rsi_overbought: RSI overbought threshold (default: 70)
            volume_multiplier: Volume spike multiplier (default: 1.5)
        """
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_multiplier = volume_multiplier
        self.name = "scalping_1min"
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        logger.info(f"Initialized {self.name} (fast_ema={fast_ema}, slow_ema={slow_ema}, "
                   f"rsi_period={rsi_period}, rsi_oversold={rsi_oversold}, "
                   f"rsi_overbought={rsi_overbought}, volume_mult={volume_multiplier})")
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch 1-minute candle data from Binance API.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            self._rate_limit()
            
            symbol = f"{coin}USDT"
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': '1m',
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {coin}: {e}")
            return None
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI (Relative Strength Index)."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(span=self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.rsi_period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _detect_volume_spike(self, volume: pd.Series) -> bool:
        """
        Detect if current volume is a spike above average.
        
        Args:
            volume: Volume series
            
        Returns:
            True if current volume is a spike
        """
        if len(volume) < 20:
            return False
        
        avg_volume = volume.iloc[-20:].mean()
        current_volume = volume.iloc[-1]
        
        return current_volume > (avg_volume * self.volume_multiplier)
    
    def _calculate_signal_strength(self, rsi: float, ema_diff: float, 
                                   volume_spike: bool, action: str) -> float:
        """
        Calculate signal strength based on indicator confluence.
        
        Args:
            rsi: Current RSI value
            ema_diff: Difference between fast and slow EMA
            volume_spike: Whether volume spike detected
            action: "BUY" or "SELL"
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        if action == "HOLD":
            return 0.0
        
        strength = 0.6  # Base strength
        
        # Add strength for RSI extremes
        if action == "BUY":
            if rsi < 35:
                strength += 0.1
            if rsi < 30:
                strength += 0.1
        elif action == "SELL":
            if rsi > 65:
                strength += 0.1
            if rsi > 70:
                strength += 0.1
        
        # Add strength for strong EMA divergence
        if abs(ema_diff) > 0.5:
            strength += 0.1
        
        # Add strength for volume spike
        if volume_spike:
            strength += 0.1
        
        return min(1.0, max(0.0, strength))
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate scalping trading signal for a coin.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # Fetch market data (need enough for EMA calculation)
            df = self._fetch_candles(coin, limit=100)
            if df is None or len(df) < max(self.slow_ema, 20) + 5:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # Calculate indicators
            fast_ema = self._calculate_ema(df['close'], self.fast_ema)
            slow_ema = self._calculate_ema(df['close'], self.slow_ema)
            rsi = self._calculate_rsi(df['close'])
            
            # Get current and previous values
            current_fast = fast_ema.iloc[-1]
            current_slow = slow_ema.iloc[-1]
            prev_fast = fast_ema.iloc[-2]
            prev_slow = slow_ema.iloc[-2]
            current_rsi = rsi.iloc[-1]
            
            # Check for volume spike
            volume_spike = self._detect_volume_spike(df['volume'])
            
            # Detect EMA crossover
            bullish_cross = (current_fast > current_slow) and (prev_fast <= prev_slow)
            bearish_cross = (current_fast < current_slow) and (prev_fast >= prev_slow)
            
            # Determine action
            action = "HOLD"
            
            # Long signal: Bullish EMA cross + RSI not overbought + Volume spike
            if (bullish_cross and 
                current_rsi > self.rsi_oversold and 
                current_rsi < self.rsi_overbought and 
                volume_spike):
                action = "BUY"
            
            # Short signal: Bearish EMA cross + RSI not oversold + Volume spike
            elif (bearish_cross and 
                  current_rsi < self.rsi_overbought and 
                  current_rsi > self.rsi_oversold and 
                  volume_spike):
                action = "SELL"
            
            # Calculate EMA difference percentage
            ema_diff_pct = ((current_fast - current_slow) / current_slow) * 100
            
            # Calculate signal strength
            strength = self._calculate_signal_strength(
                current_rsi, ema_diff_pct, volume_spike, action
            )
            
            # Create Signal object
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'fast_ema': round(current_fast, 8),
                    'slow_ema': round(current_slow, 8),
                    'ema_diff_pct': round(ema_diff_pct, 4),
                    'rsi': round(current_rsi, 2),
                    'volume_spike': volume_spike,
                    'timeframe': '1m',
                    'bullish_cross': bullish_cross,
                    'bearish_cross': bearish_cross
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            import traceback
            traceback.print_exc()
            return None
