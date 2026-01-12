#!/usr/bin/env python3
"""
Configuration verification script for Alpaca Trading Bot.
This script checks that all required environment variables are properly configured.
"""

import os
import sys
from typing import List, Tuple


def check_env_var(var_name: str, required: bool = True) -> Tuple[bool, str]:
    """Check if an environment variable is set"""
    value = os.getenv(var_name)
    if value:
        # Mask the value if it looks like a secret
        if 'KEY' in var_name or 'SECRET' in var_name:
            display_value = '*' * 8
        else:
            display_value = value
        return True, display_value
    else:
        if required:
            return False, 'NOT SET (REQUIRED)'
        else:
            return False, 'NOT SET (optional)'


def main():
    """Main verification function"""
    print("=" * 70)
    print("Alpaca Trading Bot - Configuration Verification")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    
    # Check required variables (with fallback support)
    print("REQUIRED ENVIRONMENT VARIABLES:")
    print("-" * 70)
    
    # Check API Key (supports both naming conventions)
    api_key_set = False
    api_key_new = os.getenv('APCA_API_KEY_ID')
    api_key_old = os.getenv('ALPACA_API_KEY')
    
    if api_key_new:
        print(f"  ✓ APCA_API_KEY_ID: ********")
        api_key_set = True
    elif api_key_old:
        print(f"  ✓ ALPACA_API_KEY: ******** (old naming, consider using APCA_API_KEY_ID)")
        warnings.append("Using old naming convention ALPACA_API_KEY")
        api_key_set = True
    else:
        print(f"  ✗ APCA_API_KEY_ID or ALPACA_API_KEY: NOT SET (REQUIRED)")
        errors.append("APCA_API_KEY_ID or ALPACA_API_KEY is required")
    
    # Check API Secret (supports both naming conventions)
    api_secret_set = False
    api_secret_new = os.getenv('APCA_API_SECRET_KEY')
    api_secret_old = os.getenv('ALPACA_SECRET')
    
    if api_secret_new:
        print(f"  ✓ APCA_API_SECRET_KEY: ********")
        api_secret_set = True
    elif api_secret_old:
        print(f"  ✓ ALPACA_SECRET: ******** (old naming, consider using APCA_API_SECRET_KEY)")
        warnings.append("Using old naming convention ALPACA_SECRET")
        api_secret_set = True
    else:
        print(f"  ✗ APCA_API_SECRET_KEY or ALPACA_SECRET: NOT SET (REQUIRED)")
        errors.append("APCA_API_SECRET_KEY or ALPACA_SECRET is required")
    
    print()
    print("OPTIONAL ENVIRONMENT VARIABLES:")
    print("-" * 70)
    
    # Check optional variables
    optional_vars = [
        ('TRADING_SYMBOLS', 'AAPL,GOOG,TSLA'),
        ('APCA_PAPER', 'true'),
        ('DRY_RUN', 'false'),
        ('CI_CD_ACTIONS', 'false'),
        ('RUN_ENV', 'local'),
        ('LOG_LEVEL', 'INFO'),
    ]
    
    for var_name, default in optional_vars:
        is_set, display_value = check_env_var(var_name, required=False)
        if is_set:
            print(f"  ✓ {var_name}: {display_value}")
        else:
            print(f"  - {var_name}: NOT SET (will use default: {default})")
    
    print()
    print("=" * 70)
    
    # Print warnings
    if warnings:
        print()
        print("WARNINGS:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    # Print errors
    if errors:
        print()
        print("ERRORS:")
        for error in errors:
            print(f"  ✗ {error}")
        print()
        print("Configuration is INVALID. Please set the required environment variables.")
        print("See CONFIGURATION.md for detailed setup instructions.")
        return 1
    
    # Test importing config
    print()
    print("CONFIGURATION TEST:")
    print("-" * 70)
    try:
        # Import config using standard import (works since script is in same dir as config.py)
        from config import Config
        
        config = Config()
        print("  ✓ Config class loaded successfully")
        print("  ✓ Configuration validation passed")
        print()
        print("Configuration details:")
        print(config)
    except Exception as e:
        print(f"  ✗ Failed to load configuration: {e}")
        return 1
    
    print()
    print("=" * 70)
    print("✓ Configuration is VALID and ready to use!")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
