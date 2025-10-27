# Hyperliquid-Trading-Bot

**Free Open Source Hyperliquid Trading Bot Inclusive Panel - Graphical Interface. Last Update 27 October 2025 Automated cryptocurrency trading bot with multiple technical analysis algorithms, real-time monitoring, and backtesting capabilities for Hyperliquid exchange.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/GitHub-MCMA-green)](https://github.com/aiwebarchitects/MCMA)

## Features

### Trading Capabilities
- **Multiple Signal Generators**: RSI (1min, 5min, 1h, 4h), SMA, MACD, Range-based strategies, Scalping
- **Automated Order Execution**: Buy/sell orders based on technical signals
- **Position Management**: Real-time monitoring with trailing stop-loss and take-profit
- **Risk Management**: Position limits, stop-loss, take-profit, and validation checks
- **Multi-Coin Support**: Trade multiple cryptocurrencies simultaneously

### User Interface
- **Terminal-Based Panel**: Real-time monitoring with Tkinter GUI
- **Multiple Pages**:
  - Home: Live activity feed and quick stats
  - Signals: Real-time signal monitoring for all algorithms
  - Positions: Active positions with P&L tracking
  - Monitor: Advanced position monitoring with trailing stops
  - History: Trade history and analytics
  - Backtest: Historical strategy testing
  - Settings: Configure trading parameters
  - Debug: System diagnostics

### Technical Features
- **Modular Architecture**: Easy to add new signal generators
- **Smart Timing**: Timeframe-based signal checking to optimize API usage
- **Backtesting**: Test strategies on historical data before live trading
- **Comprehensive Logging**: Detailed logs for debugging and analysis
- **API Integration**: Hyperliquid exchange with CoinGecko price data

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Hyperliquid account - **[Sign up here with bonus](https://app.hyperliquid.xyz/join/BONUS500)**
- API credentials - **[Create API keys here](https://app.hyperliquid.xyz/API)**
- USDC funding in your account
- Basic understanding of cryptocurrency trading

### Installation

1. Clone the repository:
```bash
git clone https://github.com/aiwebarchitects/MCMA.git
cd multi_crypto_multi_algo_trading_bot_0.1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# OR if pip doesn't work, try:
pip3 install -r requirements.txt
```

3. Set up Hyperliquid account:
   - **[Sign up for Hyperliquid](https://app.hyperliquid.xyz/join/BONUS500)** (get bonus with this link)
   - **[Create API credentials](https://app.hyperliquid.xyz/API)**
   - Fund your account with USDC before starting the bot

4. Configure API credentials:

**Option 1: Use the Settings Panel (Recommended)**
- Launch the panel: `python trading_panel.py` (or `python3 trading_panel.py`)
- Navigate to "API Settings" page
- Enter your secret key and account address
- Click "Save Settings"

**Option 2: Manual Configuration**
Edit `config/api_config.json`:
```json
{
  "secret_key": "your_secret_key_here",
  "account_address": "your_account_address_here"
}
```

### Running the Bot

**Launch the trading panel:**
```bash
python trading_panel.py
# OR if python doesn't work, try:
python3 trading_panel.py
```

The panel will start in monitoring mode. Click "START BOT" to begin automated trading.

## Configuration

**All settings can be configured through the trading panel UI - no need to edit files manually!**

### Using the Settings Panel (Recommended)

1. **API Settings Page**: Configure exchange credentials
   - Wallet address and private key
   - Testnet/mainnet toggle
   - Save and test connection

2. **Settings Page**: Adjust trading parameters
   - Position size and limits
   - Stop-loss and take-profit percentages
   - Trailing stop configuration
   - Monitored coins list
   - Enable/disable signal generators

3. **Debug Page**: System configuration
   - Update intervals
   - Logging levels
   - Performance tuning

### Manual Configuration (Advanced)

If you prefer to edit configuration files directly:

**Trading Settings** (`config/trading_settings.py`):
```python
TRADING_SETTINGS = {
    'max_positions': 10,              # Maximum concurrent positions
    'position_size_usd': 100,         # Default position size
    'stop_loss_percent': 0.6,         # Stop-loss percentage
    'take_profit_percent': 1.6,       # Take-profit percentage
    'trailing_stop_percent': 0.3,     # Trailing stop percentage
    'monitored_coins': [              # Coins to trade
        'BTC', 'ETH', 'SOL', 'AVAX', 'LINK',
        'UNI', 'AAVE', 'ATOM', 'DOT', 'ADA'
    ]
}
```

**Signal Generators** (`config/signal_settings.py`):
```python
SIGNAL_GENERATOR_SETTINGS = {
    'rsi_5min': {'enabled': True, 'name': 'RSI 5-Minute'},
    'rsi_1min': {'enabled': True, 'name': 'RSI 1-Minute'},
    'sma_5min': {'enabled': True, 'name': 'SMA 5-Minute'},
    'macd_15min': {'enabled': False, 'name': 'MACD 15-Minute'},
    # ... more signals
}
```

**System Settings** (`config/system_settings.py`):
```python
SYSTEM_SETTINGS = {
    'position_check_interval': 3,     # Position monitoring (seconds)
    'signal_check_intervals': {       # Per-signal check intervals
        'rsi_1min': 60,               # Check every 60s
        'rsi_5min': 300,              # Check every 5 minutes
        'rsi_1h': 3600,               # Check every hour
    }
}
```

**Note**: Changes made through the panel UI are saved to the configuration files automatically.

## Available Signal Generators

### RSI-Based Signals
- **RSI 1-Minute**: Fast scalping on 1-minute candles
- **RSI 5-Minute**: Short-term trading on 5-minute candles
- **RSI 1-Hour**: Medium-term trading on hourly candles
- **RSI 4-Hour**: Longer-term position trading

### Moving Average Signals
- **SMA 5-Minute**: Simple moving average crossover strategy

### MACD Signals
- **MACD 15-Minute**: MACD crossover on 15-minute candles

### Range-Based Signals
- **24H Low Range**: Buy near 24-hour lows
- **7D Low Range**: Buy near 7-day lows

### Scalping Signals
- **Scalping 1-Minute**: High-frequency scalping strategy

## Adding New Signals

See [how_to_add_new_signals.md](how_to_add_new_signals.md) for detailed instructions.

**Quick steps:**
1. Create signal file in `signals/` directory
2. Implement `generate_signal(coin: str)` method
3. Register in `signals/__init__.py`
4. Add to `core/trading_bot.py`
5. Add to panel display in `panel_modules/signals_display.py`

## Backtesting

Test strategies on historical data before live trading:

1. Navigate to the Backtest page in the panel
2. Select a signal generator
3. Choose coins and date range
4. Click "Run Backtest"
5. Review results and metrics

Results are saved in `results/` directory as JSON files.

## Project Structure

```
multi_crypto_multi_algo_trading_bot_0.1/
├── trading_panel.py              # Main entry point - GUI application
├── requirements.txt              # Python dependencies
├── how_to_add_new_signals.md     # Guide for adding new signals
├── DEV_PLAN.md                   # Development roadmap
├── whats_next_todo.md            # Future improvements
├── position_states.json          # Position state persistence
├── config/                       # Configuration files
│   ├── __init__.py
│   ├── trading_settings.py       # Trading parameters
│   ├── signal_settings.py        # Signal enable/disable
│   ├── system_settings.py        # System configuration
│   ├── backtest_settings.py      # Backtesting parameters
│   ├── debug_settings.py         # Debug configuration
│   └── api_config.json           # API credentials (create this)
├── core/                         # Core components
│   ├── __init__.py
│   ├── trading_bot.py            # Main bot orchestrator
│   └── signal.py                 # Signal data structure
├── signals/                      # Signal generators
│   ├── __init__.py
│   ├── rsi_1min.py               # RSI 1-minute signal
│   ├── rsi_5min.py               # RSI 5-minute signal
│   ├── rsi_1h.py                 # RSI 1-hour signal
│   ├── rsi_4h.py                 # RSI 4-hour signal
│   ├── sma_5min.py               # SMA 5-minute signal
│   ├── macd_15min.py             # MACD 15-minute signal
│   ├── scalping_1min.py          # Scalping 1-minute signal
│   ├── range_24h_low.py          # 24-hour low range signal
│   └── range_7days_low.py        # 7-day low range signal
├── managers/                     # Order and position management
│   ├── __init__.py
│   ├── order_manager.py          # Order execution
│   └── position_manager.py       # Position monitoring
├── panel_modules/                # UI components
│   ├── __init__.py
│   ├── header.py                 # Panel header
│   ├── navigation.py             # Navigation menu
│   ├── signals_display.py        # Signals display
│   ├── positions.py              # Positions display
│   ├── position_monitor.py       # Position monitoring
│   ├── orders.py                 # Orders display
│   ├── price_fetcher.py          # Price data fetcher
│   ├── coingecko_price_fetcher.py # CoinGecko integration
│   ├── api_utils.py              # API utilities
│   └── pages/                    # Panel pages
│       ├── __init__.py
│       ├── home_page.py          # Home/activity page
│       ├── settings_page.py      # Settings page
│       ├── api_settings_page.py  # API settings page
│       ├── backtest_page.py      # Backtesting page
│       └── debug_page.py         # Debug page
├── utils/                        # Utilities
│   ├── __init__.py
│   ├── api_client.py             # Exchange API wrapper
│   ├── logger.py                 # Logging utilities
│   └── backtest_results_loader.py # Backtest results loader
├── integrate/                    # Integration tests
│   ├── test_coin_specific_rsi_1min.py
│   ├── test_sky_range_24h_low.py
│   ├── test_sky_range_72h_low.py
│   └── ...
├── changes_made/                 # Development changelog
│   ├── CHANGELOG.md
│   ├── CHANGELOG_20251026.md
│   ├── BACKTEST_FIXES_20251026.md
│   ├── COIN_SPECIFIC_PARAMETERS.md
│   ├── MACD_INTEGRATION_SUMMARY.md
│   ├── SCALPING_SIGNAL_INTEGRATION.md
│   └── ...
├── results/                      # Backtest results (JSON files)
├── logs/                         # Log files
│   ├── trading_bot.log           # Main bot log
│   └── signals_log.txt           # Signals log
└── old/                          # Archived/deprecated code
```

## Risk Management

The bot implements multiple safety mechanisms:

1. **Position Limits**: Maximum concurrent positions enforced
2. **Stop-Loss**: Automatic exit on losses exceeding threshold
3. **Take-Profit**: Automatic profit-taking at target levels
4. **Trailing Stop**: Lock in profits as price moves favorably
5. **Signal Validation**: Multiple checks before order execution
6. **Rate Limiting**: API request throttling to prevent bans

## Monitoring and Logs

### Real-Time Monitoring
- **Signals Page**: Live signal generation across all algorithms
- **Positions Page**: Active positions with P&L
- **Monitor Page**: Advanced position tracking with trailing stops
- **History Page**: Trade history and performance analytics

### Log Files
- **Main Log**: `logs/trading_bot.log` - All bot activity
- **Signals Log**: `logs/signals_log.txt` - Signal generation history

## Safety Features

### Paper Trading Mode
Run the bot without executing real orders:
```python
# In trading_panel.py
self.trading_bot = TradingBot(execute_orders=False)
```

### Emergency Stop
Click "STOP BOT" in the panel or use emergency stop to:
- Close all open positions
- Cancel pending orders
- Stop signal generation

## Performance Optimization

### Smart Signal Checking
The bot uses timeframe-based intervals to optimize API usage:
- 1-minute signals: Check every 60 seconds
- 5-minute signals: Check every 5 minutes
- 1-hour signals: Check every hour
- Daily signals: Check every 30 minutes

This prevents unnecessary API calls and reduces rate limiting issues.

### Position Monitoring
Positions are monitored every 3 seconds for:
- Stop-loss triggers
- Take-profit targets
- Trailing stop adjustments

## Troubleshooting

### Common Issues

**Bot won't start:**
- Check API credentials in `config/api_config.json`
- Verify internet connection
- Check logs in `logs/trading_bot.log`

**No signals generated:**
- Verify signal generators are enabled in `config/signal_settings.py`
- Check if monitored coins have sufficient data
- Review signal-specific logs

**Orders not executing:**
- Ensure `execute_orders=True` when starting bot
- Check position limits not exceeded
- Verify sufficient account balance
- Review order manager logs

**API rate limit errors:**
- Increase signal check intervals in `config/system_settings.py`
- Reduce number of monitored coins
- Add delays between requests

## Development

### Requirements
- Python 3.8+
- Dependencies listed in `requirements.txt`

### Testing
Run individual signal generators:
```bash
python -c "from signals.rsi_5min import RSI5MinSignalGenerator; gen = RSI5MinSignalGenerator(); print(gen.generate_signal('BTC'))"
# OR if python doesn't work, try:
python3 -c "from signals.rsi_5min import RSI5MinSignalGenerator; gen = RSI5MinSignalGenerator(); print(gen.generate_signal('BTC'))"
```

### Contributing
1. Create new signal generators following the template
2. Add comprehensive logging
3. Test thoroughly with backtesting
4. Update documentation

## Technical Details

### Signal Architecture
All signals follow a standardized interface:
```python
class SignalGenerator:
    def generate_signal(self, coin: str) -> Optional[Signal]:
        # Returns Signal object with:
        # - coin: str
        # - action: "BUY" | "SELL" | "HOLD"
        # - strength: float (0.0 to 1.0)
        # - timestamp: datetime
        # - source: str (signal name)
        # - metadata: dict (additional info)
```

### Order Execution Flow
1. Signal generated by algorithm
2. Order manager validates signal
3. Check position limits and risk rules
4. Execute order on exchange
5. Position manager starts monitoring
6. Trailing stop-loss activated
7. Exit on stop-loss or take-profit

## Disclaimer

**This software is for educational purposes only. Cryptocurrency trading carries significant risk. Use at your own risk. The developers are not responsible for any financial losses incurred while using this software.**

**Always:**
- Start with small position sizes
- Test thoroughly in paper trading mode
- Understand the strategies before using them
- Monitor your positions regularly
- Never invest more than you can afford to lose

## License

Apache License 2.0

Copyright 2025 AI Web Architects

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Support

For issues, questions, or contributions:
- **GitHub Repository**: https://github.com/aiwebarchitects/MCMA
- **Issues**: https://github.com/aiwebarchitects/MCMA/issues
- Check existing documentation
- Review log files for errors
- Consult `how_to_add_new_signals.md` for customization

## Version History

### v0.1 (Current)
- Initial release
- 9 signal generators (RSI, SMA, MACD, Range, Scalping)
- Terminal-based UI with multiple pages
- Backtesting capabilities
- Position management with trailing stops
- Hyperliquid exchange integration
- Comprehensive logging and monitoring

---

**Happy Trading!** Remember to always trade responsibly and never risk more than you can afford to lose.
