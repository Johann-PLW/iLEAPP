""" LEAPPs package """

import sys
from pathlib import Path

from .data_sources.json_files import convert_json_file_to_namedtuple

# From source, data/ is one folder above this package.
# In a build, PyInstaller unpacks it into the folder named by sys._MEIPASS.
DATA = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1])) / 'data'
CONFIG_FILE = DATA / 'leapp_config.json'

leapp = convert_json_file_to_namedtuple(CONFIG_FILE)
