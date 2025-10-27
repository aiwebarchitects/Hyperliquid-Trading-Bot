"""
Signal generators module.
Each signal generator is standalone with its own parameters.
"""

from .rsi_5min import RSI5MinSignalGenerator
from .rsi_1min import RSI1MinSignalGenerator
from .rsi_1h import RSI1HSignalGenerator
from .rsi_4h import RSI4HSignalGenerator
from .sma_5min import SMA5MinSignalGenerator
from .range_24h_low import Range24HLowSignalGenerator
from .range_7days_low import Range7DaysLowSignalGenerator
from .scalping_1min import Scalping1MinSignalGenerator
from .macd_15min import MACD15MinSignalGenerator

__all__ = [
    'RSI5MinSignalGenerator',
    'RSI1MinSignalGenerator',
    'RSI1HSignalGenerator',
    'RSI4HSignalGenerator',
    'SMA5MinSignalGenerator',
    'Range24HLowSignalGenerator',
    'Range7DaysLowSignalGenerator',
    'Scalping1MinSignalGenerator',
    'MACD15MinSignalGenerator'
]
