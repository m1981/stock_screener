import multiprocessing as mp
from typing import Dict, Tuple
import pandas as pd
from metrics import MetricsEngine

class ParallelProcessor:
    """Parallel processing for metric calculations as specified in docs/specification.md"""
    
    def parallel_metric_calculation(self, stock_data_dict: Dict[str, pd.Series], 
                                  benchmark_data: pd.Series, lookback: int) -> Dict[str, Dict]:
        """Use multiprocessing for metric calculations"""
        with mp.Pool(processes=mp.cpu_count()) as pool:
            args = [(ticker, data, benchmark_data, lookback) 
                    for ticker, data in stock_data_dict.items() if data is not None]
            results = pool.starmap(self.calculate_metrics_wrapper, args)
        
        return {ticker: result for (ticker, _), result in zip(stock_data_dict.items(), results) if result}
    
    @staticmethod
    def calculate_metrics_wrapper(args: Tuple) -> Dict:
        """Wrapper function for multiprocessing"""
        ticker, stock_data, benchmark_data, lookback = args
        
        try:
            # Calculate returns
            stock_returns = stock_data.pct_change().dropna()
            benchmark_returns = benchmark_data.pct_change().dropna()
            
            # Align data
            aligned_data = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
            if len(aligned_data) < lookback:
                return None
            
            # Use recent data
            recent_stock = aligned_data.iloc[:, 0].tail(lookback)
            recent_benchmark = aligned_data.iloc[:, 1].tail(lookback)
            
            # Calculate metrics
            metrics_engine = MetricsEngine()
            return metrics_engine.calculate_all_metrics(recent_stock, recent_benchmark)
            
        except Exception as e:
            print(f"Error calculating metrics for {ticker}: {e}")
            return None