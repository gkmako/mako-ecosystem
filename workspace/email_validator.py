import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate an email address using a regular expression.
    
    Args:
        email (str): The email address to validate.
        
    Returns:
        bool: True if the email is valid, False otherwise.
        
    Example:
        >>> validate_email("test@example.com")
        True
        >>> validate_email("invalid.email")
        False
    """
    if not isinstance(email, str):
        raise TypeError("Email must be a string")
    
    if not email:
        return False
    
    # Regular expression for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def extract_domain(email: str) -> Optional[str]:
    """Extract the domain from a valid email address.
    
    Args:
        email (str): The email address to extract domain from.
        
    Returns:
        Optional[str]: The domain part of the email or None if email is invalid.
        
    Example:
        >>> extract_domain("test@example.com")
        'example.com'
        >>> extract_domain("invalid.email")
        None
    """
    if validate_email(email):
        return email.split('@')[1]
    return None