"""
JSON file data source for Leapp.
This module provides functionality to load and save JSON files,
and convert a JSON file into namedtuples for easier access to its contents.
"""

import json
from collections import namedtuple
import leapps.functions.output as leapps


def get_json_file_content(file_path):
    """
    Load a JSON file and return its content as a dictionary.
    Args:
        file_path (str|Path): The path to the JSON file.
    Returns:
        dict: The content of the JSON file as a dictionary. If an error occurs, an empty dictionary is returned.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors='replace') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        leapps.logfunc(f"Error: JSON file '{file_path}' not found.")
    except PermissionError:
        leapps.logfunc(f"Error: Permission denied when trying to read '{file_path}'.")
    except IsADirectoryError:
        leapps.logfunc(f"Error: Expected a file but found a directory at '{file_path}'.")
    except OSError as e:
        leapps.logfunc(f"Error: System error related to the file, disk, or path: {e}")
    except json.JSONDecodeError as e:
        leapps.logfunc(f"Error: JSON file '{file_path}' malformed: {str(e)}")
    except UnicodeDecodeError as e:
        leapps.logfunc(f"Error: Encoding issue reading '{file_path}': {e}")
    except RecursionError as e:
        leapps.logfunc(f"Error: JSON structure too deep to parse in '{file_path}': {e}")
    return {}


def save_content_to_json_file(file_path, data):
    """
    Save data to a JSON file.
    Args:
        file_path (str|Path): The path to the JSON file.
        data (dict): The data to save.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file)
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
    except TypeError as e:
        leapps.logfunc(f"Error: Data provided is not JSON serializable: {e}")
    except ValueError as e:
        leapps.logfunc(f"Error: Invalid data provided for JSON serialization: {e}")
    except RecursionError as e:
        leapps.logfunc(f"Error: Data structure too deep for JSON serialization: {e}")


def convert_json_file_to_namedtuple(json_file_path):
    """Load a JSON file and recursively convert dictionaries to namedtuples."""
    json_data = get_json_file_content(json_file_path)

    def convert(dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                dictionary[key] = convert(value)
        return namedtuple('GenericDict', dictionary.keys())(**dictionary)

    return convert(json_data)
