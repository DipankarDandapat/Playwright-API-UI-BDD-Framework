# """
# API Client for Playwright BDD Framework
# Handles API testing and integration with web UI tests
# """
# import json
# from playwright.sync_api import APIRequestContext
# from urllib.parse import urljoin
# from typing import Dict, Any, Optional
# from utils.logger import get_logger
#
# logger = get_logger('APIClient')
#
#
# class APIClient:
#     """HTTP API client for testing REST APIs using Playwright"""
#
#     def __init__(self, request_context: APIRequestContext, base_url: str, timeout: int = 30):
#         self.request_context = request_context
#         self.base_url = base_url.rstrip('/')
#         self.timeout = timeout * 1000  # ms
#         self.logger = get_logger(__name__)
#         self.headers: Dict[str, str] = {
#             "Content-Type": "application/json",
#             "Accept": "application/json"
#         }
#
#     # ---------- Auth ----------
#     def set_auth_token(self, token: str, token_type: str = "Bearer") -> None:
#         self.headers["Authorization"] = f"{token_type} {token}"
#
#     def set_api_key(self, api_key: str, header_name: str = "X-API-Key") -> None:
#         self.headers[header_name] = api_key
#
#     def set_basic_auth(self, username: str, password: str) -> None:
#         import base64
#         token = base64.b64encode(f"{username}:{password}".encode()).decode()
#         self.headers["Authorization"] = f"Basic {token}"
#
#     # ---------- Request Methods ----------
#     def _merge_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
#         merged = self.headers.copy()
#         if headers:
#             merged.update(headers)
#         return merged
#
#     def _build_url(self, endpoint: str) -> str:
#         """Build full URL from endpoint"""
#         if endpoint.startswith('http'):
#             # Full URL provided
#             return endpoint
#         else:
#             # Relative endpoint
#             return urljoin(self.base_url + '/', endpoint.lstrip('/'))
#
#     def get(self, endpoint: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
#         url = self._build_url(endpoint)
#         self.logger.info(f"GET request to: {url}")
#
#         try:
#             response = self.request_context.get(
#                 url,
#                 params=params,
#                 headers=self._merge_headers(headers),
#                 timeout=self.timeout
#             )
#             self._log_response(response)
#             return response
#         except Exception as e:
#             self.logger.error(f"GET request failed: {str(e)}")
#             raise
#
#     def post(self, endpoint: str, data: Dict[str, Any] = None,
#              json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
#         url = self._build_url(endpoint)
#         self.logger.info(f"POST request to: {url}")
#
#         try:
#             # Determine what data to send
#             if json_data is not None:
#                 post_data = json.dumps(json_data, indent=2)
#                 self.logger.info(f"Sending JSON data: {post_data}")
#             elif data is not None:
#                 post_data = json.dumps(data, indent=2)
#                 self.logger.info(f"Sending data as JSON: {post_data}")
#             else:
#                 post_data = None
#
#             response = self.request_context.post(
#                 url,
#                 data=post_data,
#                 headers=self._merge_headers(headers),
#                 timeout=self.timeout
#             )
#
#             self.logger.info(f"POST request completed. Status: {response.status}")
#             self._log_response(response)
#             return response
#
#         except Exception as e:
#             self.logger.error(f"POST request failed: {str(e)}")
#             self.logger.error(f"Error type: {type(e).__name__}")
#             raise
#
#     def put(self, endpoint: str, data: Dict[str, Any] = None,
#             json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
#         url = self._build_url(endpoint)
#         self.logger.info(f"PUT request to: {url}")
#
#         try:
#             # Determine what data to send
#             if json_data is not None:
#                 put_data = json.dumps(json_data, indent=2)
#             elif data is not None:
#                 put_data = json.dumps(data, indent=2)
#             else:
#                 put_data = None
#
#             response = self.request_context.put(
#                 url,
#                 data=put_data,
#                 headers=self._merge_headers(headers),
#                 timeout=self.timeout
#             )
#             self._log_response(response)
#             return response
#         except Exception as e:
#             self.logger.error(f"PUT request failed: {str(e)}")
#             raise
#
#     def patch(self, endpoint: str, data: Dict[str, Any] = None,
#               json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
#         url = self._build_url(endpoint)
#         self.logger.info(f"PATCH request to: {url}")
#
#         try:
#             # Determine what data to send
#             if json_data is not None:
#                 patch_data = json.dumps(json_data, indent=2)
#             elif data is not None:
#                 patch_data = json.dumps(data, indent=2)
#             else:
#                 patch_data = None
#
#             response = self.request_context.patch(
#                 url,
#                 data=patch_data,
#                 headers=self._merge_headers(headers),
#                 timeout=self.timeout
#             )
#             self._log_response(response)
#             return response
#         except Exception as e:
#             self.logger.error(f"PATCH request failed: {str(e)}")
#             raise
#
#     def delete(self, endpoint: str, headers: Dict[str, str] = None):
#         url = self._build_url(endpoint)
#         self.logger.info(f"DELETE request to: {url}")
#
#         try:
#             response = self.request_context.delete(
#                 url,
#                 headers=self._merge_headers(headers),
#                 timeout=self.timeout
#             )
#             self._log_response(response)
#             return response
#         except Exception as e:
#             self.logger.error(f"DELETE request failed: {str(e)}")
#             raise
#
#     def upload_file(self, endpoint: str, file_path: str,
#                     field_name: str = "file", additional_data: Dict[str, Any] = None):
#         url = self._build_url(endpoint)
#         self.logger.info(f"File upload to: {url}")
#
#         try:
#             with open(file_path, "rb") as f:
#                 response = self.request_context.post(
#                     url,
#                     multipart={
#                         field_name: f,
#                         **(additional_data or {})
#                     },
#                     headers=self._merge_headers(),
#                     timeout=self.timeout
#                 )
#             self._log_response(response)
#             return response
#         except Exception as e:
#             self.logger.error(f"File upload failed: {str(e)}")
#             raise
#
#     # ---------- Helpers ----------
#     def _log_response(self, response) -> None:
#         """Log response details"""
#         self.logger.info(f"Response Status: {response.status}")
#         self.logger.info(f"Response Headers: {dict(response.headers)}")
#
#         try:
#             response_json = response.json()
#             self.logger.info(f"Response JSON: {json.dumps(response_json, indent=2)}")
#         except Exception:
#             response_text = response.text()
#             self.logger.info(f"Response Text: {response_text[:500]}{'...' if len(response_text) > 500 else ''}")
#
#     def get_json_response(self, response) -> Dict[str, Any]:
#         """Safely parse JSON response"""
#         try:
#             return response.json()
#         except Exception as e:
#             self.logger.error(f"Failed to parse response as JSON: {e}")
#             self.logger.error(f"Response text: {response.text()}")
#             raise ValueError(f"Invalid JSON response: {e}")
#
#     def assert_status_code(self, actual_status: int, expected_status: int) -> None:
#         """Assert response status code"""
#         if actual_status != expected_status:
#             error_msg = f"Expected status {expected_status}, but got {actual_status}"
#             self.logger.error(error_msg)
#             raise AssertionError(error_msg)
#
#     def assert_response_contains(self, response, field: str, expected_value: Any = None) -> None:
#         """Assert response contains specific field and optionally check its value"""
#         response_data = self.get_json_response(response)
#
#         if field not in response_data:
#             raise AssertionError(f"Response should contain field '{field}'")
#
#         if expected_value is not None:
#             actual_value = response_data[field]
#             if actual_value != expected_value:
#                 raise AssertionError(f"Field '{field}' should be '{expected_value}', got '{actual_value}'")
#
#     def assert_response_time(self, response_time: float, max_time: float) -> None:
#         """Assert response time is within acceptable limit"""
#         if response_time > max_time:
#             raise AssertionError(f"Response time {response_time:.2f}s exceeds {max_time}s limit")
#
#
# class GraphQLClient(APIClient):
#     """GraphQL API client using Playwright"""
#
#     def query(self, query: str, variables: Dict[str, Any] = None):
#         payload = {"query": query, "variables": variables or {}}
#         self.logger.info("Executing GraphQL Query")
#         return self.post("", json_data=payload)
#
#     def mutation(self, mutation: str, variables: Dict[str, Any] = None):
#         payload = {"query": mutation, "variables": variables or {}}
#         self.logger.info("Executing GraphQL Mutation")
#         return self.post("", json_data=payload)
#
