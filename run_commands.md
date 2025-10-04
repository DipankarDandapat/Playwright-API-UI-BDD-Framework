# Test Execution Commands

Comprehensive guide for running tests in the Playwright BDD Framework.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Basic Test Execution](#basic-test-execution)
3. [Test Filtering with Tags](#test-filtering-with-tags)
4. [Parallel Execution](#parallel-execution)
5. [Browser Configuration](#browser-configuration)
6. [Advanced Execution Options](#advanced-execution-options)
7. [Direct Behave Commands](#direct-behave-commands)
8. [Feature-Specific Commands](#feature-specific-commands)
9. [Reporting](#reporting)
10. [Debugging](#debugging)
11. [CI/CD Pipeline Commands](#cicd-pipeline-commands)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install
```


---

## Basic Test Execution

### Run All Tests (UI + API)

```bash
# Default settings
python run_tests.py

# Specific environment
python run_tests.py --env dev
python run_tests.py --env stg
python run_tests.py --env prod
```

### Run UI Tests Only

```bash
# All UI tests
python run_tests.py --type ui

# Headless mode
python run_tests.py --type ui --headless

# Headed mode (with browser window)
python run_tests.py --type ui --headed

# Specific browser
python run_tests.py --type ui --browser chromium
python run_tests.py --type ui --browser firefox
python run_tests.py --type ui --browser webkit
```

### Run API Tests Only

```bash
# All API tests
python run_tests.py --type api

# With specific environment
python run_tests.py --type api --env stg
```

---

## Test Filtering with Tags

### Smoke Tests

```bash
# Both UI and API
python run_tests.py --type smoke

# Headless mode
python run_tests.py --type smoke --headless
```

### Regression Tests

```bash
# Standard execution
python run_tests.py --type regression

# With parallel execution
python run_tests.py --type regression --parallel 4
```

### Custom Tags

```bash
# Specific tags
python run_tests.py --tags "user_creation,login"

# UI tests with tags
python run_tests.py --type ui --tags "ecommerce,checkout"

# API tests with tags
python run_tests.py --type api --tags "todos,freeapi"
```

---

## Parallel Execution

Run tests concurrently for faster execution:

```bash
# All tests with 4 parallel processes
python run_tests.py --parallel 4

# UI tests with 2 parallel processes
python run_tests.py --type ui --parallel 2

# Regression tests with 8 parallel processes
python run_tests.py --type regression --parallel 8
```

---

## Browser Configuration

### Environment Variables

```bash
# Browser type
export BROWSER=chromium  # chromium, firefox, or webkit
export BROWSER=firefox
export BROWSER=webkit

# Headless mode
export HEADLESS=true
export HEADLESS=false

# Test environment
export TEST_ENV=dev
export TEST_ENV=stg
export TEST_ENV=prod
```

### Browser-Specific Execution

```bash
# Chromium
BROWSER=chromium python run_tests.py --type ui

# Firefox
BROWSER=firefox python run_tests.py --type ui

# WebKit
BROWSER=webkit python run_tests.py --type ui

# Headless
HEADLESS=true python run_tests.py --type ui
```

---

## Advanced Execution Options

### With Allure Reporting

```bash
# All tests with Allure report
python run_tests.py --allure

# Smoke tests with Allure report
python run_tests.py --type smoke --allure

# Regression with Allure report and parallel execution
python run_tests.py --type regression --parallel 4 --allure
```

### Environment-Specific Execution

```bash
# Development environment
python run_tests.py --env dev --type ui --headed

# Staging with parallel execution
python run_tests.py --env stg --parallel 4

# Production (API only)
python run_tests.py --env prod --type api
```

### Custom Configuration

```bash
# Custom environment file
TEST_ENV=custom python run_tests.py

# Override API base URL
API_BASE_URL=https://custom-api.com python run_tests.py --type api

# Custom browser timeout
BROWSER_TIMEOUT=60000 python run_tests.py --type ui
```

---

## Direct Behave Commands

### Basic Commands

```bash
# All features
behave features/

# Specific feature file
behave features/Todos_API_Testing.feature
behave features/ecommerce_ui_testing.feature

# With specific tags
behave features/ -t @smoke
behave features/ -t @api
behave features/ -t @ui
behave features/ -t @regression
```

### Output Formats

```bash
# Pretty output
behave features/ -f pretty

# JSON output
behave features/ -f json -o reports/results.json

# Multiple formats
behave features/ -f pretty -f json -o reports/results.json -f junit -o reports/junit.xml
```

### Parallel Execution

```bash
# With parallel processes
behave features/ --processes 4

# Specific tests in parallel
behave features/ -t @regression --processes 8
```

---

## Feature-Specific Commands

### E-commerce UI Testing

```bash
# All e-commerce tests
behave features/ecommerce_ui_testing.feature

# Smoke tests
behave features/ecommerce_ui_testing.feature -t @smoke

# Checkout tests
behave features/ecommerce_ui_testing.feature -t @checkout
```

### Social Media UI Testing

```bash
# All social media tests
behave features/social_media_ui_testing.feature

# Post creation tests
behave features/social_media_ui_testing.feature -t @post_creation
```

### API Testing

```bash
# All API tests
behave features/Todos_API_Testing.feature

# User-related API tests
behave features/Todos_API_Testing.feature -t @users

# API smoke tests
behave features/Todos_API_Testing.feature -t @smoke
```

### Facebook Login/Registration

```bash
# Facebook login tests
behave features/facebook_login_signup.feature
```

---

## Reporting

### Generate Reports

```bash
# Generate Allure report
allure generate reports/allure-results -o reports/allure-report --clean

# Open Allure report
allure open reports/allure-report

# Serve Allure report
allure serve reports/allure-results
```

### View Reports

```bash
# HTML report (auto-generated)
open reports/test_report_*.html

# JSON results
cat reports/results.json | jq '.'

# JUnit XML
cat reports/junit.xml
```

---

## Debugging

### Run Single Scenario

```bash
# By scenario name
behave features/ -n "Verify homepage loads correctly"

# With debugging (no capture)
behave features/ -n "Create a new user via API" --no-capture

# Verbose output
behave features/ -v
```

### Screenshots and Traces

```bash
# Run with screenshot capture on failure
python run_tests.py --type ui --headed

# Check screenshots
ls -la screenshots/

# Check traces
ls -la traces/
```

### Debug Mode

```bash
# Debug logging
LOG_LEVEL=DEBUG python run_tests.py

# Single test with full output
behave features/Todos_API_Testing.feature -n "Get all users from API" --no-capture -v

# Python debugger
python -m pdb run_tests.py --type ui
```

---

## CI/CD Pipeline Commands

### Jenkins/GitHub Actions

```bash
# Smoke tests for PR validation
python run_tests.py --type smoke --headless --allure

# Full regression for main branch
python run_tests.py --type regression --parallel 8 --headless --allure

# API tests for backend changes
python run_tests.py --type api --parallel 4
```

### Docker Commands

```bash
# Build test image
docker build -t playwright-tests .

# Run tests in container
docker run --rm -v $(pwd)/reports:/app/reports playwright-tests

# With environment variables
docker run --rm -e TEST_ENV=stg -v $(pwd)/reports:/app/reports playwright-tests
```

### Performance Testing (API)

```bash
# Multiple parallel processes
python run_tests.py --type api --parallel 10

# High concurrency
behave features/Todos_API_Testing.feature -t @performance --processes 20
```

---

## Troubleshooting

### Check Installation

```bash
# Python dependencies
pip list | grep -E "(playwright|behave|requests)"

# Playwright version
playwright --version

# Browser installation
playwright install --dry-run
```

### Clean Up

```bash
# Clean reports
rm -rf reports/*

# Clean logs
rm -rf Logs/*

# Clean artifacts
rm -rf screenshots/* traces/* videos/*
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `python run_tests.py` | Run all tests |
| `python run_tests.py --type ui` | Run UI tests only |
| `python run_tests.py --type api` | Run API tests only |
| `python run_tests.py --type smoke` | Run smoke tests |
| `python run_tests.py --parallel 4` | Run with 4 parallel processes |
| `python run_tests.py --allure` | Generate Allure report |
| `python run_tests.py --headed` | Run with visible browser |
| `behave features/` | Run all features with Behave |
| `behave features/ -t @smoke` | Run tests with @smoke tag |

---

**Last Updated:** October 2025