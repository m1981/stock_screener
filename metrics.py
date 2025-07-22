from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class MetricCalculator(ABC):
    @abstractmethod
    def calculate(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        pass

class InformationRatio(MetricCalculator):
    def calculate(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        excess_returns = stock_returns - benchmark_returns
        if excess_returns.std() == 0:
            return np.nan
        return excess_returns.mean() / excess_returns.std()

class SharpeRatio(MetricCalculator):
    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate / 252
    
    def calculate(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        excess_returns = stock_returns - self.risk_free_rate
        if stock_returns.std() == 0:
            return np.nan
        return (excess_returns.mean() / stock_returns.std()) * np.sqrt(252)

class BetaCalculator(MetricCalculator):
    def calculate(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        covariance = np.cov(stock_returns, benchmark_returns)[0, 1]
        benchmark_variance = benchmark_returns.var()
        if benchmark_variance == 0:
            return np.nan
        return covariance / benchmark_variance

class AlphaCalculator(MetricCalculator):
    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate / 252
    
    def calculate(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        beta_calc = BetaCalculator()
        beta = beta_calc.calculate(stock_returns, benchmark_returns)
        
        expected_return = self.risk_free_rate + beta * (benchmark_returns.mean() - self.risk_free_rate)
        alpha = stock_returns.mean() - expected_return
        return alpha * 252  # Annualized

class MetricsEngine:
    def __init__(self):
        self.calculators = {
            'Information Ratio': InformationRatio(),
            'Sharpe Ratio': SharpeRatio(),
            'Beta': BetaCalculator(),
            'Alpha': AlphaCalculator(),
        }
    
    def calculate_all_metrics(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> dict:
        logger.debug(f"MetricsEngine: Starting calculation with {len(stock_returns)} stock returns and {len(benchmark_returns)} benchmark returns")
        results = {}
        
        for name, calculator in self.calculators.items():
            try:
                logger.debug(f"Calculating {name}")
                result = calculator.calculate(stock_returns, benchmark_returns)
                results[name] = result
                logger.debug(f"{name} calculated: {result}")
            except Exception as e:
                logger.error(f"Error calculating {name}: {e}", exc_info=True)
                results[name] = np.nan
        
        # Add additional metrics
        try:
            logger.debug("Calculating Relative Strength")
            results['Relative Strength'] = self._calculate_relative_strength(stock_returns, benchmark_returns)
            logger.debug(f"Relative Strength calculated: {results['Relative Strength']}")
        except Exception as e:
            logger.error(f"Error calculating Relative Strength: {e}", exc_info=True)
            results['Relative Strength'] = np.nan
        
        try:
            logger.debug("Calculating Total Return")
            results['Total Return'] = (1 + stock_returns).cumprod().iloc[-1] - 1
            logger.debug(f"Total Return calculated: {results['Total Return']}")
        except Exception as e:
            logger.error(f"Error calculating Total Return: {e}", exc_info=True)
            results['Total Return'] = np.nan
        
        logger.debug(f"All metrics calculated: {results}")
        return results
    
    def add_calculator(self, name: str, calculator: MetricCalculator) -> None:
        """Add a new metric calculator"""
        self.calculators[name] = calculator
    
    def _calculate_relative_strength(self, stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate relative strength ratio"""
        logger.debug("Calculating relative strength components")
        try:
            stock_cumulative = (1 + stock_returns).cumprod().iloc[-1]
            benchmark_cumulative = (1 + benchmark_returns).cumprod().iloc[-1]
            logger.debug(f"Stock cumulative: {stock_cumulative}, Benchmark cumulative: {benchmark_cumulative}")
            
            if benchmark_cumulative == 0:
                logger.warning("Benchmark cumulative return is zero")
                return np.nan
            
            result = stock_cumulative / benchmark_cumulative
            logger.debug(f"Relative strength result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in _calculate_relative_strength: {e}", exc_info=True)
            return np.nan
