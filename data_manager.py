import sqlite3
from functools import lru_cache
import pickle
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import os
import logging

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, cache_dir="cache", min_data_points=10):
        self.cache_dir = cache_dir
        self.db_path = f"{cache_dir}/stock_data.db"
        self.min_data_points = min_data_points
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database and cache directory"""
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stock_cache (
                    ticker TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    data BLOB,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ticker, start_date, end_date)
                )
            ''')
            conn.commit()
    
    @lru_cache(maxsize=100)
    def get_stock_data(self, ticker, start_date, end_date):
        """Check cache first, then fetch if needed"""
        # Validate date parameters
        if start_date >= end_date:
            raise ValueError(f"Start date ({start_date}) must be before end date ({end_date})")
        
        cached_data = self._get_cached_data(ticker, start_date, end_date)
        if cached_data is not None:
            return cached_data
        
        # Fetch and cache new data
        data = self._fetch_fresh_data(ticker, start_date, end_date)
        if data is not None:
            self._cache_data(ticker, data, start_date, end_date)
        return data
    
    def _get_cached_data(self, ticker, start_date, end_date):
        """Retrieve cached data from SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT data FROM stock_cache WHERE ticker=? AND start_date=? AND end_date=?',
                    (ticker, str(start_date), str(end_date))
                )
                row = cursor.fetchone()
                if row:
                    return pickle.loads(row[0])
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {ticker}: {e}")
        return None
    
    def _fetch_fresh_data(self, ticker, start_date, end_date):
        """Fetch fresh data from Yahoo Finance"""
        try:
            data = yf.download(
                ticker, 
                start=start_date, 
                end=end_date, 
                progress=False,
                auto_adjust=True
            )
            
            if data.empty:
                logger.warning(f"No data returned for {ticker}")
                return None
            
            # Extract price series (handle both single and multi-ticker downloads)
            if isinstance(data.columns, pd.MultiIndex):
                if 'Close' in data.columns.get_level_values(0):
                    # Handle multiple tickers or single ticker with MultiIndex
                    close_data = data['Close']
                    if isinstance(close_data, pd.DataFrame):
                        price_series = close_data.iloc[:, 0]  # First ticker
                    else:
                        price_series = close_data  # Single ticker
                else:
                    price_series = data.iloc[:, 0]
            else:
                price_series = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
            
            # Clean the data
            price_series = price_series.dropna()
            
            if len(price_series) < self.min_data_points:
                logger.warning(f"Insufficient data for {ticker}: {len(price_series)} points")
                return None
            
            logger.info(f"Successfully fetched {len(price_series)} data points for {ticker}")
            return price_series
        
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def _cache_data(self, ticker, data, start_date, end_date):
        """Cache data in SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT OR REPLACE INTO stock_cache (ticker, start_date, end_date, data) VALUES (?, ?, ?, ?)',
                    (ticker, str(start_date), str(end_date), pickle.dumps(data))
                )
                conn.commit()
                logger.debug(f"Cached data for {ticker}")
        except Exception as e:
            logger.warning(f"Failed to cache data for {ticker}: {e}")
