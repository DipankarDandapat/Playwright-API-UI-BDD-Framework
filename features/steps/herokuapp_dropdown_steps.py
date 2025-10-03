from behave import given, when, then

from utils.config_manager import get_config


@given('I open the browser and navigate to dropdown page')
def step_open_browser(context):
    config = get_config()
    base_url = config.get('HEROKUAPP_DROPDOWN_BASE_URL', 'https://the-internet.herokuapp.com/dropdown')
    context.page.goto(base_url)

@when('I select option "{option}" from the dropdown')
def step_select_dropdown(context, option):
    context.page.select_option("#dropdown", label=option)

@then('I should see "{option}" selected')
def step_verify_dropdown(context, option):
    selected_value = context.page.locator("#dropdown").input_value()
    selected_text = context.page.locator(f"#dropdown option[value='{selected_value}']").inner_text()
    assert selected_text == option, f"Expected {option}, but got {selected_text}"
