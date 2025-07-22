from typing import Tuple, List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Data validation as specified in docs/specification.md"""
    
    def validate_stock_data(self, data: pd.Series, ticker: str) -> Tuple[bool, str]:
        """Comprehensive data validation"""
        logger.debug(f"Validating data for {ticker}")
        
        if data is None:
            logger.debug(f"Data is None for {ticker}")
            return False, f"No data for {ticker}"
        
        # Ensure we have a Series - convert DataFrame to Series if needed
        if isinstance(data, pd.DataFrame):
            if data.empty:
                logger.debug(f"DataFrame is empty for {ticker}")
                return False, f"No data for {ticker}"
            data = data.iloc[:, 0]  # Take first column
        elif data.empty:
            logger.debug(f"Data is empty for {ticker}")
            return False, f"No data for {ticker}"
        
        logger.debug(f"Data length for {ticker}: {len(data)}")
        if len(data) < 20:
            logger.debug(f"Insufficient data points for {ticker}: {len(data)}")
            return False, f"Insufficient data points: {len(data)}"
        
        # Check for excessive missing values
        missing_count = int(data.isnull().sum())
        missing_pct = missing_count / len(data)
        logger.debug(f"Missing values for {ticker}: {missing_count}/{len(data)} ({missing_pct:.1%})")
        
        if missing_pct > 0.1:
            logger.debug(f"Too many missing values for {ticker}: {missing_pct:.1%}")
            return False, f"Too many missing values: {missing_pct:.1%}"
        
        # Check data quality
        logger.debug(f"Checking data quality for {ticker}")
        if not self.check_data_quality(data):
            logger.debug(f"Poor data quality detected for {ticker}")
            return False, "Poor data quality detected"
        
        # Check for anomalies
        logger.debug(f"Detecting anomalies for {ticker}")
        anomalies = self.detect_anomalies(data)
        logger.debug(f"Anomalies detected for {ticker}: {anomalies}")
        
        if len(anomalies) > 3:
            logger.debug(f"Multiple anomalies detected for {ticker}: {anomalies}")
            return False, f"Multiple anomalies detected: {', '.join(anomalies[:3])}"
        
        logger.debug(f"Validation passed for {ticker}")
        return True, "Valid"
    
    def sanitize_ticker(self, ticker: str) -> str:
        """Clean and validate ticker symbols"""
        return ticker.strip().upper().replace(" ", "")
    
    def check_data_quality(self, data: pd.Series) -> bool:
        """Check overall data quality"""
        # Check if all values are null
        if data.isnull().all():
            return False
        
        # Check for reasonable price ranges
        if (data <= 0).any():
            return False
        
        return True
    
    def detect_anomalies(self, data: pd.Series) -> List[str]:
        """Detect data anomalies"""
        anomalies = []
        
        # Check for extreme price movements
        returns = data.pct_change().dropna()
        if len(returns) > 0:
            extreme_returns = (returns.abs() > 0.5).sum()
            if extreme_returns > len(returns) * 0.01:
                anomalies.append("Extreme price movements")
        
        # Check for flat periods
        flat_periods = (data.diff() == 0).sum()
        if flat_periods > len(data) * 0.1:
            anomalies.append("Extended flat periods")
        
        return anomalies
