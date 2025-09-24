import json
import re
from os.path import basename
from pathlib import Path


class Context:
    _report_folder = None
    _seeker = None
    _artifact_info = None
    _module_name = None
    _module_file_path = None
    _artifact_name = None
    _files_found = None
    _filename_lookup_map = {}
    _device_ids = {}
    _os_builds = {}

    @staticmethod
    def set_report_folder(report_folder):
        Context._report_folder = report_folder

    @staticmethod
    def set_seeker(seeker):
        Context._seeker = seeker

    @staticmethod
    def set_artifact_info(artifact_info):
        Context._artifact_info = artifact_info

    @staticmethod
    def set_module_name(module_name):
        Context._module_name = module_name

    @staticmethod
    def set_module_file_path(module_file_path):
        Context._module_file_path = module_file_path

    @staticmethod
    def set_artifact_name(artifact_name):
        Context._artifact_name = artifact_name

    @staticmethod
    def set_files_found(files_found):
        Context._files_found = files_found

    @staticmethod
    def _set_device_ids():
        device_ids_path = Path(
            __file__).parent.absolute().joinpath('data', 'device_ids.json')
        with open(device_ids_path, 'rt', encoding='utf-8') as json_file:
            Context._device_ids = json.load(json_file)

    @staticmethod
    def _set_os_builds():
        os_builds_path = Path(
            __file__).parent.absolute().joinpath('data', 'os_builds.json')
        with open(os_builds_path, 'rt', encoding='utf-8') as json_file:
            Context._os_builds = json.load(json_file)

    @staticmethod
    def _build_lookup_map():
        """Builds and returns a dictionary mapping filenames to a list
        of full paths."""
        if Context._files_found is None:
            raise ValueError(
                "Cannot build lookup map: _files_found is not set.")

        filename_lookup = {}
        for full_path in Context._files_found:
            filename = basename(full_path)
            if filename not in filename_lookup:
                filename_lookup[filename] = []
            filename_lookup[filename].append(full_path)
        return filename_lookup

    @staticmethod
    def get_report_folder():
        if not Context._report_folder:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._report_folder

    @staticmethod
    def get_seeker():
        if not Context._seeker:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._seeker

    @staticmethod
    def get_artifact_info():
        if not Context._artifact_info:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._artifact_info

    @staticmethod
    def get_module_name():
        if not Context._module_name:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._module_name

    @staticmethod
    def get_module_file_path():
        if not Context._module_file_path:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._module_file_path

    @staticmethod
    def get_artifact_name():
        if not Context._artifact_name:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._artifact_name

    @staticmethod
    def get_files_found():
        if Context._files_found is None:
            raise ValueError("Context not set. This function should be" +
                             " called from within an artifact.")
        return Context._files_found

    @staticmethod
    def get_filename_lookup_map():
        if not Context._filename_lookup_map:
            Context._filename_lookup_map = Context._build_lookup_map()
        return Context._filename_lookup_map

    @staticmethod
    def get_source_file_path(partial_path):
        """
        Finds the full source path for a given partial or relative path.

        This function uses a pre-computed lookup map for high-speed searching.
        It first finds candidate paths based on the filename and then verifies
        the match using the full partial path provided.

        Args:
            partial_path (str): The partial or relative path of the file
                                 to find.

        Returns:
            str: The full path of the matching source file, or None
                  if not found.
        """
        lookup_map = Context.get_filename_lookup_map()

        # Defensive check to satisfy the linter.
        # This state should not be possible in practice.
        if lookup_map is None:
            return None

        filename = basename(partial_path)

        if filename in lookup_map:
            candidate_paths = lookup_map[filename]
            for candidate in candidate_paths:
                if Path(candidate).match(partial_path):
                    return candidate

        return None

    @staticmethod
    def get_device_model(identifier):
        if not Context._device_ids:
            Context._set_device_ids()
        return Context._device_ids.get(identifier, '')

    @staticmethod
    def get_os_version(build, device_type=''):
        if not Context._os_builds:
            Context._set_os_builds()
        if 'iPhone' in device_type:
            return Context._os_builds['iOS'].get(build, '')
        if 'iPad' in device_type:
            kernel_major_version = int(re.match(r'^(\d+)', build).group(1))
            if kernel_major_version >= 17:
                return Context._os_builds['iOS'].get(
                    build, '').replace('iOS', 'iPadOS')
            return Context._os_builds['iOS'].get(build, '')
        if 'Mac' in device_type:
            return Context._os_builds['macOS'].get(build, '')
        if 'RealityDevice' in device_type:
            return Context._os_builds['visionOS'].get(build, '')
        if 'Watch' in device_type:
            return Context._os_builds['watchOS'].get(build, '')
        if 'AppleTV' in device_type:
            return Context._os_builds['tvOS'].get(build, '')
        os_version = []
        for os_family, builds in Context._os_builds.items():
            if build in builds:
                os_version.append(Context._os_builds[os_family][build])
        return (" or ").join(os_version)

    @staticmethod
    def clear():
        Context._report_folder = None
        Context._seeker = None
        Context._artifact_info = None
        Context._module_name = None
        Context._module_file_path = None
        Context._artifact_name = None
        Context._files_found = None
        Context._filename_lookup_map = None
