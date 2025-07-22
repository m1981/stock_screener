import pytest
import tempfile
import yaml
from pathlib import Path
from config import ScreenerConfig

class TestScreenerConfig:
    def test_should_load_config_from_yaml_file(self):
        # Given
        config_data = {
            'default_lookback': 60,
            'risk_free_rate': 0.04,
            'min_data_points': 30,
            'benchmarks': {'SP500': '^GSPC'},
            'default_stocks': ['AAPL', 'MSFT']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        # When
        config = ScreenerConfig.from_yaml(temp_path)
        
        # Then
        assert config.default_lookback == 60
        assert config.risk_free_rate == 0.04
        assert config.min_data_points == 30
        assert config.benchmarks == {'SP500': '^GSPC'}
        assert config.default_stocks == ['AAPL', 'MSFT']
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_should_use_default_values_for_missing_config(self):
        # Given
        minimal_config = {'default_lookback': 90}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(minimal_config, f)
            temp_path = f.name
        
        # When
        config = ScreenerConfig.from_yaml(temp_path)
        
        # Then
        assert config.default_lookback == 90
        assert config.risk_free_rate == 0.03  # Default value
        assert config.min_data_points == 50   # Default value
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_should_raise_error_for_invalid_yaml_file(self):
        # Given
        invalid_path = "nonexistent_file.yaml"
        
        # When/Then
        with pytest.raises(FileNotFoundError):
            ScreenerConfig.from_yaml(invalid_path)