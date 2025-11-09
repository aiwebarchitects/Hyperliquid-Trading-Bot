"""
Bollinger Bands 30-minute signal generator.
Uses Bollinger Bands to identify overbought/oversold conditions and volatility.
Generates BUY signals when price touches lower band and SELL signals when price touches upper band.
"""

import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
from core.signal import Signal
from utils.logger import get_logger
from utils.backtest_results_loader import get_backtest_loader

logger = get_logger(__name__)


class BollingerBands30MinSignalGenerator:
    """
    Bollinger Bands-based signal generator using 30-minute candles.
    Identifies overbought/oversold conditions based on price position relative to bands.
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, 
                 touch_threshold: float = 0.5):
        """
        Initialize Bollinger Bands 30-minute signal generator.
        
        Args:
            period: Period for moving average calculation (default: 20)
            std_dev: Number of standard deviations for bands (default: 2.0)
            touch_threshold: Percentage threshold for band touch detection (default: 0.5%)
        """
        # Store default parameters
        self.default_period = period
        self.default_std_dev = std_dev
        self.default_touch_threshold = touch_threshold
        
        # These will be set per-coin
        self.period = period
        self.std_dev = std_dev
        self.touch_threshold = touch_threshold
        
        self.name = "bollinger_bands_30min"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests to avoid rate limit
        
        # Get backtest loader
        self.backtest_loader = get_backtest_loader()
        
        logger.info(f"Initialized {self.name} (default: period={period}, std_dev={std_dev}, threshold={touch_threshold}%)")
    
    def _rate_limit(self):
        """Ensure we don't exceed Binance free API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch 30-minute candles from Binance free API.
        
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
                'interval': '30m',
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
    
    def _calculate_bollinger_bands(self, prices: pd.Series) -> tuple:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Tuple of (middle_band, upper_band, lower_band, bandwidth)
        """
        # Calculate middle band (SMA)
        middle_band = prices.rolling(window=self.period).mean()
        
        # Calculate standard deviation
        std = prices.rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)
        
        # Calculate bandwidth (volatility measure)
        bandwidth = ((upper_band - lower_band) / middle_band) * 100
        
        return middle_band, upper_band, lower_band, bandwidth
    
    def _calculate_bb_position(self, price: float, upper: float, lower: float, middle: float) -> float:
        """
        Calculate price position within Bollinger Bands (0 to 1).
        
        Args:
            price: Current price
            upper: Upper band value
            lower: Lower band value
            middle: Middle band value
            
        Returns:
            Position from 0.0 (at lower band) to 1.0 (at upper band)
        """
        if upper == lower:
            return 0.5
        
        position = (price - lower) / (upper - lower)
        return max(0.0, min(1.0, position))
    
    def _calculate_signal_strength(self, bb_position: float, bandwidth: float, 
                                  action: str, price: float, lower: float, upper: float) -> float:
        """
        Calculate signal strength based on BB position and bandwidth.
        
        Args:
            bb_position: Price position within bands (0 to 1)
            bandwidth: Bollinger Bands width percentage
            action: "BUY" or "SELL"
            price: Current price
            lower: Lower band value
            upper: Upper band value
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        if action == "BUY":
            # Stronger signal when price is closer to lower band
            # Also consider bandwidth (higher volatility = stronger signal)
            distance_to_lower = abs(price - lower) / lower * 100
            
            # Base strength from position (0.0 = at lower band = strongest)
            position_strength = 1.0 - bb_position
            
            # Adjust for distance to band
            if distance_to_lower <= self.touch_threshold:
                # Very close to band
                strength = 0.85 + (position_strength * 0.15)
            else:
                # Further from band
                strength = 0.6 + (position_strength * 0.2)
            
            # Boost for high volatility (wider bands)
            if bandwidth > 4.0:  # High volatility
                strength = min(1.0, strength + 0.1)
            
            return min(1.0, max(0.0, strength))
        
        elif action == "SELL":
            # Stronger signal when price is closer to upper band
            distance_to_upper = abs(upper - price) / upper * 100
            
            # Base strength from position (1.0 = at upper band = strongest)
            position_strength = bb_position
            
            # Adjust for distance to band
            if distance_to_upper <= self.touch_threshold:
                # Very close to band
                strength = 0.85 + (position_strength * 0.15)
            else:
                # Further from band
                strength = 0.6 + (position_strength * 0.2)
            
            # Boost for high volatility (wider bands)
            if bandwidth > 4.0:  # High volatility
                strength = min(1.0, strength + 0.1)
            
            return min(1.0, max(0.0, strength))
        
        return 0.0
    
    def _load_coin_parameters(self, coin: str):
        """
        Load coin-specific parameters from backtest results.
        Falls back to defaults if no results found.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
        """
        # Try to load optimized parameters for this coin
        params = self.backtest_loader.get_parameters(coin, "bollinger_bands-30min")
        
        if params:
            # Use optimized parameters
            self.period = params.get('period', self.default_period)
            self.std_dev = params.get('std_dev', self.default_std_dev)
            self.touch_threshold = params.get('touch_threshold', self.default_touch_threshold)
            logger.info(f"{self.name}: Using optimized parameters for {coin} - period={self.period}, std_dev={self.std_dev}, threshold={self.touch_threshold}%")
        else:
            # Use default parameters
            self.period = self.default_period
            self.std_dev = self.default_std_dev
            self.touch_threshold = self.default_touch_threshold
            logger.info(f"{self.name}: Using default parameters for {coin} - period={self.period}, std_dev={self.std_dev}, threshold={self.touch_threshold}%")
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin based on Bollinger Bands.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # Load coin-specific parameters
            self._load_coin_parameters(coin)
            
            # Fetch candles (need enough for BB calculation)
            df = self._fetch_candles(coin, limit=self.period + 50)
            if df is None or len(df) < self.period:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # Calculate Bollinger Bands
            middle_band, upper_band, lower_band, bandwidth = self._calculate_bollinger_bands(df['close'])
            
            # Get current values
            current_price = df['close'].iloc[-1]
            current_middle = middle_band.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_bandwidth = bandwidth.iloc[-1]
            
            # Check for NaN values
            if pd.isna(current_middle) or pd.isna(current_upper) or pd.isna(current_lower):
                logger.warning(f"{self.name}: Invalid BB values for {coin}")
                return None
            
            # Calculate BB position
            bb_position = self._calculate_bb_position(
                current_price, current_upper, current_lower, current_middle
            )
            
            # Determine action based on band proximity
            action = "HOLD"
            distance_to_lower = abs(current_price - current_lower) / current_lower * 100
            distance_to_upper = abs(current_upper - current_price) / current_upper * 100
            
            # BUY signal: Price near or below lower band
            if bb_position <= 0.2 or distance_to_lower <= self.touch_threshold:
                action = "BUY"
            
            # SELL signal: Price near or above upper band
            elif bb_position >= 0.8 or distance_to_upper <= self.touch_threshold:
                action = "SELL"
            
            # Calculate signal strength
            strength = self._calculate_signal_strength(
                bb_position, current_bandwidth, action, 
                current_price, current_lower, current_upper
            )
            
            # Create signal
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'current_price': round(current_price, 6),
                    'upper_band': round(current_upper, 6),
                    'middle_band': round(current_middle, 6),
                    'lower_band': round(current_lower, 6),
                    'bb_position': round(bb_position, 3),
                    'bandwidth': round(current_bandwidth, 2),
                    'period': self.period,
                    'std_dev': self.std_dev,
                    'timeframe': '30m'
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
