__artifacts_v2__ = {
    "ConnectedDeviceInformation_DeviceHistory": {
        "name": "Connected Device Information - Connected Device and OS History",
        "description": "Connected Devices",
        "author": "@SQLMcGee",
        "version": "0.3",
        "date": "2025-01-30",
        "requirements": "none",
        "category": "Device Information",
        "notes": "Queries from reserach conducted by Metadata Forensics, LLC\
        Apple product identification, common name, OS, and timeframe of use",
        "paths": ('*Health/healthdb_secure.sqlite*'),
        "output_types": "standard",
        "artifact_icon": "smartphone"
    },
    "ConnectedDeviceInformation_ConsolidatedConnectedDeviceHistory": {
        "name": "Connected Device Information - Consolidated Connected Device History",
        "description": "Connected Devices",
        "author": "@SQLMcGee",
        "version": "0.2",
        "date": "2025-01-30",
        "requirements": "none",
        "category": "Device Information",
        "notes": "Queries from reserach conducted by Metadata Forensics, LLC\
        Apple product grouped for starting and ending timeframe of use",
        "paths": ('*Health/healthdb_secure.sqlite*'),
        "output_types": "standard",
        "artifact_icon": "smartphone"
    },
    "connected_device_information_current_device_info": {
        "name": "Connected Device Information - Current Device Information",
        "description": "Connected Devices",
        "author": "@SQLMcGee",
        "version": "0.2",
        "date": "2025-01-30",
        "requirements": "none",
        "category": "Device Information",
        "notes": "Queries from reserach conducted by Metadata Forensics, LLC\
        Current Apple Device and OS Information",
        "paths": ('*Health/healthdb.sqlite*'),
        "output_types": "standard",
        "artifact_icon": "smartphone"
    }
}


from packaging import version
from scripts.builds_ids import OS_build, device_id
from scripts.ilapfuncs import artifact_processor, get_file_path, \
    does_table_exist_in_db, get_sqlite_db_records, logfunc, \
    convert_cocoa_core_data_ts_to_utc
from scripts.ilapfuncs import open_sqlite_db_readonly, convert_ts_human_to_timezone_offset

@artifact_processor
def ConnectedDeviceInformation_DeviceHistory(files_found, report_folder, seeker, wrap_text, timezone_offset):
    data_list = []
    healthdb_secure = ''

    for file_found in files_found:
        if file_found.endswith('healthdb_secure.sqlite'):
           healthdb_secure = file_found
        else:
            continue

    with open_sqlite_db_readonly(healthdb_secure) as db:
        cursor = db.cursor()

        cursor.execute('''
        SELECT
        MIN(datetime(objects.creation_date + 978307200, 'UNIXEPOCH')) AS "Start Date",
        MAX(datetime(objects.creation_date + 978307200, 'UNIXEPOCH')) AS "End Date",
        data_provenances.origin_product_type AS 'Product Origin (Common Name)',
        data_provenances.origin_product_type AS "Origin Product",
        source_id AS "Source ID",
        data_provenances.origin_build AS "iOS / WatchOS Version"
        FROM objects
        LEFT OUTER JOIN data_provenances ON objects.provenance = data_provenances.ROWID
        WHERE data_provenances.origin_product_type != "iPhone0,0" AND data_provenances.origin_product_type != "UnknownDevice"
        AND objects.creation_date > 0
        GROUP BY origin_product_type, origin_build
        HAVING MIN(datetime(objects.creation_date + 978307200, 'UNIXEPOCH')) != MAX(datetime(objects.creation_date + 978307200, 'UNIXEPOCH'))
        ORDER BY creation_date;
        ''')
    
        all_rows = cursor.fetchall()

        for row in all_rows:
            origin_product_type = device_id.get(row[2], row[2])
            origin_build = OS_build.get(row[5], row[5])
            start_timestamp = convert_ts_human_to_timezone_offset(row[0], timezone_offset)
            end_timestamp = convert_ts_human_to_timezone_offset(row[1], timezone_offset)
            data_list.append(
                (start_timestamp, end_timestamp, origin_product_type, row[3], row[4], origin_build))
        
    data_headers = (
        ('Start Time', 'datetime'), ('End Time', 'datetime'), 'Product Origin (Common Name)', 'Product Origin', 'Source ID', 'iOS / WatchOS Version')
    return data_headers, data_list, healthdb_secure

@artifact_processor
def ConnectedDeviceInformation_ConsolidatedConnectedDeviceHistory(files_found, report_folder, seeker, wrap_text, timezone_offset):
    data_list = []
    healthdb_secure = ''

    for file_found in files_found:
        if file_found.endswith('healthdb_secure.sqlite'):
           healthdb_secure = file_found
        else:
            continue

    with open_sqlite_db_readonly(healthdb_secure) as db:
        cursor = db.cursor()

        cursor.execute('''
        SELECT
        MIN(datetime(objects.creation_date + 978307200, 'UNIXEPOCH')) AS "Start Date",
        MAX(datetime(objects.creation_date + 978307200, 'UNIXEPOCH')) AS "End Date",
        data_provenances.origin_product_type AS 'Product Origin (Common Name)',
        data_provenances.origin_product_type AS "Origin Product"
        FROM objects
        LEFT OUTER JOIN data_provenances ON objects.provenance = data_provenances.ROWID
        WHERE data_provenances.origin_product_type != "UnknownDevice" and data_provenances.origin_product_type != "iPhone0,0" AND objects.creation_date > 1
        GROUP BY data_provenances.origin_product_type
        ORDER BY creation_date;
        ''')
    
        all_rows = cursor.fetchall()

        for row in all_rows:
            origin_product_type = device_id.get(row[2], row[2])
            start_timestamp = convert_ts_human_to_timezone_offset(row[0], timezone_offset)
            end_timestamp = convert_ts_human_to_timezone_offset(row[1], timezone_offset)
            data_list.append(
                (start_timestamp, end_timestamp, origin_product_type, row[3]))
        
    data_headers = (
        ('Start Time', 'datetime'), ('End Time', 'datetime'), 'Product Origin (Common Name)', 'Product Origin')
    return data_headers, data_list, healthdb_secure


@artifact_processor
def connected_device_information_current_device_info(context):
    files_found = context.get_files_found()
    source_path = get_file_path(files_found, 'healthdb.sqlite')
    data_list = []

    query = '''
    SELECT
        device_context.date_modified,
        device_context.product_type_name,
        device_context.currentOS_name || " " ||
            device_context.currentOS_version As "OS Version"
    FROM device_context;
    '''

    data_headers = (
        ('Modified Time', 'datetime'), 'Product Type', 'Device Model',
        'OS Version')

    if does_table_exist_in_db(source_path, 'device_context'):
        db_records = get_sqlite_db_records(source_path, query)
        for record in db_records:
            device_model = context.get_device_model(record[1])
            mod_timestamp = convert_cocoa_core_data_ts_to_utc(record[0])
            data_list.append(
                (mod_timestamp, record[1], device_model, record[2]))
    else:
        missing_table_message = "Note: The 'device_context' table was not " + \
            "found in this database - only in newer OS versions."
        logfunc(missing_table_message)

    return data_headers, data_list, source_path
