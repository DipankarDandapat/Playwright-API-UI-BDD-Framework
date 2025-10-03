
import json
import time
import math
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template
import matplotlib.pyplot as plt

from utils import logger
log = logger.customLogger()

# Suppress matplotlib and numpy warnings for division by zero/NaN
warnings.filterwarnings('ignore', category=RuntimeWarning, module='matplotlib')
warnings.filterwarnings('ignore', category=RuntimeWarning, module='numpy')



class TestMetrics:
    """Test execution metrics calculator"""

    
    def calculate_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive test metrics"""
        scenarios = results.get('scenarios', [])
        features = results.get('features', [])
        
        total_scenarios = len(scenarios)
        passed_scenarios = len([s for s in scenarios if s.get('status') == 'passed'])
        failed_scenarios = len([s for s in scenarios if s.get('status') == 'failed'])
        skipped_scenarios = len([s for s in scenarios if s.get('status') == 'skipped'])
        
        total_features = len(features)
        passed_features = len([f for f in features if f.get('status') == 'passed'])
        failed_features = len([f for f in features if f.get('status') == 'failed'])
        
        # Calculate durations with NaN handling
        valid_durations = [s.get('duration', 0) for s in scenarios if isinstance(s.get('duration', 0), (int, float)) and not math.isnan(s.get('duration', 0))]
        total_duration = sum(valid_durations)
        avg_scenario_duration = total_duration / total_scenarios if total_scenarios > 0 else 0
        
        # Calculate pass rates with safe division
        scenario_pass_rate = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0
        feature_pass_rate = (passed_features / total_features * 100) if total_features > 0 else 0
        
        # Ensure no NaN values
        scenario_pass_rate = 0 if math.isnan(scenario_pass_rate) else scenario_pass_rate
        feature_pass_rate = 0 if math.isnan(feature_pass_rate) else feature_pass_rate
        avg_scenario_duration = 0 if math.isnan(avg_scenario_duration) else avg_scenario_duration
        
        return {
            'summary': {
                'total_scenarios': total_scenarios,
                'passed_scenarios': passed_scenarios,
                'failed_scenarios': failed_scenarios,
                'skipped_scenarios': skipped_scenarios,
                'scenario_pass_rate': round(scenario_pass_rate, 2),
                'total_features': total_features,
                'passed_features': passed_features,
                'failed_features': failed_features,
                'feature_pass_rate': round(feature_pass_rate, 2),
                'total_duration': round(total_duration, 2),
                'avg_scenario_duration': round(avg_scenario_duration, 2)
            },
            'detailed_scenarios': scenarios,
            'detailed_features': features
        }
    
    def calculate_trend_metrics(self, historical_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend metrics from historical data"""
        if not historical_results:
            return {}
        
        trends = {
            'pass_rate_trend': [],
            'duration_trend': [],
            'scenario_count_trend': [],
            'dates': []
        }
        
        for result in historical_results:
            metrics = self.calculate_metrics(result)
            summary = metrics['summary']
            
            trends['pass_rate_trend'].append(summary['scenario_pass_rate'])
            trends['duration_trend'].append(summary['total_duration'])
            trends['scenario_count_trend'].append(summary['total_scenarios'])
            trends['dates'].append(result.get('timestamp', datetime.now().isoformat()))
        
        return trends


class ReportGenerator:
    """Generate various types of test reports"""
    
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics = TestMetrics()
    
    def generate_html_report(self, results: Dict[str, Any], template_name: str = 'default') -> str:
        """Generate HTML test report"""
        metrics = self.metrics.calculate_metrics(results)
        
        html_template = self._get_html_template(template_name)
        
        report_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': metrics,
            'results': results
        }
        
        html_content = html_template.render(**report_data)
        
        report_file = self.output_dir / f'test_report_{int(time.time())}.html'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log.info(f"HTML report generated: {report_file}")
        return str(report_file)
    
    def generate_json_report(self, results: Dict[str, Any]) -> str:
        """Generate JSON test report"""
        metrics = self.metrics.calculate_metrics(results)
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'raw_results': results
        }
        
        report_file = self.output_dir / f'test_report_{int(time.time())}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        log.info(f"JSON report generated: {report_file}")
        return str(report_file)
    
    def generate_charts(self, results: Dict[str, Any]) -> List[str]:
        """Generate test result charts"""
        chart_files = []
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                
                metrics = self.metrics.calculate_metrics(results)
                summary = metrics['summary']
                
                # Pass/Fail pie chart
                pie_chart = self._create_pass_fail_chart(summary)
                if pie_chart:
                    chart_files.append(pie_chart)
                
                # Duration bar chart
                duration_chart = self._create_duration_chart(metrics['detailed_scenarios'])
                if duration_chart:
                    chart_files.append(duration_chart)
                
                # Feature status chart
                feature_chart = self._create_feature_status_chart(metrics['detailed_features'])
                if feature_chart:
                    chart_files.append(feature_chart)
                    
        except Exception as e:
            log.warning(f"Failed to generate some charts: {e}")
        
        return chart_files
    
    def generate_trend_report(self, historical_results: List[Dict[str, Any]]) -> str:
        """Generate trend analysis report"""
        trends = self.metrics.calculate_trend_metrics(historical_results)
        
        if not trends:
            log.warning("No historical data available for trend analysis")
            return ""
        
        # Create trend charts
        trend_charts = self._create_trend_charts(trends)
        
        # Generate HTML report with trends
        html_template = self._get_html_template('trend')
        
        report_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trends': trends,
            'charts': trend_charts
        }
        
        html_content = html_template.render(**report_data)
        
        report_file = self.output_dir / f'trend_report_{int(time.time())}.html'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log.info(f"Trend report generated: {report_file}")
        return str(report_file)
    
    def _create_pass_fail_chart(self, summary: Dict[str, Any]) -> str:
        """Create pass/fail pie chart"""
        plt.figure(figsize=(8, 6))
        
        labels = ['Passed', 'Failed', 'Skipped']
        sizes = [
            int(summary['passed_scenarios'] or 0),
            int(summary['failed_scenarios'] or 0),
            int(summary['skipped_scenarios'] or 0)
        ]
        colors = ['#28a745', '#dc3545', '#ffc107']
        
        # Remove zero values and handle NaN
        valid_data = []
        for label, size, color in zip(labels, sizes, colors):
            if isinstance(size, (int, float)) and not math.isnan(size) and size > 0:
                valid_data.append((label, int(size), color))
        
        if not valid_data:
            # Create default chart if no valid data
            valid_data = [('No Data', 1, '#6c757d')]
            
        if valid_data:
            labels, sizes, colors = zip(*valid_data)
        
        # Ensure sizes are valid numbers
        sizes = [max(0, int(s)) for s in sizes]
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Test Results Distribution')
        plt.axis('equal')
        
        chart_file = self.output_dir / f'pass_fail_chart_{int(time.time())}.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_file)
    
    def _create_duration_chart(self, scenarios: List[Dict[str, Any]]) -> str:
        """Create scenario duration bar chart"""
        if not scenarios:
            return ""
        
        plt.figure(figsize=(12, 6))
        
        scenario_names = [s.get('name', f"Scenario {i}") for i, s in enumerate(scenarios)]
        durations = []
        
        # Clean duration data
        for s in scenarios:
            duration = s.get('duration', 0)
            if isinstance(duration, (int, float)) and not math.isnan(duration) and duration >= 0:
                durations.append(float(duration))
            else:
                durations.append(0.0)
        
        # Filter out scenarios with zero durations for better visualization
        valid_data = [(name, duration) for name, duration in zip(scenario_names, durations) if duration > 0]
        
        if not valid_data:
            # If no valid durations, create a simple chart
            valid_data = [('No Duration Data', 0.1)]
        
        # Limit to top 20 longest scenarios
        if len(valid_data) > 20:
            valid_data = sorted(valid_data, key=lambda x: x[1], reverse=True)[:20]
        
        names, durations = zip(*valid_data) if valid_data else ([], [])
        
        if names and durations:
            plt.bar(range(len(names)), durations)
            plt.xlabel('Scenarios')
            plt.ylabel('Duration (seconds)')
            plt.title('Scenario Execution Duration')
            plt.xticks(range(len(names)), names, rotation=45, ha='right')
        
        chart_file = self.output_dir / f'duration_chart_{int(time.time())}.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_file)
    
    def _create_feature_status_chart(self, features: List[Dict[str, Any]]) -> str:
        """Create feature status chart"""
        if not features:
            return ""
        
        plt.figure(figsize=(10, 6))
        
        feature_names = [f.get('name', f"Feature {i}") for i, f in enumerate(features)]
        statuses = [f.get('status', 'unknown') for f in features]
        
        status_colors = {'passed': '#28a745', 'failed': '#dc3545', 'skipped': '#ffc107'}
        colors = [status_colors.get(status, '#6c757d') for status in statuses]
        
        plt.bar(range(len(feature_names)), [1] * len(feature_names), color=colors)
        plt.xlabel('Features')
        plt.ylabel('Status')
        plt.title('Feature Test Status')
        plt.xticks(range(len(feature_names)), feature_names, rotation=45, ha='right')
        
        # Add legend
        unique_statuses = list(set(statuses))
        legend_colors = [status_colors.get(status, '#6c757d') for status in unique_statuses]
        plt.legend([plt.Rectangle((0,0),1,1, color=color) for color in legend_colors], unique_statuses)
        
        chart_file = self.output_dir / f'feature_status_chart_{int(time.time())}.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_file)
    
    def _create_trend_charts(self, trends: Dict[str, Any]) -> List[str]:
        """Create trend analysis charts"""
        chart_files = []
        
        # Clean trend data
        dates = trends.get('dates', [])
        pass_rates = [float(rate) if isinstance(rate, (int, float)) and not math.isnan(rate) else 0.0 
                     for rate in trends.get('pass_rate_trend', [])]
        durations = [float(dur) if isinstance(dur, (int, float)) and not math.isnan(dur) else 0.0 
                    for dur in trends.get('duration_trend', [])]
        
        if not dates or not pass_rates:
            return chart_files
        
        # Pass rate trend
        plt.figure(figsize=(12, 6))
        
        # Handle case where we have valid data
        if len(dates) == len(pass_rates) and len(dates) > 0:
            plt.plot(range(len(dates)), pass_rates, marker='o')
            plt.xlabel('Test Runs')
            plt.ylabel('Pass Rate (%)')
            plt.title('Test Pass Rate Trend')
            plt.xticks(range(len(dates)), [d[:10] if isinstance(d, str) else str(d) for d in dates], rotation=45)
        else:
            plt.text(0.5, 0.5, 'No trend data available', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Test Pass Rate Trend - No Data')
        
        plt.grid(True)
        
        #chart_file = self.output_dir / f'pass_rate_trend_{int(time.time())}.png'
        filename = f"pass_rate_trend_{int(time.time())}.png"
        chart_file = self.output_dir / filename

        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
         # Append only the relative path (with leading slash if you want)
        chart_files.append(f"{filename}")
        #chart_files.append(str(chart_file))
        
        # Duration trend
        plt.figure(figsize=(12, 6))
        
        if len(dates) == len(durations) and len(dates) > 0:
            plt.plot(range(len(dates)), durations, marker='s', color='orange')
            plt.xlabel('Test Runs')
            plt.ylabel('Total Duration (seconds)')
            plt.title('Test Execution Duration Trend')
            plt.xticks(range(len(dates)), [d[:10] if isinstance(d, str) else str(d) for d in dates], rotation=45)
        else:
            plt.text(0.5, 0.5, 'No trend data available', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Test Duration Trend - No Data')
        
        plt.grid(True)
        
        #chart_file = self.output_dir / f'duration_trend_{int(time.time())}.png'
        filename = f"duration_trend_{int(time.time())}.png"
        chart_file = self.output_dir / filename 
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(f"{filename}")
        #chart_files.append(str(chart_file))
        
        return chart_files
    
    def _get_html_template(self, template_name: str) -> Template:
        """Get HTML template for report generation"""
        if template_name == 'trend':
            template_content = self._get_trend_template()
        else:
            template_content = self._get_default_template()
        
        return Template(template_content)
    
    def _get_default_template(self) -> str:
        """Get default HTML template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background-color: #fff; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; }
        .metric-label { color: #6c757d; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p>Generated on: {{ timestamp }}</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value passed">{{ metrics.summary.passed_scenarios }}</div>
            <div class="metric-label">Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value failed">{{ metrics.summary.failed_scenarios }}</div>
            <div class="metric-label">Failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value skipped">{{ metrics.summary.skipped_scenarios }}</div>
            <div class="metric-label">Skipped</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ metrics.summary.scenario_pass_rate }}%</div>
            <div class="metric-label">Pass Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ metrics.summary.total_duration }}s</div>
            <div class="metric-label">Total Duration</div>
        </div>
    </div>
    
    <h2>Scenario Details</h2>
    <table>
        <thead>
            <tr>
                <th>Feature</th>
                <th>Scenario</th>
                <th>Status</th>
                <th>Duration</th>
                
            </tr>
        </thead>
        <tbody>
            {% for scenario in metrics.detailed_scenarios %}
            <tr>
                <td>{{ scenario.feature }}</td>
                <td>{{ scenario.name }}</td>
                <td class="{{ scenario.status }}">{{ scenario.status }}</td>
                <td>{{ scenario.duration }}s</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
        """
    
    def _get_trend_template(self) -> str:
        """Get trend analysis HTML template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Test Trend Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
        .chart-container { margin: 20px 0; text-align: center; }
        .chart-container img { max-width: 70%; height: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Trend Analysis Report</h1>
        <p>Generated on: {{ timestamp }}</p>
    </div>
    
    <div class="chart-container">
        <h2>Test Trends</h2>
        {% for chart in charts %}
        <img src="{{ chart }}" alt="Trend Chart">
        {% endfor %}
    </div>
</body>
</html>
        """


class EnhancedReporter:
    """Main enhanced reporting class"""
    
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.generator = ReportGenerator(output_dir)
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Generate comprehensive test report with multiple formats"""
        report_files = {}
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                
                # Generate HTML report
                try:
                    html_report = self.generator.generate_html_report(results)
                    report_files['html'] = html_report
                except Exception as e:
                    log.warning(f"Failed to generate HTML report: {e}")
                
                # Generate JSON report
                try:
                    json_report = self.generator.generate_json_report(results)
                    report_files['json'] = json_report
                except Exception as e:
                    log.warning(f"Failed to generate JSON report: {e}")
                
                # Generate charts
                try:
                    charts = self.generator.generate_charts(results)
                    if charts:
                        report_files['charts'] = charts
                except Exception as e:
                    log.warning(f"Failed to generate charts: {e}")
                
                log.info(f"Comprehensive report generated with {len(report_files)} components")
                
        except Exception as e:
            log.error(f"Failed to generate comprehensive report: {e}")
            # Don't re-raise, return partial results instead
        
        return report_files
    
    def save_historical_data(self, results: Dict[str, Any]) -> None:
        """Save test results for historical trend analysis"""
        historical_file = self.output_dir / 'historical_results.json'
        
        # Add timestamp to results
        results['timestamp'] = datetime.now().isoformat()
        
        # Load existing historical data
        historical_data = []
        if historical_file.exists():
            try:
                with open(historical_file, 'r') as f:
                    historical_data = json.load(f)
            except Exception as e:
                log.warning(f"Could not load historical data: {e}")
        
        # Add new results
        historical_data.append(results)
        
        # Keep only last 50 results
        if len(historical_data) > 50:
            historical_data = historical_data[-50:]
        
        # Save updated historical data
        try:
            with open(historical_file, 'w') as f:
                json.dump(historical_data, f, indent=2, default=str)
            log.info("Historical data updated")
        except Exception as e:
            log.error(f"Failed to save historical data: {e}")


# Global instance for easy access
enhanced_reporter = EnhancedReporter()


def get_enhanced_reporter() -> EnhancedReporter:
    """Get enhanced reporter instance"""
    return enhanced_reporter

