"""
Trading-specific settings for the bot.
Based on DEV_PLAN.md requirements only.
"""

TRADING_SETTINGS = {
    # Position Management (from DEV_PLAN)
    'max_positions': 10,              # Maximum concurrent positions
    'position_size_usd': 20,         # Default position size
    
    # Risk Management (from DEV_PLAN)
    'stop_loss_percent': 2.20,         # Stop loss percentage (FIXED - never trails)
    'take_profit_percent': 10.12,       # Take profit percentage fixed profit doesnt make sense.
    'trailing_stop_percent': 0.20,     # Trailing stop distance from peak is not integrated
    'trailing_stop_activation': 0.30,  # Profit % to activate trailing stop is not integrated
    'min_profit_to_sell': 0.03,       # Minimum profit to consider selling
    'min_signal_strength': 0.75,       # Minimum signal strength to execute (0.0-1.0)
    
    # Market Data (from DEV_PLAN)
    'timeframe': '5m',                # Default timeframe
    'monitored_coins': ['ZEC', 'ZEN', 'ENA', 'BTC'],              # Coins to trade
    
    # Exchange (from DEV_PLAN)
    'exchange': 'hyperliquid',
    'testnet': False,
}

# Signal Generator Settings each coin will use its own settings from backtest results. same for stop loss and take profit.
SIGNAL_SETTINGS = {
    # RSI Settings
    'rsi': {
        'period': 14,
        'oversold': 32,
        'overbought': 68,
    },
    
    # SMA Settings
    'sma': {
        'short_period': 10,
        'long_period': 20,
    },
}
