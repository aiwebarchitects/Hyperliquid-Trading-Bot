"""
Backtest Results Loader
Loads coin-specific optimized parameters from backtest results.
"""

import os
import json
import glob
from typing import Dict, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class BacktestResultsLoader:
    """
    Loads and manages coin-specific parameters from backtest results.
    """
    
    def __init__(self, results_dir: str = "results"):
        """
        Initialize the backtest results loader.
        
        Args:
            results_dir: Directory containing backtest result JSON files
        """
        self.results_dir = results_dir
        self.cache = {}  # Cache loaded results
        logger.info(f"Initialized BacktestResultsLoader with directory: {results_dir}")
    
    def _find_latest_result_file(self, coin: str, signal: str) -> Optional[str]:
        """
        Find the latest backtest result file for a coin and signal.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            signal: Signal name (e.g., "rsi-1min", "rsi-5min")
            
        Returns:
            Path to the latest result file or None if not found
        """
        pattern = os.path.join(self.results_dir, f"{coin}_{signal}_*.json")
        files = glob.glob(pattern)
        
        if not files:
            return None
        
        # Sort by filename (timestamp is in filename) and get the latest
        files.sort(reverse=True)
        return files[0]
    
    def _load_result_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load a backtest result JSON file.
        
        Args:
            filepath: Path to the result file
            
        Returns:
            Dictionary containing the result data or None if failed
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded backtest results from: {filepath}")
            return data
        except Exception as e:
            logger.error(f"Failed to load result file {filepath}: {e}")
            return None
    
    def get_parameters(self, coin: str, signal: str) -> Optional[Dict[str, Any]]:
        """
        Get optimized parameters for a coin and signal.
        
        Args:
            coin: Coin symbol (e.g., "BTC", "ETH")
            signal: Signal name (e.g., "rsi-1min", "rsi-5min")
            
        Returns:
            Dictionary of best parameters or None if not found
        """
        # Check cache first
        cache_key = f"{coin}_{signal}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Find and load the latest result file
        filepath = self._find_latest_result_file(coin, signal)
        if not filepath:
            logger.debug(f"No backtest results found for {coin} {signal}")
            return None
        
        data = self._load_result_file(filepath)
        if not data or 'best_parameters' not in data:
            logger.warning(f"Invalid result file format for {coin} {signal}")
            return None
        
        # Cache the parameters
        params = data['best_parameters']
        self.cache[cache_key] = params
        
        logger.info(f"Loaded parameters for {coin} {signal}: {params}")
        return params
    
    def clear_cache(self):
        """Clear the cached results."""
        self.cache.clear()
        logger.info("Cleared backtest results cache")
    
    def get_all_available_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available backtest results.
        
        Returns:
            Dictionary mapping "coin_signal" to their parameters
        """
        results = {}
        
        if not os.path.exists(self.results_dir):
            logger.warning(f"Results directory does not exist: {self.results_dir}")
            return results
        
        # Find all result files
        pattern = os.path.join(self.results_dir, "*_*_*.json")
        files = glob.glob(pattern)
        
        for filepath in files:
            try:
                filename = os.path.basename(filepath)
                # Parse filename: COIN_SIGNAL_TIMESTAMP.json
                parts = filename.replace('.json', '').split('_')
                if len(parts) >= 3:
                    coin = parts[0]
                    signal = parts[1]
                    
                    # Load the file
                    data = self._load_result_file(filepath)
                    if data and 'best_parameters' in data:
                        key = f"{coin}_{signal}"
                        # Keep only the latest result for each coin-signal pair
                        if key not in results:
                            results[key] = {
                                'coin': coin,
                                'signal': signal,
                                'parameters': data['best_parameters'],
                                'performance': data.get('performance', {}),
                                'timestamp': data.get('timestamp', ''),
                                'filepath': filepath
                            }
            except Exception as e:
                logger.error(f"Error processing result file {filepath}: {e}")
        
        logger.info(f"Found {len(results)} backtest results")
        return results


# Global instance
_loader = None


def get_backtest_loader() -> BacktestResultsLoader:
    """
    Get the global backtest results loader instance.
    
    Returns:
        BacktestResultsLoader instance
    """
    global _loader
    if _loader is None:
        _loader = BacktestResultsLoader()
    return _loader
