"""Data source package"""

from .search_files import FileSeekerDir, FileSeekerFile, FileSeekerZip, FileSeekerTar, FileSeekerItunes, \
    get_itunes_backup_type, check_itunes_backup_status, decrypt_itunes_backup
from .json_files import get_json_file_content, save_content_to_json_file, convert_json_file_to_namedtuple
from .sqlite_db_files import get_sqlite_db_path, open_sqlite_db_readonly, attach_sqlite_db_readonly, \
    get_sqlite_db_records, get_sqlite_multiple_db_records, does_table_exist_in_db, does_column_exist_in_db, \
    does_view_exist_in_db
from .text_files import get_txt_file_content, save_content_to_txt_file, append_content_to_txt_file

__all__ = ["FileSeekerDir", "FileSeekerFile", "FileSeekerZip", "FileSeekerTar", "FileSeekerItunes",
           "get_itunes_backup_type", "check_itunes_backup_status", "decrypt_itunes_backup"]
__all__ += ["get_json_file_content", "save_content_to_json_file", "convert_json_file_to_namedtuple"]
__all__ += ["get_sqlite_db_path", "open_sqlite_db_readonly", "attach_sqlite_db_readonly", "get_sqlite_db_records",
            "get_sqlite_multiple_db_records", "does_table_exist_in_db", "does_column_exist_in_db",
            "does_view_exist_in_db"]
__all__ += ["get_txt_file_content", "save_content_to_txt_file", "append_content_to_txt_file"]
