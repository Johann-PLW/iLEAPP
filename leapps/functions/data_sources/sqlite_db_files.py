"""SQLite database path handling and read-only access helper functions."""

import sqlite3
from urllib.parse import quote

from ..output import logfunc
from ..platform import is_platform_windows


def _log_sqlite_error(path, error):
    """
    Logs an error related to SQLite database access.
    Args:
        path (str|Path): The path of the SQLite database file that caused the error.
        error (Exception): The exception object containing error details.
    """
    logfunc(f"Error with {path}:")
    logfunc(f" --> {str(error)}")


def _log_sqlite_query_error(path, query, error):
    """
    Logs an error that occurred during execution of a SQLite query.
    Args:
        path (str|Path): The path of the SQLite database file being queried.
        query (str): The SQL query that caused the error.
        error (Exception): The exception object containing error details.
    """
    logfunc(f"Query error with {path}:")
    logfunc(f" --> query: {query}")
    logfunc(f" --> Error: {str(error)}")


def get_sqlite_db_path(path):
    """
    On Windows, this normalizes long/UNC path prefixes and percent-encodes
    URI-sensitive characters while preserving drive/segment separators.
    On non-Windows platforms, it percent-encodes the path while preserving
    forward slashes.
    Args:
        path (str|Path): Path to the SQLite database file.
    Returns:
        str: Encoded path suitable for use in a SQLite file: URI.
    """

    if is_platform_windows():
        path_str = str(path)
        if path_str.startswith("\\\\?\\UNC\\"):  # UNC long path
            remainder = path_str[4:]
        elif path_str.startswith("\\\\?\\"):     # normal long path
            remainder = path_str[4:]
        elif path_str.startswith("\\\\"):        # UNC path
            remainder = "\\UNC" + path_str[1:]
        else:                                    # normal path
            remainder = path_str
        # Encode special URI characters (e.g. "#", space) so SQLite doesn't
        # treat them as fragment delimiters or query separators. Keep ":"
        # and "/" safe so the drive letter and forward slashes are preserved.
        return "%5C%5C%3F%5C" + quote(remainder, safe=":/")
    return quote(str(path), safe="/")


def open_sqlite_db_readonly(path):
    """
    Opens a SQLite database in read-only mode, so original db (and -wal/journal are intact)
    Args:
        path (str|Path): The full path to the SQLite database.
    Returns:
        sqlite3.Connection: A connection object to the SQLite database, or None if an error occurs
    """

    try:
        if path:
            path = get_sqlite_db_path(path)
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
                return db
    except sqlite3.Error as e:
        _log_sqlite_error(path, e)
    return None


def attach_sqlite_db_readonly(path, db_name):
    """
    Return the query to attach a SQLite db in read-only mode.
    Args:
        path (str): Path of the SQLite DB to attach.
        db_name (str): Name of the SQLite DB in the query.
    Returns:
        str: The SQL query to attach the SQLite db.
    """

    path = get_sqlite_db_path(path)
    return f"""ATTACH DATABASE "file:{path}?mode=ro" AS {db_name}"""


def get_sqlite_db_records(path, query, attach_query=None):
    """
    Executes a query from a SQLite database opened in read-only mode.
    Args:
        path (str|Path): The full path to the SQLite database.
        query (str): SQL query to execute.
        attach_query (str|None): Optional ATTACH DATABASE query to run first.
    Returns:
        list: Query results as a list of sqlite3.Row objects, or an empty list
        if the database cannot be opened or query execution fails.
    """

    db = open_sqlite_db_readonly(path)
    if db:
        db.row_factory = sqlite3.Row  # For fetching columns by name
        try:
            cursor = db.cursor()
            if attach_query:
                cursor.execute(attach_query)
            cursor.execute(query)
            records = cursor.fetchall()
            return records
        except sqlite3.Error as e:
            _log_sqlite_error(path, e)
    return []


def get_sqlite_multiple_db_records(path_list, query, data_headers):
    """
    Executes the same query across multiple SQLite databases and merges results.
    Args:
            path_list (list[str|Path]): SQLite database paths to query.
            query (str): SQL query to execute against each database.
            data_headers (tuple|list): Column headers for the output data.
    Returns:
            tuple: (data_headers, data_list, source_path) where:
                    - data_headers includes an added "Source Path" column when multiple
                        databases are queried.
                    - data_list contains merged query records, with source path appended
                        to each record when multiple databases are queried.
                    - source_path is either the single source db path, a generic message
                        for multiple sources, or an empty string if no paths are provided.
    """

    multiple_source_files = len(path_list) > 1
    source_path = ""
    data_list = []
    if multiple_source_files:
        data_headers = list(data_headers)
        data_headers.append('Source Path')
        data_headers = tuple(data_headers)
        source_path = 'file path in the report below'
    elif path_list:
        source_path = path_list[0]
    for file in path_list:
        records = get_sqlite_db_records(file, query)
        for record in records:
            if multiple_source_files:
                modifiable_record = list(record)
                modifiable_record.append(file)
                record = tuple(modifiable_record)
            data_list.append(record)
    return data_headers, data_list, source_path


def does_table_exist_in_db(path, table_name):
    """
    Checks if a table with specified name exists in an SQLite db.
    Args:
        path (str|Path): The full path to the SQLite database.
        table_name (str): The name of the table to check for.
    Returns:
        bool: True if the table exists, False otherwise.
    """
    db = open_sqlite_db_readonly(path)
    if db:
        try:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            cursor = db.execute(query, (table_name,))
            record = cursor.fetchone()
            return bool(record)
        except sqlite3.OperationalError as ex:
            _log_sqlite_query_error(path, query, ex)
    return False


def does_column_exist_in_db(path, table_name, col_name):
    """
    Checks if a specific column exists in a SQLite database table.
    Args:
        path (str|Path): The full path to the SQLite database.
        table_name (str): The name of the table to check within.
        col_name (str): The name of the column to check for.
    Returns:
        bool: True if the column exists in the table, False otherwise.
    """

    col_name = col_name.lower()
    db = open_sqlite_db_readonly(path)
    if db:
        db.row_factory = sqlite3.Row  # For fetching columns by name
        try:
            query = f"pragma table_info('{table_name}');"
            cursor = db.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            for record in records:
                if record['name'].lower() == col_name:
                    return True
        except sqlite3.Error as ex:
            _log_sqlite_query_error(path, query, ex)
    return False


def does_view_exist_in_db(path, view_name):
    """
    Checks if a specific view exists in a SQLite database.
    Args:
        path (str|Path): The full path to the SQLite database.
        view_name (str): The name of the view to check for.
    Returns:
        bool: True if the view exists, False otherwise.
    """

    db = open_sqlite_db_readonly(path)
    if db:
        try:
            query = f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view_name}'"
            cursor = db.execute(query)
            record = cursor.fetchone()
            return bool(record)
        except sqlite3.OperationalError as ex:
            _log_sqlite_query_error(path, query, ex)
    return False
