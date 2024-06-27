from .cli import main, chat_with_claude, interactive_mode
from .utils import (
    print_colored, print_code, create_folder, create_file,
    write_to_file, read_file, list_files, encode_image_to_base64
)

__version__ = "0.1.0"
__all__ = [
    "main",
    "chat_with_claude",
    "interactive_mode",
    "print_colored",
    "print_code",
    "create_folder",
    "create_file",
    "write_to_file",
    "read_file",
    "list_files",
    "encode_image_to_base64"
]

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Claude Engineer package initialized")