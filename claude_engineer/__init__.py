from .cli import main, chat_with_claude
from .utils import (
    print_colored, print_code, create_folder, create_file,
    write_to_file, read_file, list_files, encode_image_to_base64,
    tavily_search, USER_COLOR, CLAUDE_COLOR, TOOL_COLOR, RESULT_COLOR
)

__version__ = "0.1.0"
__all__ = [
    "main",
    "chat_with_claude",
    "print_colored",
    "print_code",
    "create_folder",
    "create_file",
    "write_to_file",
    "read_file",
    "list_files",
    "tavily_search",
    "encode_image_to_base64",
    "USER_COLOR",
    "CLAUDE_COLOR",
    "TOOL_COLOR",
    "RESULT_COLOR"
]

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Claude Engineer package initialized")