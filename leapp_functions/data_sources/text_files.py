"""
Text file data source for Leapp.
This module provides functionality to load and save text files.
"""

import leapp_functions.output as leapps


def get_txt_file_content(file_path, line_by_line=False):
    """
    Load a text file and return its content.
    Args:
        file_path (str|Path): The path to the text file.
        line_by_line (bool): If True, return a list of lines;
            otherwise, return the entire content as a single string.
    Returns:
        list or str: The content of the text file.
        If an error occurs, an empty list or string is returned.

    """
    try:
        with open(file_path, "r", encoding="utf-8") as txt_file:
            if line_by_line:
                return txt_file.readlines()
            else:
                return txt_file.read()
    except FileNotFoundError:
        leapps.logfunc(f"Error: File '{file_path}' not found.")
    except PermissionError:
        leapps.logfunc(f"Error: Permission denied when trying to read '{file_path}'")
    except IsADirectoryError:
        leapps.logfunc(f"Error: Expected a file but found a directory at '{file_path}'.")
    except UnicodeDecodeError as e:
        leapps.logfunc(f"Error: Encoding issue reading '{file_path}': {e}")
    except OSError as e:
        leapps.logfunc(f"Error: System error related to the file, disk, or path: {e}")
    return []


def save_content_to_txt_file(file_path, data):
    """
    Save data to a text file.
    Args:
        file_path (str|Path): The path to the text file.
        data (list or str): The content to save. If a list, each item will be written as a separate line.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as txt_file:
            if isinstance(data, list):
                for item in data:
                    txt_file.write(f"{item}\n")
            else:
                txt_file.write(data)
    except FileNotFoundError:
        leapps.logfunc(f"'{file_path}' does not exist or is not a invalid path.")
    except PermissionError:
        leapps.logfunc(f"Error: Permission denied when trying to write '{file_path}'.")
    except IsADirectoryError:
        leapps.logfunc(f"Error: Expected a file but '{file_path}' is a directory.")
    except OSError as e:
        leapps.logfunc(f"Error: System error related to the file, disk, or path: {e}")
    except UnicodeEncodeError as e:
        leapps.logfunc(f"Error: Encoding issue writing '{file_path}': {e}")


def append_content_to_txt_file(file_path, data):
    """
    Append data to a text file.
    Args:
        file_path (str|Path): The path to the text file.
        data (str): The content to add to the text file.
    """
    try:
        with open(file_path, "a", encoding="utf-8") as txt_file:
            txt_file.write(data)
    except FileNotFoundError:
        leapps.logfunc(f"'{file_path}' does not exist or is not a invalid path.")
    except PermissionError:
        leapps.logfunc(f"Error: Permission denied when trying to write '{file_path}'.")
    except IsADirectoryError:
        leapps.logfunc(f"Error: Expected a file but '{file_path}' is a directory.")
    except OSError as e:
        leapps.logfunc(f"Error: System error related to the file, disk, or path: {e}")
    except UnicodeEncodeError as e:
        leapps.logfunc(f"Error: Encoding issue writing '{file_path}': {e}")
