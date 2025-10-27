# How to Add New Signals to the Trading Bot

This guide explains how to add new trading signal generators to the multi-crypto trading bot system.

## Overview

The trading bot uses a modular signal system where each signal generator is a standalone class that:
- Fetches market data independently
- Calculates technical indicators
- Returns standardized `Signal` objects
- Can be easily added or removed from the system

## Quick Start: 5 Steps to Add a New Signal

### Step 1: Create Your Signal Generator File

Create a new Python file in the `signals/` directory:

```bash
signals/your_signal_name.py
```

**Naming Convention:**
- Use lowercase with underscores
- Include the timeframe if applicable
- Examples: `macd_15min.py`, `bollinger_bands_1h.py`, `volume_spike_5min.py`

### Step 2: Implement the Signal Generator Class

Your signal generator must follow this structure:

```python
"""
Your Signal Description.
Brief explanation of what this signal does.
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
from core.signal import Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class YourSignalGenerator:
    """
    Your signal generator description.
    Each instance is standalone with its own parameters.
    """
    
    def __init__(self, param1: int = 14, param2: int = 30):
        """
        Initialize your signal generator.
        
        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2
        """
        self.param1 = param1
        self.param2 = param2
        self.name = "your_signal_name"  # Must be unique!
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Rate limiting
        
        logger.info(f"Initialized {self.name} (param1={param1}, param2={param2})")
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch candle data from Binance API.
        
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
                'interval': '5m',  # Change to your timeframe: 1m, 5m, 15m, 1h, etc.
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
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {coin}: {e}")
            return None
    
    def _calculate_your_indicator(self, df: pd.DataFrame) -> float:
        """
        Calculate your technical indicator.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Indicator value
        """
        # Implement your indicator calculation here
        # Example: RSI, MACD, Bollinger Bands, etc.
        pass
    
    def _calculate_signal_strength(self, indicator_value: float, action: str) -> float:
        """
        Calculate signal strength based on indicator value.
        
        Args:
            indicator_value: Your calculated indicator value
            action: "BUY" or "SELL"
            
        Returns:
            Signal strength from 0.0 to 1.0
        """
        # Implement your strength calculation logic
        # Stronger signals should return values closer to 1.0
        # Weaker signals should return values closer to 0.6
        # Return 0.0 for HOLD
        
        if action == "BUY":
            # Calculate buy signal strength
            strength = 0.7  # Example
            return min(1.0, max(0.0, strength))
        
        elif action == "SELL":
            # Calculate sell signal strength
            strength = 0.7  # Example
            return min(1.0, max(0.0, strength))
        
        return 0.0
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        """
        Generate trading signal for a coin.
        
        THIS IS THE REQUIRED METHOD - Must be implemented!
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            Signal object or None if unable to generate
        """
        try:
            # 1. Fetch market data
            df = self._fetch_candles(coin, limit=100)
            if df is None or len(df) < 50:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            # 2. Calculate your indicator
            indicator_value = self._calculate_your_indicator(df)
            
            # 3. Determine action based on indicator
            if indicator_value > self.param2:  # Example condition
                action = "BUY"
            elif indicator_value < self.param1:  # Example condition
                action = "SELL"
            else:
                action = "HOLD"
            
            # 4. Calculate signal strength
            strength = self._calculate_signal_strength(indicator_value, action)
            
            # 5. Create and return Signal object
            signal = Signal(
                coin=coin,
                action=action,  # Must be "BUY", "SELL", or "HOLD"
                strength=strength,  # Must be 0.0 to 1.0
                timestamp=datetime.now(),
                source=self.name,  # Your unique signal name
                metadata={
                    # Include relevant indicator values and parameters
                    'indicator_value': round(indicator_value, 2),
                    'param1': self.param1,
                    'param2': self.param2,
                    'timeframe': '5m',
                    # Add any other useful information
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
```

### Step 3: Register Your Signal in `signals/__init__.py`

Add your signal generator to the module exports:

```python
"""
Signal generators module.
Each signal generator is standalone with its own parameters.
"""

from .rsi_5min import RSI5MinSignalGenerator
from .rsi_1min import RSI1MinSignalGenerator
from .sma_5min import SMA5MinSignalGenerator
from .your_signal_name import YourSignalGenerator  # Add this line

__all__ = [
    'RSI5MinSignalGenerator',
    'RSI1MinSignalGenerator',
    'SMA5MinSignalGenerator',
    'YourSignalGenerator'  # Add this line
]
```

### Step 4: Add Your Signal to the Trading Bot

Edit `core/trading_bot.py` in the `_init_signal_generators()` method:

```python
def _init_signal_generators(self) -> List:
    """
    Initialize all signal generators.
    
    Returns:
        List of signal generator instances
    """
    generators = []
    
    # Existing signals
    generators.append(RSI5MinSignalGenerator(period=14, oversold=30, overbought=70))
    generators.append(RSI1MinSignalGenerator(period=14, oversold=30, overbought=70))
    generators.append(SMA5MinSignalGenerator(short_period=10, long_period=20))
    
    # Add your new signal here
    generators.append(YourSignalGenerator(param1=14, param2=30))
    
    return generators
```

Don't forget to import your signal at the top of the file:

```python
from signals import (
    RSI5MinSignalGenerator, 
    RSI1MinSignalGenerator, 
    SMA5MinSignalGenerator,
    YourSignalGenerator  # Add this
)
```

### Step 5: Test Your Signal

Run the trading bot in monitoring mode (no actual trading):

```bash
python trading_panel.py
```

Check the logs to verify your signal is:
- Being initialized correctly
- Generating signals for monitored coins
- Producing valid Signal objects

## Signal Object Requirements

Your `generate_signal()` method MUST return a `Signal` object with these attributes:

```python
Signal(
    coin="BTC",           # String: Coin symbol
    action="BUY",         # String: "BUY", "SELL", or "HOLD"
    strength=0.75,        # Float: 0.0 to 1.0
    timestamp=datetime.now(),  # datetime: When signal was generated
    source="your_signal_name",  # String: Your unique signal identifier
    metadata={            # Dict: Additional information
        'indicator_value': 65.5,
        'timeframe': '5m',
        # ... any other relevant data
    }
)
```

**Important Rules:**
- `action` must be exactly "BUY", "SELL", or "HOLD"
- `strength` must be between 0.0 and 1.0
- `source` should match your signal's `self.name`
- `metadata` should include useful debugging information

## Best Practices

### 1. Rate Limiting
Always implement rate limiting to avoid API bans:

```python
def _rate_limit(self):
    elapsed = time.time() - self.last_request_time
    if elapsed < self.min_request_interval:
        time.sleep(self.min_request_interval - elapsed)
    self.last_request_time = time.time()
```

### 2. Error Handling
Wrap your logic in try-except blocks:

```python
try:
    # Your signal logic
    return signal
except Exception as e:
    logger.error(f"{self.name}: Error for {coin}: {e}")
    return None
```

### 3. Data Validation
Check if you have enough data before calculating:

```python
if df is None or len(df) < required_periods:
    logger.warning(f"{self.name}: Insufficient data for {coin}")
    return None
```

### 4. Signal Strength Guidelines
- **0.9 - 1.0**: Very strong signal (rare, extreme conditions)
- **0.8 - 0.9**: Strong signal (clear indicator confirmation)
- **0.7 - 0.8**: Good signal (standard conditions met)
- **0.6 - 0.7**: Weak signal (marginal conditions)
- **0.0 - 0.6**: No signal (return HOLD instead)

### 5. Logging
Use informative log messages:

```python
logger.info(f"{self.name}: {signal}")  # Log every signal
logger.warning(f"{self.name}: Insufficient data for {coin}")  # Log warnings
logger.error(f"{self.name}: Error: {e}")  # Log errors
```

## Example: Complete MACD Signal Generator

Here's a complete example implementing a MACD signal:

```python
"""
MACD 15-minute signal generator.
Uses MACD crossover strategy on 15-minute candles.
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
from core.signal import Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class MACD15MinSignalGenerator:
    """MACD-based signal generator using 15-minute candles."""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        self.name = "macd_15min"
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        logger.info(f"Initialized {self.name} (fast={fast}, slow={slow}, signal={signal})")
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_candles(self, coin: str, limit: int = 100) -> Optional[pd.DataFrame]:
        try:
            self._rate_limit()
            symbol = f"{coin}USDT"
            url = "https://api.binance.com/api/v3/klines"
            params = {'symbol': symbol, 'interval': '15m', 'limit': limit}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['close'] = pd.to_numeric(df['close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'close']]
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {coin}: {e}")
            return None
    
    def _calculate_macd(self, prices: pd.Series):
        """Calculate MACD, Signal line, and Histogram."""
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def generate_signal(self, coin: str) -> Optional[Signal]:
        try:
            df = self._fetch_candles(coin, limit=100)
            if df is None or len(df) < self.slow + self.signal_period:
                logger.warning(f"{self.name}: Insufficient data for {coin}")
                return None
            
            macd_line, signal_line, histogram = self._calculate_macd(df['close'])
            
            current_hist = histogram.iloc[-1]
            prev_hist = histogram.iloc[-2]
            
            # Detect crossover
            action = "HOLD"
            if prev_hist <= 0 and current_hist > 0:
                action = "BUY"
            elif prev_hist >= 0 and current_hist < 0:
                action = "SELL"
            
            # Calculate strength based on histogram magnitude
            strength = 0.0
            if action != "HOLD":
                strength = min(1.0, 0.7 + abs(current_hist) * 0.1)
            
            signal = Signal(
                coin=coin,
                action=action,
                strength=strength,
                timestamp=datetime.now(),
                source=self.name,
                metadata={
                    'macd': round(macd_line.iloc[-1], 4),
                    'signal': round(signal_line.iloc[-1], 4),
                    'histogram': round(current_hist, 4),
                    'timeframe': '15m'
                }
            )
            
            logger.info(f"{self.name}: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating signal for {coin}: {e}")
            return None
```

## Testing Your Signal

### 1. Unit Testing
Create a test script to verify your signal works:

```python
from signals.your_signal_name import YourSignalGenerator

# Initialize
generator = YourSignalGenerator(param1=14, param2=30)

# Test with a coin
signal = generator.generate_signal("BTC")

if signal:
    print(f"Signal: {signal}")
    print(f"Action: {signal.action}")
    print(f"Strength: {signal.strength}")
    print(f"Metadata: {signal.metadata}")
else:
    print("No signal generated")
```

### 2. Integration Testing
Run the full trading bot in monitoring mode and check logs:

```bash
python trading_panel.py
```

Look for:
- ✅ Signal initialization messages
- ✅ Signal generation for each coin
- ✅ No errors or exceptions
- ✅ Reasonable signal strengths (0.6-1.0 for actionable signals)

## Troubleshooting

### Signal Not Appearing
- Check if you added it to `signals/__init__.py`
- Check if you imported it in `core/trading_bot.py`
- Check if you added it to `_init_signal_generators()`

### API Rate Limit Errors
- Increase `self.min_request_interval` (e.g., to 1.0 second)
- Reduce the number of candles fetched
- Add more delay between requests

### Invalid Signal Errors
- Ensure `action` is exactly "BUY", "SELL", or "HOLD"
- Ensure `strength` is between 0.0 and 1.0
- Ensure all required Signal fields are provided

### No Signals Generated
- Check if you have enough historical data
- Verify your indicator calculation logic
- Add debug logging to see intermediate values
- Test with different coins (some may not have data)

## Advanced Topics

### Multiple Timeframes
You can create multiple versions of the same signal for different timeframes:

```python
# signals/rsi_1min.py
class RSI1MinSignalGenerator:
    def __init__(self):
        self.name = "rsi_1min"
        # ... interval: '1m'

# signals/rsi_5min.py
class RSI5MinSignalGenerator:
    def __init__(self):
        self.name = "rsi_5min"
        # ... interval: '5m'
```

### Combining Multiple Indicators
You can combine multiple indicators in one signal:

```python
def generate_signal(self, coin: str) -> Optional[Signal]:
    # Calculate RSI
    rsi = self._calculate_rsi(df['close'])
    
    # Calculate MACD
    macd, signal_line, _ = self._calculate_macd(df['close'])
    
    # Combine conditions
    if rsi < 30 and macd > signal_line:
        action = "BUY"
        strength = 0.9  # High confidence with multiple confirmations
    # ... etc
```

### Custom Data Sources
You can use different APIs or data sources:

```python
def _fetch_candles(self, coin: str) -> Optional[pd.DataFrame]:
    # Use CryptoCompare, CoinGecko, or your own data source
    # Just return a DataFrame with the required columns
    pass
```

## Summary Checklist

When adding a new signal, make sure you:

- [ ] Created signal file in `signals/` directory
- [ ] Implemented `generate_signal(coin: str)` method
- [ ] Returns valid `Signal` objects
- [ ] Added to `signals/__init__.py`
- [ ] Imported in `core/trading_bot.py`
- [ ] Added to `_init_signal_generators()` method
- [ ] **⚠️ CRITICAL: Added to `panel_modules/signals_display.py`** (See below)
- [ ] **⚠️ CRITICAL: Added metadata display logic** (See below)
- [ ] Tested with monitoring mode
- [ ] Verified signals appear in logs
- [ ] No errors or exceptions
- [ ] Signal strengths are reasonable

### ⚠️ CRITICAL STEP: Panel Integration

**DO NOT SKIP THIS!** Your signal will NOT appear in the trading panel unless you complete these steps:

#### Step 1: Add to signals_display.py Generator Dictionary

Edit `panel_modules/signals_display.py` and add your signal to the `self.generators` dictionary in `__init__`:

```python
# In SignalsDisplay.__init__() method
self.generators = {
    'rsi_5min': {...},
    'rsi_1min': {...},
    'sma_5min': {...},
    
    # ADD YOUR SIGNAL HERE:
    'your_signal_id': {
        'instance': YourSignalGenerator(
            param1=value1,
            param2=value2
        ),
        'enabled': True,  # or False
        'name': 'Display Name',
        'last_signals': []
    }
}
```

#### Step 2: Add Metadata Display Logic

In the same file, find the `_update_coin_signals()` method and add your metadata display:

```python
# Update metadata
metadata_text = ""
if 'rsi' in signal.metadata:
    metadata_text = f"RSI: {signal.metadata['rsi']}"
elif 'short_sma' in signal.metadata:
    metadata_text = f"SMA: {signal.metadata['short_sma']:.2f}/{signal.metadata['long_sma']:.2f}"
# ADD YOUR METADATA DISPLAY HERE:
elif 'your_unique_key' in signal.metadata:
    metadata_text = f"Your display format: {signal.metadata['value']}"
labels['metadata'].config(text=metadata_text)
```

#### Step 3: Add Signal Logging Format

Find the `_log_signal()` method and add your logging format:

```python
# Format metadata
metadata_str = ""
if 'rsi' in signal.metadata:
    metadata_str = f"RSI={signal.metadata['rsi']}"
elif 'short_sma' in signal.metadata:
    metadata_str = f"SMA={signal.metadata['short_sma']:.2f}/{signal.metadata['long_sma']:.2f}"
# ADD YOUR LOGGING FORMAT HERE:
elif 'your_unique_key' in signal.metadata:
    metadata_str = f"YourData={signal.metadata['value']}"
```

#### Step 4: (Optional) Add to _display_coin_signals()

If you want custom display in the old display method, add to `_display_coin_signals()`:

```python
# Metadata (show key indicator)
metadata_text = ""
if 'rsi' in signal.metadata:
    metadata_text = f"RSI: {signal.metadata['rsi']}"
elif 'short_sma' in signal.metadata:
    metadata_text = f"SMA: {signal.metadata['short_sma']:.2f}/{signal.metadata['long_sma']:.2f}"
# ADD HERE TOO:
elif 'your_unique_key' in signal.metadata:
    metadata_text = f"Your display: {signal.metadata['value']}"
```

**Why This Matters:**
- Without panel integration, your signal will run in the bot but be INVISIBLE in the UI
- Users won't see your signal's output
- Debugging becomes impossible
- The signal appears "broken" even though it works

**Example: 7 Days Low Range Signal**

```python
# 1. Added to generators dictionary
'range_7days_low': {
    'instance': Range7DaysLowSignalGenerator(
        long_offset_percent=-1.0,
        tolerance_percent=2.0
    ),
    'enabled': True,
    'name': '7D Low Range',
    'last_signals': []
}

# 2. Added metadata display
elif '7days_low' in signal.metadata:
    metadata_text = f"Price: ${signal.metadata['current_price']:.6f} | Range: ${signal.metadata['buy_range_low']:.6f}-${signal.metadata['buy_range_high']:.6f}"

# 3. Added logging format
elif '7days_low' in signal.metadata:
    metadata_str = f"Price=${signal.metadata['current_price']:.6f} Range=${signal.metadata['buy_range_low']:.6f}-${signal.metadata['buy_range_high']:.6f}"
```

## Need Help?

- Check existing signals in `signals/` for examples
- Review the `Signal` class in `core/signal.py`
- Look at how signals are used in `core/trading_bot.py`
- Check logs in `logs/trading_bot.log` for errors

Happy signal building! 🚀
