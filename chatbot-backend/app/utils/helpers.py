# Helper functions
"""Helper functions for the application."""

from datetime import datetime
from typing import Union, Any, Dict, List, Optional
import re

def format_currency(value: Union[float, int, str], currency: str = '$') -> str:
    """Format a value as currency.
    
    Args:
        value: The value to format
        currency: The currency symbol to use
        
    Returns:
        Formatted currency string
    """
    try:
        # Convert to float if needed
        if isinstance(value, str):
            # Remove any existing currency symbols and commas
            value = re.sub(r'[^\d.-]', '', value)
            value = float(value)
        
        return f"{currency}{value:,.2f}"
    except (ValueError, TypeError):
        return str(value)

def format_date(date: Union[datetime, str], format_str: str = '%B %d, %Y') -> str:
    """Format a date.
    
    Args:
        date: The date to format (datetime object or string)
        format_str: The format string to use
        
    Returns:
        Formatted date string
    """
    if not date:
        return ''
        
    try:
        if isinstance(date, str):
            # Common date formats to try
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%d/%m/%Y'
            ]
            
            # Try each format
            for fmt in formats:
                try:
                    date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If none of the formats worked
                return date
        
        return date.strftime(format_str)
    except (ValueError, TypeError, AttributeError):
        return str(date)

def format_percentage(value: Union[float, int, str], decimal_places: int = 2) -> str:
    """Format a value as a percentage.
    
    Args:
        value: The value to format
        decimal_places: Number of decimal places to include
        
    Returns:
        Formatted percentage string
    """
    try:
        # Convert to float if needed
        if isinstance(value, str):
            # Remove any existing percentage symbols
            value = value.replace('%', '')
            value = float(value)
        
        # Format with specified decimal places
        format_str = f"{{:.{decimal_places}f}}%"
        return format_str.format(value)
    except (ValueError, TypeError):
        return str(value)

def snake_to_title(text: str) -> str:
    """Convert snake_case to Title Case.
    
    Args:
        text: Snake case text to convert
        
    Returns:
        Title case text
    """
    return ' '.join(word.capitalize() for word in text.split('_'))

def extract_entities(text: str) -> Dict[str, Any]:
    """Extract entities from text using simple pattern matching.
    
    This is a basic implementation. For production use, consider
    using a more sophisticated NLP approach.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        Dictionary of extracted entities
    """
    entities = {}
    
    # Extract project IDs
    project_id_match = re.search(r'project\s+(?:#|id\s*[:=]?\s*)(\d+)', text, re.IGNORECASE)
    if project_id_match:
        entities['project_id'] = int(project_id_match.group(1))
    
    # Extract dates
    date_matches = re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if date_matches:
        entities['dates'] = date_matches
    
    # Extract money amounts
    money_matches = re.findall(r'\$\s*([\d,]+(\.\d+)?)', text)
    if money_matches:
        entities['amounts'] = [float(m[0].replace(',', '')) for m in money_matches]
    
    return entities

def clean_input(text: str) -> str:
    """Clean user input by removing sensitive patterns.
    
    Args:
        text: User input text
        
    Returns:
        Cleaned text
    """
    # Remove potential SQL injection patterns
    text = re.sub(r';\s*--', ' ', text)
    text = re.sub(r';\s*DROP', ' drop', text, flags=re.IGNORECASE)
    text = re.sub(r';\s*DELETE', ' delete', text, flags=re.IGNORECASE)
    text = re.sub(r';\s*UPDATE', ' update', text, flags=re.IGNORECASE)
    
    # Remove potential XSS patterns
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'javascript:', 'js:', text, flags=re.IGNORECASE)
    
    return text.strip()

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def filter_dict(data: Dict[str, Any], keys: List[str], exclude: bool = False) -> Dict[str, Any]:
    """Filter a dictionary to include or exclude specified keys.
    
    Args:
        data: Dictionary to filter
        keys: Keys to include or exclude
        exclude: If True, exclude the specified keys
        
    Returns:
        Filtered dictionary
    """
    if exclude:
        return {k: v for k, v in data.items() if k not in keys}
    
    return {k: v for k, v in data.items() if k in keys}

def dict_to_text(data: Dict[str, Any], 
                 indent: int = 0, 
                 bullet: str = '- ',
                 separator: str = ': ',
                 include_keys: Optional[List[str]] = None,
                 exclude_keys: Optional[List[str]] = None) -> str:
    """Convert a dictionary to formatted text.
    
    Args:
        data: Dictionary to convert
        indent: Indentation level
        bullet: Bullet character or string
        separator: Separator between key and value
        include_keys: Keys to include (if None, include all)
        exclude_keys: Keys to exclude
        
    Returns:
        Formatted text
    """
    if not data:
        return ""
    
    # Filter keys if needed
    if include_keys:
        data = filter_dict(data, include_keys)
    if exclude_keys:
        data = filter_dict(data, exclude_keys, exclude=True)
    
    # Format each key-value pair
    lines = []
    indent_str = ' ' * indent
    
    for key, value in data.items():
        key_str = snake_to_title(key)
        
        if isinstance(value, dict):
            # Recursively format nested dictionaries
            lines.append(f"{indent_str}{bullet}{key_str}")
            lines.append(dict_to_text(value, indent + 2, bullet, separator))
        elif isinstance(value, list):
            # Format lists
            lines.append(f"{indent_str}{bullet}{key_str}")
            for item in value:
                if isinstance(item, dict):
                    lines.append(dict_to_text(item, indent + 2, bullet, separator))
                else:
                    lines.append(f"{indent_str}  {bullet}{item}")
        else:
            # Format simple key-value pairs
            lines.append(f"{indent_str}{bullet}{key_str}{separator}{value}")
    
    return '\n'.join(lines)