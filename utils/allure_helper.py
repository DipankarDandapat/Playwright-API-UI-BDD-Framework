
import json
import hashlib
import os
from functools import wraps


class AllureHelper:
    """Helper class to handle Allure reporting functionality"""
    
    def __init__(self):
        self._attached_content_hashes = set()
        self._allure = None
        self._allure_enabled = None  # Lazy initialization
    
    @property
    def allure_enabled(self):
        """Lazy property to check if Allure is enabled"""
        if self._allure_enabled is None:
            self._allure_enabled = self._check_allure_availability()
        return self._allure_enabled
    
    @property
    def allure(self):
        """Lazy property to get the allure module"""
        if self._allure is None and self.allure_enabled:
            try:
                import allure
                self._allure = allure
            except ImportError:
                self._allure = None
        return self._allure
    
    def _check_allure_availability(self):
        """Check if Allure is enabled and available"""
        if os.environ.get('ENABLE_ALLURE', 'false').lower() != 'true':
            return False
        
        try:
            import allure
            return True
        except ImportError:
            return False
    
    def _is_allure_behave_formatter_active(self):
        """Check if allure-behave formatter is being used"""
        import sys
        # Check if behave is running with allure formatter
        if 'behave' in sys.modules:
            # Check command line arguments for allure formatter
            if hasattr(sys, 'argv'):
                cmd_args = ' '.join(sys.argv)
                if 'allure_behave.formatter:AllureFormatter' in cmd_args:
                    return True
        return False
    
    def _is_allure_context_available(self):
        """Check if Allure context is properly initialized"""
        if not self.allure_enabled:
            return False
        try:
            # Simple check - if allure module is available, assume context is ready
            # This works better with allure-behave formatter
            return hasattr(self.allure, 'step') and hasattr(self.allure, 'attach')
        except (AttributeError, KeyError):
            return False
    
    def _attach_once(self, content, name, attachment_type):
        """Attach content to Allure only once based on content hash"""
        if not self.allure_enabled:
            return
        
        # Create hash of content + name to ensure uniqueness
        content_str = str(content)
        hash_key = hashlib.md5(f"{name}:{content_str}".encode()).hexdigest()
        
        if hash_key not in self._attached_content_hashes:
            self._attached_content_hashes.add(hash_key)
            try:
                # Try to attach - this should work with both standalone and allure-behave formatter
                self.allure.attach(content, name=name, attachment_type=attachment_type)
            except (KeyError, AttributeError, TypeError, Exception) as e:
                # Log the issue but don't fail the test
                import sys
                if hasattr(sys, 'stderr'):
                    print(f"Warning: Could not attach to Allure: {e}", file=sys.stderr)
                pass
    
    def step_decorator(self, step_description):
        """Decorator to add Allure step annotations"""
        def decorator(func):
            # If allure-behave formatter is active, don't add custom step decorations
            # to avoid conflicts
            if self._is_allure_behave_formatter_active():
                return func
                
            # Always return the original function to avoid any issues
            # Allure step decoration is optional and should not break tests
            try:
                if self.allure_enabled and self.allure and hasattr(self.allure, 'step'):
                    @self.allure.step(step_description)
                    @wraps(func)
                    def wrapper(*args, **kwargs):
                        return func(*args, **kwargs)
                    return wrapper
                else:
                    return func
            except Exception as e:
                # If anything fails with Allure, just return the original function
                # Don't let Allure issues break the actual test execution
                import sys
                if hasattr(sys, 'stderr'):
                    print(f"Warning: Allure step decoration failed, continuing without it: {e}", file=sys.stderr)
                return func
        return decorator
    
    def attach_config_details(self, base_url, has_auth):
        """Attach configuration details"""
        if not self.allure_enabled:
            return
        
        config_details = {
            "base_url": base_url,
            "authentication_configured": has_auth,
            "timestamp": self._get_current_timestamp()
        }
        
        self._attach_once(
            json.dumps(config_details, indent=2),
            "Test Configuration",
            self.allure.attachment_type.JSON
        )
    
    def attach_request_response(self, method, endpoint, response, response_time, request_data=None):
        """Attach comprehensive request/response details"""
        if not self.allure_enabled:
            return
        
        # Request summary
        request_summary = {
            "method": method,
            "endpoint": endpoint,
            "status_code": response.status,
            "response_time_seconds": round(response_time, 3),
            "timestamp": self._get_current_timestamp()
        }
        
        if request_data:
            request_summary["request_payload"] = request_data
        
        self._attach_once(
            json.dumps(request_summary, indent=2),
            f"{method} Request Summary",
            self.allure.attachment_type.JSON
        )
        
        # Response data
        try:
            response_json = response.json()
            self._attach_once(
                json.dumps(response_json, indent=2),
                f"{method} Response Data",
                self.allure.attachment_type.JSON
            )
        except:
            response_text = response.text()
            self._attach_once(
                response_text,
                f"{method} Response Text",
                self.allure.attachment_type.TEXT
            )
    
    def attach_status_verification(self, expected_status, actual_status):
        """Attach status code verification results"""
        if not self.allure_enabled:
            return
        
        verification_result = {
            "expected_status": expected_status,
            "actual_status": actual_status,
            "verification_passed": actual_status == expected_status,
            "result": "✅ PASS" if actual_status == expected_status else "❌ FAIL"
        }
        
        self._attach_once(
            json.dumps(verification_result, indent=2),
            "Status Code Verification",
            self.allure.attachment_type.JSON
        )
    
    def attach_validation_result(self, validation_name, passed, details=None):
        """Attach generic validation result"""
        if not self.allure_enabled:
            return
        
        result = {
            "validation_name": validation_name,
            "passed": passed,
            "result": "✅ PASS" if passed else "❌ FAIL",
            "timestamp": self._get_current_timestamp()
        }
        
        if details:
            result["details"] = details
        
        self._attach_once(
            json.dumps(result, indent=2),
            validation_name,
            self.allure.attachment_type.JSON
        )
    
    def attach_field_validation(self, required_fields, validation_results):
        """Attach field validation results"""
        if not self.allure_enabled:
            return
        
        validation_summary = {
            "required_fields": required_fields,
            "total_users_validated": len(validation_results),
            "validation_results": validation_results,
            "overall_passed": all(
                not result["missing_fields"] and not result["null_fields"] 
                for result in validation_results
            )
        }
        
        self._attach_once(
            json.dumps(validation_summary, indent=2),
            "Field Validation Results",
            self.allure.attachment_type.JSON
        )
    
    def attach_performance_check(self, actual_time, max_time, unit):
        """Attach performance check results"""
        if not self.allure_enabled:
            return
        
        performance_result = {
            "actual_time": actual_time,
            "max_time": max_time,
            "unit": unit,
            "within_limit": actual_time < max_time,
            "performance_ratio": round((actual_time / max_time) * 100, 2),
            "result": "✅ PASS" if actual_time < max_time else "❌ FAIL"
        }
        
        self._attach_once(
            json.dumps(performance_result, indent=2),
            f"Performance Check ({unit})",
            self.allure.attachment_type.JSON
        )
    
    def attach_structure_validation(self, validation_results):
        """Attach data structure validation results"""
        if not self.allure_enabled:
            return
        
        self._attach_once(
            json.dumps(validation_results, indent=2),
            "Data Structure Validation",
            self.allure.attachment_type.JSON
        )
    
    def attach_field_value_validation(self, field_name, expected_value, validation_results):
        """Attach field value validation results"""
        if not self.allure_enabled:
            return
        
        validation_summary = {
            "field_name": field_name,
            "expected_value": expected_value,
            "validation_results": validation_results,
            "timestamp": self._get_current_timestamp()
        }
        
        self._attach_once(
            json.dumps(validation_summary, indent=2),
            f"Field Validation: {field_name}",
            self.allure.attachment_type.JSON
        )
    
    def attach_test_data(self, data_name, data):
        """Attach test data"""
        if not self.allure_enabled:
            return
        
        test_data = {
            "data_name": data_name,
            "data": data,
            "timestamp": self._get_current_timestamp()
        }
        
        self._attach_once(
            json.dumps(test_data, indent=2),
            data_name,
            self.allure.attachment_type.JSON
        )
    
    def attach_todo_validation(self, validation_name, validation_results):
        """Attach todo-specific validation results"""
        if not self.allure_enabled:
            return
        
        validation_summary = {
            "validation_name": validation_name,
            "validation_results": validation_results,
            "overall_passed": all(result.get("exists", True) for result in validation_results),
            "timestamp": self._get_current_timestamp()
        }
        
        self._attach_once(
            json.dumps(validation_summary, indent=2),
            validation_name,
            self.allure.attachment_type.JSON
        )
    
    def attach_date_validation(self, field_name, date_string, is_valid, error_message=None):
        """Attach date validation results"""
        if not self.allure_enabled:
            return
        
        validation_result = {
            "field_name": field_name,
            "date_string": date_string,
            "is_valid_iso_format": is_valid,
            "result": "✅ VALID" if is_valid else "❌ INVALID",
            "timestamp": self._get_current_timestamp()
        }
        
        if error_message:
            validation_result["error_message"] = error_message
        
        self._attach_once(
            json.dumps(validation_result, indent=2),
            f"Date Validation - {field_name}",
            self.allure.attachment_type.JSON
        )
    
    def _get_current_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    def attach_error(self, error_message, exception=None):
        """Attach error details to Allure"""
        if not self.allure_enabled:
            return

        error_details = {
            "error_message": str(error_message),
            "timestamp": self._get_current_timestamp()
        }

        if exception:
            error_details["exception_type"] = type(exception).__name__
            error_details["exception_details"] = str(exception)

        self._attach_once(
            json.dumps(error_details, indent=2),
            "Error Details",
            self.allure.attachment_type.JSON
        )