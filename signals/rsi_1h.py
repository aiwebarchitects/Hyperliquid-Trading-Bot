"""
RSI 1-hour signal generator.
Standalone signal generator with its own parameters.
Uses Binance free API for 1-hour candles with rate limiting.
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


class RSI1HSignalGenerator:
    """
    RSI-based signal generator using 1-hour candles.
    Each instance is standalone with its own parameters.
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        Initialize RSI 1-hour signal generator.
        
        Args:
            period: RSI calculation period (default: 14)
            oversold: Oversold threshold (default: 30)
            overbought: Overbought threshold (default: 70)
        """
        # Store default parameters
        self.default_period = period
        self.default_oversold = oversold
        self.default_overbought = overbought
        
        # These will be set per-coin
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
        self.name = "rsi_1h"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests to avoid rate limit
        
        # Get backtest loader
        self.backtest_loader = get_backtest_loader()
        
        logger.info(f"Initialized {self.name} (default: period={period}, oversold={oversold}, overbought={overbought})")
    
    def _rate_limit(self):
        """Ensure we don't exceed Binance free API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch 1-hour candles from Binance free API.
        
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
                'interval': '1h',
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
    
    def _calculate_rsi(self, prices: pd.Series) -> float:
        """
        Calculate RSI indicator.
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Current RSI value
        """
        deltas = prices.diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(window=self.period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def _calculate_signal_strength(self, rsi: float, action: str) -> float:
        """
        Calculate signal strength based on RSI distance from thresholds.
        
        Args:
            rsi: Current RSI value
            action: "BUY" or "SELL"
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        if action == "BUY":
            # Stronger signal the further below oversold
            if rsi <= self.oversold:
                # Max strength at RSI 0, min at oversold threshold
                strength = 1.0 - (rsi / self.oversold)
                return min(1.0, max(0.6, strength))
            return 0.0
        
        elif action == "SELL":
            # Stronger signal the further above overbought
            if rsi >= self.overbought:
                # Max strength at RSI 100, min at overbought threshold
                strength = (rsi - self.overbought) / (100 - self.overbought)
                return min(1.0, max(0.6, strength))
            return 0.0
        
        return 0.0
    
    def _load_coin_parameters(self, coin: str):
        """
        Load coin-specific parameters from backtest results.
        Falls back to defaults if no results found.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
        """
        # Try to load optimized parameters for this coin
        params = self.backtest_loader.get_parameters(coin, "rsi-1h")
        
        if params:
            # Use optimized parameters
            self.period = params.get('period', self.default_period)
            self.oversold = params.get('oversold', self.default_oversold)
            self.overbought = params.get('overbought', self.default_overbought)
            logger.info(f"{self.name}: Using optimized parameters for {coin} - period={self.period}, oversold={self.oversold}, overbought={self.overbought}")
        else:
            # Use default parameters
            self.period = self.default_period
            self.oversold = self.default_oversold
            self.overbought = self.default_overbought
            logger.info(f"{self.name}: Using default parameters for {coin} - period={self.period}, oversold={self.oversold}, overbought={self.overbought}")
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin based on RSI.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # Load coin-specific parameters
            self._load_coin_parameters(coin)
            
            # Fetch candles
            df = self._fetch_candles(coin, limit=self.period + 50)
            if df is None or len(df) < self.period + 1:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # Calculate RSI
            rsi = self._calculate_rsi(df['close'])
            
            # Determine action
            if rsi <= self.oversold:
                action = "BUY"
            elif rsi >= self.overbought:
                action = "SELL"
            else:
                action = "HOLD"
            
            # Calculate strength
            strength = self._calculate_signal_strength(rsi, action)
            
            # Create signal
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'rsi': round(rsi, 2),
                    'period': self.period,
                    'oversold': self.oversold,
                    'overbought': self.overbought,
                    'timeframe': '1h'
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
