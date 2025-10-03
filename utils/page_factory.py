"""
Page Factory for lazy initialization of page objects
"""

def get_page_object(context, page_class):
    """
    Lazy initialization of page objects
    
    Args:
        context: Behave context object
        page_class: Page class to initialize
    
    Returns:
        Instance of the page class
    """
    page_name = page_class.__name__.lower()
    
    # Check if page object already exists in context
    if not hasattr(context, page_name):
        # Initialize page object only when needed
        setattr(context, page_name, page_class(context.page))
    
    return getattr(context, page_name)