"""
Input validation utilities
"""

import re


def validate_email(email):
    """
    Validate email address format
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_form_data(name, company, email, query):
    """
    Validate form submission data
    
    Args:
        name: Contact name
        company: Company name
        email: Email address
        query: Message/query
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    
    if not all([name, company, email, query]):
        return False, "All required fields must be filled"
    
    if not validate_email(email):
        return False, "Invalid email address format"
    
    if len(name) < 2:
        return False, "Name is too short"
    
    if len(query) < 10:
        return False, "Query message is too short"
    
    return True, ""
