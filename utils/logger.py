"""
Enhanced Logger for Playwright BDD Framework
Provides comprehensive logging with different log levels, file rotation, and console output
"""

# import logging
# import os
# import inspect
# from datetime import datetime
# from logging.handlers import RotatingFileHandler
# from pathlib import Path
# from utils.config_manager import get_config
#
#
# class FrameworkLogger:
#     """Enhanced logger for the framework"""
#
#     def __init__(self):
#         self.config = get_config()
#         self.log_dir = Path(self.config.get('LOG_DIR', 'Logs'))
#         self.log_dir.mkdir(exist_ok=True)
#         self.loggers = {}
#
#     def get_logger(self, name: str = None) -> logging.Logger:
#         """Get or create a logger instance"""
#         if name is None:
#             # Get caller information
#             stack = inspect.stack()
#             caller_frame = stack[1]
#             name = f"{Path(caller_frame.filename).stem}.{caller_frame.function}"
#
#         if name not in self.loggers:
#             self.loggers[name] = self._create_logger(name)
#
#         return self.loggers[name]
#
#     def _create_logger(self, name: str) -> logging.Logger:
#         """Create a new logger with proper configuration"""
#         logger = logging.getLogger(name)
#
#         # Set log level from config
#         log_level = getattr(logging, self.config.get('LOG_LEVEL', 'INFO').upper())
#         logger.setLevel(log_level)
#
#         # Clear existing handlers
#         logger.handlers.clear()
#
#         # Create formatters
#         detailed_formatter = logging.Formatter(
#             '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
#             datefmt='%Y-%m-%d %H:%M:%S'
#         )
#
#         console_formatter = logging.Formatter(
#             '%(asctime)s - [%(levelname)s] - %(message)s',
#             datefmt='%H:%M:%S'
#         )
#
#         # File handler with rotation
#         if self.config.get('LOG_TO_FILE', True):
#             log_file = self.log_dir / f"framework_{datetime.now().strftime('%Y%m%d')}.log"
#             file_handler = RotatingFileHandler(
#                 log_file,
#                 maxBytes=int(self.config.get('LOG_MAX_SIZE', 10 * 1024 * 1024)),  # 10MB
#                 backupCount=int(self.config.get('LOG_BACKUP_COUNT', 5)),
#                 encoding='utf-8'
#             )
#             file_handler.setLevel(log_level)
#             file_handler.setFormatter(detailed_formatter)
#             logger.addHandler(file_handler)
#
#         # Console handler
#         if self.config.get('LOG_TO_CONSOLE', True):
#             console_handler = logging.StreamHandler()
#             console_handler.setLevel(log_level)
#             console_handler.setFormatter(console_formatter)
#             logger.addHandler(console_handler)
#
#         # Separate error log file
#         if self.config.get('LOG_ERRORS_SEPARATELY', True):
#             error_log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
#             error_handler = RotatingFileHandler(
#                 error_log_file,
#                 maxBytes=int(self.config.get('LOG_MAX_SIZE', 10 * 1024 * 1024)),
#                 backupCount=int(self.config.get('LOG_BACKUP_COUNT', 5)),
#                 encoding='utf-8'
#             )
#             error_handler.setLevel(logging.ERROR)
#             error_handler.setFormatter(detailed_formatter)
#             logger.addHandler(error_handler)
#
#         return logger
#
#     def log_test_start(self, feature_name: str, scenario_name: str):
#         """Log test start"""
#         logger = self.get_logger('test_execution')
#         logger.info(f"Starting test - Feature: {feature_name}, Scenario: {scenario_name}")
#
#     def log_test_end(self, feature_name: str, scenario_name: str, status: str, duration: float):
#         """Log test end"""
#         logger = self.get_logger('test_execution')
#         logger.info(f"Finished test - Feature: {feature_name}, Scenario: {scenario_name}, Status: {status}, Duration: {duration:.2f}s")
#
#     def log_api_request(self, method: str, url: str, status_code: int, duration: float):
#         """Log API request"""
#         logger = self.get_logger('api_client')
#         logger.info(f"API {method} {url} - Status: {status_code}, Duration: {duration:.3f}s")
#
#     def log_browser_action(self, action: str, element: str = None, page_url: str = None):
#         """Log browser action"""
#         logger = self.get_logger('browser_actions')
#         message = f"Browser action: {action}"
#         if element:
#             message += f" on element: {element}"
#         if page_url:
#             message += f" at page: {page_url}"
#         logger.info(message)
#
#     def log_error(self, error_message: str, exception: Exception = None):
#         """Log error with optional exception details"""
#         logger = self.get_logger('errors')
#         if exception:
#             logger.error(f"{error_message}: {str(exception)}", exc_info=True)
#         else:
#             logger.error(error_message)
#
#     def cleanup_old_logs(self, days_to_keep: int = 7):
#         """Clean up old log files"""
#         cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
#
#         for log_file in self.log_dir.glob('*.log*'):
#             if log_file.stat().st_mtime < cutoff_date:
#                 try:
#                     log_file.unlink()
#                     print(f"Deleted old log file: {log_file}")
#                 except Exception as e:
#                     print(f"Failed to delete log file {log_file}: {e}")
#
#
# # Global logger instance
# _framework_logger = FrameworkLogger()
#
#
# def get_logger(name: str = None) -> logging.Logger:
#     """Get logger instance - main function to use throughout the framework"""
#     return _framework_logger.get_logger(name)
#
#
# def customLogger(logLevel=logging.INFO):
#     """Legacy function for backward compatibility"""
#     return get_logger()
#
#
# def log_test_start(feature_name: str, scenario_name: str):
#     """Log test start - convenience function"""
#     _framework_logger.log_test_start(feature_name, scenario_name)
#
#
# def log_test_end(feature_name: str, scenario_name: str, status: str, duration: float):
#     """Log test end - convenience function"""
#     _framework_logger.log_test_end(feature_name, scenario_name, status, duration)
#
#
# def log_api_request(method: str, url: str, status_code: int, duration: float):
#     """Log API request - convenience function"""
#     _framework_logger.log_api_request(method, url, status_code, duration)
#
#
# def log_browser_action(action: str, element: str = None, page_url: str = None):
#     """Log browser action - convenience function"""
#     _framework_logger.log_browser_action(action, element, page_url)
#
#
# def log_error(error_message: str, exception: Exception = None):
#     """Log error - convenience function"""
#     _framework_logger.log_error(error_message, exception)
#
#
# def cleanup_old_logs(days_to_keep: int = 7):
#     """Clean up old logs - convenience function"""
#     _framework_logger.cleanup_old_logs(days_to_keep)


import logging
import os
from datetime import datetime

# Global variables to ensure single log file per session
_log_file_path = None
_session_start_time = None
_root_logger_configured = False

def customLogger(logLevel=logging.INFO):
    global _log_file_path, _session_start_time, _root_logger_configured
    
    # Create the directory for logs if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Check if a shared log file is specified via environment variable
    shared_log_file = os.environ.get('SHARED_LOG_FILE')
    
    # Initialize session start time and log file path once
    if _session_start_time is None:
        _session_start_time = datetime.now()
        if shared_log_file:
            _log_file_path = shared_log_file
        else:
            current_time = datetime.strftime(_session_start_time, '%d_%m_%Y_%I_%M_%S%p')
            _log_file_path = os.path.join(log_dir, f"Log_{current_time}.log")

    logger_name = "framework_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logLevel)

    # Configure the logger only once
    if not _root_logger_configured and not logger.handlers:
        # File handler for logging to file
        fileHandler = logging.FileHandler(_log_file_path, mode='a', encoding="UTF-8")
        fileHandler.setLevel(logLevel)

        file_formatter = logging.Formatter(
            '%(asctime)s -(%(filename)s:%(lineno)s)- [%(levelname)s] %(message)s',
            datefmt='%d_%m_%Y %I:%M:%S %p'
        )
        fileHandler.setFormatter(file_formatter)
        logger.addHandler(fileHandler)

        # Console handler for logging to terminal
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logLevel)
        
        console_formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        consoleHandler.setFormatter(console_formatter)
        logger.addHandler(consoleHandler)

        # Avoid reconfiguration in next calls
        _root_logger_configured = True

    return logger