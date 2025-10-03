
#@ui
#Feature: Login functionality on The Internet website
#
#  As a user
#  I want to log in with valid and invalid credentials
#  So that I can access or be restricted from the secure area
#
#  Background:
#    Given I open the browser and navigate to herokuapp login page
#
#  Scenario: Successful login with valid credentials
#    When I enter username "tomsmith"
#    And I enter password "SuperSecretPassword!"
#    And I click the herokuapp login button
#    Then I should see the secure area page
#    And I should see a message "You logged into a secure area!"
#
#  Scenario: Failed login with invalid credentials
#    When I enter username "wronguser"
#    And I enter password "wrongpassword"
#    And I click the herokuapp login button
#    Then I should see an error message "Your username is invalid!"
