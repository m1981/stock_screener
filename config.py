from dataclasses import dataclass
from typing import Dict, List
import yaml

@dataclass
class ScreenerConfig:
    default_lookback: int = 60
    risk_free_rate: float = 0.03
    min_data_points: int = 50
    benchmarks: Dict[str, str] = None
    default_stocks: List[str] = None
    
    @classmethod
    def from_yaml(cls, path: str):
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        return cls(**config)