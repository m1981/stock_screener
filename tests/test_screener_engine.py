import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from screener_engine import ScreenerEngine
from config import ScreenerConfig

class TestScreenerEngine:
    def setup_method(self):
        self.mock_config = Mock(spec=ScreenerConfig)
        self.mock_config.min_data_points = 20
        self.engine = ScreenerEngine(self.mock_config)
    
    @patch('screener_engine.ScreenerEngine.safe_download')
    def test_should_screen_stocks_successfully(self, mock_download):
        # Given
        stock_data = pd.Series([100, 101, 102, 99, 103] * 10, 
                              index=pd.date_range('2024-01-01', periods=50))
        benchmark_data = pd.Series([100, 100.5, 101, 100.2, 101.5] * 10,
                                  index=pd.date_range('2024-01-01', periods=50))
        
        mock_download.side_effect = [benchmark_data, stock_data]
        
        # When
        results = self.engine.screen_stocks(['AAPL'], 'SPY', 30)
        
        # Then
        assert not results.empty
        assert 'AAPL' in results.index
        assert 'Information Ratio' in results.columns
    
    @patch('screener_engine.ScreenerEngine.safe_download')
    def test_should_handle_missing_benchmark_data(self, mock_download):
        # Given
        mock_download.return_value = None
        
        # When/Then
        with pytest.raises(ValueError, match="Cannot fetch benchmark data"):
            self.engine.screen_stocks(['AAPL'], 'INVALID', 30)
    
    @patch('screener_engine.ScreenerEngine.safe_download')
    def test_should_skip_stocks_with_insufficient_data(self, mock_download):
        # Given
        benchmark_data = pd.Series([100] * 50, index=pd.date_range('2024-01-01', periods=50))
        insufficient_stock_data = pd.Series([100] * 10)  # Too little data
        
        mock_download.side_effect = [benchmark_data, insufficient_stock_data]
        
        # When
        results = self.engine.screen_stocks(['AAPL'], 'SPY', 30)
        
        # Then
        assert results.empty
    
    def test_should_calculate_metrics_with_sufficient_data(self):
        # Given
        stock_data = pd.Series([100, 101, 102, 99, 103] * 10,
                              index=pd.date_range('2024-01-01', periods=50))
        benchmark_data = pd.Series([100, 100.5, 101, 100.2, 101.5] * 10,
                                  index=pd.date_range('2024-01-01', periods=50))
        
        # When
        metrics = self.engine.calculate_metrics(stock_data, benchmark_data, 30)
        
        # Then
        assert metrics is not None
        assert 'Information Ratio' in metrics
        assert 'Sharpe Ratio' in metrics
        assert 'Beta' in metrics
    
    def test_should_return_none_for_insufficient_aligned_data(self):
        # Given
        stock_data = pd.Series([100, 101], index=pd.date_range('2024-01-01', periods=2))
        benchmark_data = pd.Series([100, 100.5], index=pd.date_range('2024-01-01', periods=2))
        
        # When
        metrics = self.engine.calculate_metrics(stock_data, benchmark_data, 30)
        
        # Then
        assert metrics is None
    
    @patch('screener_engine.yf.download')
    def test_should_handle_download_errors_gracefully(self, mock_yf_download):
        # Given
        mock_yf_download.side_effect = Exception("Network error")
        
        # When
        result = self.engine.safe_download('AAPL', datetime.now() - timedelta(days=30), datetime.now())
        
        # Then
        assert result is None