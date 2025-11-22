"""
Input Validation Functions
"""

from werkzeug.datastructures import FileStorage
from app.utils.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from typing import Tuple, Optional
import imghdr


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_file(file: FileStorage) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded image file
    
    Returns:
        (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
    
    # Validate actual image content
    file_type = imghdr.what(file)
    if file_type not in ['png', 'jpeg', 'jpg', 'webp']:
        return False, "Invalid image file"
    
    file.seek(0)  # Reset for reading
    return True, None


def validate_age_group(age_group: str) -> bool:
    """Validate age group"""
    valid_groups = ['Teen', 'Young Adult', 'Middle-aged', 'Senior']
    return age_group in valid_groups


def validate_gender(gender: str) -> bool:
    """Validate gender"""
    return gender in ['Male', 'Female']
