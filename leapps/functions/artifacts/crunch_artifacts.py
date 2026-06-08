import typing
import io
import traceback

from time import process_time, perf_counter, strftime, gmtime
from getpass import getpass
from pathlib import Path
from shutil import copy2

from . import artifact_loader, context
from ..data_sources import \
    FileSeekerDir, FileSeekerFile, FileSeekerTar, FileSeekerZip, FileSeekerItunes, \
    get_itunes_backup_type, check_itunes_backup_status, decrypt_itunes_backup
from ..output import OutputParameters, GuiWindow, logfunc, logdevinfo, write_device_info_file
from ..platform import is_platform_windows
from scripts.lavafuncs import initialize_lava, lava_finalize_output, \
    lava_insert_sqlite_artifact_search_pattern, lava_insert_sqlite_file_path, \
    lava_insert_sqlite_artifact_link_pattern_to_file

from scripts.ilapfuncs import does_table_exist_in_db


def crunch_artifacts(
        leapp, artifacts: typing.Sequence[artifact_loader.ArtifactSpec], extracttype, input_path,
        custom_output_folder, output_path, wrap_text, loader: artifact_loader.ArtifactLoader, casedata,
        profile_filename, itunes_backup_password=None, decryption_keys=None):

    start = process_time()
    start_wall = perf_counter()

    out_params = OutputParameters(leapp, output_path, custom_output_folder)
    context.Context.set_output_params(out_params)

    initialize_lava(input_path, out_params.output_folder_base, extracttype)

    logfunc("Processing started. Please wait. This may take a few minutes...")

    logfunc("\n--------------------------------------------------------------------------------------")
    logfunc(f"{leapp.name} v{leapp.version}: {leapp.description}")
    logfunc(f"Objective: {leapp.objective}")
    logfunc("By: Alexis Brignoni | @AlexisBrignoni | abrignoni.com")
    logfunc("By: Yogesh Khatri   | @SwiftForensics | swiftforensics.com\n")
    logfunc()
    logdevinfo()
    seeker = None
    password = itunes_backup_password

    try:
        if extracttype == "fs":
            seeker = FileSeekerDir(input_path, out_params.data_folder)

        elif extracttype == "file":
            seeker = FileSeekerFile(input_path, out_params.data_folder)

        elif extracttype in ("tar", "gz"):
            seeker = FileSeekerTar(input_path, out_params.data_folder)

        elif extracttype == "zip":
            seeker = FileSeekerZip(input_path, out_params.data_folder)

        elif extracttype == "itunes":
            itunes_backup_type = get_itunes_backup_type(input_path)
            if itunes_backup_type:
                supported, encrypted, message = check_itunes_backup_status(input_path, itunes_backup_type)
                if not supported:
                    logfunc(message)
                    return False
                if encrypted:
                    while not decryption_keys:
                        if not password:
                            password = getpass("iTunes Backup password: ")
                        decryption_keys, _ = decrypt_itunes_backup(input_path, password)
                        if not decryption_keys:
                            return False
            else:
                logfunc("Input folder is not a valid iTunes backup!")
                return False
            seeker = FileSeekerItunes(input_path, out_params.data_folder, itunes_backup_type, decryption_keys)

        else:
            logfunc("Error on argument -o (input type)")
            return False
    except Exception:
        logfunc("Had an exception in Seeker - see details below. Terminating Program!")
        temp_file = io.StringIO()
        traceback.print_exc(file=temp_file)
        logfunc(temp_file.getvalue())
        temp_file.close()
        return False

    # Now ready to run
    # add last_build at the start except for iTunes backups
    if extracttype != "itunes":
        artifacts.insert(0, loader["last_build"])

    logfunc(f"Info: {len(loader) - 2} artifacts loaded.")  # excluding last_build and iTunesBackupInfo
    if profile_filename:
        logfunc(f"Loaded profile: {profile_filename}")
    logfunc(f"Artifact to parse: {len(artifacts)}")
    logfunc(f"File/Directory selected: {input_path}")
    logfunc("\n--------------------------------------------------------------------------------------")

    proc_files_log_path = Path(
        out_params.output_folder_base).joinpath("_HTML", "_Script_Logs", "ProcessedFilesLog.html")
    with open(proc_files_log_path, "w+", encoding="utf8") as proc_files_log:
        proc_files_log.write(f"Extraction/Path selected: {input_path}<br><br>")

        # Special processing for iTunesBackup
        # Info.plist as it is a seperate entity, not part of the Manifest.db. Seeker won't find it
        if extracttype == "itunes":
            info_plist_path = Path(input_path).joinpath("Info.plist")
            if info_plist_path.exists():
                report_folder = Path(out_params.output_folder_base).joinpath("_HTML", "iTunes Backup")
                if not report_folder.exists():
                    try:
                        report_folder.mkdir()
                    except (FileExistsError, FileNotFoundError) as ex:
                        logfunc(f"Error creating report directory at path '{report_folder}'.")
                        logfunc(f"Error was '{ex}'.")
                loader["itunes_backup_info"].method([info_plist_path], report_folder, seeker, wrap_text)
                report_folder = Path(out_params.output_folder_base).joinpath("_HTML", "Installed Apps")
                if not report_folder.exists():
                    try:
                        report_folder.mkdir()
                    except (FileExistsError, FileNotFoundError) as ex:
                        logfunc(f"Error creating report directory at path '{report_folder}'.")
                        logfunc(f"Error was '{ex}'.")
                loader["itunes_backup_installed_applications"].method([info_plist_path],
                                                                      report_folder, seeker, wrap_text)
                print([info_plist_path])  # Remove special consideration for itunes? Merge into main search
            else:
                logfunc("Info.plist not found for iTunes Backup!")
                proc_files_log.write("Info.plist not found for iTunes Backup!")

        # Search for the files per the arguments
        parsed_modules = 0
        lava_only = False
        artifact_search_pattern_id = 0
        file_path_ids = set()

        for artifact_number, artifact in enumerate(artifacts, start=1):
            logfunc()
            logfunc(f"[{artifact_number}/{len(artifacts)}] {artifact.name} [{artifact.module_name}] artifact started")
            output_types = artifact.artifact_info.get("output_types", "")
            if isinstance(artifact.search, list) or isinstance(artifact.search, tuple):
                search_regexes = artifact.search
            elif artifact.search is None:
                search_regexes = artifact.search
            else:
                search_regexes = [artifact.search]
            files_found = []
            proc_files_log.write(f"<b>For {artifact.name} module</b>")
            if search_regexes is None:
                proc_files_log.write(f"<ul><li>No search regexes provided for {artifact.name} module.")
                proc_files_log.write("<ul><li><i>'_lava_artifacts.db'</i> used as source file.</li></ul></li></ul>")
                files_found = [Path(out_params.output_folder_base).joinpath("_lava_artifacts.db")]
            else:
                for artifact_search_regex in search_regexes:
                    artifact_search_pattern_id += 1
                    lava_insert_sqlite_artifact_search_pattern(
                        artifact_search_pattern_id, artifact.module_name, artifact.name, artifact_search_regex)
                    pattern_already_searched = artifact_search_regex in seeker.searched
                    found = seeker.search(artifact_search_regex)
                    if not found:
                        if artifact.name == "logarchive" and extracttype != "fs" and extracttype != "file":
                            src = Path(input_path).parent.joinpath("logarchive.json")
                            dst = Path(out_params.data_folder).joinpath("logarchive.json")
                            if src.exists():
                                copy2(src, dst)
                                files_found.append(dst)
                        proc_files_log.write(
                            f"<ul><li>No file found for regex <i>{artifact_search_regex}</i></li></ul>")
                    else:
                        proc_files_log.write(
                            f"<ul><li>{len(found)} {'files' if len(found) > 1 else 'file'} for regex "
                            f"<i>{artifact_search_regex}</i> located at:")
                        for pathh in found:
                            if pathh.startswith("\\\\?\\"):
                                pathh = pathh[4:]
                            proc_files_log.write(f"<ul><li>{pathh}</li></ul>")
                            if seeker.file_infos.get(pathh):
                                file_path_id = id(seeker.file_infos.get(pathh))
                                if not pattern_already_searched and file_path_id not in file_path_ids:
                                    lava_insert_sqlite_file_path(file_path_id, seeker.file_infos.get(pathh).source_path)
                                    file_path_ids.add(file_path_id)
                                lava_insert_sqlite_artifact_link_pattern_to_file(
                                    artifact_search_pattern_id, file_path_id)
                        proc_files_log.write("</li></ul>")
                        files_found.extend(found)
            if files_found:
                if not lava_only and "lava_only" in output_types:
                    lava_only = True
                category_folder = Path(out_params.output_folder_base).joinpath("_HTML", artifact.category)
                if not category_folder.exists():
                    try:
                        category_folder.mkdir()
                    except (FileExistsError, FileNotFoundError) as ex:
                        logfunc(f"Error creating '{artifact.name}' report directory at path '{category_folder}'.")
                        logfunc(f"Error was '{ex}'.")
                        continue  # cannot do work
                try:
                    artifact.method(files_found, category_folder, seeker, wrap_text)
                    if artifact.name == "logarchive":
                        lava_db_path = Path(out_params.output_folder_base).joinpath("_lava_artifacts.db")
                        if does_table_exist_in_db(lava_db_path, "logarchive"):
                            loader["logarchive_artifacts"].method([lava_db_path], category_folder, seeker, wrap_text)
                        if does_table_exist_in_db(lava_db_path, "logarchive_artifacts"):
                            unifed_logs_artifacts = []
                            unifed_logs_artifacts = [artifact.name for artifact in loader.artifacts
                                                     if artifact.module_name == "logarchive"
                                                     and artifact.name != "logarchive"
                                                     and artifact.name != "logarchive_artifacts"]
                            for unifed_log_artifact in unifed_logs_artifacts:
                                loader[unifed_log_artifact].method([lava_db_path], category_folder, seeker, wrap_text)
                except Exception as ex:
                    logfunc(f"Reading '{artifact.name}' artifact had errors!")
                    logfunc(f"Error was '{ex}'.")
                    logfunc(f"Exception Traceback: '{traceback.format_exc()}'.")
                    continue  # nope
            else:
                logfunc("No file found")
            logfunc(f"{artifact.name} [{artifact.module_name}] artifact completed")
            parsed_modules += 1
            GuiWindow.set_progress_bar(parsed_modules)
            proc_files_log.flush()

    device_info = context.Context.get_device_info()
    write_device_info_file(device_info)
    # if lava_only:
    #     write_lava_only_log()
    logfunc('')
    logfunc('Processes completed.')
    end = process_time()
    end_wall = perf_counter()
    run_time_secs = end - start
    run_time_hms = strftime('%H:%M:%S', gmtime(run_time_secs))
    logfunc(f"Processing time = {run_time_hms}")
    run_time_secs = end_wall - start_wall
    run_time_hms = strftime('%H:%M:%S', gmtime(run_time_secs))
    logfunc(f"Processing time (wall)= {run_time_hms}")

    logfunc('')
    logfunc('Report generation started.')
    # remove the \\?\ prefix we added to input and output paths, so it does not reflect in report
    if is_platform_windows():
        if out_params.output_folder_base.startswith('\\\\?\\'):
            out_params.output_folder_base = out_params.output_folder_base[4:]
        if input_path.startswith('\\\\?\\'):
            input_path = input_path[4:]

    # report.generate_report(out_params.output_folder_base, run_time_secs, run_time_hms,
    #                        extracttype, input_path, casedata, profile_filename, icons, lava_only)
    logfunc('Report generation Completed.')
    logfunc('')
    logfunc(f'Report location: {out_params.output_folder_base}')
    lava_finalize_output(out_params.output_folder_base)

    return True
