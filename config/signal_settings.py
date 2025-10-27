"""
Signal Generator Settings Configuration
Controls which signal generators are enabled by default on startup
"""

# Signal Generator Enable/Disable Settings
SIGNAL_GENERATOR_SETTINGS = {
    'rsi_5min': {
        'enabled': True,
        'name': 'RSI 5-Minute'
    },
    'rsi_1min': {
        'enabled': True,
        'name': 'RSI 1-Minute'
    },
    'rsi_1h': {
        'enabled': True,
        'name': 'RSI 1-Hour'
    },
    'rsi_4h': {
        'enabled': True,
        'name': 'RSI 4-Hour'
    },
    'sma_5min': {
        'enabled': True,
        'name': 'SMA 5-Minute'
    },
    'range_7days_low': {
        'enabled': False,
        'name': '7D Low Range'
    },
    'range_24h_low': {
        'enabled': False,
        'name': '24H Low Range'
    },
    'scalping_1min': {
        'enabled': True,
        'name': 'Scalping 1-Minute'
    },
    'macd_15min': {
        'enabled': False,
        'name': 'MACD 15-Minute'
    },
}