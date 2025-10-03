@api
Feature: Todos API Testing
  As a QA engineer
  I want to test the Todos REST API thoroughly
  So that I can ensure its functionality and data integrity

  Background:
    Given the API client is configured for the Todos API in the testing environment



 @smoke @todos @freeapi
 Scenario: Get all todos from FreeAPI
   When I send GET request to "api/v1/todos"
   Then the response status code should be 400
   And the response should contain todos data structure
   And the response should have "success" field as true
   And the response should have "data" field containing todos list

 @smoke @todo_creation @freeapi
 Scenario: Create a new todo via FreeAPI
   Given I have valid todo data
     | field       | value                           |
     | title       | Test Todo for API Automation    |
     | description | This is a test todo via API     |
   When I send POST request to "api/v1/todos" with the todo data
   Then the response status code should be 201
   And the response should contain the created todo details
   And the todo should have a generated "_id"
   And the todo "title" should match the input data
   And the todo "description" should match the input data
   And the todo "isComplete" should be "false"

 @regression @todo_retrieval @freeapi
 Scenario: Retrieve specific todo by ID
   Given I have created a todo via FreeAPI
   When I send GET request to "api/v1/todos/{todo_id}"
   Then the response status code should be 200
   And the response should contain todo details
   And the todo "_id" should match the requested ID
   And the todo should have all required fields populated

 @regression @todo_update @freeapi
 Scenario: Update todo information
   Given I have created a todo via FreeAPI
   When I send PATCH request to "api/v1/todos/{todo_id}" with updated data
     | field       | value                    |
     | title       | Updated Todo Title       |
     | description | Updated todo description |
   Then the response status code should be 200
   And the response should contain updated todo details
   And the todo "title" should be "Updated Todo Title"
   And the todo "description" should be "Updated todo description"

 @regression @todo_status_toggle @freeapi
 Scenario: Toggle todo completion status
   Given I have created a todo via FreeAPI
   When I send PATCH request to "api/v1/todos/toggle/status/{todo_id}"
   Then the response status code should be 200
   And the response should contain updated todo details
   And the todo completion status should be toggled

  @regression @todo_deletion @freeapi
  Scenario: Delete todo
    Given I have created a todo via FreeAPI
    When I send DELETE request to "api/v1/todos/{todo_id}"
    Then the response status code should be 200
    When I send GET request to "api/v1/todos/{todo_id}"
    Then the response status code should be 404

  @regression @todos_filtering @freeapi
  Scenario: Filter todos by query parameters
    When I send GET request to "api/v1/todos?complete=false"
    Then the response status code should be 200
    And the response should contain todos data structure
    And all returned todos should have "isComplete" as false

  @regression @todos_search @freeapi
  Scenario: Search todos by query string
    Given I have created a todo with title "Searchable Todo"
    When I send GET request to "api/v1/todos?query=Searchable"
    Then the response status code should be 200
    And the response should contain todos matching the search query

  @negative @invalid_todo_creation @freeapi
  Scenario: Create todo with invalid data
    When I send POST request to "api/v1/todos/" with invalid todo data
      | field       | value |
      | title       |       |
      | description |       |
    Then the response status code should be 422
    And the response should contain validation errors

  @negative @invalid_todo_id @freeapi
  Scenario: Get todo with invalid ID
    When I send GET request to "api/v1/todos/invalid_id_123"
    Then the response status code should be 422
    And the response should contain validation errors

  @negative @update_nonexistent_todo @freeapi
  Scenario: Update non-existent todo
    When I send PATCH request to "api/v1/todos/nonexistent123" with updated data
      | field | value        |
      | title | Updated Todo |
    Then the response status code should be 422
    And the response should contain validation errors

 @negative @delete_nonexistent_todo @freeapi
 Scenario: Delete non-existent todo
   When I send DELETE request to "api/v1/todos/nonexistent123"
   Then the response status code should be 422

 @performance @todo_response_time @freeapi
 Scenario: Validate FreeAPI todos response times
   When I send GET request to "api/v1/todos"
   Then the response time should be less than 2 seconds
   When I send POST request to "api/v1/todos/" with valid todo data
     | field       | value                    |
     | title       | Performance Test Todo    |
     | description | Testing response time    |
   Then the response time should be less than 3 seconds

 @data_validation @todo_fields @freeapi
 Scenario: Validate todo response data types and structure
   Given I have created a todo via FreeAPI
   When I send GET request to "api/v1/todos/{todo_id}"
   Then the response status code should be 200
   And the field "_id" should be of type "string"
   And the field "title" should be of type "string"
   And the field "description" should be of type "string"
   And the field "isComplete" should be of type "boolean"
   And the field "createdAt" should be a valid ISO date format
   And the field "updatedAt" should be a valid ISO date format




