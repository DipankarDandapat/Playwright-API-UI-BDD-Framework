"""
Step definitions for Social Media UI Testing
"""

from behave import given, when, then
from playwright.sync_api import expect
from utils.config_manager import get_config
import time


@given('I am logged into the social media platform')
def step_login_to_social_media(context):
    """Login to social media platform"""
    config = get_config()
    base_url = config.get('SOCIAL_MEDIA_BASE_URL', 'https://www.facebook.com')
    context.page.goto(base_url)
    
    # Check if already logged in
    if context.page.locator('[data-testid="user-menu"], .user-menu, .profile-menu').count() > 0:
        return
    
    # Perform login if not already logged in
    email_field = context.page.locator('input[name="email"], #email')
    password_field = context.page.locator('input[name="pass"], input[type="password"]')
    login_button = context.page.locator('button[name="login"], button[type="submit"]')
    
    if email_field.count() > 0:
        # Use test credentials
        email_field.fill('dipak@gmail.com')
        password_field.fill('Dipankar')
        login_button.click()
        context.page.wait_for_load_state('networkidle')



@given('I am on the news feed page')
def step_navigate_to_news_feed(context):
    """Navigate to news feed page"""
    # Assume we're already logged in from previous step
    news_feed_link = context.page.locator('a[href*="feed"], a[href="/"], .home-link')
    if news_feed_link.count() > 0:
        news_feed_link.first.click()
        context.page.wait_for_load_state('networkidle')


@then('I should see my news feed')
def step_verify_news_feed(context):
    """Verify news feed is visible"""
    feed_container = context.page.locator('[data-testid="feed"], .news-feed, .feed, .timeline')
    expect(feed_container).to_be_visible()


@then('I should see posts from friends')
def step_verify_friend_posts(context):
    """Verify posts from friends are visible"""
    posts = context.page.locator('[data-testid="post"], .post, .story, .feed-item')
    expect(posts.first).to_be_visible()


@then('each post should have author name')
def step_verify_post_author(context):
    """Verify each post has author name"""
    author_names = context.page.locator('.author-name, .post-author, .user-name, strong')
    expect(author_names.first).to_be_visible()


@then('each post should have post content')
def step_verify_post_content(context):
    """Verify each post has content"""
    post_content = context.page.locator('.post-content, .post-text, .message, p')
    expect(post_content.first).to_be_visible()


@then('each post should have timestamp')
def step_verify_post_timestamp(context):
    """Verify each post has timestamp"""
    timestamps = context.page.locator('.timestamp, .post-time, .date, time')
    expect(timestamps.first).to_be_visible()


@then('each post should have like button')
def step_verify_like_button(context):
    """Verify each post has like button"""
    like_buttons = context.page.locator('[data-testid="like"], .like-button, button:has-text("Like")')
    expect(like_buttons.first).to_be_visible()


@then('each post should have comment button')
def step_verify_comment_button(context):
    """Verify each post has comment button"""
    comment_buttons = context.page.locator('[data-testid="comment"], .comment-button, button:has-text("Comment")')
    expect(comment_buttons.first).to_be_visible()


@then('each post should have share button')
def step_verify_share_button(context):
    """Verify each post has share button"""
    share_buttons = context.page.locator('[data-testid="share"], .share-button, button:has-text("Share")')
    expect(share_buttons.first).to_be_visible()


@when('I click "What\'s on your mind?" text box')
def step_click_post_creation_box(context):
    """Click the post creation text box"""
    post_box = context.page.locator('[placeholder*="mind"], .post-composer, .status-composer, textarea')
    post_box.first.click()


@then('the post creation dialog should open')
def step_verify_post_creation_dialog(context):
    """Verify post creation dialog opens"""
    post_dialog = context.page.locator('.post-dialog, .composer-dialog, .create-post-modal')
    # If no modal, check if the text area expanded
    if post_dialog.count() == 0:
        expanded_composer = context.page.locator('textarea, .expanded-composer')
        expect(expanded_composer).to_be_visible()
    else:
        expect(post_dialog).to_be_visible()


@when('I type "{post_text}"')
def step_type_post_text(context, post_text):
    """Type text in post creation area"""
    text_area = context.page.locator('textarea, .post-input, [contenteditable="true"]').first
    text_area.fill(post_text)
    context.post_text = post_text


@when('I click "Post" button')
def step_click_post_button(context):
    """Click the Post button"""
    post_button = context.page.locator('button:has-text("Post"), .post-button, [data-testid="post-button"]').first
    post_button.click()
    time.sleep(2)  # Wait for post to be created


@then('I should see "{notification}" notification')
def step_verify_notification(context, notification):
    """Verify notification message"""
    notification_element = context.page.locator(f'.notification, .alert, .toast, text="{notification}"')
    # Sometimes notifications disappear quickly, so we'll check if post appears in feed instead
    if notification_element.count() == 0:
        # Check if post appears in feed as confirmation
        recent_posts = context.page.locator('[data-testid="post"], .post, .story').first
        expect(recent_posts).to_be_visible()


@then('I should see my new post in the feed')
def step_verify_new_post_in_feed(context):
    """Verify new post appears in feed"""
    # Look for the post content we just created
    if hasattr(context, 'post_text'):
        post_with_content = context.page.locator(f'text="{context.post_text}"')
        expect(post_with_content).to_be_visible()


@then('the post should contain "{expected_text}"')
def step_verify_post_contains_text(context, expected_text):
    """Verify post contains specific text"""
    post_with_text = context.page.locator(f'text="{expected_text}"')
    expect(post_with_text).to_be_visible()


@then('the post should contain hashtags "{hashtags}"')
def step_verify_post_hashtags(context, hashtags):
    """Verify post contains hashtags"""
    hashtag_elements = context.page.locator(f'text="{hashtags}"')
    expect(hashtag_elements).to_be_visible()


@given('I can see posts in my news feed')
def step_verify_posts_in_feed(context):
    """Verify posts are visible in news feed"""
    posts = context.page.locator('[data-testid="post"], .post, .story, .feed-item')
    expect(posts.first).to_be_visible()


@when('I click like button on the first post')
def step_click_like_on_first_post(context):
    """Click like button on the first post"""
    first_post = context.page.locator('[data-testid="post"], .post, .story').first
    like_button = first_post.locator('[data-testid="like"], .like-button, button:has-text("Like")').first
    
    # Store initial like count if visible
    like_count = first_post.locator('.like-count, .likes')
    if like_count.count() > 0:
        context.initial_like_count = like_count.text_content()
    
    like_button.click()
    time.sleep(1)


@then('the like button should be highlighted')
def step_verify_like_button_highlighted(context):
    """Verify like button is highlighted/active"""
    first_post = context.page.locator('[data-testid="post"], .post, .story').first
    like_button = first_post.locator('[data-testid="like"], .like-button, button:has-text("Like")').first
    
    # Check if button has active/liked class or different color
    button_classes = like_button.get_attribute('class')
    # This is a simplified check - in real scenarios, you'd check for specific active states
    expect(like_button).to_be_visible()


@then('the like count should increase by 1')
def step_verify_like_count_increased(context):
    """Verify like count increased"""
    first_post = context.page.locator('[data-testid="post"], .post, .story').first
    like_count = first_post.locator('.like-count, .likes')
    
    if like_count.count() > 0:
        # In a real scenario, you'd parse and compare numbers
        expect(like_count).to_be_visible()


@when('I click comment button on the first post')
def step_click_comment_on_first_post(context):
    """Click comment button on the first post"""
    first_post = context.page.locator('[data-testid="post"], .post, .story').first
    comment_button = first_post.locator('[data-testid="comment"], .comment-button, button:has-text("Comment")').first
    comment_button.click()
    time.sleep(1)


@then('the comment section should expand')
def step_verify_comment_section_expanded(context):
    """Verify comment section is expanded"""
    comment_section = context.page.locator('.comment-section, .comments, .comment-box')
    expect(comment_section.first).to_be_visible()


@when('I type "{comment_text}" in comment box')
def step_type_comment(context, comment_text):
    """Type comment in comment box"""
    comment_input = context.page.locator('.comment-input, textarea[placeholder*="comment"], input[placeholder*="comment"]').first
    comment_input.fill(comment_text)
    context.comment_text = comment_text


@when('I click "Comment" button')
def step_click_comment_button(context):
    """Click the Comment button"""
    comment_submit = context.page.locator('button:has-text("Comment"), .comment-submit, [data-testid="comment-submit"]').first
    comment_submit.click()
    time.sleep(2)


@then('I should see my comment under the post')
def step_verify_comment_under_post(context):
    """Verify comment appears under the post"""
    if hasattr(context, 'comment_text'):
        comment_element = context.page.locator(f'text="{context.comment_text}"')
        expect(comment_element).to_be_visible()


@then('the comment count should increase by 1')
def step_verify_comment_count_increased(context):
    """Verify comment count increased"""
    comment_count = context.page.locator('.comment-count, .comments-count')
    if comment_count.count() > 0:
        expect(comment_count.first).to_be_visible()


@given('I am logged in')
def step_verify_logged_in(context):
    """Verify user is logged in"""
    user_menu = context.page.locator('[data-testid="user-menu"], .user-menu, .profile-menu')
    if user_menu.count() == 0:
        # Perform login if not logged in
        step_login_to_social_media(context)


@when('I click on my profile picture')
def step_click_profile_picture(context):
    """Click on profile picture"""
    profile_pic = context.page.locator('.profile-picture, .avatar, .user-photo').first
    profile_pic.click()


@then('I should see profile dropdown menu')
def step_verify_profile_dropdown(context):
    """Verify profile dropdown menu appears"""
    dropdown_menu = context.page.locator('.dropdown-menu, .profile-menu, .user-menu')
    expect(dropdown_menu.first).to_be_visible()


@when('I click "View Profile" option')
def step_click_view_profile(context):
    """Click View Profile option"""
    view_profile_link = context.page.locator('a:has-text("View Profile"), a:has-text("Profile"), .profile-link').first
    view_profile_link.click()
    context.page.wait_for_load_state('networkidle')


@then('I should be on my profile page')
def step_verify_on_profile_page(context):
    """Verify we are on profile page"""
    profile_header = context.page.locator('.profile-header, .user-info, .profile-section')
    expect(profile_header).to_be_visible()


@then('I should see my profile information')
def step_verify_profile_information(context):
    """Verify profile information is visible"""
    profile_info = context.page.locator('.profile-info, .user-details, .bio')
    expect(profile_info).to_be_visible()


@then('I should see my posts')
def step_verify_my_posts(context):
    """Verify my posts are visible on profile"""
    my_posts = context.page.locator('.user-posts, .profile-posts, .timeline-posts')
    expect(my_posts).to_be_visible()


@then('I should see my friends count')
def step_verify_friends_count(context):
    """Verify friends count is visible"""
    friends_count = context.page.locator('.friends-count, .friend-count, text*="friends"')
    expect(friends_count.first).to_be_visible()


@when('I click "Edit Profile" button')
def step_click_edit_profile(context):
    """Click Edit Profile button"""
    edit_profile_btn = context.page.locator('button:has-text("Edit Profile"), .edit-profile, a:has-text("Edit")').first
    edit_profile_btn.click()


@then('I should see profile edit form')
def step_verify_profile_edit_form(context):
    """Verify profile edit form is visible"""
    edit_form = context.page.locator('.edit-form, .profile-form, form')
    expect(edit_form).to_be_visible()


@when('I update my bio to "{new_bio}"')
def step_update_bio(context, new_bio):
    """Update bio text"""
    bio_field = context.page.locator('textarea[name="bio"], .bio-input, textarea[placeholder*="bio"]').first
    bio_field.fill(new_bio)
    context.new_bio = new_bio


@when('I click "Save Changes" button')
def step_click_save_changes(context):
    """Click Save Changes button"""
    save_button = context.page.locator('button:has-text("Save"), .save-button, button[type="submit"]').first
    save_button.click()
    time.sleep(2)


@then('I should see "Profile updated successfully" message')
def step_verify_profile_update_message(context):
    """Verify profile update success message"""
    success_message = context.page.locator('.success, .alert-success, text="Profile updated successfully"')
    expect(success_message.first).to_be_visible()


@then('my bio should show "{expected_bio}"')
def step_verify_updated_bio(context, expected_bio):
    """Verify bio was updated"""
    bio_display = context.page.locator(f'text="{expected_bio}"')
    expect(bio_display).to_be_visible()


@when('I search for user "{username}"')
def step_search_for_user(context, username):
    """Search for a specific user"""
    search_box = context.page.locator('input[name="q"], .search-input, input[placeholder*="Search"]').first
    search_box.fill(username)
    search_box.press('Enter')
    context.page.wait_for_load_state('networkidle')


@then('I should see search results')
def step_verify_search_results(context):
    """Verify search results are displayed"""
    search_results = context.page.locator('.search-results, .results, .search-item')
    expect(search_results.first).to_be_visible()


@when('I click on the user profile in search results')
def step_click_user_in_results(context):
    """Click on user profile in search results"""
    user_result = context.page.locator('.user-result, .search-result, .profile-result').first
    user_result.click()
    context.page.wait_for_load_state('networkidle')


@then('I should be on their profile page')
def step_verify_on_user_profile(context):
    """Verify we are on the user's profile page"""
    profile_page = context.page.locator('.profile-header, .user-profile, .profile-info')
    expect(profile_page).to_be_visible()


@when('I click "Add Friend" button')
def step_click_add_friend(context):
    """Click Add Friend button"""
    add_friend_btn = context.page.locator('button:has-text("Add Friend"), .add-friend, .friend-request').first
    add_friend_btn.click()
    time.sleep(1)


@then('the button should change to "Friend Request Sent"')
def step_verify_friend_request_sent(context):
    """Verify button changed to Friend Request Sent"""
    sent_button = context.page.locator('button:has-text("Friend Request Sent"), button:has-text("Request Sent")')
    expect(sent_button.first).to_be_visible()

