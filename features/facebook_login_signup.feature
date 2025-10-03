 @ui
 Feature: Facebook Login Functionality
   As a Facebook user
   I want to log in to my account
   So that I can access my feed and interact with friends


   Scenario: Successful Login with Valid Credentials
     Given I am on the Facebook login page
     When I enter valid username and password
     And I click the login button
     Then I should be logged in successfully


   Scenario: Unsuccessful Login with Invalid Password
     Given I am on the Facebook login page
     When I enter valid username and invalid password
     And I click the login button
     Then I should see an error message indicating invalid credentials


