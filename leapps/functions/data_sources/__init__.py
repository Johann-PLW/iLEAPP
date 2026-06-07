"""Data source package"""

from .json_files import get_json_file_content, save_content_to_json_file, convert_json_file_to_namedtuple
from .text_files import get_txt_file_content, save_content_to_txt_file

__all__ = ["get_json_file_content", "save_content_to_json_file", "convert_json_file_to_namedtuple"]
__all__ += ["get_txt_file_content", "save_content_to_txt_file"]
