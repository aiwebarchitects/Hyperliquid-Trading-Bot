"""
24 Hours Low Range Buyer Signal Generator.
Generates BUY signals when price is within a specified range of the 24-hour low.
Uses 1-hour candles to calculate 24-hour (24 hours) low and high.
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
from core.signal import Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class Range24HLowSignalGenerator:
    """
    24 Hours Low Range-based signal generator.
    
    Strategy:
    - Fetches 24 hours of 1-hour candles (24 candles)
    - Calculates 24-hour low and high
    - Generates BUY signal when current price is within range of 24-hour low
    - Range is defined by: 24h_low * (1 + long_offset) to 24h_low * (1 + long_offset + tolerance)
    """
    
    def __init__(self, long_offset_percent: float = -1.0, tolerance_percent: float = 2.0):
        """
        Initialize 24 Hours Low Range signal generator.
        
        Args:
            long_offset_percent: Offset from 24-hour low in percent (default: -1.0%)
            tolerance_percent: Range tolerance in percent (default: 2.0%)
        """
        self.long_offset_percent = long_offset_percent
        self.tolerance_percent = tolerance_percent
        self.name = "range_24h_low"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Rate limiting
        
        logger.info(
            f"Initialized {self.name} "
            f"(long_offset={long_offset_percent}%, tolerance={tolerance_percent}%)"
        )
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 24) -> Optional[pd.DataFrame]:
        """
        Fetch 1-hour candle data from Binance API for 24 hours.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            limit: Number of candles to fetch (default: 24 for 24 hours)
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            self._rate_limit()
            
            symbol = f"{coin}USDT"
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': '1h',  # 1-hour candles
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"{self.name}: No candle data for {coin}")
                return None
            
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
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to fetch candles for {coin}: {e}")
            return None
    
    def _get_current_price(self, coin: str) -> Optional[float]:
        """
        Get current price from Binance ticker.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Current price or None if failed
        """
        try:
            self._rate_limit()
            
            symbol = f"{coin}USDT"
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': symbol}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return float(data['price'])
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to fetch current price for {coin}: {e}")
            return None
    
    def _calculate_buy_range(self, low_24h: float) -> tuple:
        """
        Calculate buy range based on 24-hour low.
        
        Args:
            low_24h: 24-hour low price
            
        Returns:
            Tuple of (buy_range_low, buy_range_high)
        """
        long_offset = self.long_offset_percent / 100
        tolerance = self.tolerance_percent / 100
        
        buy_range_low = low_24h * (1 + long_offset)
        buy_range_high = low_24h * (1 + long_offset + tolerance)
        
        return buy_range_low, buy_range_high
    
    def _calculate_signal_strength(self, current_price: float, buy_range_low: float, 
                                   buy_range_high: float) -> float:
        """
        Calculate signal strength based on position within buy range.
        
        Args:
            current_price: Current price
            buy_range_low: Lower bound of buy range
            buy_range_high: Upper bound of buy range
            
        Returns:
            Signal strength from 0.7 to 1.0 (stronger when closer to range low)
        """
        # Calculate position within range (0.0 = at low, 1.0 = at high)
        range_width = buy_range_high - buy_range_low
        if range_width == 0:
            return 0.85  # Default strength if range is zero
        
        position_in_range = (current_price - buy_range_low) / range_width
        
        # Invert so lower prices get higher strength
        # 0.0 position (at low) -> 1.0 strength
        # 1.0 position (at high) -> 0.7 strength
        strength = 1.0 - (position_in_range * 0.3)
        
        return min(1.0, max(0.7, strength))
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin based on 24-hour low range.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # 1. Fetch 24 hours of candle data (24 hours)
            df = self._fetch_candles(coin, limit=24)
            if df is None or len(df) < 24:
                logger.warning(
                    f"{self.name}: Insufficient data for {coin} "
                    f"(got {len(df) if df is not None else 0}/24 candles)"
                )
                return None
            
            # 2. Get current price
            current_price = self._get_current_price(coin)
            if current_price is None:
                logger.warning(f"{self.name}: Could not fetch current price for {coin}")
                return None
            
            # 3. Calculate 24-hour low and high
            low_24h = df['low'].min()
            high_24h = df['high'].max()
            
            # 4. Calculate buy range
            buy_range_low, buy_range_high = self._calculate_buy_range(low_24h)
            
            # 5. Determine if price is in buy range
            in_range = buy_range_low <= current_price <= buy_range_high
            
            # 6. Generate signal
            if in_range:
                action = "BUY"
                strength = self._calculate_signal_strength(
                    current_price, buy_range_low, buy_range_high
                )
            else:
                action = "HOLD"
                strength = 0.0
            
            # 7. Create Signal object
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'current_price': round(current_price, 6),
                    '24h_low': round(low_24h, 6),
                    '24h_high': round(high_24h, 6),
                    'buy_range_low': round(buy_range_low, 6),
                    'buy_range_high': round(buy_range_high, 6),
                    'range_width': round(buy_range_high - buy_range_low, 6),
                    'in_range': in_range,
                    'long_offset_percent': self.long_offset_percent,
                    'tolerance_percent': self.tolerance_percent,
                    'timeframe': '1h',
                    'lookback_period': '24h'
                }
            )
            
            if action == "BUY":
                logger.info(
                    f"{self.name}: {coin} BUY signal - "
                    f"Price ${current_price:.6f} in range "
                    f"[${buy_range_low:.6f}, ${buy_range_high:.6f}] "
                    f"(strength: {strength:.2f})"
                )
            else:
                logger.debug(
                    f"{self.name}: {coin} HOLD - "
                    f"Price ${current_price:.6f} outside range "
                    f"[${buy_range_low:.6f}, ${buy_range_high:.6f}]"
                )
            
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
