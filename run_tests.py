import argparse
import os
import sys
import json
import math
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import subprocess
import re
import time
from utils.config_manager import get_config
from utils.parallel_runner import ParallelTestRunner, TestGroupBuilder
from utils.enhanced_reporter import get_enhanced_reporter
from utils.test_retry_handler import get_retry_handler, get_flakiness_detector, RetryConfig
from utils import logger

# Initialize logger
log = logger.customLogger()

# Global configuration
class TestConfig:
    """Centralized configuration management"""
    
    def __init__(self):
        self.shared_log_file = self._setup_shared_log()
        self.config = get_config()
        
    def _setup_shared_log(self) -> str:
        """Setup shared log file for the entire session"""
        current_time = datetime.strftime(datetime.now(), '%d_%m_%Y_%I_%M_%S%p')
        shared_log_file = f"logs/Log_{current_time}.log"
        os.environ['SHARED_LOG_FILE'] = shared_log_file
        return shared_log_file
    
    def get_env_var(self, key: str, default: Any = None) -> Any:
        """Get environment variable with fallback to config"""
        return os.environ.get(key, self.config.get(key.lower(), default))
    
    def set_test_env(self, env: str):
        """Set test environment"""
        os.environ['TEST_ENV'] = env

# Global config instance
test_config = TestConfig()

# Generic utility functions
def create_test_groups(test_type: str, parallel_count: int, tags: Optional[str] = None) -> List[Dict]:
    """Generic function to create test groups for parallel execution"""
    groups = []
    
    if test_type == 'api':
        api_feature_files = discover_feature_files_by_tags(['@api'], ['@ui'])
        if not api_feature_files:
            api_feature_files = ['features']
        
        for i in range(parallel_count):
            groups.append({
                'name': f'API Tests Group {i+1}',
                'tags': ['@api'], 
                'type': 'api',
                'features': api_feature_files
            })
    elif test_type == 'ui':
        for i in range(parallel_count):
            groups.append({
                'name': f'UI Tests Group {i+1}',
                'tags': ['@ui'], 
                'type': 'ui'
            })
    elif test_type in ['smoke', 'regression']:
        for i in range(parallel_count):
            groups.append({
                'name': f'{test_type.title()} Tests Group {i+1}',
                'tags': [f'@{test_type}'], 
                'type': 'mixed'
            })
    else:
        builder = TestGroupBuilder()
        groups = (builder
                 .add_smoke_tests()
                 .add_api_tests()
                 .add_ui_tests()
                 .add_regression_tests()
                 .build())
    
    # Add custom tags if specified
    if tags:
        for group in groups:
            group['tags'].extend(tags.split(','))
    
    return groups

def setup_environment_variables(headless: Optional[bool] = None, browser: Optional[str] = None) -> Dict[str, str]:
    """Generic function to setup environment variables"""
    env = os.environ.copy()
    
    if headless is not None:
        env['HEADLESS'] = str(headless).lower()
    if browser:
        env['BROWSER'] = browser
    
    # Set common environment variables from config
    env['API_ONLY'] = env.get('API_ONLY', 'false')
    env['SKIP_BROWSER'] = env.get('SKIP_BROWSER', 'false')
    
    return env



def build_behave_command(test_type: str, tags: Optional[str] = None, parallel: Optional[int] = None) -> List[str]:
    """Generic function to build behave command"""
    cmd = [sys.executable, '-m', 'behave']
    
    # Add feature files based on test type
    if test_type == 'api':
        api_feature_files = discover_feature_files_by_tags(['@api'], ['@ui'])
        if api_feature_files:
            cmd.extend(api_feature_files)
        else:
            cmd.extend(['features'])
    elif test_type == 'ui':
        ui_feature_files = discover_feature_files_by_tags(['@ui'], ['@api'])
        if ui_feature_files:
            cmd.extend(ui_feature_files)
        else:
            cmd.extend(['features'])
    else:
        cmd.extend(['features'])
    
    # Add tags
    test_tags = []
    if test_type == 'api':
        test_tags = ['@api']
        if 'features' in cmd:
            test_tags.append('~@ui')
    elif test_type == 'ui':
        test_tags = ['@ui']
        if 'features' in cmd:
            test_tags.append('~@api')
    elif test_type in ['smoke', 'regression']:
        test_tags = [f'@{test_type}']
    
    if tags:
        test_tags.extend(tags.split(','))
    
    for tag in test_tags:
        cmd.extend(['-t', tag.strip()])
    
    # Add parallel execution if supported and specified
    if parallel and test_type in ['all', 'mixed']:
        cmd.extend(['--processes', str(parallel)])
    
    return cmd

def add_allure_custom_formatters(cmd: List[str], output_file: str):
    """Add custom formatters"""
    # Always add JSON formatter for our reporting
    cmd.extend(['-f', 'json', '-o', output_file])
    
    # Add Allure formatter if enabled
    if test_config.get_env_var('ENABLE_ALLURE', 'false').lower() == 'true':
        try:
            cmd.extend(['-f', 'allure_behave.formatter:AllureFormatter', '-o', 'reports/allure-results'])
            log.info("Allure formatter added to command")
        except Exception as e:
            log.warning(f"Could not add Allure formatter: {e}")
    
    # Add pretty formatter for console output
    #cmd.extend(['-f', 'pretty'])

def execute_subprocess_with_output(cmd: List[str], env: Dict[str, str]) -> Tuple[int, str]:
    """Generic function to execute subprocess with real-time output capture"""
    try:
        process = subprocess.Popen(
            cmd, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True, 
            bufsize=1, 
            universal_newlines=True
        )
        
        captured_output = []
        
        for line in iter(process.stdout.readline, ''):
            captured_output.append(line)
            
            # Show all output except verbose JSON logs
            clean_line = line.strip()
            if not (clean_line.startswith('{"keyword":') or clean_line.startswith('[{"keyword":')):
                print(line, end='')
        
        process.stdout.close()
        return_code = process.wait()
        full_output = ''.join(captured_output)
        
        return return_code, full_output
    except Exception as e:
        log.error(f"Error executing subprocess: {e}")
        return 1, str(e)

def display_test_summary(return_code: int, json_report_path: str, full_output: str, test_type: str):
    """Generic function to display test summary"""
    if return_code != 0:
        log.error(f"{test_type} tests failed - analyzing failures...")
        display_failure_summary(json_report_path, full_output)
    else:
        log.info(f"{test_type} tests completed successfully")

def run_tests_with_enhanced_features(args):
    """Run tests with enhanced features"""
    setup_enhanced_environment()
    test_config.set_test_env(args.env)
    
    log.info(f"Starting enhanced test execution - Type: {args.type}, Environment: {args.env}")
    
    try:
        if args.parallel and args.parallel > 1:
            if args.type in ['api', 'ui', 'smoke', 'regression']:
                log.info(f"Running {args.type} tests sequentially (scenario-level parallelization not implemented)")
                success, results = run_sequential_tests(args)
            else:
                log.info(f"Using advanced parallel runner with {args.parallel} workers")
                success, results = run_parallel_tests(args)
        else:
            success, results = run_sequential_tests(args)
        
        if results:
            generate_enhanced_reports(results, args)
        
        if args.analyze_flakiness:
            analyze_test_flakiness()
        
        return success
        
    except Exception as e:
        log.error(f"Enhanced test execution failed: {e}")
        return False

def run_parallel_tests(args) -> Tuple[bool, Dict]:
    """Run tests in parallel using advanced parallel runner"""
    groups = create_test_groups(args.type, args.parallel, args.tags)
    
    log.info(f"Starting parallel execution with {len(groups)} group(s)")
    for i, group in enumerate(groups, 1):
        log.info(f"Group {i}: {group['name']} (tags: {group['tags']})")
    
    runner = ParallelTestRunner(max_workers=args.parallel)
    parallel_results = runner.run_tests_parallel(groups)
    
    aggregated_results = load_test_results()
    aggregated_results.update({
        'parallel_execution': True,
        'groups_executed': len(groups),
        'parallel_summary': parallel_results
    })
    
    print_parallel_summary(parallel_results)
    
    success = parallel_results['failed'] == 0
    return success, aggregated_results

def print_parallel_summary(parallel_results: Dict):
    """Print parallel execution summary"""
    print(f"\n{'='*60}")
    print("🔄 PARALLEL EXECUTION SUMMARY:")
    print(f"{'='*60}")
    print(f"✅ Groups Passed: {parallel_results['passed']}")
    print(f"❌ Groups Failed: {parallel_results['failed']}")
    print(f"📊 Total Groups: {parallel_results['total_groups']}")
    
    for result in parallel_results.get('group_results', []):
        status_icon = "✅" if result['success'] else "❌"
        duration = result.get('duration', 0)
        print(f"{status_icon} {result['group_name']}: {duration:.2f}s")
    
    print(f"{'='*60}")

def discover_feature_files_by_tags(include_tags: List[str], exclude_tags: List[str], base_dir: str = 'features') -> List[str]:
    """Discover .feature files based on tags"""
    discovered = []
    
    try:
        for path in Path(base_dir).glob('**/*.feature'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (FileNotFoundError, OSError):
                continue
            
            lines = content.split('\n')
            active_tags = []
            for line in lines:
                line = line.strip()
                if line.startswith('@') and not line.startswith('#'):
                    active_tags.extend([tag.strip() for tag in line.split() if tag.startswith('@')])
            
            has_included = not include_tags or any(tag in active_tags for tag in include_tags)
            has_excluded = any(tag in active_tags for tag in exclude_tags) if exclude_tags else False
            
            if has_included and not has_excluded:
                discovered.append(str(path))
    except Exception:
        return []
    
    return discovered

def run_generic_tests(test_type: str, tags: Optional[str] = None, parallel: Optional[int] = None, 
                     headless: Optional[bool] = None, browser: Optional[str] = None) -> bool:
    """Generic function to run any type of tests"""
    # Temporarily rename behave.ini to avoid formatter conflicts
    behave_ini = Path('behave.ini')
    behave_ini_backup = Path('behave.ini.backup')
    
    try:
        if behave_ini.exists():
            behave_ini.rename(behave_ini_backup)
        
        cmd = build_behave_command(test_type, tags, parallel)
        env = setup_environment_variables(headless, browser)
        
        # Set specific environment variables for test type
        if test_type == 'api':
            env['API_ONLY'] = 'true'
            env['SKIP_BROWSER'] = 'true'

        
        # Add custom formatters if needed
        output_file = f'reports/{test_type}_results.json'
        add_allure_custom_formatters(cmd, output_file)
        
        log.info(f"Running {test_type} tests with command: {' '.join(cmd)}")
        
        # Execute with retry if enabled for API tests
        if test_type == 'api':
            max_retries = int(test_config.get_env_var('MAX_RETRIES', 0))
            return_code, full_output = run_api_tests_with_retry(cmd, env, max_retries)
        else:
            return_code, full_output = execute_subprocess_with_output(cmd, env)
        
        display_test_summary(return_code, output_file, full_output, test_type)
        return return_code == 0
        
    finally:
        # Restore behave.ini
        if behave_ini_backup.exists():
            behave_ini_backup.rename(behave_ini)

def run_ui_tests(tags=None, parallel=None, headless=None, browser=None):
    """Run UI tests"""
    return run_generic_tests('ui', tags, parallel, headless, browser)

def run_api_tests(tags=None, parallel=None):
    """Run API tests"""
    return run_generic_tests('api', tags, parallel)

def run_all_tests(tags=None, parallel=None, headless=None, browser=None):
    """Run all tests"""
    return run_generic_tests('all', tags, parallel, headless, browser)

def run_smoke_tests(headless=None, browser=None):
    """Run smoke tests"""
    return run_generic_tests('smoke', None, None, headless, browser)

def run_regression_tests(parallel=None, headless=None, browser=None):
    """Run regression tests"""
    return run_generic_tests('regression', None, parallel, headless, browser)

def run_api_tests_with_retry(cmd: List[str], env: Dict[str, str], max_retries: int = 0) -> Tuple[int, str]:
    """Execute API test command with retry logic"""
    retry_handler = get_retry_handler()
    
    def execute_api_tests():
        result = subprocess.run(cmd, env=env, text=True, capture_output=False)
        return_code = result.returncode
        full_output = ""
        
        if return_code != 0:
            retry_all_failures = test_config.get_env_var('RETRY_ALL_FAILURES', 'false').lower() == 'true'
            
            if retry_all_failures:
                log.warning(f"Test failed with exit code {return_code}, retrying all failures")
                raise Exception(f"Test execution failure (exit code: {return_code})")
            elif is_transient_failure(full_output):
                log.warning("Detected transient failure that may benefit from retry")
                raise Exception(f"Transient test execution failure (exit code: {return_code})")
            else:
                log.info("Test failure appears to be assertion-based, not retrying")
        
        return return_code, full_output
    
    if max_retries > 0:
        retry_config = RetryConfig(
            max_attempts=max_retries + 1,
            delay_between_attempts=2.0,
            exponential_backoff=True,
            retry_on_exceptions=[Exception]
        )
        
        try:
            return retry_handler.execute_with_retry(execute_api_tests, retry_config)
        except Exception as e:
            log.error(f"All retry attempts exhausted: {e}")
            return 1, str(e)
    else:
        return execute_api_tests()

def is_transient_failure(output: str) -> bool:
    """Determine if a test failure is transient and should be retried"""
    transient_indicators = [
        'connection refused', 'connection timeout', 'network unreachable',
        'temporary failure', 'service temporarily unavailable', 'internal server error',
        'gateway timeout', 'bad gateway', 'cannot connect to', 'browser launch failed',
        'page crash', 'browser disconnected', 'websocket connection failed'
    ]
    
    assertion_indicators = [
        'expected status', 'assert failed', 'assertionerror', 'expected', 'but was', 'but got'
    ]
    
    output_lower = output.lower()
    
    # Don't retry assertion failures
    if any(indicator in output_lower for indicator in assertion_indicators):
        return False
    
    # Check for transient failure indicators
    return any(indicator in output_lower for indicator in transient_indicators)

def run_sequential_tests(args) -> Tuple[bool, Dict]:
    """Run tests sequentially"""
    headless = None
    if args.headless:
        headless = True
    elif args.headed:
        headless = False
    
    # Map test types to functions
    test_functions = {
        'ui': lambda: run_ui_tests(args.tags, args.parallel, headless, args.browser),
        'api': lambda: run_api_tests(args.tags, args.parallel),
        'smoke': lambda: run_smoke_tests(headless, args.browser),
        'regression': lambda: run_regression_tests(args.parallel, headless, args.browser),
        'all': lambda: run_all_tests(args.tags, args.parallel, headless, args.browser)
    }
    
    success = test_functions.get(args.type, test_functions['all'])()
    results = load_test_results()
    
    if hasattr(args, 'analyze_flakiness') and args.analyze_flakiness:
        record_test_results_for_flakiness(results, success)
    
    return success, results

# Keep existing complex functions that are already well-structured
def parse_test_results(json_file_path):
    """Parse JSON test results to extract failing scenarios and steps"""
    failed_details = []
    
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return failed_details
                
                json_objects = []
                if content.startswith('['):
                    json_objects = json.loads(content)
                else:
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and line.startswith('{'):
                            try:
                                json_objects.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                
                for feature in json_objects:
                    if isinstance(feature, dict) and feature.get('keyword') == 'Feature':
                        feature_name = feature.get('name', 'Unknown Feature')
                        location = feature.get('location', 'Unknown Location')
                        
                        for element in feature.get('elements', []):
                            if element.get('type') != 'scenario':
                                continue

                            scenario_name = element.get('name', 'Unknown Scenario')
                            scenario_location = element.get('location', 'Unknown Location')

                            steps = element.get('steps', [])
                            has_failure = False
                            failed_steps = []

                            for step in steps:
                                step_result = step.get('result', {})
                                step_status = step_result.get('status', '')
                                if step_status in ['failed', 'error']:
                                    has_failure = True
                                    step_name = step.get('name', 'Unknown Step')
                                    step_keyword = step.get('keyword', '')
                                    error_message = step_result.get('error_message', 'No error message')
                                    step_location = step.get('location', 'Unknown Location')

                                    failed_steps.append({
                                        'step': f"{step_keyword.strip()} {step_name}",
                                        'location': step_location,
                                        'error': error_message,
                                        'status': step_status
                                    })

                            if has_failure and failed_steps:
                                failed_details.append({
                                    'feature': feature_name,
                                    'feature_location': location,
                                    'scenario': scenario_name,
                                    'scenario_location': scenario_location,
                                    'failed_steps': failed_steps
                                })
    except Exception as e:
        log.error(f"Error parsing test results: {e}")
    
    return failed_details

def parse_pretty_format_failures(json_file_path):
    """Parse Behave 'pretty' formatter output to extract failing steps"""
    failures = []

    try:
        if not os.path.exists(json_file_path):
            return failures

        with open(json_file_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]

        current_feature = None
        current_feature_loc = None
        current_scenario = None
        current_scenario_loc = None
        failed_steps = []
        last_step = None

        feature_re = re.compile(r'^Feature:\s+(.*?)\s+#\s+(.*)$')
        scenario_re = re.compile(r'^\s*Scenario:\s+(.*?)\s+#\s+(.*)$')
        step_re = re.compile(r'^\s*(Given|When|Then|And|But)\s+(.*?)\s+#\s+(.*)$')
        assert_re = re.compile(r'^\s*ASSERT FAILED:\s*(.*)$')

        def flush_scenario():
            nonlocal current_feature, current_feature_loc, current_scenario, current_scenario_loc, failed_steps
            if current_feature and current_scenario and failed_steps:
                failures.append({
                    'feature': current_feature,
                    'feature_location': current_feature_loc or '',
                    'scenario': current_scenario,
                    'scenario_location': current_scenario_loc or '',
                    'failed_steps': failed_steps.copy()
                })
            failed_steps.clear()

        for raw in lines:
            line = raw.strip()
            if not line:
                continue

            m = feature_re.match(line)
            if m:
                flush_scenario()
                current_feature = m.group(1).strip()
                current_feature_loc = m.group(2).strip()
                current_scenario = None
                current_scenario_loc = None
                last_step = None
                continue

            m = scenario_re.match(line)
            if m:
                flush_scenario()
                current_scenario = m.group(1).strip()
                current_scenario_loc = m.group(2).strip()
                last_step = None
                continue

            m = step_re.match(line)
            if m:
                keyword, name, loc = m.groups()
                last_step = {
                    'step': f"{keyword} {name}",
                    'location': loc.strip(),
                    'error': '',
                    'status': 'passed'
                }
                continue

            m = assert_re.match(line)
            if m and last_step is not None:
                last_step_failed = last_step.copy()
                last_step_failed['error'] = f"ASSERT FAILED: {m.group(1).strip()}"
                last_step_failed['status'] = 'failed'
                failed_steps.append(last_step_failed)
                last_step = None

        flush_scenario()

    except Exception:
        return []

    return failures

def extract_errors_from_stdout(output):
    """Extract error messages from stdout output"""
    errors = []
    lines = output.split('\n')
    for line in lines:
        clean = line.strip()
        lower = clean.lower()

        if not clean or clean.startswith('{"keyword":') or clean.startswith('[{"keyword":'):
            continue

        if clean.startswith('USING RUNNER:') or clean in ['[', ']']:
            continue

        if (re.match(r'^\d+\s+features?\s+(passed|failed|skipped)', clean, flags=re.IGNORECASE) or
            re.match(r'^\d+\s+scenarios?\s+(passed|failed|skipped)', clean, flags=re.IGNORECASE) or
            re.match(r'^\d+\s+steps?\s+(passed|failed|skipped)', clean, flags=re.IGNORECASE) or
            clean.startswith('Failing scenarios:') or clean.startswith('Errored scenarios:') or
            clean.startswith('features/') and ':' in clean):
            continue

        if any(keyword in lower for keyword in ['error', 'failed', 'exception', 'traceback']):
            errors.append(clean)
    return errors[:10]

def display_failure_summary(json_file_path, stdout_output=None):
    """Display a detailed summary of failing tests"""
    if stdout_output:
        complete_summary = extract_failing_scenarios_summary(stdout_output)
        if complete_summary:
            print(complete_summary)
    
    failed_details = parse_test_results(json_file_path)
    
    if not failed_details:
        pretty_failures = parse_pretty_format_failures(json_file_path)
        if pretty_failures:
            failed_details = pretty_failures
        else:
            if stdout_output and ("error" in stdout_output.lower() or "failed" in stdout_output.lower()):
                extracted_errors = extract_errors_from_stdout(stdout_output)
                if extracted_errors:
                    print(f"\n{'='*70}")
                    print("⚠️  ERROR DETAILS FROM STDOUT")
                    print(f"{'='*70}")
                    for error in extracted_errors:
                        print(f"💥 {error}")
                    print(f"{'='*70}")
            return
    
    print(f"\n{'='*70}")
    print("❌ DETAILED FAILURE ANALYSIS - DEBUG INFORMATION")
    print(f"{'='*70}")
    
    for idx, failure in enumerate(failed_details, 1):
        print(f"\n📋 FAILED FEATURE {idx}:")
        print(f"   Name: {failure['feature']}")
        print(f"   📍 File: {failure['feature_location']}")
        
        print(f"\n🧪 FAILED SCENARIO:")
        print(f"   Name: {failure['scenario']}")
        print(f"   📍 Line: {failure['scenario_location']}")
        print(f"   {'─'*50}")
        
        for i, step in enumerate(failure['failed_steps'], 1):
            step_status = step.get('status', 'failed')
            status_icon = "💥" if step_status == 'error' else "❌"
            status_text = "ERRORED STEP" if step_status == 'error' else "FAILED STEP"
            
            print(f"\n{status_icon} {status_text} {i}:")
            print(f"   Step: {step['step']}")
            print(f"   📍 Location: {step['location']}")
            print(f"   {'─'*30}")
            print(f"   💥 ERROR MESSAGE:")
            
            error_lines = (step.get('error') or '').split('\n')
            for line in error_lines:
                if line.strip():
                    if "ASSERT FAILED" in line:
                        print(f"   🚨 {line.strip()}")
                    elif "Expected" in line or "Actual" in line:
                        print(f"   📝 {line.strip()}")
                    elif "Traceback" in line or "Exception" in line:
                        print(f"   💥 {line.strip()}")
                    else:
                        print(f"   ℹ️  {line.strip()}")
            
            # Add debugging tips
            if step_status == 'error':
                print(f"   💡 Debug Tip: Runtime error - check for exceptions, missing imports, or code issues")
            elif "Expected status" in step['error']:
                print(f"   💡 Debug Tip: Check API endpoint response and expected status code")
            elif "Response time" in step['error']:
                print(f"   💡 Debug Tip: API response time exceeded limit - check network/server performance")
            elif "Invalid todoId" in step['error']:
                print(f"   💡 Debug Tip: The todo ID format is not valid - check ID generation/format")
            
            if i < len(failure['failed_steps']):
                print(f"   {'─'*50}")

    if failed_details:
        print(f"\n{'='*70}")
        print("❌ FAILED STEP(S):")
        print(f"{'='*70}")
        for failure in failed_details:
            context = f"{failure.get('feature', '')} / {failure.get('scenario', '')}"
            for step in failure.get('failed_steps', []):
                print(f"  - {context}: {step.get('step', '')}")
        print(f"   {'─'*70}")

def extract_failing_scenarios_summary(output):
    """Extract a clean test summary including failing scenarios and statistics"""
    lines = output.split('\n')
    summary_lines = []
    capture_failing = False
    
    stats_lines = []
    for line in lines:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith('{"keyword":') or clean_line.startswith('[{"keyword":'):
            continue

        if "feature" in clean_line and any(word in clean_line for word in ["passed", "failed", "skipped", "error"]):
            stats_lines.append(('feature', clean_line))
        elif "scenario" in clean_line and any(word in clean_line for word in ["passed", "failed", "skipped", "error"]):
            stats_lines.append(('scenario', clean_line))
        elif "step" in clean_line and any(word in clean_line for word in ["passed", "failed", "skipped", "error"]):
            stats_lines.append(('steps', clean_line))
        elif "Took" in clean_line and ("min" in clean_line or "sec" in clean_line):
            stats_lines.append(('time', clean_line))

    if stats_lines:
        summary_lines.append(f"\n{'='*60}")
        summary_lines.append("📊 TEST EXECUTION SUMMARY:")
        summary_lines.append(f"{'='*60}")
        
        order = {'feature': 1, 'scenario': 2, 'steps': 3, 'time': 4}
        stats_lines.sort(key=lambda x: order.get(x[0], 5))
        
        for stat_type, stat in stats_lines:
            if ("failed" in stat.lower() and not ("0 failed" in stat.lower())) or ("error" in stat.lower() and not ("0 error" in stat.lower())):
                summary_lines.append(f"❌ {stat}")
            elif "passed" in stat.lower() or "Took" in stat:
                if stat_type == 'time':
                    summary_lines.append(f"📈 {stat}")
                else:
                    summary_lines.append(f"✅ {stat}")
            elif "skipped" in stat.lower() and not ("0 skipped" in stat.lower()):
                summary_lines.append(f"⚠️ {stat}")
            else:
                summary_lines.append(f"📈 {stat}")
        summary_lines.append(f"{'='*60}")

    capture_failing = False
    capture_errored = False
    
    for line in lines:
        clean_line = line.strip()
        
        if clean_line.startswith("Failing scenarios:"):
            capture_failing = True
            capture_errored = False
            summary_lines.append(f"\n{'='*60}")
            summary_lines.append("❌ FAILING SCENARIOS:")
            summary_lines.append(f"{'='*60}")
            continue
            
        if clean_line.startswith("Errored scenarios:"):
            capture_errored = True
            capture_failing = False
            summary_lines.append(f"\n{'='*60}")
            summary_lines.append("💥 ERRORED SCENARIOS:")
            summary_lines.append(f"{'='*60}")
            continue

        if (capture_failing or capture_errored):
            if clean_line and any(word in clean_line for word in ["features passed", "scenarios passed", "steps passed"]):
                capture_failing = False
                capture_errored = False
                continue
                
            if clean_line.startswith("features/"):
                parts = clean_line.split()
                if len(parts) >= 2:
                    location = parts[0]
                    scenario_name = " ".join(parts[1:])
                    icon = "💥" if capture_errored else "🔸"
                    summary_lines.append(f"  {icon} {location}")
                    summary_lines.append(f"     📝 {scenario_name}")
                else:
                    icon = "💥" if capture_errored else "🔸"
                    summary_lines.append(f"  {icon} {clean_line}")
            elif not clean_line and (capture_failing or capture_errored):
                capture_failing = False
                capture_errored = False

    return "\n".join(summary_lines) if summary_lines else ""

def record_test_results_for_flakiness(results: Dict, overall_success: bool):
    """Record test results in flakiness detector for historical analysis"""
    detector = get_flakiness_detector()
    
    if not results or 'scenarios' not in results:
        log.warning("No scenario results available for flakiness recording")
        return
    
    for scenario in results['scenarios']:
        test_name = f"{scenario.get('feature', 'Unknown')}/{scenario.get('name', 'Unknown')}"
        success = (scenario.get('status', 'failed') == 'passed')
        
        attempts = 1
        if 'duration' in scenario and scenario['duration'] > 10:
            attempts = 2
        
        detector.record_test_result(
            test_name=test_name,
            success=success,
            attempts=attempts
        )
        
        log.debug(f"Recorded flakiness data for: {test_name} (success: {success})")
    
    detector.record_test_result(
        test_name="Overall_Test_Execution",
        success=overall_success,
        attempts=1
    )
    
    log.info(f"Recorded {len(results['scenarios'])} scenario results for flakiness detection")

def parse_pretty_format_to_json(content: str) -> List:
    """Parse Behave pretty format output to JSON-like structure"""
    features = []
    feature_map = {}
    current_feature = None
    current_scenario = None
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('Feature:') and '#' in line:
            feature_match = re.match(r'Feature:\s+(.+?)\s+#\s+(.+)', line)
            if feature_match:
                feature_name = feature_match.group(1).strip()
                feature_location = feature_match.group(2).strip()
                
                if feature_name in feature_map:
                    current_feature = feature_map[feature_name]
                else:
                    current_feature = {
                        'keyword': 'Feature',
                        'name': feature_name,
                        'location': feature_location,
                        'elements': []
                    }
                    features.append(current_feature)
                    feature_map[feature_name] = current_feature
        
        elif line.startswith('Scenario:') and '#' in line and current_feature:
            scenario_match = re.match(r'Scenario:\s+(.+?)\s+#\s+(.+)', line)
            if scenario_match:
                scenario_name = scenario_match.group(1).strip()
                scenario_location = scenario_match.group(2).strip()
                
                existing_scenario = None
                for element in current_feature['elements']:
                    if element.get('name') == scenario_name and element.get('type') == 'scenario':
                        existing_scenario = element
                        break
                
                if existing_scenario:
                    current_scenario = existing_scenario
                else:
                    current_scenario = {
                        'type': 'scenario',
                        'keyword': 'Scenario',
                        'name': scenario_name,
                        'location': scenario_location,
                        'steps': []
                    }
                    current_feature['elements'].append(current_scenario)
        
        elif current_scenario and ('#' in line or 'ASSERT FAILED:' in line):
            if 'ASSERT FAILED:' in line:
                if current_scenario['steps']:
                    last_step = current_scenario['steps'][-1]
                    last_step['result'] = {
                        'status': 'failed',
                        'error_message': line.strip(),
                        'duration': 0
                    }
            elif '#' in line:
                step_match = re.match(r'\s*(Given|When|Then|And|But)\s+(.+?)\s+#\s+(.+)', line)
                if step_match:
                    keyword = step_match.group(1).strip()
                    step_name = step_match.group(2).strip()
                    step_location = step_match.group(3).strip()
                    
                    step_exists = False
                    for existing_step in current_scenario['steps']:
                        if (existing_step.get('keyword') == keyword and 
                            existing_step.get('name') == step_name and
                            existing_step.get('location') == step_location):
                            step_exists = True
                            break
                    
                    if not step_exists:
                        step = {
                            'keyword': keyword,
                            'name': step_name,
                            'location': step_location,
                            'result': {
                                'status': 'passed',
                                'duration': 0
                            }
                        }
                        current_scenario['steps'].append(step)
        
        i += 1
    
    return features

def load_test_results() -> Dict:
    """Load test results from JSON files"""
    results = {'scenarios': [], 'features': []}
    
    reports_dir = Path('reports')
    if reports_dir.exists():
        for result_file in reports_dir.glob('*_results.json'):
            try:
                if result_file.stat().st_size < 10:
                    continue
                    
                with open(result_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                if not content:
                    continue

                data = []
                if content.startswith('[') and content.endswith(']'):
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = []
                elif content.startswith('{'):
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and line.startswith('{'):
                            try:
                                data.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                else:
                    data = parse_pretty_format_to_json(content)
                    
                if isinstance(data, list):
                    for feature in data:
                        if 'elements' in feature:
                            actual_scenarios = []
                            for element in feature['elements']:
                                if element.get('type') == 'scenario':
                                    scenario_data = {
                                        'name': element.get('name', ''),
                                        'status': get_scenario_status(element),
                                        'duration': get_scenario_duration(element),
                                        'feature': feature.get('name', '')
                                    }
                                    results['scenarios'].append(scenario_data)
                                    actual_scenarios.append(element)
                        
                        if any(element.get('type') == 'scenario' for element in feature.get('elements', [])):
                            results['features'].append({
                                'name': feature.get('name', ''),
                                'status': get_feature_status(feature)
                            })
                        
            except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
                log.warning(f"Could not load results from {result_file}: {e}")
            except Exception as e:
                log.error(f"Unexpected error loading {result_file}: {e}")
        
        for name in ['all_results.json', 'ui_results.json', 'api_results.json']:
            result_file = reports_dir / name
            try:
                if not result_file.exists() or result_file.stat().st_size < 10:
                    continue
                with open(result_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if not content:
                    continue
                data = []
                if content.startswith('['):
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = []
                else:
                    data = parse_pretty_format_to_json(content)
                if isinstance(data, list):
                    for feature in data:
                        if 'elements' in feature:
                            for element in feature['elements']:
                                if element.get('type') == 'scenario':
                                    scenario_data = {
                                        'name': element.get('name', ''),
                                        'status': get_scenario_status(element),
                                        'duration': get_scenario_duration(element),
                                        'feature': feature.get('name', '')
                                    }
                                    results['scenarios'].append(scenario_data)
                        if any(element.get('type') == 'scenario' for element in feature.get('elements', [])):
                            results['features'].append({
                                'name': feature.get('name', ''),
                                'status': get_feature_status(feature)
                            })
            except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
                log.warning(f"Could not load results from {result_file}: {e}")
            except Exception as e:
                log.error(f"Unexpected error loading {result_file}: {e}")
    
    # Deduplicate results
    unique_scenarios = []
    seen_scenarios = set()
    for scenario in results['scenarios']:
        scenario_key = (scenario['name'], scenario['feature'], scenario['status'])
        if scenario_key not in seen_scenarios:
            unique_scenarios.append(scenario)
            seen_scenarios.add(scenario_key)
    
    unique_features = []
    seen_features = set()
    for feature in results['features']:
        feature_key = (feature['name'], feature['status'])
        if feature_key not in seen_features:
            unique_features.append(feature)
            seen_features.add(feature_key)
    
    results['scenarios'] = unique_scenarios
    results['features'] = unique_features
    
    return results

def get_scenario_status(scenario: Dict) -> str:
    """Extract scenario status from behave JSON"""
    if 'steps' in scenario:
        for step in scenario['steps']:
            if step.get('result', {}).get('status') == 'failed':
                return 'failed'
        return 'passed'
    return 'unknown'

def get_scenario_duration(scenario: Dict) -> float:
    """Extract scenario duration from behave JSON"""
    total_duration = 0.0
    if 'steps' in scenario:
        for step in scenario['steps']:
            result = step.get('result', {})
            duration = result.get('duration', 0)
            if isinstance(duration, (int, float)) and not math.isnan(duration):
                total_duration += float(duration)
    return round(total_duration, 3)

def get_feature_status(feature: Dict) -> str:
    """Extract feature status from behave JSON"""
    if 'elements' in feature:
        actual_scenarios = [elem for elem in feature['elements'] if elem.get('type') == 'scenario']
        
        if not actual_scenarios:
            return 'unknown'
            
        for scenario in actual_scenarios:
            if get_scenario_status(scenario) == 'failed':
                return 'failed'
        return 'passed'
    return 'unknown'

def generate_enhanced_reports(results: Dict, args):
    """Generate enhanced test reports"""
    try:
        reporter = get_enhanced_reporter()
        
        report_files = reporter.generate_comprehensive_report(results)
        
        log.info("Enhanced reports generated:")
        for report_type, file_path in report_files.items():
            if isinstance(file_path, list):
                log.info(f"  {report_type}: {len(file_path)} files")
                for file in file_path:
                    log.info(f"    - {file}")
            else:
                log.info(f"  {report_type}: {file_path}")
        
        reporter.save_historical_data(results)
        
        if args.trend_analysis:
            try:
                historical_file = Path('reports/historical_results.json')
                if historical_file.exists():
                    with open(historical_file, 'r') as f:
                        historical_data = json.load(f)
                    
                    trend_report = reporter.generator.generate_trend_report(historical_data)
                    log.info(f"Trend analysis report: {trend_report}")
                else:
                    log.warning("No historical data available for trend analysis")
            except Exception as e:
                log.warning(f"Could not generate trend report: {e}")
        
    except Exception as e:
        log.error(f"Failed to generate enhanced reports: {e}")

def analyze_test_flakiness():
    """Analyze test flakiness with enhanced reporting"""
    try:
        detector = get_flakiness_detector()
        flaky_tests = detector.get_flaky_tests()
        
        print(f"\n{'='*60}")
        print("🔬 FLAKINESS ANALYSIS REPORT")
        print(f"{'='*60}")
        
        if flaky_tests:
            log.warning(f"Found {len(flaky_tests)} potentially flaky tests:")
            print(f"🚨 Found {len(flaky_tests)} FLAKY TEST(S):")
            
            for i, test in enumerate(flaky_tests, 1):
                print(f"\n{i}. 📋 Test: {test['test_name']}")
                print(f"   🎯 Flakiness Confidence: {test['confidence']:.1%}")
                print(f"   📉 Failure Rate: {test['failure_rate']:.1%}")
                print(f"   🔄 Retry Rate: {test['retry_rate']:.1%}")
                print(f"   📊 Total Runs: {test['total_runs']}")
                print(f"   ❌ Failed Runs: {test['failed_runs']}")
                print(f"   🔁 Retry Runs: {test['retry_runs']}")
                
                if test['failure_rate'] > 0.5:
                    print(f"   💡 Recommendation: High failure rate - investigate test logic")
                elif test['retry_rate'] > 0.3:
                    print(f"   💡 Recommendation: High retry rate - check for timing issues")
                else:
                    print(f"   💡 Recommendation: Monitor this test - may be environment dependent")
                
                log.warning(f"  - {test['test_name']}: {test['confidence']:.2%} flakiness")
                
        else:
            print("✅ No flaky tests detected")
            log.info("No flaky tests detected")
            
            print(f"\n📊 Flakiness Detection Status:")
            
            if hasattr(detector, 'test_history') and detector.test_history:
                print(f"   📈 Test history available: {len(detector.test_history)} test(s)")
                
                for test_name, history in detector.test_history.items():
                    analysis = detector.analyze_flakiness(test_name)
                    total_runs = history['total_runs']
                    
                    if total_runs < 5:
                        print(f"   ⚠️  {test_name}: Only {total_runs} runs (need ≥5 for analysis)")
                    else:
                        confidence = analysis.get('confidence', 0)
                        print(f"   ✅ {test_name}: {total_runs} runs, {confidence:.1%} flakiness (below 30% threshold)")
                        
            else:
                print(f"   ❌ No test execution history found")
                print(f"   💡 Tip: Run tests multiple times with --analyze-flakiness to build history")
        
        save_flakiness_report(flaky_tests, detector)
        
        print(f"{'='*60}")
            
    except Exception as e:
        log.error(f"Flakiness analysis failed: {e}")
        print(f"❌ Flakiness analysis failed: {e}")

def save_flakiness_report(flaky_tests: List, detector):
    """Save flakiness analysis report to file"""
    try:
        report_data = {
            'timestamp': time.time(),
            'analysis_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'flaky_tests_found': len(flaky_tests),
            'flaky_tests': flaky_tests,
            'test_history_summary': {}
        }
        
        if hasattr(detector, 'test_history'):
            for test_name, history in detector.test_history.items():
                report_data['test_history_summary'][test_name] = {
                    'total_runs': history['total_runs'],
                    'failed_runs': history['failed_runs'],
                    'retry_runs': history['retry_runs']
                }
        
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"flakiness_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Flakiness report saved: {report_file}")
        
    except Exception as e:
        log.warning(f"Could not save flakiness report: {e}")

def cleanup_reports_folder():
    """Clean up reports folder and related directories except historical data"""
    directories_to_clean = ['reports', 'screenshots', 'traces', 'videos', 'har']
    preserved_files = ['historical_results.json', 'flakiness_history.json']
    
    cleaned_count = 0
    
    try:
        for dir_name in directories_to_clean:
            directory = Path(dir_name)
            
            if not directory.exists():
                log.debug(f"Directory {dir_name} does not exist, skipping cleanup")
                continue
                
            log.info(f"Cleaning directory: {dir_name}")
            
            if dir_name == 'reports':
                for item in directory.iterdir():
                    if item.is_file() and item.name not in preserved_files:
                        try:
                            item.unlink()
                            cleaned_count += 1
                            log.debug(f"Deleted report file: {item.name}")
                        except OSError as e:
                            log.warning(f"Could not delete {item.name}: {e}")
                    elif item.is_dir():
                        try:
                            shutil.rmtree(item)
                            cleaned_count += 1
                            log.debug(f"Deleted report directory: {item.name}")
                        except OSError as e:
                            log.warning(f"Could not delete directory {item.name}: {e}")
            else:
                for item in directory.iterdir():
                    if item.is_file():
                        try:
                            item.unlink()
                            cleaned_count += 1
                            log.debug(f"Deleted {dir_name} file: {item.name}")
                        except OSError as e:
                            log.warning(f"Could not delete {item.name} from {dir_name}: {e}")
                    elif item.is_dir():
                        try:
                            shutil.rmtree(item)
                            cleaned_count += 1
                            log.debug(f"Deleted {dir_name} directory: {item.name}")
                        except OSError as e:
                            log.warning(f"Could not delete directory {item.name} from {dir_name}: {e}")
        
        if cleaned_count > 0:
            log.info(f"Cleaned up {cleaned_count} old files/directories")
        else:
            log.info("No old files to clean up")
            
    except Exception as e:
        log.error(f"Error cleaning folders: {e}")

def setup_enhanced_environment():
    """Setup enhanced test environment"""
    cleanup_reports_folder()
    
    directories = ['reports', 'logs', 'screenshots', 'traces', 'videos']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        log.info(f"Created/ensured directory: {directory}")
    
    try:
        log.info("Test data manager initialized")
    except Exception as e:
        log.warning(f"Could not initialize test data manager: {e}")

def generate_allure_report():
    """Generate Allure report"""
    try:
        result = subprocess.run(
            ['allure.bat', 'generate', 'reports/allure-results', '-o', 'reports/allure-report', '--clean'],
            capture_output=True, text=True, shell=True
        )
        
        if result.returncode == 0:
            log.info("Allure report generated successfully")
            print("Allure report generated at: reports/allure-report/index.html")
            
            try:
                subprocess.run(['allure', 'open', 'reports/allure-report'], check=False)
            except:
                print("To view the report, run: allure open reports/allure-report")
        else:
            log.warning(f"Allure report generation failed: {result.stderr}")
    
    except Exception as e:
        log.warning(f"Could not generate Allure report: {e}")

def main():
    """Main function for enhanced test runner"""
    parser = argparse.ArgumentParser(description='Enhanced Playwright BDD Test Runner')
    
    parser.add_argument('--type', choices=['ui', 'api', 'all', 'smoke', 'regression'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--tags', type=str, help='Comma-separated list of tags to include')
    parser.add_argument('--parallel', type=int, help='Number of parallel processes')
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], 
                       default='chromium', help='Browser to use for UI tests')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--headed', action='store_true', help='Run browser in headed mode')
    parser.add_argument('--env', choices=['dev', 'stg', 'prod'], 
                       default='dev', help='Environment to run tests against')
    parser.add_argument('--retry', action='store_true', help='Enable test retry on failure')
    parser.add_argument('--max-retries', type=int, default=2, help='Maximum number of retries')
    parser.add_argument('--retry-all-failures', action='store_true', help='Retry ALL failures including assertion failures')
    parser.add_argument('--analyze-flakiness', action='store_true', help='Analyze test flakiness')
    parser.add_argument('--trend-analysis', action='store_true', help='Generate trend analysis report')
    parser.add_argument('--data-driven', action='store_true', help='Enable data-driven testing')
    parser.add_argument('--enhanced-reports', action='store_true', default=True, 
                       help='Generate enhanced reports with charts and analytics')
    parser.add_argument('--allure', action='store_true', help='Generate Allure report after tests')

    args = parser.parse_args()
    
    if args.retry:
        retry_handler = get_retry_handler()
        retry_handler.default_config = RetryConfig(max_attempts=args.max_retries + 1)
        os.environ['MAX_RETRIES'] = str(args.max_retries)
        
    if args.allure:
        os.environ['ENABLE_ALLURE'] = 'true'
        log.info("Allure reporting enabled - data will be collected during test execution")
    
    success = run_tests_with_enhanced_features(args)
    
    if args.allure:
        generate_allure_report()
    
    if success:
        print("✅ Enhanced test execution completed successfully")
        sys.exit(0)
    else:
        print("❌ Enhanced test execution failed")
        sys.exit(1)

if __name__ == '__main__':
    main()