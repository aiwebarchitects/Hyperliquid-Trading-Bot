"""
Configuration module for the trading bot.
Contains system settings and trading parameters.

NOTE: Algorithm-specific settings will be loaded from backtested configurations
      in the future. Each algorithm will use its optimized parameters from
      backtesting results rather than static configuration files.
"""

from .system_settings import SYSTEM_SETTINGS
from .trading_settings import TRADING_SETTINGS, SIGNAL_SETTINGS
from .debug_settings import DEBUG_SETTINGS, get_debug_setting, set_debug_setting
from .backtest_settings import BACKTEST_SETTINGS

__all__ = [
    'SYSTEM_SETTINGS',
    'TRADING_SETTINGS',
    'SIGNAL_SETTINGS',
    'DEBUG_SETTINGS',
    'BACKTEST_SETTINGS',
    'get_debug_setting',
    'set_debug_setting'
]
