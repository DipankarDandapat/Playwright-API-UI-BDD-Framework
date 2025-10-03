#@ui
#Feature: E-commerce Website UI Testing
# As a customer
# I want to browse and purchase products online
# So that I can shop conveniently from home
#
# Background:
#   Given I am on the e-commerce homepage
#
# @smoke @homepage
# Scenario: Verify homepage loads correctly
#   Then I should see the main navigation menu
#   And I should see featured products section
#   And I should see search functionality
#   And I should see shopping cart icon

# @smoke @search
# Scenario: Search for products
#   When I search for "laptop"
#   Then I should see search results for "laptop"
#   And each result should display product name
#   And each result should display product price
#   And each result should display product image
#
# @regression @product
# Scenario: View product details
#   Given I search for "smartphone"
#   When I click on the first product in search results
#   Then I should be on the product details page
#   And I should see product title
#   And I should see product price
#   And I should see product description
#   And I should see product images
#   And I should see "Add to Cart" button
#   And I should see quantity selector
#
# @regression @cart
# Scenario: Add product to shopping cart
#   Given I am viewing a product details page
#   When I select quantity "2"
#   And I click "Add to Cart" button
#   Then I should see cart notification "Product added to cart"
#   And the cart icon should show "2" items
#   When I click on the cart icon
#   Then I should see the product in my cart
#   And I should see correct quantity "2"
#   And I should see correct total price
#
# @regression @checkout
# Scenario: Complete checkout process
#   Given I have products in my shopping cart
#   When I proceed to checkout
#   Then I should be on the checkout page
#   When I fill in shipping information
#     | field          | value              |
#     | first_name     | John               |
#     | last_name      | Doe                |
#     | email          | john.doe@test.com  |
#     | address        | 123 Main St        |
#     | city           | New York           |
#     | postal_code    | 10001              |
#     | phone          | 555-123-4567       |
#   And I select payment method "Credit Card"
#   And I fill in payment information
#     | field       | value            |
#     | card_number | 4111111111111111 |
#     | expiry      | 12/25            |
#     | cvv         | 123              |
#     | card_name   | John Doe         |
#   And I click "Place Order" button
#   Then I should see order confirmation page
#   And I should see order number
#   And I should see "Thank you for your order" message
#
# @negative @validation
# Scenario: Validate form fields on checkout
#   Given I am on the checkout page
#   When I click "Place Order" button without filling required fields
#   Then I should see validation error "First name is required"
#   And I should see validation error "Email is required"
#   And I should see validation error "Address is required"
#   When I enter invalid email "invalid-email"
#   And I click "Place Order" button
#   Then I should see validation error "Please enter a valid email address"
#
# @regression @user_account
# Scenario: User registration and login
#   Given I am on the homepage
#   When I click "Sign Up" link
#   Then I should be on the registration page
#   When I fill in registration form
#     | field            | value                    |
#     | first_name       | {{random_first_name}}    |
#     | last_name        | {{random_last_name}}     |
#     | email            | {{random_email}}         |
#     | password         | {{random_password}}      |
#     | confirm_password | {{random_password}}      |
#   And I click "Create Account" button
#   Then I should see "Account created successfully" message
#   And I should be logged in
#   When I logout
#   And I click "Sign In" link
#   And I login with the registered credentials
#   Then I should be logged in successfully
#
# @regression @filters
# Scenario: Filter and sort products
#   Given I am on the products page
#   When I apply price filter "100-500"
#   Then all displayed products should be within price range "100-500"
#   When I apply category filter "Electronics"
#   Then all displayed products should be in "Electronics" category
#   When I sort products by "Price: Low to High"
#   Then products should be sorted by price in ascending order
#   When I sort products by "Customer Rating"
#   Then products should be sorted by rating in descending order
#
# @regression @wishlist
# Scenario: Add products to wishlist
#   Given I am logged in
#   And I am viewing a product details page
#   When I click "Add to Wishlist" button
#   Then I should see "Added to wishlist" notification
#   When I navigate to my wishlist
#   Then I should see the product in my wishlist
#   When I click "Remove from Wishlist" for the product
#   Then the product should be removed from wishlist
#
#@responsive @mobile
# Scenario: Verify mobile responsive design
#   Given I am using a mobile device viewport
#   When I navigate to the homepage
#   Then I should see mobile navigation menu
#   And I should see mobile-optimized product grid
#   When I search for products on mobile
#   Then search results should be mobile-friendly
#   When I add product to cart on mobile
#   Then mobile cart functionality should work correctly

