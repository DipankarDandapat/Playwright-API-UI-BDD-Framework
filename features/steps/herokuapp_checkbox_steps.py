import time
from behave import given, when, then
from utils.config_manager import get_config


@given('I open the browser and navigate to checkboxes page')
def step_open_browser(context):
    config = get_config()
    base_url = config.get('HEROKUAPP_CHECKBOX_BASE_URL', 'https://the-internet.herokuapp.com/checkboxes')
    context.page.goto(base_url)
    time.sleep(10)

@when("I check the first checkbox")
def step_check_first(context):
    checkbox = context.page.locator("input[type='checkbox']").nth(0)
    if not checkbox.is_checked():
        checkbox.check()

@then("the first checkbox should be selected")
def step_first_selected(context):
    checkbox = context.page.locator("input[type='checkbox']").nth(0)
    assert checkbox.is_checked(), "First checkbox is not selected"

@when("I uncheck the second checkbox")
def step_uncheck_second(context):
    checkbox = context.page.locator("input[type='checkbox']").nth(1)
    if checkbox.is_checked():
        checkbox.uncheck()

@then("the second checkbox should not be selected")
def step_second_unselected(context):
    checkbox = context.page.locator("input[type='checkbox']").nth(1)
    assert not checkbox.is_checked(), "Second checkbox is still selected"
