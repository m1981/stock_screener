import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timedelta
from data_manager import DataManager

class TestDataManager:
    def setup_method(self):
        self.data_manager = DataManager(cache_dir="test_cache", min_data_points=5)
    
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
        mock_data = pd.DataFrame({'Adj Close': [100, 101, 102, 99, 103, 104, 98, 105, 106, 107, 108, 109]})
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert isinstance(result, pd.Series)
        assert len(result) == 12
        assert result.iloc[0] == 100
        assert result.iloc[-1] == 109

    @patch('data_manager.yf.download')
    def test_should_extract_price_series_from_multiindex_columns(self, mock_download):
        # Given
        columns = pd.MultiIndex.from_tuples([('Close', 'AAPL'), ('Volume', 'AAPL')])
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): [100, 101, 102, 99, 103, 104, 98, 105, 106, 107, 108, 109],
            ('Volume', 'AAPL'): [1000] * 12
        }, columns=columns)
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert isinstance(result, pd.Series)
        assert len(result) == 12
        assert result.iloc[0] == 100
        assert result.iloc[-1] == 109

    @patch('data_manager.yf.download')
    def test_should_extract_price_series_from_multiindex_multiple_tickers(self, mock_download):
        # Given
        columns = pd.MultiIndex.from_tuples([
            ('Close', 'AAPL'), ('Close', 'MSFT'), ('Volume', 'AAPL'), ('Volume', 'MSFT')
        ])
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): [100, 101, 102, 99, 103, 104, 98, 105, 106, 107, 108, 109],
            ('Close', 'MSFT'): [200, 201, 202, 199, 203, 204, 198, 205, 206, 207, 208, 209],
            ('Volume', 'AAPL'): [1000] * 12,
            ('Volume', 'MSFT'): [2000] * 12
        }, columns=columns)
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert isinstance(result, pd.Series)
        assert len(result) == 12
        assert result.iloc[0] == 100  # Should get AAPL data (first ticker)

    @patch('data_manager.yf.download')
    def test_should_handle_insufficient_data_gracefully(self, mock_download):
        # Given
        mock_data = pd.DataFrame({'Adj Close': [100, 101, 102]})  # Only 3 points
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert result is None

    @patch('data_manager.yf.download')
    def test_should_handle_empty_data(self, mock_download):
        # Given
        mock_data = pd.DataFrame()
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert result is None

    @patch('data_manager.yf.download')
    def test_should_handle_data_with_nans(self, mock_download):
        # Given
        import numpy as np
        mock_data = pd.DataFrame({
            'Adj Close': [100, 101, np.nan, 99, 103, 104, 98, 105, 106, 107, 108, 109]
        })
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert isinstance(result, pd.Series)
        assert len(result) == 11  # NaN should be dropped
        assert not result.isna().any()
    
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
        with pytest.raises(ValueError, match="Start date .* must be before end date"):
            self.data_manager.get_stock_data('AAPL', invalid_start, invalid_end)

    def test_should_validate_equal_dates(self):
        # Given
        same_date = date(2024, 1, 1)

        # When/Then
        with pytest.raises(ValueError, match="Start date .* must be before end date"):
            self.data_manager.get_stock_data('AAPL', same_date, same_date)

    @patch('data_manager.yf.download')
    def test_should_handle_close_column_not_available(self, mock_download):
        # Given - DataFrame without Close column
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102, 99, 103, 104, 98, 105, 106, 107, 108, 109],
            'High': [101, 102, 103, 100, 104, 105, 99, 106, 107, 108, 109, 110]
        })
        mock_download.return_value = mock_data

        # When
        result = self.data_manager._fetch_fresh_data('AAPL', date(2024, 1, 1), date(2024, 1, 31))

        # Then
        assert isinstance(result, pd.Series)
        assert len(result) == 12
        assert result.iloc[0] == 100  # Should use first column (Open)
