"""
Data fetching utilities for backtesting
"""
import requests
import pandas as pd
from datetime import datetime
from typing import Optional


def fetch_historical_data(coin: str, minutes: int, interval: str = '1m') -> Optional[pd.DataFrame]:
    """
    Fetch historical candles from Binance
    
    Args:
        coin: Coin symbol (e.g., 'BTC')
        minutes: Number of minutes of historical data
        interval: Candle interval (e.g., '1m', '5m', '1h')
        
    Returns:
        DataFrame with OHLCV data or None if error
    """
    try:
        symbol = f"{coin}USDT"
        url = "https://api.binance.com/api/v3/klines"
        
        # Calculate how many candles we need based on interval and time range
        interval_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        
        candles_needed = minutes // interval_minutes.get(interval, 1)
        limit = min(candles_needed, 1000)  # Binance max is 1000
        
        # Calculate start time based on time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = end_time - (minutes * 60 * 1000)
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
    except Exception as e:
        print(f"Error fetching data for {coin}: {e}")
        return None
