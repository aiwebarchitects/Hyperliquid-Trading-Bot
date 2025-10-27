"""
SMA 5-minute signal generator.
Standalone signal generator with its own parameters.
Uses Binance free API for 5-minute candles with rate limiting.
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


class SMA5MinSignalGenerator:
    """
    SMA crossover signal generator using 5-minute candles.
    Each instance is standalone with its own parameters.
    """
    
    def __init__(self, short_period: int = 10, long_period: int = 20):
        """
        Initialize SMA 5-minute signal generator.
        
        Args:
            short_period: Short SMA period (default: 10)
            long_period: Long SMA period (default: 20)
        """
        self.short_period = short_period
        self.long_period = long_period
        self.name = "sma_5min"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests to avoid rate limit
        self.previous_crossover = {}  # Track previous crossover state per coin
        
        logger.info(f"Initialized {self.name} (short={short_period}, long={long_period})")
    
    def _rate_limit(self):
        """Ensure we don't exceed Binance free API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch 5-minute candles from Binance free API.
        
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
                'interval': '5m',
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
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {coin}: {e}")
            return None
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: Series of closing prices
            period: SMA period
            
        Returns:
            Series of SMA values
        """
        return prices.rolling(window=period).mean()
    
    def _calculate_signal_strength(self, short_sma: float, long_sma: float, 
                                   price: float, action: str) -> float:
        """
        Calculate signal strength based on SMA separation and price position.
        
        Args:
            short_sma: Short SMA value
            long_sma: Long SMA value
            price: Current price
            action: "BUY" or "SELL"
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        # Calculate percentage separation between SMAs
        separation = abs(short_sma - long_sma) / long_sma
        
        if action == "BUY":
            # Stronger signal when short SMA is well above long SMA
            # and price is above short SMA
            if short_sma > long_sma and price > short_sma:
                # Base strength on separation (more separation = stronger signal)
                strength = min(1.0, 0.6 + (separation * 20))
                return strength
            return 0.0
        
        elif action == "SELL":
            # Stronger signal when short SMA is well below long SMA
            # and price is below short SMA
            if short_sma < long_sma and price < short_sma:
                # Base strength on separation
                strength = min(1.0, 0.6 + (separation * 20))
                return strength
            return 0.0
        
        return 0.0
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin based on SMA crossover.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # Fetch candles (need enough for long SMA + buffer)
            df = self._fetch_candles(coin, limit=self.long_period + 50)
            if df is None or len(df) < self.long_period + 1:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # Calculate SMAs
            df['short_sma'] = self._calculate_sma(df['close'], self.short_period)
            df['long_sma'] = self._calculate_sma(df['close'], self.long_period)
            
            # Get current and previous values
            current_short = df['short_sma'].iloc[-1]
            current_long = df['long_sma'].iloc[-1]
            prev_short = df['short_sma'].iloc[-2]
            prev_long = df['long_sma'].iloc[-2]
            current_price = df['close'].iloc[-1]
            
            # Detect crossover
            action = "HOLD"
            
            # Bullish crossover: short crosses above long
            if prev_short <= prev_long and current_short > current_long:
                action = "BUY"
                self.previous_crossover[coin] = "bullish"
            
            # Bearish crossover: short crosses below long
            elif prev_short >= prev_long and current_short < current_long:
                action = "SELL"
                self.previous_crossover[coin] = "bearish"
            
            # No crossover, but maintain trend signal if SMAs are separated
            elif current_short > current_long:
                # Uptrend - only signal if we haven't already
                if self.previous_crossover.get(coin) != "bullish":
                    action = "BUY"
                    self.previous_crossover[coin] = "bullish"
            
            elif current_short < current_long:
                # Downtrend - only signal if we haven't already
                if self.previous_crossover.get(coin) != "bearish":
                    action = "SELL"
                    self.previous_crossover[coin] = "bearish"
            
            # Calculate strength
            strength = self._calculate_signal_strength(
                current_short, current_long, current_price, action
            )
            
            # Create signal
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'short_sma': round(current_short, 2),
                    'long_sma': round(current_long, 2),
                    'current_price': round(current_price, 2),
                    'short_period': self.short_period,
                    'long_period': self.long_period,
                    'timeframe': '5m',
                    'separation_pct': round(abs(current_short - current_long) / current_long * 100, 2)
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
