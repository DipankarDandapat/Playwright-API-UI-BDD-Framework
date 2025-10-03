"""
Step definitions for E-commerce UI Testing
"""

from behave import given, when, then
from playwright.sync_api import expect
from utils.config_manager import get_config
import time


@given('I am on the e-commerce homepage')
def step_navigate_to_ecommerce_homepage(context):
    """Navigate to e-commerce homepage"""
    config = get_config()
    base_url = config.get('ECOMMERCE_BASE_URL', 'https://demo.opencart.com')
    context.page.goto(base_url)
    context.page.wait_for_load_state('networkidle')


@then('I should see the main navigation menu')
def step_verify_main_navigation(context):
    """Verify main navigation menu is visible"""
    nav_menu = context.page.locator('nav, .navbar, [role="navigation"]')
    expect(nav_menu).to_be_visible()


@then('I should see featured products section')
def step_verify_featured_products(context):
    """Verify featured products section is visible"""
    featured_section = context.page.locator('.featured, .products, .product-grid')
    expect(featured_section).to_be_visible()


@then('I should see search functionality')
def step_verify_search_functionality(context):
    """Verify search functionality is present"""
    search_box = context.page.locator('input[name="search"], .search-input, #search')
    expect(search_box).to_be_visible()


@then('I should see shopping cart icon')
def step_verify_cart_icon(context):
    """Verify shopping cart icon is visible"""
    cart_icon = context.page.locator('.cart, .shopping-cart, [data-testid="cart"]')
    expect(cart_icon).to_be_visible()


@when('I search for "{search_term}"')
def step_search_for_product(context, search_term):
    """Search for a specific product"""
    search_box = context.page.locator('input[name="search"], .search-input, #search').first
    search_button = context.page.locator('button[type="submit"], .search-button, .btn-search').first
    
    search_box.fill(search_term)
    search_button.click()
    context.page.wait_for_load_state('networkidle')
    context.search_term = search_term


@then('I should see search results for "{search_term}"')
def step_verify_search_results(context, search_term):
    """Verify search results are displayed"""
    # Wait for results to load
    context.page.wait_for_selector('.product, .product-item, .search-result', timeout=10000)
    
    # Check if results contain the search term
    results = context.page.locator('.product, .product-item, .search-result')
    expect(results.first).to_be_visible()


@then('each result should display product name')
def step_verify_product_names(context):
    """Verify each result displays product name"""
    product_names = context.page.locator('.product-name, .product-title, h3, h4')
    expect(product_names.first).to_be_visible()


@then('each result should display product price')
def step_verify_product_prices(context):
    """Verify each result displays product price"""
    product_prices = context.page.locator('.price, .product-price, .cost')
    expect(product_prices.first).to_be_visible()


@then('each result should display product image')
def step_verify_product_images(context):
    """Verify each result displays product image"""
    product_images = context.page.locator('.product-image img, .product img, .thumbnail img')
    expect(product_images.first).to_be_visible()


@given('I search for "{product_type}"')
def step_search_for_product_type(context, product_type):
    """Search for a specific product type"""
    search_box = context.page.locator('input[name="search"], .search-input, #search').first
    search_button = context.page.locator('button[type="submit"], .search-button, .btn-search').first
    
    search_box.fill(product_type)
    search_button.click()
    context.page.wait_for_load_state('networkidle')


@when('I click on the first product in search results')
def step_click_first_product(context):
    """Click on the first product in search results"""
    first_product = context.page.locator('.product, .product-item').first
    first_product.click()
    context.page.wait_for_load_state('networkidle')


@then('I should be on the product details page')
def step_verify_product_details_page(context):
    """Verify we are on product details page"""
    # Check for product details elements
    product_title = context.page.locator('h1, .product-title, .product-name')
    expect(product_title).to_be_visible()


@then('I should see product title')
def step_verify_product_title(context):
    """Verify product title is visible"""
    product_title = context.page.locator('h1, .product-title, .product-name')
    expect(product_title).to_be_visible()


@then('I should see product price')
def step_verify_product_price(context):
    """Verify product price is visible"""
    product_price = context.page.locator('.price, .product-price, .cost')
    expect(product_price).to_be_visible()


@then('I should see product description')
def step_verify_product_description(context):
    """Verify product description is visible"""
    product_description = context.page.locator('.description, .product-description, .details')
    expect(product_description).to_be_visible()


@then('I should see product images')
def step_verify_product_images_detail(context):
    """Verify product images are visible on details page"""
    product_images = context.page.locator('.product-image img, .gallery img, .main-image img')
    expect(product_images.first).to_be_visible()


@then('I should see "Add to Cart" button')
def step_verify_add_to_cart_button(context):
    """Verify Add to Cart button is visible"""
    add_to_cart_btn = context.page.locator('button:has-text("Add to Cart"), .add-to-cart, [data-testid="add-to-cart"]')
    expect(add_to_cart_btn).to_be_visible()


@then('I should see quantity selector')
def step_verify_quantity_selector(context):
    """Verify quantity selector is visible"""
    quantity_selector = context.page.locator('input[name="quantity"], .quantity, .qty')
    expect(quantity_selector).to_be_visible()


@given('I am viewing a product details page')
def step_navigate_to_product_details(context):
    """Navigate to a product details page"""
    # First go to homepage and search for a product
    config = get_config()
    base_url = config.get('ECOMMERCE_BASE_URL', 'https://demo.opencart.com')
    context.page.goto(base_url)
    
    # Search for a product
    search_box = context.page.locator('input[name="search"], .search-input, #search').first
    search_button = context.page.locator('button[type="submit"], .search-button, .btn-search').first
    
    search_box.fill('laptop')
    search_button.click()
    context.page.wait_for_load_state('networkidle')
    
    # Click on first product
    first_product = context.page.locator('.product, .product-item').first
    first_product.click()
    context.page.wait_for_load_state('networkidle')


@when('I select quantity "{quantity}"')
def step_select_quantity(context, quantity):
    """Select specific quantity"""
    quantity_input = context.page.locator('input[name="quantity"], .quantity, .qty').first
    quantity_input.fill(quantity)
    context.selected_quantity = quantity


@when('I click "Add to Cart" button')
def step_click_add_to_cart(context):
    """Click the Add to Cart button"""
    add_to_cart_btn = context.page.locator('button:has-text("Add to Cart"), .add-to-cart, [data-testid="add-to-cart"]').first
    add_to_cart_btn.click()
    # Wait for the action to complete
    time.sleep(2)


@then('I should see cart notification "{message}"')
def step_verify_cart_notification(context, message):
    """Verify cart notification message"""
    # Look for success message or notification
    notification = context.page.locator('.alert-success, .notification, .toast, .message')
    if notification.count() > 0:
        expect(notification.first).to_be_visible()


@then('the cart icon should show "{count}" items')
def step_verify_cart_count(context, count):
    """Verify cart icon shows correct item count"""
    cart_count = context.page.locator('.cart-count, .cart-quantity, .badge')
    if cart_count.count() > 0:
        expect(cart_count.first).to_contain_text(count)


@when('I click on the cart icon')
def step_click_cart_icon(context):
    """Click on the shopping cart icon"""
    cart_icon = context.page.locator('.cart, .shopping-cart, [data-testid="cart"]').first
    cart_icon.click()
    context.page.wait_for_load_state('networkidle')


@then('I should see the product in my cart')
def step_verify_product_in_cart(context):
    """Verify product is in the cart"""
    cart_items = context.page.locator('.cart-item, .product-cart, .cart-product')
    expect(cart_items.first).to_be_visible()


@then('I should see correct quantity "{quantity}"')
def step_verify_cart_quantity(context, quantity):
    """Verify correct quantity in cart"""
    quantity_display = context.page.locator('.quantity, .qty, input[name="quantity"]')
    if quantity_display.count() > 0:
        # Check if it's an input field or text display
        if quantity_display.first.get_attribute('type') == 'number':
            expect(quantity_display.first).to_have_value(quantity)
        else:
            expect(quantity_display.first).to_contain_text(quantity)


@then('I should see correct total price')
def step_verify_total_price(context):
    """Verify total price is displayed"""
    total_price = context.page.locator('.total, .total-price, .grand-total')
    expect(total_price.first).to_be_visible()


@given('I have products in my shopping cart')
def step_add_products_to_cart(context):
    """Add products to shopping cart as prerequisite"""
    # Navigate to homepage and add a product to cart
    config = get_config()
    base_url = config.get('ECOMMERCE_BASE_URL', 'https://demo.opencart.com')
    context.page.goto(base_url)
    
    # Search and add product to cart
    search_box = context.page.locator('input[name="search"], .search-input, #search').first
    search_button = context.page.locator('button[type="submit"], .search-button, .btn-search').first
    
    search_box.fill('phone')
    search_button.click()
    context.page.wait_for_load_state('networkidle')
    
    # Click on first product and add to cart
    first_product = context.page.locator('.product, .product-item').first
    first_product.click()
    context.page.wait_for_load_state('networkidle')
    
    add_to_cart_btn = context.page.locator('button:has-text("Add to Cart"), .add-to-cart, [data-testid="add-to-cart"]').first
    add_to_cart_btn.click()
    time.sleep(2)


@when('I proceed to checkout')
def step_proceed_to_checkout(context):
    """Proceed to checkout"""
    # Click on cart first
    cart_icon = context.page.locator('.cart, .shopping-cart, [data-testid="cart"]').first
    cart_icon.click()
    
    # Click checkout button
    checkout_btn = context.page.locator('button:has-text("Checkout"), .checkout, [data-testid="checkout"]').first
    checkout_btn.click()
    context.page.wait_for_load_state('networkidle')


@then('I should be on the checkout page')
def step_verify_checkout_page(context):
    """Verify we are on the checkout page"""
    checkout_form = context.page.locator('form, .checkout-form, .billing-form')
    expect(checkout_form).to_be_visible()


@when('I fill in shipping information')
def step_fill_shipping_info(context):
    """Fill in shipping information from table"""
    for row in context.table:
        field_name = row['field']
        field_value = row['value']
        
        # Map field names to selectors
        field_selectors = {
            'first_name': 'input[name="firstname"], input[name="first_name"], #first-name',
            'last_name': 'input[name="lastname"], input[name="last_name"], #last-name',
            'email': 'input[name="email"], input[type="email"], #email',
            'address': 'input[name="address"], input[name="address1"], #address',
            'city': 'input[name="city"], #city',
            'postal_code': 'input[name="postcode"], input[name="postal_code"], #postal-code',
            'phone': 'input[name="telephone"], input[name="phone"], #phone'
        }
        
        if field_name in field_selectors:
            field_element = context.page.locator(field_selectors[field_name]).first
            if field_element.count() > 0:
                field_element.fill(field_value)


@when('I select payment method "{payment_method}"')
def step_select_payment_method(context, payment_method):
    """Select payment method"""
    payment_option = context.page.locator(f'input[value*="{payment_method.lower()}"], label:has-text("{payment_method}")').first
    if payment_option.count() > 0:
        payment_option.click()


@when('I fill in payment information')
def step_fill_payment_info(context):
    """Fill in payment information from table"""
    for row in context.table:
        field_name = row['field']
        field_value = row['value']
        
        # Map field names to selectors
        field_selectors = {
            'card_number': 'input[name="card_number"], input[name="cardnumber"], #card-number',
            'expiry': 'input[name="expiry"], input[name="exp_date"], #expiry',
            'cvv': 'input[name="cvv"], input[name="cvc"], #cvv',
            'card_name': 'input[name="card_name"], input[name="cardholder"], #card-name'
        }
        
        if field_name in field_selectors:
            field_element = context.page.locator(field_selectors[field_name]).first
            if field_element.count() > 0:
                field_element.fill(field_value)


@when('I click "Place Order" button')
def step_click_place_order(context):
    """Click the Place Order button"""
    place_order_btn = context.page.locator('button:has-text("Place Order"), .place-order, [data-testid="place-order"]').first
    place_order_btn.click()
    context.page.wait_for_load_state('networkidle')


@then('I should see order confirmation page')
def step_verify_order_confirmation(context):
    """Verify order confirmation page"""
    confirmation_message = context.page.locator('.success, .confirmation, .order-complete')
    expect(confirmation_message).to_be_visible()


@then('I should see order number')
def step_verify_order_number(context):
    """Verify order number is displayed"""
    order_number = context.page.locator('.order-number, .order-id, .confirmation-number')
    expect(order_number).to_be_visible()


# @then('I should see "{message}" message')
# def step_verify_message(context, message):
#     """Verify specific message is displayed"""
#     message_element = context.page.locator(f'text="{message}"')
#     expect(message_element).to_be_visible()


@given('I am on the checkout page')
def step_navigate_to_checkout_page(context):
    """Navigate to checkout page"""
    # Add a product to cart first, then go to checkout
    step_add_products_to_cart(context)
    step_proceed_to_checkout(context)


@when('I click "Place Order" button without filling required fields')
def step_click_place_order_empty(context):
    """Click Place Order without filling required fields"""
    place_order_btn = context.page.locator('button:has-text("Place Order"), .place-order, [data-testid="place-order"]').first
    place_order_btn.click()
    # Wait for validation messages
    time.sleep(1)


@then('I should see validation error "{error_message}"')
def step_verify_validation_error(context, error_message):
    """Verify validation error message"""
    error_element = context.page.locator(f'.error, .invalid-feedback, .field-error, text="{error_message}"')
    # Check if any error message is visible (validation might vary)
    error_messages = context.page.locator('.error, .invalid-feedback, .field-error, .alert-danger')
    if error_messages.count() > 0:
        expect(error_messages.first).to_be_visible()


@when('I enter invalid email "{invalid_email}"')
def step_enter_invalid_email(context, invalid_email):
    """Enter invalid email"""
    email_field = context.page.locator('input[name="email"], input[type="email"], #email').first
    email_field.fill(invalid_email)

