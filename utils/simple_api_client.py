import json
import time
import os
from typing import Dict, Any, Optional
from playwright.sync_api import APIRequestContext, sync_playwright
from utils import logger
log = logger.customLogger()


# Import Allure if enabled
import hashlib
import sys

def _is_allure_behave_formatter_active():
    """Check if allure-behave formatter is being used"""
    # Check if behave is running with allure formatter
    if 'behave' in sys.modules:
        # Check command line arguments for allure formatter
        if hasattr(sys, 'argv'):
            cmd_args = ' '.join(sys.argv)
            if 'allure_behave.formatter:AllureFormatter' in cmd_args:
                return True
    return False

if os.environ.get('ENABLE_ALLURE', 'false').lower() == 'true' and not _is_allure_behave_formatter_active():
    try:
        import allure
        ALLURE_ENABLED = True
    except ImportError:
        ALLURE_ENABLED = False
else:
    ALLURE_ENABLED = False

# Global set to track attached content and prevent duplicates
_api_attached_content_hashes = set()


def _is_allure_context_available():
    """Check if Allure context is properly initialized"""
    if not ALLURE_ENABLED:
        return False
    try:
        # Check if allure module has proper context
        if hasattr(allure, '_allure') and allure._allure:
            # Try to access the reporter to ensure it's initialized
            reporter = allure._allure
            if hasattr(reporter, '_items') and reporter._items:
                return True
        return False
    except (AttributeError, KeyError):
        return False


def api_attach_once(content, name, attachment_type):
    """Attach content to Allure only once based on content hash"""
    if not ALLURE_ENABLED or not _is_allure_context_available():
        return

    content_str = str(content)
    hash_key = hashlib.md5(f"{name}:{content_str}".encode()).hexdigest()

    if hash_key not in _api_attached_content_hashes:
        _api_attached_content_hashes.add(hash_key)
        try:
            allure.attach(content, name=name, attachment_type=attachment_type)
        except (KeyError, AttributeError, TypeError):
            # Silently handle any remaining Allure context issues
            pass


class SimpleAPIClient:
    """Simple API client wrapping Playwright APIRequestContext"""

    def __init__(self, request_context: APIRequestContext, base_url: str, timeout: int = 30):
        if not isinstance(request_context, APIRequestContext):
            raise TypeError("Expected Playwright APIRequestContext for 'request_context'")
        self.request_context = request_context
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._request_counter = 0
        self._allure_attached = set()

    def _build_url(self, endpoint: str) -> str:
        return endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}"

    def _log_response(self, response, duration: float) -> None:
        """Log response details"""
        try:
            log.info(f"Response Status: {response.status}")
            log.info(f"Response Time: {duration:.3f}s")

            try:
                response_json = response.json()
                response_str = json.dumps(response_json, indent=2)
                if len(response_str) > 1000:
                    log.info(f"Response JSON (truncated): {response_str[:1000]}...")
                else:
                    log.info(f"Response JSON: {response_str}")
            except Exception:
                text = response.text()
                if len(text) > 500:
                    log.info(f"Response Text (truncated): {text[:500]}...")
                else:
                    log.info(f"Response Text: {text}")
        except Exception as e:
            log.error(f"Error logging response: {e}")

    def _add_allure_response_attachments(self, response, duration: float, method: str, url: str, request_id: int):
        if not ALLURE_ENABLED:
            return

        response_key = f"response_{request_id}_{url}_{response.status}"
        if response_key in self._allure_attached:
            return
        self._allure_attached.add(response_key)

        try:
            response_summary = {
                "request_id": request_id,
                "method": method,
                "url": url,
                "status_code": response.status,
                "response_time_seconds": round(duration, 3),
                "response_headers": dict(response.headers)
            }
            api_attach_once(json.dumps(response_summary, indent=2), f"Response Summary (#{request_id})", allure.attachment_type.JSON)

            try:
                response_json = response.json()
                api_attach_once(json.dumps(response_json, indent=2), f"Response Body JSON (#{request_id})", allure.attachment_type.JSON)
            except:
                api_attach_once(response.text(), f"Response Body Text (#{request_id})", allure.attachment_type.TEXT)

            api_attach_once(f"Response Time: {duration:.3f}s\nStatus Code: {response.status}\nURL: {url}",
                            f"Performance Info (#{request_id})", allure.attachment_type.TEXT)
        except Exception as e:
            api_attach_once(f"Error creating response attachments: {str(e)}",
                            f"Attachment Error (#{request_id})", allure.attachment_type.TEXT)

    # ---------- HTTP METHODS ----------

    def get(self, endpoint: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
        return self._send("GET", endpoint, params=params, headers=headers)

    def post(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        return self._send("POST", endpoint, data=data, json_data=json_data, headers=headers)

    def put(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        return self._send("PUT", endpoint, data=data, json_data=json_data, headers=headers)

    def patch(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        return self._send("PATCH", endpoint, data=data, json_data=json_data, headers=headers)

    def delete(self, endpoint: str, headers: Dict[str, str] = None):
        return self._send("DELETE", endpoint, headers=headers)


    def _send(self, method: str, endpoint: str, params=None, data=None, json_data=None, headers=None):
        url = self._build_url(endpoint)
        self._request_counter += 1
        request_id = self._request_counter

        merged_headers = headers or {}
        body = None

        # Handle JSON encoding
        if json_data is not None:
            body = json.dumps(json_data)
            merged_headers["Content-Type"] = "application/json"
        elif data is not None:
            body = data  # can be dict, str, or bytes

        if ALLURE_ENABLED:
            attachment_key = f"request_{request_id}_{url}"
            if attachment_key not in self._allure_attached:
                self._allure_attached.add(attachment_key)
                request_info = {
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "headers": merged_headers,
                    "params": params or {},
                    "payload": json_data if json_data is not None else data,
                    "timeout": self.timeout
                }
                api_attach_once(json.dumps(request_info, indent=2), f"Request Details (#{request_id})",
                                allure.attachment_type.JSON)

        log.info(f"{method} request to: {url}")

        start_time = time.time()
        try:
            response = self.request_context.fetch(
                url,
                method=method,
                params=params,
                data=body,
                headers=merged_headers,
                timeout=self.timeout * 1000  # ms
            )
            duration = time.time() - start_time

            if ALLURE_ENABLED:
                self._add_allure_response_attachments(response, duration, method, url, request_id)

            self._log_response(response, duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log.error(f"{method} request failed after {duration:.2f}s: {str(e)}")
            if ALLURE_ENABLED:
                api_attach_once(f"{method} request failed after {duration:.2f}s: {str(e)}",
                                f"Request Error (#{request_id})", allure.attachment_type.TEXT)
            raise

    def get_json_response(self, response) -> Dict[str, Any]:
        """Safely parse JSON response"""
        try:
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse response as JSON: {e}")
            self.logger.error(f"Response text: {response.text()}")
            raise ValueError(f"Invalid JSON response: {e}")
