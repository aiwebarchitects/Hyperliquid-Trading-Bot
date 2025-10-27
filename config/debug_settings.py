"""
Debug settings for the trading bot.
Controls console output and debugging features.
"""

DEBUG_SETTINGS = {
    # Position Monitoring Debug
    'position_check_debug': True,      # Show detailed position check info in console
    
    # Future debug options can be added here
    # 'signal_debug': False,           # Show signal generation details
    # 'api_debug': False,              # Show API request/response details
    # 'order_debug': False,            # Show order execution details
}


def get_debug_setting(key: str, default=False) -> bool:
    """
    Get a debug setting value.
    
    Args:
        key: Setting key
        default: Default value if key not found
        
    Returns:
        Boolean value of the setting
    """
    return DEBUG_SETTINGS.get(key, default)


def set_debug_setting(key: str, value: bool):
    """
    Set a debug setting value.
    
    Args:
        key: Setting key
        value: Boolean value to set
    """
    if key in DEBUG_SETTINGS:
        DEBUG_SETTINGS[key] = value
        return True
    return False


def get_all_debug_settings() -> dict:
    """
    Get all debug settings.
    
    Returns:
        Dictionary of all debug settings
    """
    return DEBUG_SETTINGS.copy()
