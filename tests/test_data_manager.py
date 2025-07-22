import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timedelta
from data_manager import DataManager

class TestDataManager:
    def setup_method(self):
        self.data_manager = DataManager()
    
    @patch('data_manager.DataManager._get_cached_data')
    @patch('data_manager.DataManager._fetch_fresh_data')
    def test_should_return_cached_data_when_available(self, mock_fetch, mock_cache):
        # Given
        cached_data = pd.Series([100, 101, 102])
        mock_cache.return_value = cached_data
        
        # When
        result = self.data_manager.get_stock_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        # Then
        assert result.equals(cached_data)
        mock_fetch.assert_not_called()
    
    @patch('data_manager.DataManager._get_cached_data')
    @patch('data_manager.DataManager._fetch_fresh_data')
    @patch('data_manager.DataManager._cache_data')
    def test_should_fetch_fresh_data_when_cache_miss(self, mock_cache_store, mock_fetch, mock_cache_get):
        # Given
        mock_cache_get.return_value = None
        fresh_data = pd.Series([100, 101, 102])
        mock_fetch.return_value = fresh_data
        
        # When
        result = self.data_manager.get_stock_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        # Then
        assert result.equals(fresh_data)
        mock_fetch.assert_called_once()
        mock_cache_store.assert_called_once()
    
    @patch('data_manager.yf.download')
    def test_should_extract_price_series_from_single_column(self, mock_download):
        # Given
        mock_data = pd.DataFrame({'Adj Close': [100, 101, 102]})
        mock_download.return_value = mock_data
        
        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        # Then
        assert isinstance(result, pd.Series)
        assert len(result) == 3
    
    @patch('data_manager.yf.download')
    def test_should_handle_empty_download_response(self, mock_download):
        # Given
        mock_download.return_value = pd.DataFrame()
        
        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        # Then
        assert result is None
    
    def test_should_validate_date_parameters(self):
        # Given
        invalid_start = date(2024, 2, 1)
        invalid_end = date(2024, 1, 1)  # End before start
        
        # When/Then
        with pytest.raises(ValueError):
            self.data_manager.get_stock_data('AAPL', invalid_start, invalid_end)