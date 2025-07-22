import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

@pytest.fixture
def sample_stock_data():
    """Sample stock price data for testing"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.01)
    return pd.Series(prices, index=dates)

@pytest.fixture
def sample_benchmark_data():
    """Sample benchmark data for testing"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.005)
    return pd.Series(prices, index=dates)

@pytest.fixture
def sample_returns_data():
    """Sample returns data for testing"""
    return pd.Series([0.01, 0.02, -0.01, 0.03, -0.005, 0.015])

@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary"""
    return {
        'default_lookback': 60,
        'risk_free_rate': 0.03,
        'min_data_points': 20,
        'benchmarks': {
            'SP500': '^GSPC',
            'NASDAQ': '^IXIC'
        },
        'default_stocks': ['AAPL', 'MSFT', 'GOOGL']
    }