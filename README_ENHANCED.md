# Enhanced Playwright BDD Framework

## Overview

This enhanced Playwright BDD framework provides comprehensive API and UI testing capabilities with advanced features including parallel execution, intelligent retry mechanisms, enhanced reporting, and comprehensive test data management.

## New Features Added

### 1. Comprehensive API Testing
- **FreeAPI Integration**: Full support for FreeAPI todos endpoints
- **JSONPlaceholder Support**: Extended support for JSONPlaceholder API
- **API-Only Execution**: Run API tests without browser initialization
- **Enhanced API Client**: Improved error handling and logging

### 2. Enhanced Test Execution
- **Parallel Test Runner**: Execute tests in parallel for faster execution
- **Intelligent Retry Logic**: Automatic retry on failures with configurable policies
- **Test Data Factory**: Dynamic test data generation with Faker integration
- **Flakiness Detection**: Identify and analyze flaky tests

### 3. Advanced Reporting
- **Enhanced HTML Reports**: Rich HTML reports with charts and metrics
- **Trend Analysis**: Historical trend analysis with visualizations
- **Test Metrics**: Comprehensive test execution metrics
- **Chart Generation**: Automatic generation of test result charts

### 4. Improved Configuration
- **Environment-Specific Configs**: Support for multiple environments
- **Browser Optimization**: Optimized browser lifecycle management
- **API-Only Mode**: Skip browser initialization for API tests

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
pip install faker matplotlib seaborn jinja2
```

2. Install Playwright browsers (for UI tests only):
```bash
playwright install
```

## Usage

### Basic Test Execution

#### Run API Tests Only (No Browser)
```bash
python run_tests.py --type api
```

#### Run UI Tests Only
```bash
python run_tests.py --type ui --browser chromium --headless
```

#### Run All Tests
```bash
python run_tests.py --type all
```

### Enhanced Test Execution

#### Run Tests with Enhanced Features
```bash
python run_tests.py --type api --enhanced-reports
```

#### Run Tests in Parallel
```bash
python run_tests.py --type all --parallel 4
```

#### Run Tests with Retry Logic
```bash
python run_tests.py --type api --retry --max-retries 3
```

#### Generate Trend Analysis
```bash
python run_tests.py --type all --trend-analysis
```

#### Analyze Test Flakiness
```bash
python run_tests.py --type all --analyze-flakiness
```

### Command Line Options

#### Basic Options
- `--type`: Test type (ui, api, all, smoke, regression)
- `--tags`: Comma-separated list of tags
- `--env`: Environment (dev, stg, prod)
- `--browser`: Browser for UI tests (chromium, firefox, webkit)
- `--headless/--headed`: Browser mode

#### Enhanced Options
- `--parallel`: Number of parallel processes
- `--retry`: Enable test retry on failure
- `--max-retries`: Maximum number of retries
- `--analyze-flakiness`: Analyze test flakiness
- `--trend-analysis`: Generate trend analysis
- `--enhanced-reports`: Generate enhanced reports

## API Testing Features

### FreeAPI Todos Endpoints
The framework now supports comprehensive testing of FreeAPI todos:

- **Create Todo**: POST `/api/v1/todos/`
- **Get Todo by ID**: GET `/api/v1/todos/{id}`
- **Get All Todos**: GET `/api/v1/todos`
- **Update Todo**: PATCH `/api/v1/todos/{id}`
- **Toggle Status**: PATCH `/api/v1/todos/toggle/status/{id}`
- **Delete Todo**: DELETE `/api/v1/todos/{id}`

### Test Scenarios Covered
- ✅ CRUD operations for todos
- ✅ Data validation and error handling
- ✅ Response time validation
- ✅ Negative testing scenarios
- ✅ Boundary value testing
- ✅ Search and filtering

### Example API Test
```gherkin
@api @smoke @todos @freeapi
Scenario: Create a new todo via FreeAPI
  Given I have valid todo data
    | field       | value                           |
    | title       | Test Todo for API Automation    |
    | description | This is a test todo via API     |
  When I send POST request to "https://api.freeapi.app/api/v1/todos/" with the todo data
  Then the response status code should be 201
  And the response should contain the created todo details
  And the todo should have a generated "_id"
  And the todo "title" should match the input data
```

## Enhanced Features

### 1. Test Data Factory
Generate dynamic test data for comprehensive testing:

```python
from utils.test_data_factory import get_test_data_factory

factory = get_test_data_factory()

# Generate user data
user_data = factory.generate_user_data()

# Generate todo data
todo_data = factory.generate_todo_data()

# Generate invalid data for negative testing
invalid_data = factory.generate_invalid_data('todo')
```

### 2. Parallel Test Execution
Run tests in parallel for faster execution:

```python
from utils.parallel_runner import ParallelTestRunner, TestGroupBuilder

# Create test groups
builder = TestGroupBuilder()
groups = (builder
         .add_api_tests()
         .add_ui_tests()
         .add_smoke_tests()
         .build())

# Run in parallel
runner = ParallelTestRunner(max_workers=4)
results = runner.run_tests_parallel(groups)
```

### 3. Enhanced Reporting
Generate comprehensive reports with charts and analytics:

```python
from utils.enhanced_reporter import get_enhanced_reporter

reporter = get_enhanced_reporter()
report_files = reporter.generate_comprehensive_report(results)
```

### 4. Retry Logic
Implement intelligent retry mechanisms:

```python
from utils.test_retry_handler import get_retry_handler, RetryConfig

# Configure retry behavior
config = RetryConfig(
    max_attempts=3,
    delay_between_attempts=2.0,
    exponential_backoff=True
)

# Use retry decorator
@retry_handler.retry_on_failure(config)
def flaky_test_function():
    # Test implementation
    pass
```

## Configuration

### Environment Configuration
Configure different environments in `config/`:

```json
{
  "API_BASE_URL": "https://api.freeapi.app",
  "BROWSER_ENGINE": "chromium",
  "HEADLESS": true,
  "TIMEOUT": 30000
}
```

### Retry Configuration
Configure retry behavior for different test types:

```python
# Network-related retries
NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    delay_between_attempts=2.0,
    exponential_backoff=True,
    retry_on_exceptions=[ConnectionError, TimeoutError]
)

# UI test retries
UI_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    delay_between_attempts=1.0,
    exponential_backoff=False
)
```

## Reports and Analytics

### Generated Reports
- **HTML Reports**: Rich HTML reports with test metrics and charts
- **JSON Reports**: Machine-readable test results
- **Trend Reports**: Historical trend analysis
- **Chart Files**: PNG charts for pass/fail rates, durations, etc.

### Report Locations
- `reports/test_report_*.html` - HTML reports
- `reports/test_report_*.json` - JSON reports
- `reports/trend_report_*.html` - Trend analysis
- `reports/*_chart_*.png` - Generated charts
- `reports/historical_results.json` - Historical data

### Metrics Tracked
- Pass/fail rates
- Test execution duration
- Scenario and feature counts
- Retry statistics
- Flakiness analysis

## Best Practices

### API Testing
1. Use appropriate HTTP methods for different operations
2. Validate response status codes and data structure
3. Test both positive and negative scenarios
4. Include performance testing (response times)
5. Test error handling and edge cases

### Test Organization
1. Use descriptive scenario names
2. Group related tests with appropriate tags
3. Separate API and UI tests for better execution control
4. Use data-driven testing for comprehensive coverage

### Parallel Execution
1. Design tests to be independent and stateless
2. Use appropriate number of parallel workers
3. Consider resource constraints when setting parallelism
4. Monitor test execution for optimal performance

### Retry Logic
1. Configure retries based on test type and failure patterns
2. Use exponential backoff for network-related retries
3. Monitor retry statistics to identify flaky tests
4. Set reasonable retry limits to avoid infinite loops

## Troubleshooting

### Common Issues

#### Browser Not Opening for API Tests
✅ **Fixed**: The framework now properly skips browser initialization for API-only tests.

#### API Test Failures
- Check API endpoint availability
- Verify request data format
- Check authentication if required
- Review response validation logic

#### Parallel Execution Issues
- Ensure tests are independent
- Check resource constraints
- Verify test data isolation
- Monitor system resources

### Debug Mode
Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
python run_tests.py --type api
```

## Contributing

1. Follow existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for new functionality
4. Ensure backward compatibility
5. Add appropriate logging and error handling

## License

This enhanced framework builds upon the original Playwright BDD framework with additional features for comprehensive testing capabilities.

