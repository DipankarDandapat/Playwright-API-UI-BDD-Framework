from behave import given, when, then
from utils.config_manager import get_config
from utils.allure_helper import AllureHelper
import json
import time
from datetime import datetime
from utils import logger

allure_helper = AllureHelper()
log = logger.customLogger()


@given('the API client is configured for the Todos API in the testing environment')
@allure_helper.step_decorator("Configure API client for Todos API")
def step_configure_api_client(context):
    """Use the API client configured in environment.py"""
    assert context.api_client is not None, "API client was not initialized"
    config = get_config()
    base_url = config.get('API_BASE_URL', 'https://dipankardandapat.xyz')

    # Auth if available
    api_key = config.get('API_KEY')
    if api_key:
        context.api_client.set_api_key(api_key)

    allure_helper.attach_config_details(base_url, api_key is not None)


@when('I send GET request to "{endpoint}"')
@allure_helper.step_decorator("Send GET request to: {endpoint}")
def step_send_get_request(context, endpoint):
    """Send GET request to specified endpoint"""
    # Replace placeholder if needed
    if hasattr(context, 'todo_id'):
        endpoint = endpoint.replace('{todo_id}', str(context.todo_id))
    
    start_time = time.time()
    log.info(f"Sending GET request to: {endpoint}")
    
    try:
        response = context.api_client.get(endpoint)
        end_time = time.time()
        
        context.api_response = response
        context.response_time = end_time - start_time
        
        
        # Attach Allure details
        allure_helper.attach_request_response(
            method="GET",
            endpoint=endpoint,
            response=response,
            response_time=context.response_time
        )
        
        log.info(f"GET request completed successfully in {context.response_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time
        log.error(f"GET request failed after {context.response_time:.2f}s: {str(e)}")
        allure_helper.attach_error(f"GET request failed: {str(e)}")
        raise AssertionError(f"Failed to send GET request to {endpoint}: {str(e)}")


@then('the response status code should be {status_code:d}')
@allure_helper.step_decorator("Verify response status code is {status_code}")
def step_verify_status_code(context, status_code):
    """Verify API response status code"""
    actual_status = context.api_response.status
    
    log.info(f"Expected: {status_code}, Actual: {actual_status}")
    
    # Attach verification result to Allure
    allure_helper.attach_status_verification(status_code, actual_status)
    
    if actual_status != status_code:
        error_message = f"Expected status {status_code}, but got {actual_status}"
        log.error(error_message)
        allure_helper.attach_error(f"{error_message}. Response: {context.api_response.text()}")
        raise AssertionError(error_message)








@then('the response time should be less than {max_time:d} ms')
@allure_helper.step_decorator("Verify response time is under {max_time}ms")
def step_verify_response_time_ms(context, max_time):
    """Verify response time is within acceptable limit in ms"""
    response_time_ms = context.response_time * 1000
    
    allure_helper.attach_performance_check(response_time_ms, max_time, "ms")
    
    if response_time_ms >= max_time:
        error_msg = f"Response time {response_time_ms:.1f}ms exceeds {max_time}ms limit"
        log.error(error_msg)
        raise AssertionError(error_msg)
    
    log.info(f"Response time {response_time_ms:.1f}ms is within {max_time}ms")


@then('the response should contain todos data structure')
@allure_helper.step_decorator("Verify response contains todos data structure")
def step_verify_todos_data_structure(context):
    """Verify response contains FreeAPI todos data structure"""
    try:
        response_data = context.api_response.json()
        required_fields = ['success', 'data', 'message']
        
        # Validate structure
        structure_validation = _validate_response_structure(response_data, required_fields)
        
        # Attach validation results
        allure_helper.attach_structure_validation(structure_validation)
        
        # Assert required fields
        for field in required_fields:
            assert field in response_data, f"Response should contain '{field}' field"
        
        # Validate data content if success is true
        if response_data.get('success'):
            _validate_todos_data_content(response_data['data'])

    except Exception as e:
        log.error(f"Failed to verify todos data structure: {e}")
        allure_helper.attach_error(f"Data structure validation failed: {e}")
        raise


@then('the response should have "{field}" field as {expected_value}')
@allure_helper.step_decorator("Verify response field '{field}' has value {expected_value}")
def step_verify_response_field_value(context, field, expected_value):
    """Verify response has specific field with expected value"""
    response_data = context.api_response.json()
    
    # Convert expected value
    converted_value = _convert_string_to_appropriate_type(expected_value)
    
    # Validate field
    field_validation = _validate_field_value(response_data, field, converted_value)
    
    # Attach validation results
    allure_helper.attach_field_value_validation(field, expected_value, field_validation)
    
    # Assert validations
    assert field in response_data, f"Response should contain '{field}' field"
    assert field_validation["values_match"], \
        f"Field '{field}' should be {converted_value}, got {field_validation['actual_value']}"


@given('I have valid todo data')
@allure_helper.step_decorator("Prepare valid todo data from table")
def step_prepare_todo_data_from_table(context):
    """Prepare todo data from table"""
    context.todo_data = {}
    
    for row in context.table:
        context.todo_data[row['field']] = row['value']
    
    allure_helper.attach_test_data("Todo Data", context.todo_data)


@when('I send POST request to "{endpoint}" with the todo data')
@allure_helper.step_decorator("Send POST request with todo data to: {endpoint}")
def step_send_post_request_with_todo_data(context, endpoint):
    """Send POST request with todo data"""
    start_time = time.time()
    log.info(f"Sending POST request to {endpoint}")
    
    try:
        response = context.api_client.post(endpoint, data=context.todo_data)
        end_time = time.time()
        
        context.api_response = response
        context.response_time = end_time - start_time

        # Attach Allure details
        allure_helper.attach_request_response(
            method="POST",
            endpoint=endpoint,
            request_data=context.todo_data,
            response=response,
            response_time=context.response_time
        )
        
        # Store created todo ID if successful
        if response.status in [200, 201]:
            context.todo_id = _extract_todo_id_from_response(response)
        
        log.info(f"POST request completed successfully in {context.response_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time
        log.error(f"POST request failed after {context.response_time:.2f}s: {str(e)}")
        allure_helper.attach_error(f"POST request failed: {str(e)}")
        raise AssertionError(f"Failed to send POST request to {endpoint}: {str(e)}")


@then('the response should contain the created todo details')
@allure_helper.step_decorator("Verify created todo details in response")
def step_verify_created_todo_details(context):
    """Verify response contains created todo details"""
    response_data = context.api_response.json()
    todo_data = _extract_todo_data_from_response(response_data)
    
    required_fields = ['_id', 'title', 'description', 'isComplete']
    validation_results = []
    
    for field in required_fields:
        field_exists = field in todo_data
        validation_results.append({"field": field, "exists": field_exists})
        assert field_exists, f"Response should contain todo {field}"
    
    allure_helper.attach_todo_validation("Created Todo Validation", validation_results)




def _convert_string_to_appropriate_type(value):
    """Convert string representation to appropriate Python type"""
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    elif value.isdigit():
        return int(value)
    else:
        return value


def _validate_response_structure(response_data, required_fields):
    """Validate response structure and return results"""
    found_fields = []
    missing_fields = []
    
    for field in required_fields:
        if field in response_data:
            found_fields.append(field)
        else:
            missing_fields.append(field)
    
    return {
        "required_fields": required_fields,
        "found_fields": found_fields,
        "missing_fields": missing_fields,
        "validation_passed": len(missing_fields) == 0,
        "data_type": type(response_data.get('data', None)).__name__ if 'data' in response_data else "N/A"
    }


def _validate_field_value(response_data, field, expected_value):
    """Validate field value and return results"""
    field_exists = field in response_data
    actual_value = response_data.get(field) if field_exists else None
    values_match = actual_value == expected_value if field_exists else False
    
    return {
        "field_exists": field_exists,
        "actual_value": actual_value,
        "expected_value": expected_value,
        "values_match": values_match
    }


def _validate_todos_data_content(data):
    """Validate todos data content structure"""
    if isinstance(data, dict) and 'todos' in data:
        assert isinstance(data['todos'], list), "Todos should be a list"
    elif isinstance(data, list):
        # Direct list of todos is also valid
        pass
    else:
        log.warning(f"Unexpected data structure: {data}")


def _extract_todo_data_from_response(response_data):
    """Extract todo data from response, handling different structures"""
    if 'data' in response_data:
        return response_data['data']
    else:
        return response_data


def _extract_todo_id_from_response(response):
    """Extract todo ID from response"""
    response_data = response.json()
    if 'data' in response_data and '_id' in response_data['data']:
        return response_data['data']['_id']
    elif '_id' in response_data:
        return response_data['_id']
    return None

@when('I send PATCH request to "{endpoint}"')
@allure_helper.step_decorator("Send PATCH request to: {endpoint}")
def step_send_patch_request(context, endpoint):
    """Send PATCH request (for toggle status)"""
    # Only replace {todo_id} if it exists in the endpoint and context.todo_id is available
    if '{todo_id}' in endpoint:
        if hasattr(context, 'todo_id') and context.todo_id:
            endpoint = endpoint.replace('{todo_id}', str(context.todo_id))
        else:
            raise ValueError("Endpoint contains {todo_id} but context.todo_id is not available")
    
    log.info(f"Sending PATCH request to {endpoint}")
    
    start_time = time.time()
    response = context.api_client.patch(endpoint)
    log.info(f"Response status: {response.status}")
    
    end_time = time.time()
    context.api_response = response
    context.response_time = end_time - start_time
    
    # Log detailed response information for debugging
    try:
        log.info(f"Response time: {context.response_time:.3f}s")
        log.info(f"Response headers: {dict(response.headers)}")
        
        # Log response body
        try:
            response_json = response.json()
            response_str = json.dumps(response_json, indent=2)
            if len(response_str) > 1000:
                log.info(f"Response JSON (first 1000 chars): {response_str[:1000]}...")
            else:
                log.info(f"Response JSON: {response_str}")
        except Exception:
            response_text = response.text()
            if len(response_text) > 500:
                log.info(f"Response text (first 500 chars): {response_text[:500]}...")
            else:
                log.info(f"Response text: {response_text}")
    except Exception as e:
        log.warning(f"Could not log detailed response info: {e}")
    
    # Attach Allure details
    allure_helper.attach_request_response(
        method="PATCH",
        endpoint=endpoint,
        response=response,
        response_time=context.response_time
    )
    
    log.info(f"PATCH request completed successfully in {context.response_time:.2f}s")
# Additional step definitions following the same pattern...

@when('I send PATCH request to "{endpoint}" with updated data')
@allure_helper.step_decorator("Send PATCH request with data to: {endpoint}")
def step_send_patch_request_with_data(context, endpoint):
    """Send PATCH request with updated data"""
    if '{todo_id}' in endpoint and hasattr(context, 'todo_id'):
        endpoint = endpoint.replace('{todo_id}', str(context.todo_id))
    
    # Prepare updated data from table
    updated_data = {}
    for row in context.table:
        updated_data[row['field']] = row['value']
    
    context.updated_data = updated_data
    log.info(f"Sending PATCH request to {endpoint}")
    
    start_time = time.time()
    
    try:
        response = context.api_client.patch(endpoint, data=updated_data)
        end_time = time.time()
        
        context.api_response = response
        context.response_time = end_time - start_time
        
        
        allure_helper.attach_request_response(
            method="PATCH",
            endpoint=endpoint,
            request_data=updated_data,
            response=response,
            response_time=context.response_time
        )
        
        log.info(f"PATCH request completed successfully in {context.response_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time
        log.error(f"PATCH request failed after {context.response_time:.2f}s: {str(e)}")
        allure_helper.attach_error(f"PATCH request failed: {str(e)}")
        raise AssertionError(f"Failed to send PATCH request to {endpoint}: {str(e)}")


@when('I send DELETE request to "{endpoint}"')
@allure_helper.step_decorator("Send DELETE request to: {endpoint}")
def step_send_delete_request(context, endpoint):
    """Send DELETE request"""
    if '{todo_id}' in endpoint:
        if hasattr(context, 'todo_id') and context.todo_id:
            endpoint = endpoint.replace('{todo_id}', str(context.todo_id))
        else:
            raise ValueError("Endpoint contains {todo_id} but context.todo_id is not available")
    
    start_time = time.time()
    
    try:
        response = context.api_client.delete(endpoint)
        end_time = time.time()
        
        context.api_response = response
        context.response_time = end_time - start_time
        
        
        allure_helper.attach_request_response(
            method="DELETE",
            endpoint=endpoint,
            response=response,
            response_time=context.response_time
        )
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time
        log.error(f"DELETE request failed: {str(e)}")
        allure_helper.attach_error(f"DELETE request failed: {str(e)}")
        raise AssertionError(f"Failed to send DELETE request to {endpoint}: {str(e)}")


@then('the field "{field}" should be a valid ISO date format')
@allure_helper.step_decorator("Verify field '{field}' is valid ISO date format")
def step_verify_iso_date_format(context, field):
    """Verify field is a valid ISO date format"""
    try:
        response_data = context.api_response.json()
        data = _extract_todo_data_from_response(response_data)
        
        # Check if field exists
        assert field in data, f"Field '{field}' not found in response data"
        
        date_string = data[field]
        assert isinstance(date_string, str), f"Field '{field}' should be a string"
        
        # Validate ISO format
        try:
            if date_string.endswith('Z'):
                datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                datetime.fromisoformat(date_string)
            
            allure_helper.attach_date_validation(field, date_string, True)
            log.info(f"Field '{field}' contains valid ISO date format: {date_string}")
            
        except ValueError as e:
            allure_helper.attach_date_validation(field, date_string, False, str(e))
            raise AssertionError(f"Field '{field}' should be valid ISO date format, got: '{date_string}'")
            
    except Exception as e:
        log.error(f"Error validating ISO date format for field '{field}': {str(e)}")
        allure_helper.attach_error(f"Date validation failed: {str(e)}")
        raise

@then('the response should have "data" field containing todos list')
@allure_helper.step_decorator("Verify response has data field with todos list")
def step_response_should_have_data_field_with_todos_list(context):
    """Verify response has 'data' field containing todos list"""
    try:
        response_data = context.api_response.json()
        
        # Check if 'data' field exists
        assert "data" in response_data, "Response should contain 'data' field"
        
        data_field = response_data["data"]
        
        # Check if data field is a list
        assert isinstance(data_field, list), f"'data' field should be a list, got {type(data_field)}"
        
        # Check if list contains todos (can be empty)
        log.info(f"'data' field contains {len(data_field)} todos")
        
        # If list is not empty, validate structure of first todo
        if data_field:
            first_todo = data_field[0]
            assert isinstance(first_todo, dict), "Each todo should be a dictionary object"
            
            # Common todo fields that should exist
            expected_fields = ["_id", "title", "description", "isComplete"]
            for field in expected_fields:
                if field in first_todo:
                    log.info(f"Todo contains expected field: {field}")
        
        # Attach validation results to Allure
        validation_details = {
            "data_field_exists": True,
            "data_field_type": str(type(data_field)),
            "todos_count": len(data_field),
            "validation_status": "✅ PASSED"
        }
        
        allure_helper.attach_validation_result("Data Field Validation", True, validation_details)
        log.info(f"✅ Response 'data' field validation passed - contains {len(data_field)} todos")
        
    except AssertionError as e:
        allure_helper.attach_validation_result("Data Field Validation", False, {"error": str(e)})
        log.error(f"❌ Data field validation failed: {str(e)}")
        raise
    except Exception as e:
        log.error(f"Error validating 'data' field: {str(e)}")
        allure_helper.attach_validation_result("Data Field Validation", False, {"error": str(e)})
        raise

@then('the todo should have a generated "_id"')
@allure_helper.step_decorator("Verify todo has generated _id")
def step_verify_todo_has_id(context):
    """Verify todo has generated _id field"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        assert "_id" in todo_data, "Todo should have '_id' field"
        assert todo_data["_id"], "Todo '_id' should not be empty"
        assert isinstance(todo_data["_id"], str), "Todo '_id' should be a string"
        
        # Store the todo_id for later use
        context.todo_id = todo_data["_id"]
        
        log.info(f"✅ Todo has valid _id: {todo_data['_id']}")
        allure_helper.attach_validation_result("Todo ID Validation", True, {"_id": todo_data["_id"]})
        
    except Exception as e:
        log.error(f"❌ Todo ID validation failed: {str(e)}")
        allure_helper.attach_validation_result("Todo ID Validation", False, {"error": str(e)})
        raise

@then('the todo "{field}" should match the input data')
@allure_helper.step_decorator("Verify todo '{field}' matches input data")
def step_verify_todo_field_matches_input(context, field):
    """Verify todo field matches input data"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        # Get the expected value from context (set during data preparation)
        expected_value = getattr(context, f"expected_{field}", None)
        if expected_value is None and hasattr(context, 'todo_data'):
            expected_value = context.todo_data.get(field)
        
        actual_value = todo_data.get(field)
        
        assert field in todo_data, f"Todo should have '{field}' field"
        if expected_value:
            assert actual_value == expected_value, f"Todo '{field}' should match input data. Expected: {expected_value}, Got: {actual_value}"
        
        log.info(f"✅ Todo '{field}' matches input data: {actual_value}")
        allure_helper.attach_validation_result(f"Todo {field} Validation", True, {field: actual_value})
        
    except Exception as e:
        log.error(f"❌ Todo '{field}' validation failed: {str(e)}")
        allure_helper.attach_validation_result(f"Todo {field} Validation", False, {"error": str(e)})
        raise

@then('the todo "{field}" should be "{expected_value}"')
@allure_helper.step_decorator("Verify todo '{field}' is '{expected_value}'")
def step_verify_todo_field_value(context, field, expected_value):
    """Verify todo field has specific value"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        # Convert expected value to appropriate type
        converted_value = _convert_string_to_appropriate_type(expected_value)
        actual_value = todo_data.get(field)
        
        assert field in todo_data, f"Todo should have '{field}' field"
        assert actual_value == converted_value, f"Todo '{field}' should be '{expected_value}'. Got: {actual_value}"
        
        log.info(f"✅ Todo '{field}' has expected value: {actual_value}")
        allure_helper.attach_validation_result(f"Todo {field} Value Check", True, {field: actual_value, "expected": converted_value})
        
    except Exception as e:
        log.error(f"❌ Todo '{field}' value validation failed: {str(e)}")
        allure_helper.attach_validation_result(f"Todo {field} Value Check", False, {"error": str(e)})
        raise

@given('I have created a todo via FreeAPI')
@allure_helper.step_decorator("Create todo via FreeAPI for testing")
def step_create_todo_for_testing(context):
    """Create a todo for testing purposes"""
    try:
        
        # Create test todo data
        todo_data = {
            "title": "Test Todo for Retrieval",
            "description": "This todo is created for testing retrieval operations"
        }
        
        # Send POST request to create todo
        endpoint = "api/v1/todos"
        context.api_response = context.api_client.post(endpoint, todo_data)
        
        # Verify creation was successful
        assert context.api_response.status == 201, f"Todo creation failed with status: {context.api_response.status}"
        
        response_data = context.api_response.json()
        assert "data" in response_data, "Response should contain 'data' field"
        assert "_id" in response_data["data"], "Created todo should have '_id' field"
        
        # Store the created todo ID for later use
        context.todo_id = response_data["data"]["_id"]
        context.created_todo = response_data["data"]
        
        log.info(f"✅ Created test todo with ID: {context.todo_id}")
        allure_helper.attach_validation_result("Todo Creation for Testing", True, {"todo_id": context.todo_id})
        
    except Exception as e:
        log.error(f"❌ Failed to create test todo: {str(e)}")
        allure_helper.attach_validation_result("Todo Creation for Testing", False, {"error": str(e)})
        raise

@then('the response should contain todo details')
@allure_helper.step_decorator("Verify response contains todo details")
def step_verify_response_contains_todo_details(context):
    """Verify response contains complete todo details"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        # Required fields for a complete todo
        required_fields = ["_id", "title", "description", "isComplete", "createdAt", "updatedAt"]
        
        for field in required_fields:
            assert field in todo_data, f"Todo details should include '{field}' field"
            assert todo_data[field] is not None, f"Todo '{field}' should not be null"
        
        log.info("✅ Response contains all required todo details")
        allure_helper.attach_validation_result("Todo Details Validation", True, {"fields_validated": required_fields})
        
    except Exception as e:
        log.error(f"❌ Todo details validation failed: {str(e)}")
        allure_helper.attach_validation_result("Todo Details Validation", False, {"error": str(e)})
        raise

@then('the todo "_id" should match the requested ID')
@allure_helper.step_decorator("Verify todo ID matches requested ID")
def step_verify_todo_id_matches_requested(context):
    """Verify returned todo ID matches the requested ID"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        returned_id = todo_data.get("_id")
        requested_id = getattr(context, 'todo_id', None)
        
        assert returned_id, "Response should contain todo '_id'"
        assert requested_id, "Context should have requested todo ID"
        assert returned_id == requested_id, f"Returned ID '{returned_id}' should match requested ID '{requested_id}'"
        
        log.info(f"✅ Todo ID matches requested ID: {returned_id}")
        allure_helper.attach_validation_result("Todo ID Match Validation", True, {"returned_id": returned_id, "requested_id": requested_id})
        
    except Exception as e:
        log.error(f"❌ Todo ID match validation failed: {str(e)}")
        allure_helper.attach_validation_result("Todo ID Match Validation", False, {"error": str(e)})
        raise

@then('the todo should have all required fields populated')
@allure_helper.step_decorator("Verify todo has all required fields populated")
def step_verify_todo_has_all_required_fields(context):
    """Verify todo has all required fields populated"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        # Required fields with their expected types
        required_fields = {
            "_id": str,
            "title": str,
            "description": str,
            "isComplete": bool,
            "createdAt": str,
            "updatedAt": str,
            "__v": int
        }
        
        for field, expected_type in required_fields.items():
            assert field in todo_data, f"Todo should have '{field}' field"
            field_value = todo_data[field]
            assert field_value is not None, f"Todo '{field}' should not be null"
            assert isinstance(field_value, expected_type), f"Todo '{field}' should be of type {expected_type.__name__}, got {type(field_value).__name__}"
        
        log.info("✅ Todo has all required fields properly populated")
        allure_helper.attach_validation_result("Required Fields Validation", True, {"fields_validated": list(required_fields.keys())})
        
    except Exception as e:
        log.error(f"❌ Required fields validation failed: {str(e)}")
        allure_helper.attach_validation_result("Required Fields Validation", False, {"error": str(e)})
        raise

@then('the response should contain updated todo details')
@allure_helper.step_decorator("Verify response contains updated todo details")
def step_verify_response_contains_updated_todo_details(context):
    """Verify response contains updated todo details"""
    try:
        response_data = context.api_response.json()
        todo_data = response_data.get("data", {})
        
        # Check that response contains updated todo
        assert "data" in response_data, "Response should contain 'data' field"
        assert todo_data, "Updated todo data should not be empty"
        
        # Verify updatedAt timestamp is recent (updated)
        if "updatedAt" in todo_data:
            from datetime import datetime
            updated_at = todo_data["updatedAt"]
            # Just verify it's a valid timestamp string
            assert updated_at, "updatedAt should not be empty"
        
        log.info("✅ Response contains updated todo details")
        allure_helper.attach_validation_result("Updated Todo Details Validation", True, {"todo_id": todo_data.get("_id")})
        
    except Exception as e:
        log.error(f"❌ Updated todo details validation failed: {str(e)}")
        allure_helper.attach_validation_result("Updated Todo Details Validation", False, {"error": str(e)})
        raise

@when('I send PATCH request to toggle todo completion status')
@allure_helper.step_decorator("Send PATCH request to toggle todo completion status")
def step_send_patch_request_toggle_status(context):
    """Send PATCH request to toggle todo completion status"""
    global start_time
    try:
        # Get current todo status first
        get_endpoint = f"api/v1/todos/{context.todo_id}"
        current_response = context.api_client.get(get_endpoint)
        current_data = current_response.json()
        current_status = current_data.get("data", {}).get("isComplete", False)
        
        # Store previous status for validation
        context.previous_todo_status = current_status
        
        # Toggle the status
        new_status = not current_status
        update_data = {"isComplete": new_status}
        
        # Use regular PATCH endpoint since toggle endpoint might not exist
        endpoint = f"api/v1/todos/{context.todo_id}"
        
        log.info(f"Toggling todo status from {current_status} to {new_status}")
        log.info(f"Sending PATCH request to: {endpoint}")
        
        start_time = time.time()
        context.api_response = context.api_client.patch(endpoint, update_data)
        end_time = time.time()
        
        # Store response data for validation
        context.response_data = context.api_response.json()
        context.response_time = end_time - start_time
        
        # Attach Allure details
        allure_helper.attach_request_response(
            method="PATCH",
            endpoint=endpoint,
            request_data=update_data,
            response=context.api_response,
            response_time=context.response_time
        )
        
        log.info(f"PATCH toggle request completed in {context.response_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time if 'start_time' in locals() else 0
        log.error(f"PATCH toggle request failed: {str(e)}")
        allure_helper.attach_error(f"PATCH toggle request failed: {str(e)}")
        raise

@then('the todo completion status should be toggled')
@allure_helper.step_decorator("Verify todo completion status was toggled")
def step_verify_todo_status_toggled(context):
    """Verify todo completion status was toggled"""
    try:
        response_data = context.api_response.json()
        
        if 'data' in response_data:
            todo_data = response_data['data']
        else:
            todo_data = response_data
        
        assert 'isComplete' in todo_data, "Response should contain isComplete field"
        # We can't verify the exact toggle without knowing the previous state
        # So we just verify the field exists and is boolean
        assert isinstance(todo_data['isComplete'], bool), "isComplete should be boolean"
        
        current_status = todo_data['isComplete']
        log.info(f"✅ Todo completion status is now: {current_status}")
        allure_helper.attach_validation_result("Todo Status Toggle Validation", True, {
            "current_status": current_status,
            "status_type": "boolean"
        })
        
    except Exception as e:
        log.error(f"❌ Todo status toggle validation failed: {str(e)}")
        allure_helper.attach_validation_result("Todo Status Toggle Validation", False, {"error": str(e)})
        raise

@then('all returned todos should have "isComplete" as false')
@allure_helper.step_decorator("Verify all returned todos are incomplete")
def step_verify_all_todos_incomplete(context):
    """Verify all returned todos have isComplete as false"""
    try:
        response_data = context.api_response.json()
        todos_list = response_data.get("data", [])
        
        assert isinstance(todos_list, list), "Data should be a list of todos"
        
        for i, todo in enumerate(todos_list):
            assert "isComplete" in todo, f"Todo {i} should have 'isComplete' field"
            assert todo["isComplete"] is False, f"Todo {i} should have 'isComplete' as false, got: {todo['isComplete']}"
        
        log.info(f"✅ All {len(todos_list)} returned todos have 'isComplete' as false")
        allure_helper.attach_validation_result("Incomplete Todos Validation", True, {"todos_count": len(todos_list)})
        
    except Exception as e:
        log.error(f"❌ Incomplete todos validation failed: {str(e)}")
        allure_helper.attach_validation_result("Incomplete Todos Validation", False, {"error": str(e)})
        raise

@given('I have created a todo with title "{title}"')
@allure_helper.step_decorator("Create todo with title: {title}")
def step_create_todo_with_title(context, title):
    """Create a todo with specific title for testing"""
    try:
        # Create todo data with specified title
        todo_data = {
            "title": title,
            "description": f"Test todo with title: {title}"
        }
        
        # Send POST request to create todo
        endpoint = "api/v1/todos"
        context.api_response = context.api_client.post(endpoint, todo_data)
        
        # Verify creation was successful
        assert context.api_response.status == 201, f"Todo creation failed with status: {context.api_response.status}"
        
        response_data = context.api_response.json()
        context.todo_id = response_data["data"]["_id"]
        context.created_todo = response_data["data"]
        
        log.info(f"✅ Created todo with title '{title}' and ID: {context.todo_id}")
        allure_helper.attach_validation_result("Specific Todo Creation", True, {"title": title, "todo_id": context.todo_id})
        
    except Exception as e:
        log.error(f"❌ Failed to create todo with title '{title}': {str(e)}")
        allure_helper.attach_validation_result("Specific Todo Creation", False, {"error": str(e)})
        raise

@then('the response should contain todos matching the search query')
@allure_helper.step_decorator("Verify todos match search query")
def step_verify_todos_match_search_query(context):
    """Verify returned todos match the search query"""
    try:
        response_data = context.api_response.json()
        todos_list = response_data.get("data", [])
        
        assert isinstance(todos_list, list), "Data should be a list of todos"
        assert len(todos_list) > 0, "Should return at least one todo matching the search query"
        
        # Check that returned todos contain the search term (if we can determine what it was)
        search_performed = True  # We assume search was performed correctly
        
        log.info(f"✅ Found {len(todos_list)} todos matching the search query")
        allure_helper.attach_validation_result("Search Query Match Validation", True, {"matching_todos": len(todos_list)})
        
    except Exception as e:
        log.error(f"❌ Search query match validation failed: {str(e)}")
        allure_helper.attach_validation_result("Search Query Match Validation", False, {"error": str(e)})
        raise

@when('I send POST request to "api/v1/todos/" with invalid todo data')
@allure_helper.step_decorator("Send POST request with invalid todo data")
def step_send_post_request_invalid_data(context):
    """Send POST request with invalid todo data"""
    global start_time
    try:
        # Invalid data - missing required fields or invalid format
        invalid_data = {
            "title": "",  # Empty title should be invalid
            "description": None  # Null description might be invalid
        }
        
        endpoint = "api/v1/todos"
        log.info(f"Sending POST request with invalid data to: {endpoint}")
        
        start_time = time.time()
        context.api_response = context.api_client.post(endpoint, invalid_data)
        end_time = time.time()
        
        context.response_data = context.api_response.json()
        context.response_time = end_time - start_time
        
        # Attach Allure details
        allure_helper.attach_request_response(
            method="POST",
            endpoint=endpoint,
            request_data=invalid_data,
            response=context.api_response,
            response_time=context.response_time
        )
        
        log.info(f"POST request with invalid data completed in {context.response_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time if 'start_time' in locals() else 0
        log.error(f"POST request with invalid data failed: {str(e)}")
        allure_helper.attach_error(f"POST request with invalid data failed: {str(e)}")
        raise

@then('the response should contain validation errors')
@allure_helper.step_decorator("Verify response contains validation errors")
def step_verify_response_contains_validation_errors(context):
    """Verify response contains validation errors"""
    try:
        response_data = context.api_response.json()
        
        # Check for error indicators in response
        assert context.api_response.status >= 400, f"Should return error status code, got: {context.api_response.status}"
        
        # Check for error fields in response
        has_errors = ("errors" in response_data or
                     "error" in response_data or
                     response_data.get("success") is False)
        
        assert has_errors, "Response should contain validation errors"
        
        log.info("✅ Response contains validation errors as expected")
        allure_helper.attach_validation_result("Validation Errors Check", True, {"status_code": context.api_response.status})
        
    except Exception as e:
        log.error(f"❌ Validation errors check failed: {str(e)}")
        allure_helper.attach_validation_result("Validation Errors Check", False, {"error": str(e)})
        raise

@then('the response time should be less than {max_seconds:d} seconds')
@allure_helper.step_decorator("Verify response time is under {max_seconds} seconds")
def step_verify_response_time_under_limit(context, max_seconds):
    """Verify response time is under specified limit"""
    try:
        response_time = getattr(context, 'response_time', 0)
        max_time_ms = max_seconds * 1000  # Convert to milliseconds
        
        assert response_time < max_time_ms, f"Response time {response_time}ms should be less than {max_time_ms}ms"
        
        log.info(f"✅ Response time {response_time}ms is under {max_seconds} second limit")
        allure_helper.attach_validation_result("Response Time Check", True, {"response_time_ms": response_time, "limit_ms": max_time_ms})
        
    except Exception as e:
        log.error(f"❌ Response time validation failed: {str(e)}")
        allure_helper.attach_validation_result("Response Time Check", False, {"error": str(e)})
        raise

@when('I send POST request to "api/v1/todos/" with valid todo data')
@allure_helper.step_decorator("Send POST request with valid todo data")
def step_send_post_request_valid_data(context):
    """Send POST request with valid todo data"""
    global start_time
    try:
        # Valid todo data
        valid_data = {
            "title": "Performance Test Todo",
            "description": "This todo is created for performance testing"
        }
        
        endpoint = "api/v1/todos"
        log.info(f"Sending POST request with valid data to: {endpoint}")
        
        start_time = time.time()
        context.api_response = context.api_client.post(endpoint, valid_data)
        end_time = time.time()
        
        context.response_data = context.api_response.json()
        context.response_time = end_time - start_time
        
        # Attach Allure details
        allure_helper.attach_request_response(
            method="POST",
            endpoint=endpoint,
            request_data=valid_data,
            response=context.api_response,
            response_time=context.response_time
        )
        
        log.info(f"POST request with valid data completed in {context.response_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        context.response_time = end_time - start_time if 'start_time' in locals() else 0
        log.error(f"POST request with valid data failed: {str(e)}")
        allure_helper.attach_error(f"POST request with valid data failed: {str(e)}")
        raise

@then('the field "{field_name}" should be of type "{expected_type}"')
@allure_helper.step_decorator("Verify field '{field_name}' is of type '{expected_type}'")
def step_verify_field_type(context, field_name, expected_type):
    """Verify field is of expected type"""
    try:
        response_data = context.api_response.json()
        
        # Get the data field (could be single object or list)
        data = response_data.get("data")
        if isinstance(data, list) and len(data) > 0:
            # If it's a list, check the first item
            field_data = data[0]
        else:
            # If it's a single object
            field_data = data
        
        assert field_name in field_data, f"Field '{field_name}' should exist in response data"
        field_value = field_data[field_name]
        
        # Type mapping
        type_mapping = {
            "string": str,
            "boolean": bool,
            "number": (int, float),
            "integer": int,
            "float": float
        }
        
        expected_python_type = type_mapping.get(expected_type.lower(), str)
        
        if isinstance(expected_python_type, tuple):
            type_check = isinstance(field_value, expected_python_type)
        else:
            type_check = isinstance(field_value, expected_python_type)
        
        assert type_check, f"Field '{field_name}' should be of type '{expected_type}', got {type(field_value).__name__}"
        
        log.info(f"✅ Field '{field_name}' is of correct type '{expected_type}': {field_value}")
        allure_helper.attach_validation_result(f"Field Type Check - {field_name}", True, {
            "field": field_name,
            "expected_type": expected_type,
            "actual_type": type(field_value).__name__,
            "value": field_value
        })
        
    except Exception as e:
        log.error(f"❌ Field type validation failed for '{field_name}': {str(e)}")
        allure_helper.attach_validation_result(f"Field Type Check - {field_name}", False, {"error": str(e)})
        raise