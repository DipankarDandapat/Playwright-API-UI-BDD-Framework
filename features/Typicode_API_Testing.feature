@api
Feature: Comprehensive API Testing As a QA engineer I want to test REST APIs thoroughly So that I can ensure API functionality and data integrity

  Background:
    Given the API client is configured for testing environment

  @smoke @users
  Scenario: Get all users from API
    When user send GET request to "/users"
    Then response status code should be 200
    And the response should contain a list of users
    And each user should have required fields "id", "name", "email"
    And response time should be less than 300 ms

  @smoke @user_creation
  Scenario: Create a new user via API
    Given I have valid user data
      | field     | value                    |
      | name      | {{random_name}}          |
      | email     | {{random_email}}         |
      | username  | {{random_username}}      |
      | phone     | {{random_phone}}         |
      | website   | https://example.com      |
    When I send POST request to "/users" with the user data
    Then response status code should be 201
    And the response should contain the created user details
    And the user should have a generated "id"
    And the user "name" should match the input data
    And the user "email" should match the input data

  @api @regression @user_retrieval
  Scenario: Retrieve specific user by ID
    Given I have created a user via API
    When user send GET request to "/users/{user_id}"
    Then the response status code should be 200
    And the response should contain user details
    And the user "id" should match the requested ID
    And the user should have all required fields populated

  @api @regression @user_update
  Scenario: Update user information
    Given I have created a user via API
    When I send PUT request to "/users/{user_id}" with updated data
      | field | value                |
      | name  | Updated User Name    |
      | email | updated@example.com  |
    Then the response status code should be 200
    And the response should contain updated user details
    And the user "name" should be "Updated User Name"
    And the user "email" should be "updated@example.com"

  @api @regression @user_deletion
  Scenario: Delete user
    Given I have created a user via API
    When user send DELETE request to "/users/{user_id}"
    Then the response status code should be 200
    When user send GET request to "/users/{user_id}"
    Then the response status code should be 404

  @api @smoke @posts
  Scenario: Get all posts from API
    When user send GET request to "/posts"
    Then the response status code should be 200
    And the response should contain a list of posts
    And each post should have required fields "id", "title", "body", "userId"
    And the response should contain at least 10 posts

  @api @regression @post_creation
  Scenario: Create a new post
    Given I have a valid user ID
    When I send POST request to "/posts" with post data
      | field  | value                                    |
      | title  | Test Post for API Automation            |
      | body   | This is a test post created via API     |
      | userId | {user_id}                               |
    Then the response status code should be 201
    And the response should contain the created post
    And the post "title" should be "Test Post for API Automation"
    And the post "userId" should match the provided user ID

  @api @regression @posts_by_user
  Scenario: Get posts by specific user
    Given I have a valid user ID
    When user send GET request to "/posts?userId={user_id}"
    Then the response status code should be 200
    And the response should contain posts for the user
    And all posts should have "userId" matching the requested user

  @api @smoke @comments
  Scenario: Get comments for a post
    Given I have a valid post ID
    When user send GET request to "/posts/{post_id}/comments"
    Then the response status code should be 200
    And the response should contain a list of comments
    And each comment should have required fields "id", "name", "email", "body", "postId"

  @api @regression @comment_creation
  Scenario: Add comment to a post
    Given I have a valid post ID
    When I send POST request to "/posts/{post_id}/comments" with comment data
      | field  | value                           |
      | name   | Test Commenter                  |
      | email  | commenter@example.com           |
      | body   | This is a test comment via API  |
    Then the response status code should be 201
    And the response should contain the created comment
    And the comment "postId" should match the post ID

  @api @smoke @albums
  Scenario: Get all albums
    When user send GET request to "/albums"
    Then the response status code should be 200
    And the response should contain a list of albums
    And each album should have required fields "id", "title", "userId"

  @api @regression @photos
  Scenario: Get photos from an album
    Given I have a valid album ID
    When user send GET request to "/albums/{album_id}/photos"
    Then the response status code should be 200
    And the response should contain a list of photos
    And each photo should have required fields "id", "title", "url", "thumbnailUrl", "albumId"

  @api @negative @invalid_endpoints
  Scenario: Test invalid API endpoints
    When user send GET request to "/invalid-endpoint"
    Then the response status code should be 404
    When user send GET request to "/users/999999"
    Then the response status code should be 404

  @api @negative @invalid_data
  Scenario: Test API with invalid data
    When I send POST request to "/users" with invalid data
      | field | value |
      | name  |       |
      | email | invalid-email |
    Then the response status code should be 400
    And response should contain validation errors

  @api @regression @data_validation
  Scenario: Validate API response data types
    When user send GET request to "/users/1"
    Then the response status code should be 200
    And field "id" should be of type "integer"
    And field "name" should be of type "string"
    And field "email" should be of type "string"
    And field "email" should be a valid email format

  @api @performance @response_time
  Scenario: Validate API response times
    When user send GET request to "/users"
    Then the response time should be less than 1 second
    When user send GET request to "/posts"
    Then the response time should be less than 1 second
    When user send GET request to "/comments"
    Then the response time should be less than 2 seconds

  @api @regression @pagination
  Scenario: Test API pagination
    When user send GET request to "/posts?_page=1&_limit=10"
    Then the response status code should be 200
    And the response should contain exactly 10 posts
    When user send GET request to "/posts?_page=2&_limit=5"
    Then the response status code should be 200
    And the response should contain exactly 5 posts

  @api @regression @filtering
  Scenario: Test API filtering and searching
    When user send GET request to "/posts?userId=1"
    Then the response status code should be 200
    And all posts should have "userId" equal to 1
    When user send GET request to "/users?name=Leanne Graham"
    Then the response status code should be 200
    And the response should contain users with name "Leanne Graham"

  @api @integration @ui_api_sync
  Scenario: Verify UI and API data consistency
    Given I have created a user via API
    When I navigate to the user profile page in UI
    Then the UI should display the same user information as API
    And the user name should match between UI and API
    And the user email should match between UI and API


