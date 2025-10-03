
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration loading from environment-specific .env files"""
    
    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from environment-specific .env file"""
        project_root = Path(__file__).parent.parent
        env_file = project_root / f".env.{self.environment}"
        
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        
        # Load environment variables from file
        with open(env_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Convert string values to appropriate types
                    self.config[key] = self._convert_value(value)
                    # Also set as environment variable
                    os.environ[key] = value
    
    def _convert_value(self, value: str) -> Any:
        """Convert string values to appropriate Python types"""
        value = value.strip()
        
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        if value.isdigit():
            return int(value)
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string if no conversion applies
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser-specific configuration"""
        return {
            'headless': self.get('HEADLESS', False),
            'slow_mo': self.get('SLOW_MO', 0),
            'viewport': {
                'width': self.get('VIEWPORT_WIDTH', 1920),
                'height': self.get('VIEWPORT_HEIGHT', 1080)
            },
            'record_video_dir': 'videos/' if self.get('VIDEO_RECORDING', False) else None,
            'record_har_path': 'har/' if self.get('TRACE_ON_FAILURE', False) else None
        }
    
    def get_timeout_config(self) -> Dict[str, int]:
        """Get timeout-related configuration"""
        return {
            'default_timeout': self.get('TIMEOUT', 30000),
            'element_timeout': self.get('ELEMENT_TIMEOUT', 10000),
            'page_load_timeout': self.get('PAGE_LOAD_TIMEOUT', 30000),
            'network_timeout': self.get('NETWORK_TIMEOUT', 30000)
        }
    
    def get_test_config(self) -> Dict[str, Any]:
        """Get test execution configuration"""
        return {
            'parallel_workers': self.get('PARALLEL_WORKERS', 1),
            'retry_count': self.get('RETRY_COUNT', 1),
            'screenshot_on_failure': self.get('SCREENSHOT_ON_FAILURE', True),
            'trace_on_failure': self.get('TRACE_ON_FAILURE', False),
            'log_level': self.get('LOG_LEVEL', 'INFO'),
            'report_format': self.get('REPORT_FORMAT', 'html')
        }
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment from ENV variable or default to 'dev'"""
        return os.environ.get('ENV', 'dev')


# Global configuration instance
config_manager = None


def get_config(environment: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance"""
    global config_manager
    
    if config_manager is None or (environment and environment != config_manager.environment):
        env = environment or ConfigManager.get_environment()
        config_manager = ConfigManager(env)
    
    return config_manager

