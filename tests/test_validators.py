import pytest
import pandas as pd
import numpy as np
from validators import DataValidator

class TestDataValidator:
    def setup_method(self):
        self.validator = DataValidator()
    
    def test_should_validate_good_stock_data(self):
        # Given
        good_data = pd.Series([100, 101, 102, 99, 103] * 5)  # 25 points
        
        # When
        is_valid, message = self.validator.validate_stock_data(good_data, "AAPL")
        
        # Then
        assert is_valid is True
        assert message == "Valid"
    
    def test_should_reject_insufficient_data_points(self):
        # Given
        insufficient_data = pd.Series([100, 101, 102])  # Only 3 points
        
        # When
        is_valid, message = self.validator.validate_stock_data(insufficient_data, "AAPL")
        
        # Then
        assert is_valid is False
        assert "Insufficient data points" in message
    
    def test_should_reject_excessive_missing_values(self):
        # Given
        data_with_nulls = pd.Series([100, np.nan, np.nan, np.nan, np.nan] * 5)  # 80% nulls
        
        # When
        is_valid, message = self.validator.validate_stock_data(data_with_nulls, "AAPL")
        
        # Then
        assert is_valid is False
        assert "Too many missing values" in message
    
    def test_should_handle_dataframe_input(self):
        # Given
        df_data = pd.DataFrame({'Close': [100, 101, 102, 99, 103] * 5})
        
        # When
        is_valid, message = self.validator.validate_stock_data(df_data, "AAPL")
        
        # Then
        assert is_valid is True
        assert message == "Valid"
    
    def test_should_sanitize_ticker_symbols(self):
        # Given
        dirty_tickers = [" aapl ", "MSFT", "nvda ", " GOOGL"]
        
        # When
        clean_tickers = [self.validator.sanitize_ticker(t) for t in dirty_tickers]
        
        # Then
        assert clean_tickers == ["AAPL", "MSFT", "NVDA", "GOOGL"]
    
    def test_should_detect_poor_data_quality(self):
        # Given
        bad_data = pd.Series([0, -1, 100, 101])  # Contains zero and negative
        
        # When
        quality_ok = self.validator.check_data_quality(bad_data)
        
        # Then
        assert quality_ok is False
    
    def test_should_detect_extreme_price_movements(self):
        # Given
        volatile_data = pd.Series([100, 200, 50, 150, 25])  # Extreme movements
        
        # When
        anomalies = self.validator.detect_anomalies(volatile_data)
        
        # Then
        assert "Extreme price movements" in anomalies
    
    def test_should_detect_flat_periods(self):
        # Given
        flat_data = pd.Series([100] * 15 + [101, 102])  # Mostly flat
        
        # When
        anomalies = self.validator.detect_anomalies(flat_data)
        
        # Then
        assert "Extended flat periods" in anomalies