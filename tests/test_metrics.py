import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from metrics import (
    MetricCalculator, InformationRatio, SharpeRatio, 
    BetaCalculator, AlphaCalculator, MetricsEngine
)

class TestInformationRatio:
    def test_should_calculate_information_ratio_with_valid_data(self):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.005, 0.015, -0.005, 0.025])
        calculator = InformationRatio()
        
        # When
        result = calculator.calculate(stock_returns, benchmark_returns)
        
        # Then
        assert isinstance(result, float)
        assert not np.isnan(result)
    
    def test_should_return_nan_when_excess_returns_have_zero_std(self):
        # Given
        stock_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        benchmark_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        calculator = InformationRatio()
        
        # When
        result = calculator.calculate(stock_returns, benchmark_returns)
        
        # Then
        assert np.isnan(result)

class TestSharpeRatio:
    def test_should_calculate_sharpe_ratio_with_default_risk_free_rate(self):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.005, 0.015, -0.005, 0.025])
        calculator = SharpeRatio()
        
        # When
        result = calculator.calculate(stock_returns, benchmark_returns)
        
        # Then
        assert isinstance(result, float)
        assert not np.isnan(result)
    
    def test_should_calculate_sharpe_ratio_with_custom_risk_free_rate(self):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.005, 0.015, -0.005, 0.025])
        calculator = SharpeRatio(risk_free_rate=0.05)
        
        # When
        result = calculator.calculate(stock_returns, benchmark_returns)
        
        # Then
        assert isinstance(result, float)
        assert calculator.risk_free_rate == 0.05 / 252

class TestBetaCalculator:
    def test_should_calculate_beta_with_valid_data(self):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.005, 0.015, -0.005, 0.025])
        calculator = BetaCalculator()
        
        # When
        result = calculator.calculate(stock_returns, benchmark_returns)
        
        # Then
        assert isinstance(result, float)
        assert not np.isnan(result)
    
    def test_should_return_nan_when_benchmark_variance_is_zero(self):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        calculator = BetaCalculator()
        
        # When
        result = calculator.calculate(stock_returns, benchmark_returns)
        
        # Then
        assert np.isnan(result)

class TestMetricsEngine:
    def test_should_calculate_all_metrics_successfully(self):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.005, 0.015, -0.005, 0.025])
        engine = MetricsEngine()
        
        # When
        results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        expected_metrics = ['Information Ratio', 'Sharpe Ratio', 'Beta', 'Alpha', 'Relative Strength', 'Total Return']
        assert all(metric in results for metric in expected_metrics)
        assert len(results) == len(expected_metrics)
    
    @patch('metrics.logger')
    def test_should_handle_calculation_errors_gracefully(self, mock_logger):
        # Given
        stock_returns = pd.Series([])
        benchmark_returns = pd.Series([])
        engine = MetricsEngine()
        
        # When
        results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        assert all(np.isnan(value) for value in results.values() if isinstance(value, float))
        mock_logger.error.assert_called()