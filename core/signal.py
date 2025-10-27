"""
Signal data structure for trading bot.
Universal format used by all signal generators.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Signal:
    """
    Universal signal format for all trading algorithms.
    
    Attributes:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        action: Trading action - "BUY", "SELL", or "HOLD"
        strength: Signal strength from 0.0 to 1.0
        timestamp: When the signal was generated
        source: Name of the algorithm that generated this signal
        metadata: Additional information (indicators, reasons, etc.)
    """
    coin: str
    action: str  # "BUY", "SELL", "HOLD"
    strength: float  # 0.0 to 1.0
    timestamp: datetime
    source: str  # Algorithm name (e.g., "rsi_5min", "sma_5min")
    metadata: Dict  # Additional data like RSI value, SMA values, etc.
    
    def __post_init__(self):
        """Validate signal data after initialization."""
        assert self.action in ["BUY", "SELL", "HOLD"], f"Invalid action: {self.action}"
        assert 0.0 <= self.strength <= 1.0, f"Strength must be 0-1, got {self.strength}"
        assert self.coin, "Coin symbol cannot be empty"
        assert self.source, "Source cannot be empty"
    
    def is_actionable(self, min_strength: float = 0.7) -> bool:
        """Check if signal is strong enough to act on."""
        return self.action in ["BUY", "SELL"] and self.strength >= min_strength
    
    def __str__(self) -> str:
        """String representation of signal."""
        return f"{self.source}: {self.action} {self.coin} (strength: {self.strength:.2f})"
