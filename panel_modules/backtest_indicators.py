"""
Technical indicators for backtesting
"""
import pandas as pd


def calculate_rsi(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate RSI indicator
    
    Args:
        prices: Series of prices
        period: RSI period
        
    Returns:
        Series of RSI values
    """
    deltas = prices.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average
    
    Args:
        prices: Series of prices
        period: SMA period
        
    Returns:
        Series of SMA values
    """
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average
    
    Args:
        prices: Series of prices
        period: EMA period
        
    Returns:
        Series of EMA values
    """
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(prices: pd.Series, fast: int, slow: int, signal: int) -> tuple:
    """
    Calculate MACD indicator
    
    Args:
        prices: Series of prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_volume_spike(volume: pd.Series, multiplier: float, window: int = 20) -> pd.Series:
    """
    Calculate volume spike indicator
    
    Args:
        volume: Series of volume data
        multiplier: Volume multiplier threshold
        window: Rolling window for average volume
        
    Returns:
        Series of boolean values indicating volume spikes
    """
    avg_volume = volume.rolling(window=window).mean()
    return volume > (avg_volume * multiplier)
