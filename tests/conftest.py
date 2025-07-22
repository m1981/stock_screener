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
    """Sample stock price data for testing with sufficient data points"""
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    prices = 100 + np.cumsum(np.random.randn(50) * 0.01)
    return pd.Series(prices, index=dates)

@pytest.fixture
def sample_benchmark_data():
    """Sample benchmark data for testing with sufficient data points"""
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    prices = 100 + np.cumsum(np.random.randn(50) * 0.005)
    return pd.Series(prices, index=dates)

@pytest.fixture
def sample_returns_data():
    """Sample returns data for testing"""
    return pd.Series([0.01, 0.02, -0.01, 0.03, -0.005, 0.015, 0.008, -0.012, 0.025, 0.001])

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

@pytest.fixture
def sufficient_stock_data():
    """Stock data with enough points to pass validation"""
    return pd.DataFrame({
        'Adj Close': [100 + i + np.random.randn() * 0.5 for i in range(25)]
    })

@pytest.fixture
def multiindex_stock_data():
    """Stock data with MultiIndex columns"""
    columns = pd.MultiIndex.from_tuples([
        ('Close', 'AAPL'), ('Volume', 'AAPL'), ('Open', 'AAPL')
    ])
    return pd.DataFrame({
        ('Close', 'AAPL'): [100 + i for i in range(25)],
        ('Volume', 'AAPL'): [1000000] * 25,
        ('Open', 'AAPL'): [99 + i for i in range(25)]
    }, columns=columns)