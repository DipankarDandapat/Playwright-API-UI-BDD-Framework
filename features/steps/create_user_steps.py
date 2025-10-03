# from behave import *
# from playwright.sync_api import expect
# import os
# import json
#
# @given("I am on the Facebook registration page")
# def step_impl(context):
#     context.facebook_createuser_page.navigate_to_facebook_signup()
#     #context.facebook_createuser_page.verify_page_title("Sign Up for Facebook")
#
# @when("I enter valid registration details")
# def step_impl(context):
#     # Load test data from JSON file
#     test_data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata', 'facebook', 'facebook_createuser_data.json')
#     with open(test_data_path, 'r') as f:
#         test_data = json.load(f)
#
#     user_details = test_data["valid_user_details"]
#     context.facebook_createuser_page.enter_registration_details(
#         user_details["first_name"],
#         user_details["last_name"],
#         user_details["email"],
#         user_details["password"],
#         user_details["birth_day"],
#         user_details["birth_month"],
#         user_details["birth_year"],
#         user_details["gender"]
#     )
#
# @when("I click the sign up button")
# def step_impl(context):
#     context.facebook_createuser_page.click_signup_button()
#
# @then("I should see a confirmation of successful registration")
# def step_impl(context):
#     pass
#     # This step needs to be adapted based on what indicates a successful registration
#     # For Facebook, after successful registration, it might redirect to a welcome page or home page
#     # Or a specific element on the home page becomes visible
#     #expect(context.page).to_have_url(os.getenv("FACEBOOK_BASE_URL") + "r.php") # Example URL after successful signup
#     # Alternatively, check for an element that only appears after successful registration
#     # context.facebook_createuser_page.verify_element_is_visible("welcome_message") # Assuming 'welcome_message' is defined in elements/facebook_home_page.json
#
#
