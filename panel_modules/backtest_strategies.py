"""
Strategy-specific backtest implementations
"""
import pandas as pd
from typing import Optional, Dict, List
from .backtest_indicators import (
    calculate_rsi, calculate_sma, calculate_ema, 
    calculate_macd, calculate_volume_spike, calculate_bollinger_bands
)
from .backtest_simulator import simulate_trades, calculate_trade_statistics


def run_rsi_backtest(df: pd.DataFrame, coin: str, period: int, 
                     oversold: int, overbought: int, position_size: float) -> Optional[Dict]:
    """
    Run RSI-based backtest
    
    Args:
        df: DataFrame with OHLCV data
        coin: Coin symbol
        period: RSI period
        oversold: Oversold threshold
        overbought: Overbought threshold
        position_size: Position size in USD
        
    Returns:
        Dictionary with backtest results or None
    """
    try:
        df_copy = df.copy()
        df_copy['rsi'] = calculate_rsi(df_copy['close'], period)
        
        # Generate signals
        signals = []
        for i in range(len(df_copy)):
            if pd.isna(df_copy.iloc[i]['rsi']):
                continue
            
            rsi = df_copy.iloc[i]['rsi']
            if rsi <= oversold:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': rsi,
                    'action': 'BUY'
                })
            elif rsi >= overbought:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': rsi,
                    'action': 'SELL'
                })
        
        # Simulate trades
        trades = simulate_trades(signals, position_size)
        stats = calculate_trade_statistics(trades)
        
        if not stats:
            return None
        
        return {
            'coin': coin,
            'period': period,
            'oversold': oversold,
            'overbought': overbought,
            'signals_generated': len(signals),
            **stats
        }
        
    except Exception as e:
        print(f"Error in RSI backtest: {e}")
        return None


def run_sma_backtest(df: pd.DataFrame, coin: str, short_period: int,
                     long_period: int, position_size: float) -> Optional[Dict]:
    """
    Run SMA crossover backtest
    
    Args:
        df: DataFrame with OHLCV data
        coin: Coin symbol
        short_period: Short SMA period
        long_period: Long SMA period
        position_size: Position size in USD
        
    Returns:
        Dictionary with backtest results or None
    """
    try:
        df_copy = df.copy()
        df_copy['short_sma'] = calculate_sma(df_copy['close'], short_period)
        df_copy['long_sma'] = calculate_sma(df_copy['close'], long_period)
        
        # Generate signals
        signals = []
        for i in range(1, len(df_copy)):
            if pd.isna(df_copy.iloc[i]['short_sma']) or pd.isna(df_copy.iloc[i]['long_sma']):
                continue
            
            curr_short = df_copy.iloc[i]['short_sma']
            curr_long = df_copy.iloc[i]['long_sma']
            prev_short = df_copy.iloc[i-1]['short_sma']
            prev_long = df_copy.iloc[i-1]['long_sma']
            
            # Bullish crossover
            if prev_short <= prev_long and curr_short > curr_long:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': 0,
                    'action': 'BUY'
                })
            # Bearish crossover
            elif prev_short >= prev_long and curr_short < curr_long:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': 0,
                    'action': 'SELL'
                })
        
        # Simulate trades
        trades = simulate_trades(signals, position_size)
        stats = calculate_trade_statistics(trades)
        
        if not stats:
            return None
        
        return {
            'coin': coin,
            'period': short_period,
            'oversold': long_period,
            'overbought': 0,
            'signals_generated': len(signals),
            **stats
        }
        
    except Exception as e:
        print(f"Error in SMA backtest: {e}")
        return None


def run_range_backtest(df: pd.DataFrame, coin: str, long_offset: float,
                       tolerance: float, position_size: float) -> Optional[Dict]:
    """
    Run range-based backtest
    
    Args:
        df: DataFrame with OHLCV data
        coin: Coin symbol
        long_offset: Offset from period low (%)
        tolerance: Tolerance range (%)
        position_size: Position size in USD
        
    Returns:
        Dictionary with backtest results or None
    """
    try:
        period_low = df['low'].min()
        period_high = df['high'].max()
        
        buy_range_low = period_low * (1 + long_offset / 100)
        buy_range_high = period_low * (1 + long_offset / 100 + tolerance / 100)
        
        # Generate signals
        signals = []
        in_range = False
        
        for i in range(len(df)):
            current_price = df.iloc[i]['close']
            
            if not in_range and buy_range_low <= current_price <= buy_range_high:
                signals.append({
                    'timestamp': df.iloc[i]['timestamp'],
                    'price': current_price,
                    'rsi': 0,
                    'action': 'BUY'
                })
                in_range = True
            
            elif in_range and current_price > buy_range_high:
                signals.append({
                    'timestamp': df.iloc[i]['timestamp'],
                    'price': current_price,
                    'rsi': 0,
                    'action': 'SELL'
                })
                in_range = False
            
            elif in_range and current_price < buy_range_low:
                signals.append({
                    'timestamp': df.iloc[i]['timestamp'],
                    'price': current_price,
                    'rsi': 0,
                    'action': 'SELL'
                })
                in_range = False
        
        # Simulate trades
        trades = simulate_trades(signals, position_size)
        stats = calculate_trade_statistics(trades)
        
        if not stats:
            return None
        
        return {
            'coin': coin,
            'period': long_offset,
            'oversold': tolerance,
            'overbought': 0,
            'signals_generated': len(signals),
            **stats
        }
        
    except Exception as e:
        print(f"Error in range backtest: {e}")
        return None


def run_scalping_backtest(df: pd.DataFrame, coin: str, fast_ema: int,
                          slow_ema: int, rsi_period: int, rsi_oversold: int,
                          rsi_overbought: int, volume_multiplier: float,
                          position_size: float) -> Optional[Dict]:
    """
    Run scalping strategy backtest
    
    Args:
        df: DataFrame with OHLCV data
        coin: Coin symbol
        fast_ema: Fast EMA period
        slow_ema: Slow EMA period
        rsi_period: RSI period
        rsi_oversold: RSI oversold threshold
        rsi_overbought: RSI overbought threshold
        volume_multiplier: Volume spike multiplier
        position_size: Position size in USD
        
    Returns:
        Dictionary with backtest results or None
    """
    try:
        df_copy = df.copy()
        
        df_copy['fast_ema'] = calculate_ema(df_copy['close'], fast_ema)
        df_copy['slow_ema'] = calculate_ema(df_copy['close'], slow_ema)
        df_copy['rsi'] = calculate_rsi(df_copy['close'], rsi_period)
        df_copy['volume_spike'] = calculate_volume_spike(df_copy['volume'], volume_multiplier)
        
        # Generate signals
        signals = []
        for i in range(1, len(df_copy)):
            if pd.isna(df_copy.iloc[i]['fast_ema']) or pd.isna(df_copy.iloc[i]['rsi']):
                continue
            
            curr_fast = df_copy.iloc[i]['fast_ema']
            curr_slow = df_copy.iloc[i]['slow_ema']
            prev_fast = df_copy.iloc[i-1]['fast_ema']
            prev_slow = df_copy.iloc[i-1]['slow_ema']
            curr_rsi = df_copy.iloc[i]['rsi']
            vol_spike = df_copy.iloc[i]['volume_spike']
            
            # Bullish crossover
            if (prev_fast <= prev_slow and curr_fast > curr_slow and
                curr_rsi > rsi_oversold and curr_rsi < rsi_overbought and vol_spike):
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': curr_rsi,
                    'action': 'BUY'
                })
            
            # Bearish crossover
            elif (prev_fast >= prev_slow and curr_fast < curr_slow and
                  curr_rsi < rsi_overbought and curr_rsi > rsi_oversold and vol_spike):
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': curr_rsi,
                    'action': 'SELL'
                })
        
        # Simulate trades
        trades = simulate_trades(signals, position_size)
        stats = calculate_trade_statistics(trades)
        
        if not stats:
            return None
        
        return {
            'coin': coin,
            'period': fast_ema,
            'oversold': slow_ema,
            'overbought': rsi_period,
            'signals_generated': len(signals),
            **stats
        }
        
    except Exception as e:
        print(f"Error in scalping backtest: {e}")
        return None


def run_macd_backtest(df: pd.DataFrame, coin: str, fast: int,
                      slow: int, signal_period: int, position_size: float) -> Optional[Dict]:
    """
    Run MACD strategy backtest
    
    Args:
        df: DataFrame with OHLCV data
        coin: Coin symbol
        fast: Fast EMA period
        slow: Slow EMA period
        signal_period: Signal line period
        position_size: Position size in USD
        
    Returns:
        Dictionary with backtest results or None
    """
    try:
        df_copy = df.copy()
        
        macd_line, signal_line, histogram = calculate_macd(df_copy['close'], fast, slow, signal_period)
        
        # Generate signals
        signals = []
        for i in range(1, len(df_copy)):
            if pd.isna(histogram.iloc[i]) or pd.isna(histogram.iloc[i-1]):
                continue
            
            curr_hist = histogram.iloc[i]
            prev_hist = histogram.iloc[i-1]
            
            # Bullish crossover
            if prev_hist <= 0 and curr_hist > 0:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': 0,
                    'action': 'BUY'
                })
            # Bearish crossover
            elif prev_hist >= 0 and curr_hist < 0:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': df_copy.iloc[i]['close'],
                    'rsi': 0,
                    'action': 'SELL'
                })
        
        # Simulate trades
        trades = simulate_trades(signals, position_size)
        stats = calculate_trade_statistics(trades)
        
        if not stats:
            return None
        
        return {
            'coin': coin,
            'period': fast,
            'oversold': slow,
            'overbought': signal_period,
            'signals_generated': len(signals),
            **stats
        }
        
    except Exception as e:
        print(f"Error in MACD backtest: {e}")
        return None


def run_bollinger_bands_backtest(df: pd.DataFrame, coin: str, period: int,
                                 std_dev: float, touch_threshold: float,
                                 position_size: float) -> Optional[Dict]:
    """
    Run Bollinger Bands strategy backtest
    
    Args:
        df: DataFrame with OHLCV data
        coin: Coin symbol
        period: BB period (SMA)
        std_dev: Standard deviation multiplier
        touch_threshold: Band touch threshold (%)
        position_size: Position size in USD
        
    Returns:
        Dictionary with backtest results or None
    """
    try:
        df_copy = df.copy()
        
        middle_band, upper_band, lower_band = calculate_bollinger_bands(
            df_copy['close'], period, std_dev
        )
        
        # Generate signals
        signals = []
        for i in range(len(df_copy)):
            if pd.isna(upper_band.iloc[i]) or pd.isna(lower_band.iloc[i]):
                continue
            
            current_price = df_copy.iloc[i]['close']
            upper = upper_band.iloc[i]
            lower = lower_band.iloc[i]
            middle = middle_band.iloc[i]
            
            # Calculate BB position (0 to 1)
            if upper != lower:
                bb_position = (current_price - lower) / (upper - lower)
            else:
                bb_position = 0.5
            
            # Calculate distance to bands
            distance_to_lower = abs(current_price - lower) / lower * 100
            distance_to_upper = abs(upper - current_price) / upper * 100
            
            # BUY signal: Price near or below lower band
            if bb_position <= 0.2 or distance_to_lower <= touch_threshold:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': current_price,
                    'rsi': 0,
                    'action': 'BUY'
                })
            
            # SELL signal: Price near or above upper band
            elif bb_position >= 0.8 or distance_to_upper <= touch_threshold:
                signals.append({
                    'timestamp': df_copy.iloc[i]['timestamp'],
                    'price': current_price,
                    'rsi': 0,
                    'action': 'SELL'
                })
        
        # Simulate trades
        trades = simulate_trades(signals, position_size)
        stats = calculate_trade_statistics(trades)
        
        if not stats:
            return None
        
        return {
            'coin': coin,
            'period': period,
            'oversold': std_dev,
            'overbought': touch_threshold,
            'signals_generated': len(signals),
            **stats
        }
        
    except Exception as e:
        print(f"Error in Bollinger Bands backtest: {e}")
        return None
