""" LEAPPs package """

from .data_sources.json_files import convert_json_file_to_namedtuple

leapp = convert_json_file_to_namedtuple("data/leapp_config.json")
