# iOS:
#   https://www.gkgigs.com/list-apple-ios-version-history/
#   https://betawiki.net/wiki/Category:IOS
#   https://theapplewiki.com/wiki/Models
# watchOS:
#   https://www.gkgigs.com/latest-watchos-version/
#   https://www.theiphonewiki.com/wiki/beta_Firmware
# tvOS:
#   https://gkgigs.com/latest-tvos-version/
#   https://www.theiphonewiki.com/wiki/beta_Firmware
# macOS:
#   https://www.gkgigs.com/list-of-all-macos-version-history/
#   https://betawiki.net/wiki/Category:MacOS_versions
# All:
# https://x.com/iSWUpdates
# https://theapplewiki.com/wiki/Firmware

from os.path import join
OS_build = {}

domains = {
    "AppDomain-": "private/var/mobile/Containers/Data/Application",
    "AppDomainGroup-": "private/var/mobile/Containers/Shared/AppGroup",
    "AppDomainPlugin-": "private/var/mobile/Containers/Data/PluginKitPlugin",
    "CameraRollDomain": "private/var/mobile",
    "DatabaseDomain": "private/var/db",
    "HealthDomain": "private/var/mobile",
    "HomeDomain": "private/var/mobile",
    "HomeKitDomain": "private/var/mobile",
    "InstallDomain": "private/var/installd",
    "KeyboardDomain": "private/var/mobile",
    "KeychainDomain": "private/var/protected/trustd/private",
    "ManagedPreferencesDomain": "private/var/Managed Preferences",
    "MediaDomain": "private/var/mobile",
    "MobileDeviceDomain": "private/var/MobileDevice",
    "NetworkDomain": "private/var/networkd",
    "ProtectedDomain": "private/var/protected",
    "RootDomain": "private/var/root",
    "SysContainerDomain-": "private/var/containers/Data/System",
    "SysSharedContainerDomain-": "private/var/containers/Shared/SystemGroup",
    "SystemPreferencesDomain": "private/var/preferences",
    "TonesDomain": "private/var/mobile",
    "WirelessDomain": "private/var/wireless"
}

device_id = {}

# https://theapplewiki.com/wiki/Bluetooth_PIDs
bluetooth_pid = {
    "0x0034": "Apple Watch Series 5",
    "0x003b": "Apple Watch Series 9",
    "0x0040": "iPhone10,4",
    "0x0267": "Magic Keyboard (1st generation)",
    "0x2002": "AirPods (1st generation)",
    "0x200A": "AirPods Max",
    "0x200E": "AirPods Pro (1st generation)",
    "0x2013": "AirPods (3rd generation)",
    "0x2014": "AirPods Pro (2nd generation) (Lightning)",
    "0x2016": "Beats Studio Buds +",
    "0x201b": "AirPods 4 (ANC)",
    "0x2024": "AirPods Pro (2nd generation) (USB-C)",
}

code_name = {
    "J1": "iPad (3rd Gen) (Wifi)",
    "J2": "iPad (3rd Gen) (Wifi & Cellular)",
    "J72": "iPad Air",
    "J82": "iPad Air 2",
    "J85": "iPad Mini w/ Retina Display",
    "J96": "iPad Mini 4",
    "J98": "iPad Pro",
    "J99": "iPad Pro",
    "K48": "iPad (1st Gen)",
    "K93": "iPad 2 (Wifi)",
    "K94": "iPad 2 (Wifi & GSM)",
    "K95": "iPad 2 (Wifi & CDMA)",
    "P101": "iPad (4th Gen) (Wifi)",
    "P103": "iPad (4th Gen) (Wifi & Cellular International)",
    "P105": "iPad Mini (1st Gen) (Wifi)",
    "P107": "iPad Mini (1st Gen) (Wifi & Cellular International)",
    "M68": "iPhone (1st Gen)",
    "N82": "iPhone 3G",
    "N88": "iPhone 3GS",
    "N90": "iPhone 4",
    "N92": "iPhone 4 (CDMA)",
    "N94": "iPhone 4S",
    "N41": "iPhone 5",
    "N42": "iPhone 5",
    "N48": "iPhone 5C",
    "Mesa": "Touch ID",
    "N51": "iPhone 5S",
    "N53": "iPhone 5S",
    "N61": "iPhone 6",
    "N56": "iPhone 6 Plus",
    "N69": "iPhone SE (1st Gen)",
    "N71": "iPhone 6S",
    "N66": "iPhone 6S Plus",
    "D10": "iPhone 7",
    "D11": "iPhone 7 Plus",
    "D20": "iPhone 8",
    "D21": "iPhone 8 Plus",
    "Pearl": "Face ID",
    "D22": "iPhone X",
    "N84": "iPhone XR",
    "D32": "iPhone XS",
    "D33": "iPhone XS Max",
    "N104": "iPhone 11",
    "D42": "iPhone 11 Pro",
    "D43": "iPhone 11 Pro Max",
    "D52G": "iPhone 12 Mini",
    "D53G": "iPhone 12",
    "D52P": "iPhone 12 Pro",
    "D52P": "iPhone 12 Pro Max",
    "D79": "iPhone SE (2nd Gen)",
    "D16": "iPhone 13 mini",
    "D17": "iPhone 13",
    "D63": "iPhone 13 Pro",
    "D64": "iPhone 13 Pro Max",
    "D27": "iPhone 14",
    "D28": "iPhone 14 Plus",
    "D73": "iPhone 14 Pro",
    "D74": "iPhone 14 Pro Max",
    "D37": "iPhone 15",
    "D38": "iPhone 15 Plus",
    "D83": "iPhone 15 Pro",
    "D84": "iPhone 15 Pro Max",
    "D49": "iPhone SE (3rd Gen)",
    "D59": "iPhone SE (4th Gen)",
    "D47": "iPhone 16",
    "D48": "iPhone 16 Plus",
    "D93": "iPhone 16 Pro",
    "D94": "iPhone 16 Pro Max",
}

region_code = {
    "AB": "Egypt, Jordan, Saudi Arabia, United Arab Emirates",
    "AM": "United States (Assembled in Vietnam)",
    "B": "Ireland, UK",
    "BR": "Brazil (Assembled in Brazil)",
    "BZ": "Brazil (Assembled in China)",
    "C": "Canada",
    "CL": "Canada",
    "CH": "China",
    "CZ": "Czech Republic",
    "D": "Germany",
    "DN": "Austria, Germany, Netherlands",
    "E": "Mexico",
    "EE": "Estonia",
    "FB": "France, Luxembourg",
    "FD": "Austria, Liechtenstein, Switzerland",
    "GR": "Greece",
    "HN": "India",
    "IP": "Italy",
    "HB": "Israel",
    "J": "Japan",
    "KH": "Korea",
    "KN": "Norway",
    "KS": "Finland, Sweden",
    "LA": "Colombia, Ecuador, El Salvador, Guatemala, Honduras, Peru",
    "LE": "Argentina",
    "LL": "USA, Canada",
    "LZ": "Chile, Paraguay, Uruguay",
    "MG": "Hungary",
    "MO": "Macau, Hong Kong",
    "MY": "Malaysia",
    "NF": "Belgium, France, Luxembourg",
    "PL": "Poland",
    "PO": "Portugal",
    "PP": "Philippines",
    "RO": "Romania",
    "RS": "Russia",
    "SL": "Slovakia",
    "SO": "South Africa",
    "T": "Italy",
    "TA": "Taiwan",
    "TU": "Turkey",
    "TY": "Italy",
    "VC": "Canada",
    "X": "Australia, New Zealand",
    "Y": "Spain",
    "ZA": "Singapore",
    "ZP": "Hong Kong, Macau",
}

platforms = {
    1: "iPad",
    2: "iPhone",
    3: "macOS",
    4: "macOS",
    6: "watchOS"
}


def get_root_path_from_domain(domain):
    if domain in domains:
        return domains[domain]
    elif '-' in domain:
        dash_position = domain.find("-") + 1
        path = domains[domain[:dash_position]]
        bundle_identifier = domain[dash_position:]
        return join(path, bundle_identifier)
    return ''
