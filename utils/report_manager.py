
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class ReportManager:
    """Manages test reporting and metrics collection"""
    
    def __init__(self, report_dir: str = "reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.test_results = []
        self.test_metrics = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'features': {},
            'browser_info': {},
            'environment': None
        }
    
    def start_test_run(self, environment: str, browser_info: Dict[str, Any]) -> None:
        """Initialize test run metrics"""
        self.test_metrics['start_time'] = datetime.now().isoformat()
        self.test_metrics['environment'] = environment
        self.test_metrics['browser_info'] = browser_info
    
    def end_test_run(self) -> None:
        """Finalize test run metrics"""
        self.test_metrics['end_time'] = datetime.now().isoformat()
        
        if self.test_metrics['start_time']:
            start = datetime.fromisoformat(self.test_metrics['start_time'])
            end = datetime.fromisoformat(self.test_metrics['end_time'])
            self.test_metrics['duration'] = (end - start).total_seconds()
    
    def add_test_result(self, feature_name: str, scenario_name: str, status: str, 
                       duration: float = 0, error_message: str = None, 
                       screenshot_path: str = None, trace_path: str = None) -> None:
        """Add a test result to the report"""
        result = {
            'feature': feature_name,
            'scenario': scenario_name,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'error_message': error_message,
            'screenshot_path': screenshot_path,
            'trace_path': trace_path
        }
        
        self.test_results.append(result)
        
        # Update metrics
        self.test_metrics['total_tests'] += 1
        
        if status == 'passed':
            self.test_metrics['passed_tests'] += 1
        elif status == 'failed':
            self.test_metrics['failed_tests'] += 1
        elif status == 'skipped':
            self.test_metrics['skipped_tests'] += 1
        
        # Update feature metrics
        if feature_name not in self.test_metrics['features']:
            self.test_metrics['features'][feature_name] = {
                'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0
            }
        
        feature_metrics = self.test_metrics['features'][feature_name]
        feature_metrics['total'] += 1
        feature_metrics[status] += 1
    
    def generate_html_report(self) -> str:
        """Generate HTML test report"""
        html_template = self._get_html_template()
        
        # Calculate pass rate
        pass_rate = 0
        if self.test_metrics['total_tests'] > 0:
            pass_rate = (self.test_metrics['passed_tests'] / self.test_metrics['total_tests']) * 100
        
        # Generate test results table
        results_html = self._generate_results_table()
        
        # Generate feature summary
        feature_summary_html = self._generate_feature_summary()
        
        # Replace placeholders in template
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            environment=self.test_metrics['environment'],
            browser=self.test_metrics['browser_info'].get('name', 'Unknown'),
            total_tests=self.test_metrics['total_tests'],
            passed_tests=self.test_metrics['passed_tests'],
            failed_tests=self.test_metrics['failed_tests'],
            skipped_tests=self.test_metrics['skipped_tests'],
            pass_rate=f"{pass_rate:.1f}%",
            duration=f"{self.test_metrics['duration']:.2f}s",
            results_table=results_html,
            feature_summary=feature_summary_html
        )
        
        # Save HTML report
        report_path = self.report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, 'w') as file:
            file.write(html_content)
        
        return str(report_path)
    
    def generate_json_report(self) -> str:
        """Generate JSON test report"""
        report_data = {
            'metrics': self.test_metrics,
            'results': self.test_results,
            'generated_at': datetime.now().isoformat()
        }
        
        report_path = self.report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as file:
            json.dump(report_data, file, indent=2)
        
        return str(report_path)
    
    def generate_junit_xml(self) -> str:
        """Generate JUnit XML report"""
        xml_content = self._get_junit_xml_template()
        
        # Generate test cases XML
        testcases_xml = ""
        for result in self.test_results:
            testcase_xml = f'''
        <testcase classname="{result['feature']}" name="{result['scenario']}" time="{result['duration']}">'''
            
            if result['status'] == 'failed':
                testcase_xml += f'''
            <failure message="{result.get('error_message', 'Test failed')}">{result.get('error_message', '')}</failure>'''
            elif result['status'] == 'skipped':
                testcase_xml += '''
            <skipped/>'''
            
            testcase_xml += '''
        </testcase>'''
            testcases_xml += testcase_xml
        
        # Replace placeholders
        xml_content = xml_content.format(
            tests=self.test_metrics['total_tests'],
            failures=self.test_metrics['failed_tests'],
            skipped=self.test_metrics['skipped_tests'],
            time=self.test_metrics['duration'],
            timestamp=self.test_metrics['start_time'],
            testcases=testcases_xml
        )
        
        report_path = self.report_dir / f"junit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        with open(report_path, 'w') as file:
            file.write(xml_content)
        
        return str(report_path)
    
    def _generate_results_table(self) -> str:
        """Generate HTML table for test results"""
        html = ""
        for result in self.test_results:
            status_class = f"status-{result['status']}"
            screenshot_link = ""
            
            if result.get('screenshot_path'):
                screenshot_link = f'<a href="{result["screenshot_path"]}" target="_blank">Screenshot</a>'
            
            html += f'''
            <tr class="{status_class}">
                <td>{result['feature']}</td>
                <td>{result['scenario']}</td>
                <td><span class="status {status_class}">{result['status'].upper()}</span></td>
                <td>{result['duration']:.2f}s</td>
                <td>{result.get('error_message', '')}</td>
                <td>{screenshot_link}</td>
            </tr>'''
        
        return html
    
    def _generate_feature_summary(self) -> str:
        """Generate HTML for feature summary"""
        html = ""
        for feature_name, metrics in self.test_metrics['features'].items():
            pass_rate = (metrics['passed'] / metrics['total']) * 100 if metrics['total'] > 0 else 0
            
            html += f'''
            <tr>
                <td>{feature_name}</td>
                <td>{metrics['total']}</td>
                <td>{metrics['passed']}</td>
                <td>{metrics['failed']}</td>
                <td>{metrics['skipped']}</td>
                <td>{pass_rate:.1f}%</td>
            </tr>'''
        
        return html
    
    def _get_html_template(self) -> str:
        """Get HTML report template"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 10px; background-color: #e9e9e9; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .status-passed {{ background-color: #d4edda; }}
        .status-failed {{ background-color: #f8d7da; }}
        .status-skipped {{ background-color: #fff3cd; }}
        .status.status-passed {{ color: #155724; background-color: #d4edda; padding: 2px 8px; border-radius: 3px; }}
        .status.status-failed {{ color: #721c24; background-color: #f8d7da; padding: 2px 8px; border-radius: 3px; }}
        .status.status-skipped {{ color: #856404; background-color: #fff3cd; padding: 2px 8px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Environment:</strong> {environment}</p>
        <p><strong>Browser:</strong> {browser}</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>{total_tests}</h3>
            <p>Total Tests</p>
        </div>
        <div class="metric">
            <h3>{passed_tests}</h3>
            <p>Passed</p>
        </div>
        <div class="metric">
            <h3>{failed_tests}</h3>
            <p>Failed</p>
        </div>
        <div class="metric">
            <h3>{skipped_tests}</h3>
            <p>Skipped</p>
        </div>
        <div class="metric">
            <h3>{pass_rate}</h3>
            <p>Pass Rate</p>
        </div>
        <div class="metric">
            <h3>{duration}</h3>
            <p>Duration</p>
        </div>
    </div>
    
    <h2>Feature Summary</h2>
    <table>
        <thead>
            <tr>
                <th>Feature</th>
                <th>Total</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Pass Rate</th>
            </tr>
        </thead>
        <tbody>
            {feature_summary}
        </tbody>
    </table>
    
    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Feature</th>
                <th>Scenario</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Error Message</th>
                <th>Artifacts</th>
            </tr>
        </thead>
        <tbody>
            {results_table}
        </tbody>
    </table>
</body>
</html>'''
    
    def _get_junit_xml_template(self) -> str:
        """Get JUnit XML report template"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite tests="{tests}" failures="{failures}" skipped="{skipped}" time="{time}" timestamp="{timestamp}">
    {testcases}
</testsuite>'''


# Global report manager instance
report_manager = ReportManager()


def get_report_manager() -> ReportManager:
    """Get global report manager instance"""
    return report_manager

