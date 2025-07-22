from typing import List, Dict
import pandas as pd
from datetime import datetime, timedelta
from data_manager import DataManager
from metrics import MetricsEngine
from validators import DataValidator
from config import ScreenerConfig
from async_fetcher import AsyncDataFetcher
import asyncio
import logging

logger = logging.getLogger(__name__)

class ScreenerEngine:
    """Main screener engine as specified in docs/specification.md"""
    
    def __init__(self, config: ScreenerConfig):
        self.config = config
        self.data_manager = DataManager()
        self.metrics_engine = MetricsEngine()
        self.validator = DataValidator()
        self.async_fetcher = AsyncDataFetcher()
    
    def screen_stocks(self, tickers: List[str], benchmark: str, lookback: int) -> pd.DataFrame:
        """Run screening analysis on stocks"""
        logger.info(f"Starting screening for {len(tickers)} tickers with benchmark {benchmark}")
        results = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback + 100)  # Extra buffer
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Get benchmark data
        logger.info(f"Fetching benchmark data for {benchmark}")
        benchmark_data = self.safe_download(benchmark, start_date, end_date)
        if benchmark_data is None:
            raise ValueError(f"Cannot fetch benchmark data for {benchmark}")
        logger.info(f"Benchmark data fetched: {len(benchmark_data)} points")
        
        # Process each ticker
        for ticker in tickers:
            try:
                logger.info(f"Processing ticker: {ticker}")
                
                # Sanitize ticker
                clean_ticker = self.validator.sanitize_ticker(ticker)
                logger.debug(f"Sanitized ticker: {clean_ticker}")
                
                # Get stock data
                logger.info(f"Fetching stock data for {clean_ticker}")
                stock_data = self.safe_download(clean_ticker, start_date, end_date)
                logger.info(f"Stock data fetched for {clean_ticker}: {len(stock_data) if stock_data is not None else 0} points")
                
                # Validate data
                logger.info(f"Validating data for {clean_ticker}")
                is_valid, message = self.validator.validate_stock_data(stock_data, clean_ticker)
                logger.info(f"Validation result for {clean_ticker}: {is_valid}, {message}")
                
                if not is_valid:
                    logger.warning(f"Validation failed for {clean_ticker}: {message}")
                    continue
                
                # Calculate metrics
                logger.info(f"Calculating metrics for {clean_ticker}")
                metrics = self.calculate_metrics(stock_data, benchmark_data, lookback)
                logger.info(f"Metrics calculated for {clean_ticker}: {metrics is not None}")
                
                if metrics:
                    metrics['Ticker'] = clean_ticker
                    results.append(metrics)
                    logger.info(f"Added results for {clean_ticker}")
                else:
                    logger.warning(f"No metrics calculated for {clean_ticker}")
                    
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}", exc_info=True)
                continue
        
        logger.info(f"Screening complete. {len(results)} stocks processed successfully")
        
        if results:
            df = pd.DataFrame(results)
            df.set_index('Ticker', inplace=True)
            return df.sort_values('Information Ratio', ascending=False)
        
        return pd.DataFrame()
    
    def calculate_metrics(self, stock_data: pd.Series, benchmark_data: pd.Series, lookback: int) -> Dict:
        """Calculate all metrics for a stock"""
        logger.debug(f"Starting metrics calculation with lookback: {lookback}")
        
        if stock_data is None:
            logger.warning("Stock data is None")
            return None
        
        if benchmark_data is None:
            logger.warning("Benchmark data is None")
            return None
        
        if stock_data.empty:
            logger.warning("Stock data is empty")
            return None
            
        if benchmark_data.empty:
            logger.warning("Benchmark data is empty")
            return None
        
        logger.debug(f"Stock data length: {len(stock_data)}, Benchmark data length: {len(benchmark_data)}")
        
        # Calculate returns
        logger.debug("Calculating stock returns")
        stock_returns = stock_data.pct_change().dropna()
        logger.debug(f"Stock returns calculated: {len(stock_returns)} points")
        
        logger.debug("Calculating benchmark returns")
        benchmark_returns = benchmark_data.pct_change().dropna()
        logger.debug(f"Benchmark returns calculated: {len(benchmark_returns)} points")
        
        # Align data
        logger.debug("Aligning data")
        aligned_data = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
        logger.debug(f"Aligned data length: {len(aligned_data)}")
        
        if len(aligned_data) < lookback:
            logger.warning(f"Insufficient aligned data: {len(aligned_data)} < {lookback}")
            return None
        
        # Use recent data for calculations
        logger.debug("Extracting recent data")
        recent_stock = aligned_data.iloc[:, 0].tail(lookback)
        recent_benchmark = aligned_data.iloc[:, 1].tail(lookback)
        logger.debug(f"Recent stock data: {len(recent_stock)}, Recent benchmark data: {len(recent_benchmark)}")
        
        # Calculate all metrics using MetricsEngine
        logger.debug("Calling MetricsEngine.calculate_all_metrics")
        try:
            metrics = self.metrics_engine.calculate_all_metrics(recent_stock, recent_benchmark)
            logger.debug(f"Metrics calculated successfully: {list(metrics.keys()) if metrics else None}")
            return metrics
        except Exception as e:
            logger.error(f"Error in MetricsEngine.calculate_all_metrics: {e}", exc_info=True)
            return None
    
    def safe_download(self, ticker: str, start_date: datetime, end_date: datetime) -> pd.Series:
        """Download stock data safely using DataManager"""
        return self.data_manager.get_stock_data(ticker, start_date, end_date)