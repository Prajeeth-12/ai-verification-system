import re
import os

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename by:
    1. Converting to lowercase
    2. Replacing spaces with underscores
    3. Removing unsafe characters (anything not alphanumeric, underscore, or dot)
    """
    # 1. Split name and extension
    name, ext = os.path.splitext(filename)
    
    # 2. Lowercase and replace spaces
    name = name.lower().replace(" ", "_")
    
    # 3. Remove unsafe characters
    # Keep alphanumeric and underscores
    name = re.sub(r'[^a-z0-9_]', '', name)
    
    # 4. Handle edge cases (empty name after sanitization)
    if not name:
        name = "unnamed_file"
        
    return f"{name}{ext.lower()}"
