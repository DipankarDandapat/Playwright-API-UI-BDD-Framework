 Feature: Facebook User Creation Functionality
   As a new user
   I want to create a new Facebook account
   So that I can join the Facebook community

   Scenario: Successful User Registration
     Given I am on the Facebook registration page
     When I enter valid registration details
     And I click the sign up button
     Then I should see a confirmation of successful registration


