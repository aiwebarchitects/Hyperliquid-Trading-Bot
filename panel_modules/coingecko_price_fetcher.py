"""
CoinGecko Price Fetcher - Gets real-time prices from CoinGecko Free API
"""

import requests
from typing import Dict, Optional
from datetime import datetime, timedelta


class CoinGeckoPriceFetcher:
    """Fetches real-time cryptocurrency prices from CoinGecko Free API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.prices = {}
        self.last_fetch = {}
        self.cache_duration = 30  # Cache for 30 seconds to avoid rate limits
        
        # Mapping of common symbols to CoinGecko IDs
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'AVAX': 'avalanche-2',
            'ATOM': 'cosmos',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'ICP': 'internet-computer',
            'FIL': 'filecoin',
            'AAVE': 'aave',
            'SAND': 'the-sandbox',
            'MANA': 'decentraland',
            'AXS': 'axie-infinity',
            'THETA': 'theta-token',
            'XTZ': 'tezos',
            'ETC': 'ethereum-classic',
            'EGLD': 'elrond-erd-2',
            'FLOW': 'flow',
            'FTM': 'fantom',
            'HBAR': 'hedera-hashgraph',
            'NEAR': 'near',
            'GRT': 'the-graph',
            'STX': 'blockstack',
            'RUNE': 'thorchain',
            'ZEC': 'zcash',
            'MKR': 'maker',
            'SNX': 'havven',
            'COMP': 'compound-governance-token',
            'YFI': 'yearn-finance',
            'SUSHI': 'sushi',
            'CRV': 'curve-dao-token',
            '1INCH': '1inch',
            'ENJ': 'enjincoin',
            'BAT': 'basic-attention-token',
            'ZRX': '0x',
            'KNC': 'kyber-network-crystal',
            'STORJ': 'storj',
            'REN': 'republic-protocol',
            'LDO': 'lido-dao',
            'IMX': 'immutable-x',
            'OP': 'optimism',
            'ARB': 'arbitrum',
            'SUI': 'sui',
            'APT': 'aptos',
            'INJ': 'injective-protocol',
            'TIA': 'celestia',
            'SEI': 'sei-network',
            'SHIB': 'shiba-inu',
            'TRX': 'tron',
            'TON': 'the-open-network',
            'CELO': 'celo',
            'QNT': 'quant-network',
            'CHZ': 'chiliz',
            'PAXG': 'pax-gold',
            'TAO': 'bittensor',
            'ICX': 'icon',
            'ZIL': 'zilliqa',
            'OKB': 'okb',
            'LEO': 'leo-token',
            'ENA': 'ethena',
        }
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.last_fetch:
            return False
        
        time_diff = datetime.now() - self.last_fetch[symbol]
        return time_diff.total_seconds() < self.cache_duration
    
    def _get_coingecko_id(self, symbol: str) -> Optional[str]:
        """Convert trading symbol to CoinGecko ID"""
        # Remove USDT suffix if present
        clean_symbol = symbol.replace('USDT', '').replace('USD', '')
        return self.symbol_to_id.get(clean_symbol)
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSDT', 'ETH')
            
        Returns:
            Current price in USD or None if error
        """
        # Check cache first
        if self._is_cache_valid(symbol) and symbol in self.prices:
            return self.prices[symbol]
        
        coin_id = self._get_coingecko_id(symbol)
        if not coin_id:
            print(f"Unknown symbol: {symbol}")
            return self.prices.get(symbol)
        
        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    'ids': coin_id,
                    'vs_currencies': 'usd'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if coin_id in data and 'usd' in data[coin_id]:
                    price = float(data[coin_id]['usd'])
                    self.prices[symbol] = price
                    self.last_fetch[symbol] = datetime.now()
                    return price
            else:
                print(f"CoinGecko API error: {response.status_code}")
                return self.prices.get(symbol)
                
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return self.prices.get(symbol)  # Return cached price if available
    
    def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """
        Get 24h ticker data including high, low, volume, price change
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSDT')
            
        Returns:
            Dict with ticker data or None
        """
        coin_id = self._get_coingecko_id(symbol)
        if not coin_id:
            print(f"Unknown symbol: {symbol}")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/coins/{coin_id}",
                params={
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                
                return {
                    'price': float(market_data.get('current_price', {}).get('usd', 0)),
                    'high_24h': float(market_data.get('high_24h', {}).get('usd', 0)),
                    'low_24h': float(market_data.get('low_24h', {}).get('usd', 0)),
                    'volume_24h': float(market_data.get('total_volume', {}).get('usd', 0)),
                    'price_change_pct': float(market_data.get('price_change_percentage_24h', 0)),
                    'market_cap': float(market_data.get('market_cap', {}).get('usd', 0)),
                    'circulating_supply': float(market_data.get('circulating_supply', 0))
                }
            else:
                print(f"CoinGecko API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching 24h ticker for {symbol}: {e}")
            return None
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """
        Get prices for multiple symbols at once
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            Dict of symbol -> price
        """
        # Convert symbols to CoinGecko IDs
        coin_ids = []
        symbol_map = {}
        
        for symbol in symbols:
            coin_id = self._get_coingecko_id(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                symbol_map[coin_id] = symbol
        
        if not coin_ids:
            return {}
        
        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    'ids': ','.join(coin_ids),
                    'vs_currencies': 'usd'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                for coin_id, symbol in symbol_map.items():
                    if coin_id in data and 'usd' in data[coin_id]:
                        price = float(data[coin_id]['usd'])
                        prices[symbol] = price
                        self.prices[symbol] = price
                        self.last_fetch[symbol] = datetime.now()
                
                return prices
            else:
                print(f"CoinGecko API error: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error fetching multiple prices: {e}")
            return {}
    
    def get_market_chart(self, symbol: str, days: int = 1) -> Optional[Dict]:
        """
        Get historical market data (price, volume, market cap)
        
        Args:
            symbol: Trading symbol
            days: Number of days of data (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            Dict with historical data or None
        """
        coin_id = self._get_coingecko_id(symbol)
        if not coin_id:
            print(f"Unknown symbol: {symbol}")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/coins/{coin_id}/market_chart",
                params={
                    'vs_currency': 'usd',
                    'days': days
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"CoinGecko API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching market chart for {symbol}: {e}")
            return None
