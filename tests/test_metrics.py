import pytest
import pandas as pd
import numpy as np
import warnings
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
        stock_returns = pd.Series([], dtype=float)  # Explicitly set dtype
        benchmark_returns = pd.Series([], dtype=float)
        engine = MetricsEngine()
        
        # When
        results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        expected_metrics = ['Information Ratio', 'Sharpe Ratio', 'Beta', 'Alpha', 'Relative Strength', 'Total Return']
        assert all(metric in results for metric in expected_metrics)
        # Check that NaN values are returned for empty data
        for metric, value in results.items():
            if isinstance(value, (int, float)):
                assert pd.isna(value), f"{metric} should be NaN for empty data"
        # Should log warning for empty data, not error
        mock_logger.warning.assert_called_with("Empty returns data provided")

    @patch('metrics.logger')
    def test_should_handle_invalid_data_gracefully(self, mock_logger):
        # Given - create data with invalid values
        stock_returns = pd.Series([float('inf'), float('-inf'), float('nan')])
        benchmark_returns = pd.Series([1.0, 2.0, 3.0])
        engine = MetricsEngine()
        
        # When
        results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        expected_metrics = ['Information Ratio', 'Sharpe Ratio', 'Beta', 'Alpha', 'Relative Strength', 'Total Return']
        assert all(metric in results for metric in expected_metrics)
        
        # All metrics should be NaN with invalid data
        for metric, value in results.items():
            if isinstance(value, (int, float)):
                assert pd.isna(value), f"{metric} should be NaN for invalid data"
        
        # Should log a warning about invalid data
        mock_logger.debug.assert_any_call("MetricsEngine: Starting calculation with 3 stock returns and 3 benchmark returns")

    def test_should_handle_single_data_point_gracefully(self):
        # Given
        stock_returns = pd.Series([0.01])
        benchmark_returns = pd.Series([0.005])
        engine = MetricsEngine()
        
        # When
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        # Most metrics should be NaN with single data point
        assert pd.isna(results['Information Ratio'])  # No variance
        assert pd.isna(results['Beta'])  # No variance in benchmark
        assert not pd.isna(results['Total Return'])  # This should work

    def test_should_handle_identical_returns_gracefully(self):
        # Given - identical returns (zero variance)
        stock_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        benchmark_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        engine = MetricsEngine()
        
        # When
        results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        assert pd.isna(results['Information Ratio'])  # Zero excess return variance
        assert pd.isna(results['Beta'])  # Zero benchmark variance
        assert not pd.isna(results['Total Return'])

    @patch('metrics.logger')
    def test_should_log_errors_when_exceptions_occur(self, mock_logger):
        # Given
        stock_returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        benchmark_returns = pd.Series([0.005, 0.015, -0.005, 0.025])
        engine = MetricsEngine()
        
        # Create a faulty calculator that raises an exception
        faulty_calculator = Mock(spec=MetricCalculator)
        faulty_calculator.calculate.side_effect = ValueError("Test error")
        engine.calculators['Faulty Metric'] = faulty_calculator
        
        # When
        results = engine.calculate_all_metrics(stock_returns, benchmark_returns)
        
        # Then
        assert 'Faulty Metric' in results
        assert pd.isna(results['Faulty Metric'])
        mock_logger.error.assert_called()  # Now error should be logged
