import os
import sys
import subprocess
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.config_manager import get_config
from utils import logger

log = logger.customLogger()

class ParallelTestRunner:
    """Advanced parallel test execution manager"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 4)
        self.config = get_config()
        
    def run_tests_parallel(self, test_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run test groups in parallel"""
        log.info(f"Starting parallel execution with {self.max_workers} workers")
        
        results = {
            'total_groups': len(test_groups),
            'passed': 0,
            'failed': 0,
            'group_results': []
        }
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all test groups
            future_to_group = {
                executor.submit(self._run_test_group, group): group 
                for group in test_groups
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_group):
                group = future_to_group[future]
                try:
                    result = future.result()
                    results['group_results'].append(result)
                    
                    if result['success']:
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        
                    log.info(f"Group '{group['name']}' completed: {'PASSED' if result['success'] else 'FAILED'}")
                    
                except Exception as e:
                    log.error(f"Group '{group['name']}' failed with exception: {e}")
                    results['failed'] += 1
                    results['group_results'].append({
                        'group_name': group['name'],
                        'success': False,
                        'error': str(e),
                        'duration': 0
                    })
        
        log.info(f"Parallel execution completed: {results['passed']} passed, {results['failed']} failed")
        return results
    
    def _run_test_group(self, group: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test group"""
        import time
        start_time = time.time()
        
        group_name = group['name']
        tags = group.get('tags', [])
        features = group.get('features', [])
        test_type = group.get('type', 'ui')
        scenarios = group.get('scenarios', [])  # Specific scenarios to run
        
        log.info(f"Starting test group: {group_name}")
        
        try:
            # Build behave command
            cmd = [sys.executable, '-m', 'behave']
            
            # Add features or use default
            if features:
                cmd.extend(features)
            else:
                cmd.extend(['features'])
            
            # Add tags
            for tag in tags:
                cmd.extend(['-t', tag])
            
            # Add specific scenarios if provided (for scenario-level parallelization)
            if scenarios:
                for scenario in scenarios:
                    cmd.extend(['--name', scenario])
            
            # Add output format
            output_file = f"reports/{group_name.replace(' ', '_').lower()}_results.json"
            cmd.extend(['-f', 'json', '-o', output_file])
            
            # Set environment variables
            env = os.environ.copy()
            if test_type == 'api':
                env['API_ONLY'] = 'true'
                env['SKIP_BROWSER'] = 'true'
            
            # Run the command with real-time output
            log.info(f"Running command for {group_name}: {' '.join(cmd)}")
            
            # Use Popen for real-time output streaming
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, 
                bufsize=1, 
                universal_newlines=True
            )
            
            # Capture output for later analysis while showing real-time
            captured_output = []
            
            # Stream output in real-time with cleaner formatting
            for line in iter(process.stdout.readline, ''):
                captured_output.append(line)
                # Only show important lines to avoid clutter in parallel execution
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('{"keyword":') and not clean_line.startswith('[{"keyword":'):
                    # Show key information with group prefix
                    if any(keyword in clean_line.lower() for keyword in ['info', 'error', 'warning', 'starting', 'completed', 'failed', 'passed']):
                        prefixed_line = f"[{group_name}] {clean_line}"
                        print(prefixed_line)
                
            # Wait for process completion
            process.stdout.close()
            return_code = process.wait()
            
            duration = time.time() - start_time
            success = return_code == 0
            full_output = ''.join(captured_output)
            
            log.info(f"Group {group_name} completed with return code {return_code}")
            
            return {
                'group_name': group_name,
                'success': success,
                'duration': duration,
                'output_file': output_file,
                'stdout': full_output,
                'stderr': '',  # stderr is combined with stdout
                'return_code': return_code
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            log.error(f"Test group '{group_name}' timed out after 1 hour")
            return {
                'group_name': group_name,
                'success': False,
                'duration': duration,
                'error': 'Test execution timed out',
                'return_code': -1
            }
        except Exception as e:
            duration = time.time() - start_time
            log.error(f"Test group '{group_name}' failed: {e}")
            return {
                'group_name': group_name,
                'success': False,
                'duration': duration,
                'error': str(e),
                'return_code': -1
            }
    
    def create_test_groups_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Create test groups based on tags"""
        groups = []
        for tag in tags:
            groups.append({
                'name': f"Tests with tag {tag}",
                'tags': [tag],
                'type': 'api' if 'api' in tag.lower() else 'ui'
            })
        return groups
    
    def create_test_groups_by_features(self, feature_files: List[str]) -> List[Dict[str, Any]]:
        """Create test groups based on feature files"""
        groups = []
        for feature_file in feature_files:
            feature_name = Path(feature_file).stem
            groups.append({
                'name': f"Feature {feature_name}",
                'features': [feature_file],
                'type': 'api' if 'api' in feature_name.lower() else 'ui'
            })
        return groups
    
    def create_balanced_groups(self, scenarios: List[Dict[str, Any]], group_count: int) -> List[Dict[str, Any]]:
        """Create balanced test groups for optimal parallel execution"""
        # Simple round-robin distribution
        groups = [{'name': f'Group {i+1}', 'scenarios': [], 'tags': []} for i in range(group_count)]
        
        for i, scenario in enumerate(scenarios):
            group_index = i % group_count
            groups[group_index]['scenarios'].append(scenario)
            
            # Add scenario tags to group tags
            scenario_tags = scenario.get('tags', [])
            for tag in scenario_tags:
                if tag not in groups[group_index]['tags']:
                    groups[group_index]['tags'].append(tag)
        
        return groups


class TestGroupBuilder:
    """Builder for creating test execution groups"""
    
    def __init__(self):
        self.groups = []
    
    def add_smoke_tests(self) -> 'TestGroupBuilder':
        """Add smoke test group"""
        self.groups.append({
            'name': 'Smoke Tests',
            'tags': ['@smoke'],
            'type': 'mixed'
        })
        return self
    
    def add_api_tests(self) -> 'TestGroupBuilder':
        """Add API test group"""
        self.groups.append({
            'name': 'API Tests',
            'tags': ['@api'],
            'type': 'api'
        })
        return self
    
    def add_ui_tests(self) -> 'TestGroupBuilder':
        """Add UI test group"""
        self.groups.append({
            'name': 'UI Tests',
            'tags': ['@ui'],
            'type': 'ui'
        })
        return self
    
    def add_regression_tests(self) -> 'TestGroupBuilder':
        """Add regression test group"""
        self.groups.append({
            'name': 'Regression Tests',
            'tags': ['@regression'],
            'type': 'mixed'
        })
        return self
    
    def add_custom_group(self, name: str, tags: List[str], test_type: str = 'mixed') -> 'TestGroupBuilder':
        """Add custom test group"""
        self.groups.append({
            'name': name,
            'tags': tags,
            'type': test_type
        })
        return self
    
    def build(self) -> List[Dict[str, Any]]:
        """Build and return test groups"""
        return self.groups.copy()


def create_default_parallel_groups() -> List[Dict[str, Any]]:
    """Create default parallel test groups"""
    builder = TestGroupBuilder()
    return (builder
            .add_smoke_tests()
            .add_api_tests()
            .add_ui_tests()
            .add_regression_tests()
            .build())


def run_parallel_tests(groups: Optional[List[Dict[str, Any]]] = None, max_workers: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function to run parallel tests"""
    if groups is None:
        groups = create_default_parallel_groups()
    
    runner = ParallelTestRunner(max_workers=max_workers)
    return runner.run_tests_parallel(groups)

