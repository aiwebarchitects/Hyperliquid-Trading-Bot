"""
Price Fetcher - Gets real-time prices from Binance API
"""

import requests
from typing import Dict, Optional


class PriceFetcher:
    """Fetches real-time cryptocurrency prices from Binance"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.prices = {}
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
            
        Returns:
            Current price or None if error
        """
        try:
            response = requests.get(
                f"{self.base_url}/ticker/price",
                params={'symbol': symbol},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                self.prices[symbol] = price
                return price
            else:
                return None
                
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return self.prices.get(symbol)  # Return cached price if available
    
    def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """
        Get 24h ticker data including high, low, volume, price change
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            Dict with ticker data or None
        """
        try:
            response = requests.get(
                f"{self.base_url}/ticker/24hr",
                params={'symbol': symbol},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'price': float(data['lastPrice']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'volume_24h': float(data['volume']),
                    'price_change_pct': float(data['priceChangePercent'])
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error fetching 24h ticker for {symbol}: {e}")
            return None
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """
        Get prices for multiple symbols at once
        
        Args:
            symbols: List of trading pairs
            
        Returns:
            Dict of symbol -> price
        """
        prices = {}
        for symbol in symbols:
            price = self.get_price(symbol)
            if price:
                prices[symbol] = price
        return prices
