import time
import traceback
import json
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from pathlib import Path
from utils import logger

log = logger.customLogger()


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 delay_between_attempts: float = 1.0,
                 exponential_backoff: bool = True,
                 retry_on_exceptions: Optional[List[type]] = None,
                 retry_conditions: Optional[List[Callable]] = None):
        self.max_attempts = max_attempts
        self.delay_between_attempts = delay_between_attempts
        self.exponential_backoff = exponential_backoff
        self.retry_on_exceptions = retry_on_exceptions or [Exception]
        self.retry_conditions = retry_conditions or []


class RetryResult:
    """Result of retry operation"""
    
    def __init__(self):
        self.success = False
        self.attempts = 0
        self.total_duration = 0.0
        self.last_exception = None
        self.attempt_details = []
    
    def add_attempt(self, attempt_num: int, success: bool, duration: float, exception: Optional[Exception] = None):
        """Add attempt details"""
        self.attempt_details.append({
            'attempt': attempt_num,
            'success': success,
            'duration': duration,
            'exception': str(exception) if exception else None
        })
        
        if success:
            self.success = True
        else:
            self.last_exception = exception


class TestRetryHandler:
    """Handles test retry logic with intelligent failure analysis"""
    
    def __init__(self, default_config: Optional[RetryConfig] = None):
        self.default_config = default_config or RetryConfig()
        self.retry_statistics = {}
    
    def retry_on_failure(self, config: Optional[RetryConfig] = None):
        """Decorator for retrying functions on failure"""
        retry_config = config or self.default_config
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_with_retry(func, retry_config, *args, **kwargs)
            return wrapper
        return decorator
    
    def execute_with_retry(self, func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        result = RetryResult()
        
        for attempt in range(1, config.max_attempts + 1):
            start_time = time.time()
            
            try:
                log.info(f"Attempt {attempt}/{config.max_attempts} for {func.__name__}")
                
                # Execute the function
                return_value = func(*args, **kwargs)
                
                duration = time.time() - start_time
                result.add_attempt(attempt, True, duration)
                result.attempts = attempt
                result.total_duration += duration
                
                log.info(f"Function {func.__name__} succeeded on attempt {attempt}")
                self._update_statistics(func.__name__, attempt, True)
                
                return return_value
                
            except Exception as e:
                duration = time.time() - start_time
                result.add_attempt(attempt, False, duration, e)
                result.attempts = attempt
                result.total_duration += duration
                
                # Check if we should retry this exception
                should_retry = self._should_retry_exception(e, config)
                
                if attempt == config.max_attempts or not should_retry:
                    log.error(f"Function {func.__name__} failed after {attempt} attempts")
                    self._update_statistics(func.__name__, attempt, False)
                    raise e
                
                log.warning(f"Function {func.__name__} failed on attempt {attempt}: {str(e)}")
                
                # Wait before next attempt
                if attempt < config.max_attempts:
                    delay = self._calculate_delay(attempt, config)
                    log.info(f"Waiting {delay:.2f}s before next attempt")
                    time.sleep(delay)
    
    def _should_retry_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """Determine if exception should trigger a retry"""
        # Check exception types
        for exc_type in config.retry_on_exceptions:
            if isinstance(exception, exc_type):
                break
        else:
            return False
        
        # Check custom retry conditions
        for condition in config.retry_conditions:
            if not condition(exception):
                return False
        
        return True
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay before next attempt"""
        if config.exponential_backoff:
            return config.delay_between_attempts * (2 ** (attempt - 1))
        else:
            return config.delay_between_attempts
    
    def _update_statistics(self, func_name: str, attempts: int, success: bool):
        """Update retry statistics"""
        if func_name not in self.retry_statistics:
            self.retry_statistics[func_name] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_attempts': 0,
                'avg_attempts_to_success': 0
            }
        
        stats = self.retry_statistics[func_name]
        stats['total_executions'] += 1
        stats['total_attempts'] += attempts
        
        if success:
            stats['successful_executions'] += 1
            # Update average attempts to success
            stats['avg_attempts_to_success'] = (
                stats['total_attempts'] / stats['successful_executions']
            )
        else:
            stats['failed_executions'] += 1
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return self.retry_statistics.copy()
    
    def reset_statistics(self):
        """Reset retry statistics"""
        self.retry_statistics.clear()


class ScenarioRetryHandler:
    """Handles retry logic specifically for BDD scenarios"""
    
    def __init__(self, retry_handler: TestRetryHandler):
        self.retry_handler = retry_handler
        self.scenario_configs = {}
    
    def set_scenario_retry_config(self, scenario_name: str, config: RetryConfig):
        """Set retry configuration for specific scenario"""
        self.scenario_configs[scenario_name] = config
    
    def get_scenario_retry_config(self, scenario_name: str) -> RetryConfig:
        """Get retry configuration for scenario"""
        return self.scenario_configs.get(scenario_name, self.retry_handler.default_config)
    
    def should_retry_scenario(self, scenario_name: str, exception: Exception) -> bool:
        """Determine if scenario should be retried"""
        config = self.get_scenario_retry_config(scenario_name)
        return self.retry_handler._should_retry_exception(exception, config)


class FlakynessDetector:
    """Detects flaky tests based on retry patterns"""
    
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold  # Flakiness threshold (30% failure rate)
        self.test_history = {}
        self.persistence_file = Path('reports/flakiness_history.json')
        self._load_persistent_history()
    
    def record_test_result(self, test_name: str, success: bool, attempts: int):
        """Record test execution result"""
        if test_name not in self.test_history:
            self.test_history[test_name] = {
                'executions': [],
                'total_runs': 0,
                'failed_runs': 0,
                'retry_runs': 0
            }
        
        history = self.test_history[test_name]
        history['executions'].append({
            'success': success,
            'attempts': attempts,
            'timestamp': time.time()
        })
        
        history['total_runs'] += 1
        if not success:
            history['failed_runs'] += 1
        if attempts > 1:
            history['retry_runs'] += 1
        
        # Save to persistent storage after each update
        self._save_persistent_history()
    
    def analyze_flakiness(self, test_name: str) -> Dict[str, Any]:
        """Analyze flakiness for a specific test"""
        if test_name not in self.test_history:
            return {'flaky': False, 'confidence': 0.0, 'reason': 'No execution history'}
        
        history = self.test_history[test_name]
        
        if history['total_runs'] < 1:
            return {'flaky': False, 'confidence': 0.0, 'reason': 'Insufficient data'}
        
        failure_rate = history['failed_runs'] / history['total_runs']
        retry_rate = history['retry_runs'] / history['total_runs']
        
        # Calculate flakiness score
        flakiness_score = (failure_rate * 0.7) + (retry_rate * 0.3)
        print(f"Flakiness score: {flakiness_score}")
        
        is_flaky = flakiness_score >= self.threshold
        
        return {
            'flaky': is_flaky,
            'confidence': flakiness_score,
            'failure_rate': failure_rate,
            'retry_rate': retry_rate,
            'total_runs': history['total_runs'],
            'failed_runs': history['failed_runs'],
            'retry_runs': history['retry_runs']
        }
    
    def get_flaky_tests(self) -> List[Dict[str, Any]]:
        """Get list of flaky tests"""
        flaky_tests = []
        
        for test_name in self.test_history:
            analysis = self.analyze_flakiness(test_name)
            if analysis['flaky']:
                flaky_tests.append({
                    'test_name': test_name,
                    **analysis
                })
        
        # Sort by flakiness confidence
        flaky_tests.sort(key=lambda x: x['confidence'], reverse=True)
        
        return flaky_tests
    
    def _load_persistent_history(self):
        """Load test history from persistent storage"""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    saved_data = json.load(f)
                
                self.test_history = saved_data.get('test_history', {})
                log.debug(f"Loaded persistent flakiness history: {len(self.test_history)} tests")
            else:
                log.debug("No persistent flakiness history found, starting fresh")
                
        except Exception as e:
            log.warning(f"Could not load persistent flakiness history: {e}")
            self.test_history = {}
    
    def _save_persistent_history(self):
        """Save test history to persistent storage"""
        try:
            # Ensure reports directory exists
            self.persistence_file.parent.mkdir(exist_ok=True)
            
            # Prepare data to save
            save_data = {
                'last_updated': time.time(),
                'test_history': self.test_history
            }
            
            # Write to file
            with open(self.persistence_file, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            log.debug(f"Saved persistent flakiness history: {len(self.test_history)} tests")
            
        except Exception as e:
            log.warning(f"Could not save persistent flakiness history: {e}")
    
    def clear_history(self):
        """Clear all test history (for testing purposes)"""
        self.test_history = {}
        try:
            if self.persistence_file.exists():
                self.persistence_file.unlink()
                log.info("Cleared persistent flakiness history")
        except Exception as e:
            log.warning(f"Could not clear persistent history file: {e}")


# Predefined retry configurations
NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    delay_between_attempts=2.0,
    exponential_backoff=True,
    retry_on_exceptions=[ConnectionError, TimeoutError]
)

UI_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    delay_between_attempts=1.0,
    exponential_backoff=False,
    retry_on_exceptions=[Exception]  # Retry on any exception for UI tests
)

API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    delay_between_attempts=1.5,
    exponential_backoff=True,
    retry_on_exceptions=[ConnectionError, TimeoutError]
)


# Global instances
retry_handler = TestRetryHandler()
scenario_retry_handler = ScenarioRetryHandler(retry_handler)
flakiness_detector = FlakynessDetector()


def get_retry_handler() -> TestRetryHandler:
    """Get retry handler instance"""
    return retry_handler


def get_scenario_retry_handler() -> ScenarioRetryHandler:
    """Get scenario retry handler instance"""
    return scenario_retry_handler


def get_flakiness_detector() -> FlakynessDetector:
    """Get flakiness detector instance"""
    return flakiness_detector

