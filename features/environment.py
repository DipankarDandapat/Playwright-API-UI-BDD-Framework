import traceback
import os
from playwright.sync_api import sync_playwright
from utils.config_manager import get_config
from utils.simple_api_client import SimpleAPIClient
from utils import logger
import allure
import threading

log = logger.customLogger()

# Global lock for thread-safe Playwright operations
playwright_lock = threading.Lock()

def before_all(context):
    """Global setup before all tests"""
    context.playwright = None
    context.browser = None
    context.config_manager = None
    context.scenario_count = 0
    context._browsers = {}  # Store browsers per feature
    context._api_clients = {}  # Store API clients per feature

    try:
        log.info("Starting test execution...")

        # Get environment from env variable set by run_tests.py
        environment = os.environ.get('TEST_ENV', 'dev')
        log.info(f"Running tests in '{environment}' environment")

        # Initialize configuration manager
        context.config_manager = get_config(environment)
        log.info("Configuration loaded successfully")

        # Initialize Playwright once for the entire run
        with playwright_lock:
            if context.playwright is None:
                context.playwright = sync_playwright().start()
                log.info("Playwright initialized globally")

        context.is_api_test = False

    except Exception as e:
        error_msg = f"ERROR during global initialization: {str(e)}"
        log.error(error_msg)
        log.error(traceback.format_exc())
        _cleanup_global_resources(context)
        raise

def before_feature(context, feature):
    """Setup before each feature"""
    try:
        log.info(f"Starting feature: {feature.name}")

        # Detect API run
        import sys
        cli_api_run = any(
            arg == "--type" and i + 1 < len(sys.argv) and sys.argv[i + 1].lower() == "api"
            for i, arg in enumerate(sys.argv)
        )
        tag_api_run = 'api' in feature.tags
        context.is_api_test = cli_api_run or tag_api_run

        # Use thread-safe operations
        with playwright_lock:
            if context.is_api_test:
                config = context.config_manager
                base_url = config.get('API_BASE_URL', 'https://dipankardandapat.xyz')

                try:
                    request_context = context.playwright.request.new_context(
                        base_url=base_url,
                        extra_http_headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                    )
                    # Store API client per feature
                    context._api_clients[feature.name] = SimpleAPIClient(request_context, base_url)
                    context.api_client = context._api_clients[feature.name]
                    log.info("Playwright API client initialized successfully")
                except Exception as e:
                    log.warning(f"Error creating requests client: {e}")

                # Auth if available
                api_key = config.get('API_KEY')
                if api_key:
                    context.api_client.set_api_key(api_key)

                context.feature_name = feature.name
                return

            # --- UI tests only from here ---
            browser_config = context.config_manager.get_browser_config()
            browser_engine = context.config_manager.get('BROWSER_ENGINE', 'chromium')

            # Create browser instance for this feature
            if browser_engine == 'chromium':
                browser = context.playwright.chromium.launch(**_get_launch_options(browser_config))
            elif browser_engine == 'firefox':
                browser = context.playwright.firefox.launch(**_get_launch_options(browser_config))
            elif browser_engine == 'webkit':
                browser = context.playwright.webkit.launch(**_get_launch_options(browser_config))
            else:
                raise ValueError(f"Unsupported browser engine: {browser_engine}")

            # Store browser per feature
            context._browsers[feature.name] = browser
            context.browser = browser
            log.info(f"Browser '{browser_engine}' launched for feature: {feature.name}")
            context.feature_name = feature.name

    except Exception as e:
        log.error(f"Feature setup failed for '{feature.name}': {str(e)}")
        log.error(traceback.format_exc())
        raise

def before_step(context, step):
    """Before each step - for Allure reporting"""
    if os.environ.get('ENABLE_ALLURE', 'false').lower() == 'true':
        try:
            allure.dynamic.title(f"{step.keyword} {step.name}")
        except:
            pass

def after_step(context, step):
    """After each step - for Allure reporting"""
    if os.environ.get('ENABLE_ALLURE', 'false').lower() == 'true':
        try:
            if step.status == 'failed':
                allure.attach(
                    body=str(step.exception) if hasattr(step, 'exception') else "Step failed",
                    name="Step Failure Details",
                    attachment_type=allure.attachment_type.TEXT
                )
        except:
            pass

def before_scenario(context, scenario):
    """Setup before each scenario"""
    try:
        log.info("###########################################################")
        context.scenario_count += 1
        log.info(f"Starting scenario {context.scenario_count}: {scenario.name}")
        log.info(f"Total scenarios executed so far: {context.scenario_count}")

        # Skip browser setup for API tests
        if hasattr(context, 'is_api_test') and context.is_api_test:
            log.info(f"Skipping browser setup for API scenario: {scenario.name}")
            return

        # Create new browser context for isolation (UI tests only)
        browser_config = context.config_manager.get_browser_config()
        timeout_config = context.config_manager.get_timeout_config()

        context_options = {
            'viewport': browser_config['viewport'],
            'record_video_dir': f"videos/{context.feature_name}" if browser_config.get('record_video_dir') else None,
            'record_har_path': f"har/{context.feature_name}_{scenario.name}.har" if browser_config.get('record_har_path') else None
        }

        # Remove None values
        context_options = {k: v for k, v in context_options.items() if v is not None}

        # Use thread-safe operations for browser context creation
        with playwright_lock:
            context.browser_context = context.browser.new_context(**context_options)

        # Set timeouts
        context.browser_context.set_default_timeout(timeout_config['default_timeout'])
        context.browser_context.set_default_navigation_timeout(timeout_config['page_load_timeout'])

        # Create new page
        context.page = context.browser_context.new_page()

        # Store scenario info for reporting
        context.current_scenario = scenario
        
        # Add Allure scenario info
        if os.environ.get('ENABLE_ALLURE', 'false').lower() == 'true':
            try:
                allure.dynamic.title(scenario.name)
                allure.dynamic.description(f"Feature: {context.feature_name}")
                for tag in scenario.tags:
                    allure.dynamic.tag(tag)
            except:
                pass

        log.info(f"Scenario setup completed: {scenario.name}")

    except Exception as e:
        log.error(f"Scenario setup failed for '{scenario.name}': {str(e)}")
        log.error(traceback.format_exc())
        raise

def after_scenario(context, scenario):
    """Cleanup after each scenario"""
    try:
        # Skip cleanup for API tests
        if hasattr(context, 'is_api_test') and context.is_api_test:
            return

        # Handle test failure artifacts
        if scenario.status == "failed":
            _handle_test_failure(context, scenario)
            
            # Add Allure failure info
            if os.environ.get('ENABLE_ALLURE', 'false').lower() == 'true':
                try:
                    if hasattr(context, 'page'):
                        screenshot = context.page.screenshot()
                        allure.attach(
                            body=screenshot,
                            name="Failure Screenshot",
                            attachment_type=allure.attachment_type.PNG
                        )
                except:
                    pass

        # Close browser context with thread safety
        with playwright_lock:
            if hasattr(context, 'browser_context') and context.browser_context:
                context.browser_context.close()
                log.info(f"Browser context closed for scenario: {scenario.name}")

        log.info(f"Scenario completed: {scenario.name} - Status: {scenario.status}")

    except Exception as e:
        log.error(f"Scenario cleanup failed for '{scenario.name}': {str(e)}")
        log.error(traceback.format_exc())

def after_feature(context, feature):
    """Cleanup after each feature"""
    try:
        # Skip cleanup for API tests
        if hasattr(context, 'is_api_test') and context.is_api_test:
            # Cleanup API client for this feature
            if hasattr(context, '_api_clients') and feature.name in context._api_clients:
                del context._api_clients[feature.name]
            return

        # Close browser for this feature with thread safety
        with playwright_lock:
            if hasattr(context, '_browsers') and feature.name in context._browsers:
                context._browsers[feature.name].close()
                del context._browsers[feature.name]
                log.info(f"Browser closed for feature: {feature.name}")

        log.info(f"Feature completed: {feature.name}")

    except Exception as e:
        log.error(f"Feature cleanup failed for '{feature.name}': {str(e)}")
        log.error(traceback.format_exc())

def after_all(context):
    """Global cleanup after all tests"""
    try:
        log.info("Test execution completed. Performing cleanup...")
        _cleanup_global_resources(context)
        log.info("Cleanup completed successfully")
        log.info(f"{'='*60}")

    except Exception as e:
        error_msg = f"Global cleanup failed: {str(e)}"
        if log:
            log.error(error_msg)
            log.error(traceback.format_exc())
        else:
            print(error_msg)
            print(traceback.format_exc())

def _cleanup_global_resources(context):
    """Cleanup global resources with thread safety"""
    try:
        with playwright_lock:
            # Close any remaining browsers
            if hasattr(context, '_browsers'):
                for feature_name, browser in context._browsers.items():
                    try:
                        browser.close()
                        log.info(f"Closed browser for feature: {feature_name}")
                    except Exception as e:
                        log.error(f"Failed to close browser for {feature_name}: {str(e)}")
                context._browsers.clear()
            
            # Stop Playwright
            if hasattr(context, 'playwright') and context.playwright:
                context.playwright.stop()
                log.info("Playwright stopped")
                
    except Exception as e:
        if log:
            log.error(f"Failed during global cleanup: {str(e)}")

def _get_launch_options(browser_config):
    """Get browser launch options from configuration"""
    return {
        'headless': browser_config['headless'],
        'slow_mo': browser_config['slow_mo'],
        'args': [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
        ]
    }

def _handle_test_failure(context, scenario):
    """Handle test failure by capturing artifacts"""
    try:
        test_config = context.config_manager.get_test_config()
        
        # Take screenshot on failure
        if test_config['screenshot_on_failure'] and hasattr(context, 'page'):
            screenshot_path = f"screenshots/{context.feature_name}_{scenario.name}_failure.png"
            context.page.screenshot(path=screenshot_path, full_page=True)
            log.info(f"Failure screenshot saved: {screenshot_path}")
        
        # Save trace on failure
        if test_config['trace_on_failure'] and hasattr(context, 'browser_context'):
            trace_path = f"traces/{context.feature_name}_{scenario.name}_failure.zip"
            # Note: Tracing needs to be started before the test
            log.info(f"Trace would be saved to: {trace_path}")
        
        # Log failure details
        log.error(f"Test failed: {scenario.name}")
        if hasattr(scenario, 'exception'):
            log.error(f"Exception: {scenario.exception}")
        
    except Exception as e:
        log.error(f"Failed to handle test failure artifacts: {str(e)}")







