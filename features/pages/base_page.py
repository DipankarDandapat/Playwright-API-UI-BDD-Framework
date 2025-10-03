from playwright.sync_api import Page, expect, Locator
from typing import Optional, Union, List, Dict, Pattern, Any
import json
from pathlib import Path
import re
from utils.logger import customLogger

log = customLogger()

class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.elements: Dict[str, Any] = {}
        self._load_elements()


    def _load_elements(self):
        """Load elements from JSON file based on the page name."""
        page_name = self.__class__.__name__.lower().replace("page", "")
        element_file = Path(__file__).parent.parent / "elements" / f"{page_name}_page.json"

        if not element_file.exists():
            error_msg = f"Element file not found: {element_file}"
            log.error(error_msg)
            raise FileNotFoundError(error_msg)

        with open(element_file) as f:
            self.elements = json.load(f)
        log.info(f"Loaded elements from: {element_file}")

    def _get_locator(self, element_key: str) -> Any:
        """Get the locator based on the element key and its type."""
        if element_key not in self.elements:
            error_msg = f"Element '{element_key}' not found in page elements"
            log.error(error_msg)
            raise KeyError(error_msg)

        locator_info = self.elements[element_key]

        if isinstance(locator_info, dict):
            # Handle locator with type and value
            locator_type = locator_info.get("type", "css")

            if locator_type == "testid":
                return self.page.get_by_test_id(locator_info["value"])
            elif locator_type == "role":
                role = locator_info.get("role")
                name = locator_info.get("value")
                if not role or not name:
                    error_msg = f"Both 'role' and 'name' must be provided for locator type 'role'"
                    log.error(error_msg)
                    raise ValueError(error_msg)
                return self.page.get_by_role(role, name=name)
            elif locator_type == "text":
                return self.page.get_by_text(locator_info["value"])
            elif locator_type == "label":
                return self.page.get_by_label(locator_info["value"])
            elif locator_type == "title":
                return self.page.get_by_title(locator_info["value"])
            elif locator_type == "alt":
                return self.page.get_by_alt_text(locator_info["value"])
            elif locator_type == "placeholder":
                return self.page.get_by_placeholder(locator_info["value"])
            else:
                # Default to CSS/xpath selector
                return self.page.locator(locator_info["value"])
        else:
            # Default to CSS selector for backward compatibility
            return self.page.locator(locator_info)

    def wait_for_element_visible(self, element_key: str, timeout: int = 10000):
        """Wait for an element to be visible."""
        locator = self._get_locator(element_key)
        log.info(f"Waiting for element '{element_key}' to be visible")
        expect(locator).to_be_visible(timeout=timeout)

    def wait_for_element_clickable(self, element_key: str, timeout: int = 10000):
        """Wait for an element to be clickable."""
        locator = self._get_locator(element_key)
        log.info(f"Waiting for element '{element_key}' to be clickable")
        expect(locator).to_be_enabled(timeout=timeout)

    def click(self, element_key: str):
        """Click an element with built-in waits."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        self.wait_for_element_clickable(element_key)
        log.info(f"Clicking on '{element_key}'")
        locator.click()

    def enter_text(self, element_key: str, text: str):
        """Enter text into a field with validation."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Entering text '{text}' in '{element_key}'")
        locator.fill(text)

    def select_dropdown(self, element_key: str, value: str):
        """Select an option from a dropdown."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Selecting '{value}' from '{element_key}'")
        locator.select_option(value)

    def wait_for_network_idle(self, timeout: int = 30000):
        """Wait for the network to be idle."""
        log.info("Waiting for network to be idle")
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def take_screenshot(self, name: str):
        """Take a screenshot and save it to the reports folder."""
        screenshot_path = Path(__file__).parent.parent / "reports" / f"{name}.png"
        self.page.screenshot(path=screenshot_path)
        log.info(f"Screenshot saved: {screenshot_path}")


    def check_checkbox(self, element_key: str):
        """Check a checkbox or radio button."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Checking checkbox/radio: '{element_key}'")
        locator.check()

    def uncheck_checkbox(self, element_key: str):
        """Uncheck a checkbox."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Unchecking checkbox: '{element_key}'")
        locator.uncheck()

    def select_option(self, element_key: str, values: Union[str, List[str]]):
        """Select option(s) in a dropdown."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Selecting option(s) '{values}' in '{element_key}'")
        locator.select_option(values)

    def double_click(self, element_key: str):
        """Double click an element."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Double clicking: '{element_key}'")
        locator.dblclick()

    def right_click(self, element_key: str):
        """Right click an element."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Right clicking: '{element_key}'")
        locator.click(button="right")

    def press_key(self, element_key: str, key: str):
        """Press specific keyboard key on element."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Pressing key '{key}' on: '{element_key}'")
        locator.press(key)

    def upload_file(self, element_key: str, files: Union[str, List[str]]):
        """Upload file(s) to file input."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Uploading files '{files}' to: '{element_key}'")
        locator.set_input_files(files)

    def focus_element(self, element_key: str):
        """Focus on specified element."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Focusing on: '{element_key}'")
        locator.focus()

    def hover_element(self, element_key: str):
        """Hover mouse over element."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Hovering over: '{element_key}'")
        locator.hover()

    def drag_and_drop(self, source_key: str, target_key: str):
        """Drag element to target location."""
        source_locator = self._get_locator(source_key)
        target_locator = self._get_locator(target_key)
        self.wait_for_element_visible(source_key)
        self.wait_for_element_visible(target_key)
        log.info(f"Dragging '{source_key}' to '{target_key}'")
        source_locator.drag_to(target_locator)

    def scroll_to_element(self, element_key: str):
        """Scroll element into view."""
        locator = self._get_locator(element_key)
        log.info(f"Scrolling to: '{element_key}'")
        locator.scroll_into_view_if_needed()

    def clear_input(self, element_key: str):
        """Clear input field content."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Clearing input: '{element_key}'")
        locator.clear()

    def get_text_content(self, element_key: str) -> str:
        """Get text content of element."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Getting text from: '{element_key}'")
        return locator.text_content()

    def force_click(self, element_key: str):
        """Force click element bypassing actionability checks."""
        locator = self._get_locator(element_key)
        log.warning(f"Force clicking: '{element_key}'")
        locator.click(force=True)

    def type_text(self, element_key: str, text: str, delay: int = None):
        """Type text character by character with optional delay."""
        locator = self._get_locator(element_key)
        self.wait_for_element_visible(element_key)
        log.info(f"Typing text '{text}' in: '{element_key}'")
        locator.press_sequentially(text, delay=delay)

    def verify_element_is_attached(self, element_key: str):
        """Verify element is attached to the DOM."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is attached")
        expect(locator).to_be_attached()

    def verify_checkbox_is_checked(self, element_key: str):
        """Verify checkbox is checked."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying checkbox '{element_key}' is checked")
        expect(locator).to_be_checked()

    def verify_element_is_disabled(self, element_key: str):
        """Verify element is disabled."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is disabled")
        expect(locator).to_be_disabled()

    def verify_element_is_editable(self, element_key: str):
        """Verify element is editable."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is editable")
        expect(locator).to_be_editable()

    def verify_element_is_empty(self, element_key: str):
        """Verify element is empty."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is empty")
        expect(locator).to_be_empty()

    def verify_element_is_enabled(self, element_key: str):
        """Verify element is enabled."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is enabled")
        expect(locator).to_be_enabled()

    def verify_element_is_focused(self, element_key: str):
        """Verify element is focused."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is focused")
        expect(locator).to_be_focused()

    def verify_element_is_hidden(self, element_key: str):
        """Verify element is hidden."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is hidden")
        expect(locator).to_be_hidden()

    def verify_element_in_viewport(self, element_key: str):
        """Verify element is in viewport."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is in viewport")
        expect(locator).to_be_in_viewport()

    def verify_element_is_visible(self, element_key: str):
        """Verify element is visible."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' is visible")
        expect(locator).to_be_visible()

    def verify_element_contains_text(self, element_key: str, text: Union[str, Pattern]):
        """Verify element contains text."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' contains text: {text}")
        expect(locator).to_contain_text(text)

    def verify_element_has_attribute(self, element_key: str, attribute: str, value: Optional[str] = None):
        """Verify element has attribute with optional value."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has attribute '{attribute}'")
        expect(locator).to_have_attribute(attribute, value)

    def verify_element_has_class(self, element_key: str, class_name: Union[str, Pattern, List[Union[str, Pattern]]]):
        """Verify element has class name."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has class '{class_name}'")
        expect(locator).to_have_class(class_name)

    def verify_element_count(self, element_key: str, count: int):
        """Verify element has exact count."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' count is {count}")
        expect(locator).to_have_count(count)

    def verify_element_has_css(self, element_key: str, css: Dict[str, str]):
        """Verify element has CSS properties."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has CSS properties: {css}")
        expect(locator).to_have_css(**css)

    def verify_element_has_id(self, element_key: str, element_id: str):
        """Verify element has ID."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has ID '{element_id}'")
        expect(locator).to_have_id(element_id)

    def verify_element_has_js_property(self, element_key: str, prop_name: str, value: Any):
        """Verify element has JavaScript property."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has JS property '{prop_name}'")
        expect(locator).to_have_js_property(prop_name, value)

    def verify_element_has_text(self, element_key: str, text: Union[str, Pattern, List[Union[str, Pattern]]]):
        """Verify element matches text."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has text: {text}")
        expect(locator).to_have_text(text)

    def verify_element_has_value(self, element_key: str, value: str):
        """Verify input element has value."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has value: {value}")
        expect(locator).to_have_value(value)

    def verify_element_has_values(self, element_key: str, values: List[str]):
        """Verify select element has selected values."""
        locator = self._get_locator(element_key)
        log.info(f"Verifying element '{element_key}' has selected values: {values}")
        expect(locator).to_have_values(values)

    def verify_page_title(self, title: Union[str, Pattern]):
        """Verify page has title."""
        log.info(f"Verifying page title is: {title}")
        log.info(f"Orginal page title is: {self.page.title()}")
        expect(self.page).to_have_title(title)

    def verify_page_url(self, url: Union[str, Pattern]):
        """Verify page has URL."""
        log.info(f"Verifying page URL is: {url}")
        expect(self.page).to_have_url(url)

    def filter_by_text(self, element_key: str, text: Union[str, re.Pattern], strict: bool = True) -> Locator:
        """Filter elements by text content."""
        locator = self._get_locator(element_key)
        filtered = locator.filter(has_text=text)
        self._handle_strictness(filtered, f"Elements filtered by text '{text}'", strict)
        return filtered

    def filter_by_child(self, parent_key: str, child_locator: Union[str, Locator], strict: bool = True) -> Locator:
        """Filter parent elements containing specific child."""
        parent_locator = self._get_locator(parent_key)
        if isinstance(child_locator, str):
            child_locator = self._get_locator(child_locator)
        filtered = parent_locator.filter(has=child_locator)
        self._handle_strictness(filtered, f"Elements filtered by child", strict)
        return filtered

    def get_list_items(self, list_key: str) -> List[Locator]:
        """Get all elements in a list."""
        locator = self._get_locator(list_key)
        log.info(f"Getting all items in list: '{list_key}'")
        return locator.all()

    def click_list_item_by_text(self, list_key: str, text: str, button_key: Optional[str] = None):
        """Click specific item in a list based on text."""
        locator = self._get_locator(list_key)
        target_item = locator.filter(has_text=text)
        if button_key:
            button_locator = self._get_locator(button_key)
            log.info(f"Clicking button '{button_key}' in list item with text '{text}'")
            target_item.locator(button_locator).click()
        else:
            log.info(f"Clicking list item with text '{text}'")
            target_item.click()

    def click_nth_element(self, element_key: str, index: int, strict: bool = True):
        """Click nth element in a list."""
        locator = self._get_locator(element_key).nth(index)
        self._handle_strictness(locator, f"{index}th element", strict)
        log.info(f"Clicking {index}th element: '{element_key}'")
        locator.click()


    def get_element_count(self, element_key: str) -> int:
        """Get count of matching elements."""
        locator = self._get_locator(element_key)
        log.info(f"Getting count of elements: '{element_key}'")
        return locator.count()


    def assert_list_contains_texts(self, list_key: str, expected_texts: List[str]):
        """Assert list contains exactly the specified texts."""
        locator = self._get_locator(list_key)
        actual_texts = [item.text_content() for item in locator.all()]
        log.info(f"Asserting list '{list_key}' contains texts: {expected_texts}")
        assert sorted(actual_texts) == sorted(expected_texts), \
            f"Expected texts {expected_texts} not matching actual {actual_texts}"

    def _handle_strictness(self, locator: Locator, context: str, strict: bool = True):
        """Handle strict mode checks."""
        if strict and locator.count() > 1:
            error_msg = f"Strictness violation: Multiple elements found for {context}"
            log.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def for_network_idle(page: Page, timeout: float = 30000):
        page.wait_for_load_state("networkidle", timeout=timeout)

    @staticmethod
    def for_element_contains_text(page: Page, locator: str, text: str, timeout: float = 30000):
        expect(page.locator(locator)).to_contain_text(text, timeout=timeout)

    @staticmethod
    def for_element_count(page: Page, locator: str, count: int, timeout: float = 30000):
        expect(page.locator(locator)).to_have_count(count, timeout=timeout)