"""
Backtest-specific settings
"""

BACKTEST_SETTINGS = {
    # Trade Settings
    'position_size_usd': 100,  # Default position size for backtesting
    
    # Optimization Ranges for RSI 1min
    'rsi_1min_optimization': {
        'period': [10, 12, 14, 16, 18, 20],  # RSI periods to test
        'oversold': [25, 28, 30, 32, 35],     # Oversold thresholds to test
        'overbought': [65, 68, 70, 72, 75],   # Overbought thresholds to test
        'interval': '1m',  # Binance API interval
    },
    
    # Optimization Ranges for RSI 5min
    'rsi_5min_optimization': {
        'period': [10, 12, 14, 16, 18, 20],
        'oversold': [25, 28, 30, 32, 35],
        'overbought': [65, 68, 70, 72, 75],
        'interval': '5m',
    },
    
    # Optimization Ranges for RSI 1h
    'rsi_1h_optimization': {
        'period': [10, 12, 14, 16, 18, 20],
        'oversold': [25, 28, 30, 32, 35],
        'overbought': [65, 68, 70, 72, 75],
        'interval': '1h',
    },
    
    # Optimization Ranges for RSI 4h
    'rsi_4h_optimization': {
        'period': [10, 12, 14, 16, 18, 20],
        'oversold': [25, 28, 30, 32, 35],
        'overbought': [65, 68, 70, 72, 75],
        'interval': '4h',
    },
    
    # Optimization Ranges for SMA 5min
    'sma_5min_optimization': {
        'short_period': [5, 8, 10, 12, 15],      # Short SMA periods to test
        'long_period': [20, 25, 30, 35, 40],     # Long SMA periods to test
        'interval': '5m',
    },
    
    # Optimization Ranges for Range 24h Low
    'range_24h_low_optimization': {
        'long_offset': [-2.0, -1.5, -1.0, -0.5, 0.0],     # Offset from 24h low in percent
        'tolerance': [1.0, 1.5, 2.0, 2.5, 3.0],           # Range tolerance in percent
        'interval': '1h',
    },
    
    # Optimization Ranges for Range 7days Low
    'range_7days_low_optimization': {
        'long_offset': [-2.0, -1.5, -1.0, -0.5, 0.0],     # Offset from 7days low in percent
        'tolerance': [1.0, 1.5, 2.0, 2.5, 3.0],           # Range tolerance in percent
        'interval': '1h',
    },
    
    # Optimization Ranges for Scalping 1min
    'scalping_1min_optimization': {
        'fast_ema': [3, 5, 8],                            # Fast EMA periods to test
        'slow_ema': [10, 13, 15, 20],                     # Slow EMA periods to test
        'rsi_period': [5, 7, 9],                          # RSI periods to test
        'rsi_oversold': [25, 30, 35],                     # RSI oversold thresholds
        'rsi_overbought': [65, 70, 75],                   # RSI overbought thresholds
        'volume_multiplier': [1.3, 1.5, 1.8, 2.0],        # Volume spike multipliers
        'interval': '1m',
    },
    
    # Optimization Ranges for MACD 15min
    'macd_15min_optimization': {
        'fast': [8, 10, 12, 14, 16],                      # Fast EMA periods to test
        'slow': [20, 23, 26, 29, 32],                     # Slow EMA periods to test
        'signal': [7, 8, 9, 10, 11],                      # Signal line periods to test
        'interval': '15m',
    },
    
    # Time Ranges
    'time_ranges': {
        '24 Hours': 1440,   # minutes
        '72 Hours': 4320,
        '7 Days': 10080,
    },
    
    # Coins to backtest (loaded from trading_settings.py)
    'enabled_coins': [],  # Will be populated from TRADING_SETTINGS['monitored_coins']
}
