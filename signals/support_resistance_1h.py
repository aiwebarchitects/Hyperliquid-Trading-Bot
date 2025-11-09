"""
Support and Resistance 1-hour signal generator.
Identifies key support and resistance levels based on historical price data.
Generates BUY signals near support and SELL signals near resistance.
"""

import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Tuple
from core.signal import Signal
from utils.logger import get_logger
from utils.backtest_results_loader import get_backtest_loader

logger = get_logger(__name__)


class SupportResistance1HSignalGenerator:
    """
    Support and Resistance-based signal generator using 1-hour candles.
    Identifies key price levels where price tends to bounce or reverse.
    """
    
    def __init__(self, lookback_periods: int = 100, min_touches: int = 3, 
                 tolerance_percent: float = 1.0, min_distance_percent: float = 2.0):
        """
        Initialize Support and Resistance 1-hour signal generator.
        
        Args:
            lookback_periods: Number of periods to analyze for S/R levels (default: 100)
            min_touches: Minimum number of touches to validate a level (default: 3)
            tolerance_percent: Price tolerance for S/R level detection (default: 1.0%)
            min_distance_percent: Minimum distance between S/R levels (default: 2.0%)
        """
        # Store default parameters
        self.default_lookback_periods = lookback_periods
        self.default_min_touches = min_touches
        self.default_tolerance_percent = tolerance_percent
        self.default_min_distance_percent = min_distance_percent
        
        # These will be set per-coin
        self.lookback_periods = lookback_periods
        self.min_touches = min_touches
        self.tolerance_percent = tolerance_percent
        self.min_distance_percent = min_distance_percent
        
        self.name = "support_resistance_1h"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests to avoid rate limit
        
        # Get backtest loader
        self.backtest_loader = get_backtest_loader()
        
        logger.info(f"Initialized {self.name} (default: lookback={lookback_periods}, min_touches={min_touches}, tolerance={tolerance_percent}%)")
    
    def _rate_limit(self):
        """Ensure we don't exceed Binance free API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 200) -> Optional[pd.DataFrame]:
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
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            df['volume'] = pd.to_numeric(df['volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {coin}: {e}")
            return None
    
    def _find_pivot_points(self, df: pd.DataFrame, window: int = 5) -> Tuple[List[float], List[float]]:
        """
        Find pivot points (highs and lows) in the price data.
        
        Args:
            df: DataFrame with OHLC data
            window: Window size for pivot detection
            
        Returns:
            Tuple of (resistance_levels, support_levels)
        """
        highs = []
        lows = []
        
        for i in range(window, len(df) - window):
            # Check for resistance (local high)
            current_high = df['high'].iloc[i]
            is_resistance = True
            
            for j in range(i - window, i + window + 1):
                if j != i and df['high'].iloc[j] >= current_high:
                    is_resistance = False
                    break
            
            if is_resistance:
                highs.append(current_high)
            
            # Check for support (local low)
            current_low = df['low'].iloc[i]
            is_support = True
            
            for j in range(i - window, i + window + 1):
                if j != i and df['low'].iloc[j] <= current_low:
                    is_support = False
                    break
            
            if is_support:
                lows.append(current_low)
        
        return highs, lows
    
    def _cluster_levels(self, levels: List[float], tolerance_percent: float) -> List[float]:
        """
        Cluster similar price levels together.
        
        Args:
            levels: List of price levels
            tolerance_percent: Tolerance for clustering as percentage
            
        Returns:
            List of clustered levels
        """
        if not levels:
            return []
        
        # Sort levels
        sorted_levels = sorted(levels)
        clustered = []
        
        for level in sorted_levels:
            if not clustered:
                clustered.append([level])
            else:
                # Check if level is close to the last cluster
                last_cluster_avg = np.mean(clustered[-1])
                tolerance = last_cluster_avg * (tolerance_percent / 100)
                
                if abs(level - last_cluster_avg) <= tolerance:
                    clustered[-1].append(level)
                else:
                    clustered.append([level])
        
        # Return average of each cluster
        return [np.mean(cluster) for cluster in clustered if len(cluster) >= self.min_touches]
    
    def _filter_levels_by_distance(self, levels: List[float], min_distance_percent: float) -> List[float]:
        """
        Filter levels to ensure minimum distance between them.
        
        Args:
            levels: List of price levels
            min_distance_percent: Minimum distance as percentage
            
        Returns:
            Filtered list of levels
        """
        if not levels:
            return []
        
        filtered = [levels[0]]
        
        for level in levels[1:]:
            is_valid = True
            
            for filtered_level in filtered:
                distance = abs(level - filtered_level) / filtered_level * 100
                if distance < min_distance_percent:
                    is_valid = False
                    break
            
            if is_valid:
                filtered.append(level)
        
        return filtered
    
    def _identify_support_resistance_levels(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        Identify key support and resistance levels.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Tuple of (resistance_levels, support_levels)
        """
        # Find pivot points
        highs, lows = self._find_pivot_points(df)
        
        # Cluster similar levels
        resistance_levels = self._cluster_levels(highs, self.tolerance_percent)
        support_levels = self._cluster_levels(lows, self.tolerance_percent)
        
        # Filter by minimum distance
        resistance_levels = self._filter_levels_by_distance(resistance_levels, self.min_distance_percent)
        support_levels = self._filter_levels_by_distance(support_levels, self.min_distance_percent)
        
        return resistance_levels, support_levels
    
    def _find_nearest_levels(self, current_price: float, resistance_levels: List[float], 
                           support_levels: List[float]) -> Tuple[Optional[float], Optional[float]]:
        """
        Find the nearest resistance and support levels to current price.
        
        Args:
            current_price: Current price
            resistance_levels: List of resistance levels
            support_levels: List of support levels
            
        Returns:
            Tuple of (nearest_resistance, nearest_support)
        """
        nearest_resistance = None
        nearest_support = None
        
        # Find nearest resistance above current price
        valid_resistance = [r for r in resistance_levels if r > current_price]
        if valid_resistance:
            nearest_resistance = min(valid_resistance)
        
        # Find nearest support below current price
        valid_support = [s for s in support_levels if s < current_price]
        if valid_support:
            nearest_support = max(valid_support)
        
        return nearest_resistance, nearest_support
    
    def _calculate_signal_strength(self, current_price: float, nearest_resistance: Optional[float], 
                                 nearest_support: Optional[float], action: str) -> float:
        """
        Calculate signal strength based on distance to S/R levels.
        
        Args:
            current_price: Current price
            nearest_resistance: Nearest resistance level
            nearest_support: Nearest support level
            action: "BUY" or "SELL"
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        if action == "BUY" and nearest_support:
            # Stronger signal the closer to support
            distance_to_support = (current_price - nearest_support) / nearest_support * 100
            # Max strength at 0% distance, min at 2% distance
            strength = max(0.6, 1.0 - (distance_to_support / 2.0))
            return min(1.0, max(0.0, strength))
        
        elif action == "SELL" and nearest_resistance:
            # Stronger signal the closer to resistance
            distance_to_resistance = (nearest_resistance - current_price) / nearest_resistance * 100
            # Max strength at 0% distance, min at 2% distance
            strength = max(0.6, 1.0 - (distance_to_resistance / 2.0))
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
        params = self.backtest_loader.get_parameters(coin, "support_resistance-1h")
        
        if params:
            # Use optimized parameters
            self.lookback_periods = params.get('lookback_periods', self.default_lookback_periods)
            self.min_touches = params.get('min_touches', self.default_min_touches)
            self.tolerance_percent = params.get('tolerance_percent', self.default_tolerance_percent)
            self.min_distance_percent = params.get('min_distance_percent', self.default_min_distance_percent)
            logger.info(f"{self.name}: Using optimized parameters for {coin} - lookback={self.lookback_periods}, min_touches={self.min_touches}, tolerance={self.tolerance_percent}%")
        else:
            # Use default parameters
            self.lookback_periods = self.default_lookback_periods
            self.min_touches = self.default_min_touches
            self.tolerance_percent = self.default_tolerance_percent
            self.min_distance_percent = self.default_min_distance_percent
            logger.info(f"{self.name}: Using default parameters for {coin} - lookback={self.lookback_periods}, min_touches={self.min_touches}, tolerance={self.tolerance_percent}%")
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin based on support and resistance levels.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # Load coin-specific parameters
            self._load_coin_parameters(coin)
            
            # Fetch candles (need more data for S/R analysis)
            df = self._fetch_candles(coin, limit=self.lookback_periods + 50)
            if df is None or len(df) < self.lookback_periods:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Identify support and resistance levels
            resistance_levels, support_levels = self._identify_support_resistance_levels(df)
            
            if not resistance_levels and not support_levels:
                logger.warning(f"{self.name}: No S/R levels found for {coin}")
                return None
            
            # Find nearest levels
            nearest_resistance, nearest_support = self._find_nearest_levels(
                current_price, resistance_levels, support_levels
            )
            
            # Determine action based on proximity to S/R levels
            action = "HOLD"
            proximity_threshold = 0.5  # 0.5% proximity threshold
            
            if nearest_support:
                distance_to_support = (current_price - nearest_support) / nearest_support * 100
                if distance_to_support <= proximity_threshold:
                    action = "BUY"
            
            if nearest_resistance:
                distance_to_resistance = (nearest_resistance - current_price) / nearest_resistance * 100
                if distance_to_resistance <= proximity_threshold:
                    action = "SELL"
            
            # Calculate signal strength
            strength = self._calculate_signal_strength(
                current_price, nearest_resistance, nearest_support, action
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
                    'nearest_resistance': round(nearest_resistance, 6) if nearest_resistance else None,
                    'nearest_support': round(nearest_support, 6) if nearest_support else None,
                    'resistance_levels_count': len(resistance_levels),
                    'support_levels_count': len(support_levels),
                    'lookback_periods': self.lookback_periods,
                    'min_touches': self.min_touches,
                    'tolerance_percent': self.tolerance_percent,
                    'timeframe': '1h'
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
