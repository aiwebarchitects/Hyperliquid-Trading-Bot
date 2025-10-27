"""
System-level settings for the trading bot.
Based on DEV_PLAN.md requirements only.
"""

SYSTEM_SETTINGS = {
    # Bot Behavior
    'ask_on_start': True,             # Ask user confirmation before starting
    'autopilot': False,               # Manual approval mode
    
    # Update Intervals (optimized to prevent rate limits)
    'position_check_interval': 3,     # Position monitoring interval (3s for SL/TP checks)
    'price_update_interval': 2,       # Price updates for panel display (2s)
    'balance_check_interval': 10,     # Balance check interval (10s)
    'panel_refresh_interval': 2,      # Panel UI refresh rate (2s)
    
    # Signal Check Intervals - Smart timing based on timeframe
    # Each signal generator checks at appropriate intervals for its timeframe
    'signal_check_intervals': {
        'rsi_1min': 60,               # Check every 60s (1 minute) - new candle every minute
        'rsi_5min': 300,              # Check every 300s (5 minutes) - new candle every 5 minutes
        'rsi_1h': 3600,               # Check every 3600s (1 hour) - new candle every hour
        'rsi_4h': 14400,              # Check every 14400s (4 hours) - new candle every 4 hours
        'sma_5min': 300,              # Check every 300s (5 minutes) - new candle every 5 minutes
        'range_7days_low': 3600,      # Check every 3600s (1 hour) - daily data doesn't change often
        'range_24h_low': 1800,        # Check every 1800s (30 min) - 24h data changes more frequently
        'macd_15min': 900,            # Check every 900s (15 minutes) - new candle every 15 minutes
    },
    
    # Logging
    'log_level': 'INFO',
    'log_file': 'logs/trading_bot.log',
}
