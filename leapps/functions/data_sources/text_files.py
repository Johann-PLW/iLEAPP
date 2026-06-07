"""
Text file data source for Leapp.
This module provides functionality to load and save text files.
"""

from leapps.functions.output import logfunc


def get_txt_file_content(file_path):
    """
    Load a text file and return its content.
    Args:
        file_path (str|Path): The path to the text file.
    Returns:
        list: The content of the text file as a list (one line --> one list item)
        If an error occurs, an empty list is returned.

    """
    try:
        with open(file_path, "r", encoding="utf-8") as txt_file:
            return txt_file.readlines()
    except FileNotFoundError:
        logfunc(f"Error: File '{file_path}' not found.")
    except PermissionError:
        logfunc(f"Error: Permission denied when trying to read '{file_path}'")
    except IsADirectoryError:
        logfunc(f"Error: Expected a file but found a directory at '{file_path}'.")
    except UnicodeDecodeError as e:
        logfunc(f"Error: Encoding issue reading '{file_path}': {e}")
    except OSError as e:
        logfunc(f"Error: System error related to the file, disk, or path: {e}")
    return []


def save_content_to_txt_file(file_path, data):
    """
    Save data to a text file.
    Args:
        file_path (str|Path): The path to the text file.
        data (list): The list to save (one list item --> one line).
    """
    try:
        with open(file_path, "w", encoding="utf-8") as txt_file:
            for item in data:
                txt_file.write(f"{item}\n")
    except FileNotFoundError:
        logfunc(f"'{file_path}' does not exist or is not a invalid path.")
    except PermissionError:
        logfunc(f"Error: Permission denied when trying to write '{file_path}'.")
    except IsADirectoryError:
        logfunc(f"Error: Expected a file but '{file_path}' is a directory.")
    except OSError as e:
        logfunc(f"Error: System error related to the file, disk, or path: {e}")
    except UnicodeEncodeError as e:
        logfunc(f"Error: Encoding issue writing '{file_path}': {e}")
