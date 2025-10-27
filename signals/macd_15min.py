"""
MACD 15-minute signal generator.
Uses MACD crossover strategy on 15-minute candles.
Standalone signal generator with its own parameters.
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
from core.signal import Signal
from utils.logger import get_logger
from utils.backtest_results_loader import get_backtest_loader

logger = get_logger(__name__)


class MACD15MinSignalGenerator:
    """
    MACD-based signal generator using 15-minute candles.
    Each instance is standalone with its own parameters.
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        Initialize MACD 15-minute signal generator.
        
        Args:
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
        """
        # Store default parameters
        self.default_fast = fast
        self.default_slow = slow
        self.default_signal = signal
        
        # These will be set per-coin
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        
        self.name = "macd_15min"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests to avoid rate limit
        
        # Get backtest loader
        self.backtest_loader = get_backtest_loader()
        
        logger.info(f"Initialized {self.name} (default: fast={fast}, slow={slow}, signal={signal})")
    
    def _rate_limit(self):
        """Ensure we don't exceed Binance free API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch 15-minute candles from Binance free API.
        
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
                'interval': '15m',
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
    
    def _calculate_macd(self, prices: pd.Series):
        """
        Calculate MACD, Signal line, and Histogram.
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        
        # MACD line = Fast EMA - Slow EMA
        macd_line = ema_fast - ema_slow
        
        # Signal line = EMA of MACD line
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        
        # Histogram = MACD line - Signal line
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_signal_strength(self, histogram: float, prev_histogram: float, action: str) -> float:
        """
        Calculate signal strength based on histogram magnitude and momentum.
        
        Args:
            histogram: Current histogram value
            prev_histogram: Previous histogram value
            action: "BUY" or "SELL"
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        if action == "BUY":
            # Stronger signal with larger positive histogram and momentum
            momentum = abs(histogram - prev_histogram)
            base_strength = 0.7
            histogram_boost = min(0.2, abs(histogram) * 0.05)
            momentum_boost = min(0.1, momentum * 0.02)
            return min(1.0, base_strength + histogram_boost + momentum_boost)
        
        elif action == "SELL":
            # Stronger signal with larger negative histogram and momentum
            momentum = abs(histogram - prev_histogram)
            base_strength = 0.7
            histogram_boost = min(0.2, abs(histogram) * 0.05)
            momentum_boost = min(0.1, momentum * 0.02)
            return min(1.0, base_strength + histogram_boost + momentum_boost)
        
        return 0.0
    
    def _load_coin_parameters(self, coin: str):
        """
        Load coin-specific parameters from backtest results.
        Falls back to defaults if no results found.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
        """
        # Try to load optimized parameters for this coin
        params = self.backtest_loader.get_parameters(coin, "macd-15min")
        
        if params:
            # Use optimized parameters
            self.fast = params.get('period', self.default_fast)  # 'period' stores fast
            self.slow = params.get('oversold', self.default_slow)  # 'oversold' stores slow
            self.signal_period = params.get('overbought', self.default_signal)  # 'overbought' stores signal
            logger.info(f"{self.name}: Using optimized parameters for {coin} - fast={self.fast}, slow={self.slow}, signal={self.signal_period}")
        else:
            # Use default parameters
            self.fast = self.default_fast
            self.slow = self.default_slow
            self.signal_period = self.default_signal
            logger.info(f"{self.name}: Using default parameters for {coin} - fast={self.fast}, slow={self.slow}, signal={self.signal_period}")
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin based on MACD crossover.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # Load coin-specific parameters
            self._load_coin_parameters(coin)
            
            # Fetch candles (need enough for slow EMA + signal line)
            required_candles = self.slow + self.signal_period + 10
            df = self._fetch_candles(coin, limit=min(required_candles, 200))
            
            if df is None or len(df) < required_candles:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # Calculate MACD
            macd_line, signal_line, histogram = self._calculate_macd(df['close'])
            
            # Get current and previous histogram values
            current_hist = histogram.iloc[-1]
            prev_hist = histogram.iloc[-2]
            
            # Detect crossover
            action = "HOLD"
            
            # Bullish crossover: histogram crosses above zero
            if prev_hist <= 0 and current_hist > 0:
                action = "BUY"
            # Bearish crossover: histogram crosses below zero
            elif prev_hist >= 0 and current_hist < 0:
                action = "SELL"
            
            # Calculate strength
            strength = self._calculate_signal_strength(current_hist, prev_hist, action)
            
            # Create signal
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'macd': round(macd_line.iloc[-1], 6),
                    'signal': round(signal_line.iloc[-1], 6),
                    'histogram': round(current_hist, 6),
                    'fast': self.fast,
                    'slow': self.slow,
                    'signal_period': self.signal_period,
                    'timeframe': '15m'
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
