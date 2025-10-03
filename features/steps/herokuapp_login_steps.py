from behave import given, when, then
from utils.config_manager import get_config



# --- Step Definitions ---

@given('I open the browser and navigate to herokuapp login page')
def step_open_browser(context):
    config = get_config()
    base_url = config.get('HEROKUAPP_LOGIN_BASE_URL', 'https://the-internet.herokuapp.com/login')
    context.page.goto(base_url)


@when('I enter username "{username}"')
def step_enter_username(context, username):
    context.page.fill("#username", username)


@when('I enter password "{password}"')
def step_enter_password(context, password):
    context.page.fill("#password", password)


@when("I click the herokuapp login button")
def step_click_login(context):
    context.page.click("button[type='submit']")


@then("I should see the secure area page")
def step_secure_area(context):
    assert "/secure" in context.page.url, "Not redirected to secure area"


@then('I should see a message "{message}"')
def step_success_message(context, message):
    page_text = context.page.inner_text("#flash")
    assert message in page_text, f"Expected success message not found. Got: {page_text}"


@then('I should see an error message "{message}"')
def step_error_message(context, message):
    page_text = context.page.inner_text("#flash")
    assert message in page_text, f"Expected error message not found. Got: {page_text}"