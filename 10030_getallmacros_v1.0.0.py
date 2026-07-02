####################################################################################################
# Name: Zabbix _ Get All Macros                                                                    #
# Job: Get all Global, Host, and Template user macros from Zabbix API                              #
#      and save the result into a TXT file.                                                        #
#      - Compatible with Zabbix Version 5.0.4                                                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-06-30                                                                                 #
####################################################################################################

import requests
import json
import getpass
import sys
from datetime import datetime

#====================================================================================================
# Normalize Zabbix API URL
#====================================================================================================

def normalize_zabbix_url(url):                             # Convert normal Zabbix frontend URL to Zabbix API URL.

    url = url.strip().rstrip("/")

    if url.endswith("api_jsonrpc.php"):
        return url

    return url + "/api_jsonrpc.php"

#====================================================================================================
# Send Request to Zabbix API
#====================================================================================================

def zabbix_api_request(api_url, method, params, auth_token=None, request_id=1):          # Send a JSON-RPC request to Zabbix API.

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

    # user.login does not need auth token
    if auth_token:
        payload["auth"] = auth_token

    headers = {
        "Content-Type": "application/json-rpc"
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=20
        )

        response.raise_for_status()
        result = response.json()

    except requests.exceptions.RequestException as error:
        print(f"[ERROR] Connection error: {error}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON response from Zabbix server.")
        sys.exit(1)

    if "error" in result:
        error_data = result["error"]

        print("[ERROR] Zabbix API Error")
        print(f"Code    : {error_data.get('code')}")
        print(f"Message : {error_data.get('message')}")
        print(f"Data    : {error_data.get('data')}")

        sys.exit(1)

    return result.get("result")

#====================================================================================================
# Login to Zabbix
#====================================================================================================

def zabbix_login(api_url, username, password):

    params = {
        "user": username,                                  # "user" in zabbix version 5.0.4 API
        "password": password
    }

    token = zabbix_api_request(
        api_url=api_url,
        method="user.login",
        params=params,
        request_id=1
    )

    return token

#====================================================================================================
# Logout from Zabbix
#====================================================================================================

def zabbix_logout(api_url, auth_token):

    try:
        zabbix_api_request(
            api_url=api_url,
            method="user.logout",
            params=[],
            auth_token=auth_token,
            request_id=99
        )
    except Exception:
        pass

#====================================================================================================
# Convert Macro Type to Human-Readable Name
#====================================================================================================

def macro_type_to_name(macro_type):

    macro_types = {
        "0": "Text",
        "1": "Secret"
    }

    return macro_types.get(str(macro_type), "Unknown")

#====================================================================================================
# Get Global Macros
#====================================================================================================

def get_global_macros(api_url, auth_token):                 # Get all global user macros.

    params = {
        "output": [
            "globalmacroid",
            "macro",
            "value",
            "description",
            "type"
        ],
        "globalmacro": True,
        "sortfield": "macro",
        "sortorder": "ASC"
    }

    macros = zabbix_api_request(
        api_url=api_url,
        method="usermacro.get",
        params=params,
        auth_token=auth_token,
        request_id=2
    )

    return macros

#====================================================================================================
# Get Host and Template Macros
#====================================================================================================

def get_host_and_template_macros(api_url, auth_token):
    """
    Get all host-level and template-level user macros.
    In Zabbix, templates are also stored internally as host-like objects.
    That is why host macros and template macros are both returned by usermacro.get.
    """

    params = {
        "output": [
            "hostmacroid",
            "hostid",
            "macro",
            "value",
            "description",
            "type"
        ],
        "selectHosts": [
            "hostid",
            "host",
            "name"
        ],
        "selectTemplates": [
            "templateid",
            "host",
            "name"
        ],
        "selectGroups": [
            "groupid",
            "name"
        ],
        "sortfield": "macro",
        "sortorder": "ASC"
    }

    macros = zabbix_api_request(
        api_url=api_url,
        method="usermacro.get",
        params=params,
        auth_token=auth_token,
        request_id=3
    )

    return macros

#====================================================================================================
# Detect Macro Owner
#====================================================================================================

def detect_macro_owner(macro):                              # etect if the macro belongs to a Host or Template.

    hosts = macro.get("hosts", [])
    templates = macro.get("templates", [])

    if hosts:
        owner_type = "Host"
        owner_id = hosts[0].get("hostid", "Unknown")
        owner_host = hosts[0].get("host", "Unknown")
        owner_name = hosts[0].get("name", "Unknown")

    elif templates:
        owner_type = "Template"
        owner_id = templates[0].get("templateid", "Unknown")
        owner_host = templates[0].get("host", "Unknown")
        owner_name = templates[0].get("name", "Unknown")

    else:
        owner_type = "Unknown"
        owner_id = macro.get("hostid", "Unknown")
        owner_host = "Unknown"
        owner_name = "Unknown"

    return owner_type, owner_id, owner_host, owner_name

#====================================================================================================
# Create TXT Report Header
#====================================================================================================

def create_report_header(zabbix_url):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("#" * 100)
    lines.append("#" + "ZABBIX ALL MACROS REPORT".center(98) + "#")
    lines.append("#" * 100)
    lines.append(f"Report Date       : {now}")
    lines.append(f"Zabbix URL        : {zabbix_url}")
    lines.append(f"Compatibility     : Zabbix Server 5.0.4")
    lines.append(f"Report Type       : Global, Host, and Template User Macros")
    lines.append("#" * 100)
    lines.append("")

    return lines

#====================================================================================================
# Add Global Macros to Report
#====================================================================================================

def add_global_macros_to_report(lines, macros):            # Add global macros section to TXT report.

    lines.append("=" * 100)
    lines.append("GLOBAL MACROS".center(100))
    lines.append("=" * 100)
    lines.append("")

    if not macros:
        lines.append("No global macros found.")
        lines.append("")
        return lines

    lines.append(f"Total Global Macros: {len(macros)}")
    lines.append("-" * 100)

    for macro in macros:
        lines.append(f"Global Macro ID : {macro.get('globalmacroid', '')}")
        lines.append(f"Macro           : {macro.get('macro', '')}")
        lines.append(f"Value           : {macro.get('value', '')}")
        lines.append(f"Type            : {macro_type_to_name(macro.get('type'))}")
        lines.append(f"Description     : {macro.get('description', '')}")
        lines.append("-" * 100)

    lines.append("")

    return lines

#====================================================================================================
# Add Host and Template Macros to Report
#====================================================================================================

def add_host_template_macros_to_report(lines, macros):     # Add host and template macros section to TXT report.

    lines.append("=" * 100)
    lines.append("HOST AND TEMPLATE MACROS".center(100))
    lines.append("=" * 100)
    lines.append("")

    if not macros:
        lines.append("No host or template macros found.")
        lines.append("")
        return lines

    lines.append(f"Total Host/Template Macros: {len(macros)}")
    lines.append("-" * 100)

    for macro in macros:
        owner_type, owner_id, owner_host, owner_name = detect_macro_owner(macro)

        groups = macro.get("groups", [])

        lines.append(f"Macro ID        : {macro.get('hostmacroid', '')}")
        lines.append(f"Macro           : {macro.get('macro', '')}")
        lines.append(f"Value           : {macro.get('value', '')}")
        lines.append(f"Type            : {macro_type_to_name(macro.get('type'))}")
        lines.append(f"Description     : {macro.get('description', '')}")
        lines.append(f"Owner Type      : {owner_type}")
        lines.append(f"Owner ID        : {owner_id}")
        lines.append(f"Owner Host      : {owner_host}")
        lines.append(f"Owner Name      : {owner_name}")

        if groups:
            group_names = [group.get("name", "") for group in groups]
            lines.append(f"Groups          : {', '.join(group_names)}")
        else:
            lines.append("Groups          : None")

        lines.append("-" * 100)

    lines.append("")

    return lines


#====================================================================================================
# Save Report to TXT File
#====================================================================================================

def save_report_to_file(lines, output_file):               # Save final report lines into a TXT file.

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

    except OSError as error:
        print(f"[ERROR] Could not write report file: {error}")
        sys.exit(1)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API All Macros TXT Exporter")
    print("[+] Compatible with Zabbix Server 5.0.4\n")

    zabbix_url = input("Enter Zabbix URL, example http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    # Create output file name based on current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"Zabbix_All_Macros_Report_{timestamp}.txt"

    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print("[+] Getting global macros...")
    global_macros = get_global_macros(api_url, auth_token)

    print("[+] Getting host and template macros...")
    host_template_macros = get_host_and_template_macros(api_url, auth_token)

    print("[+] Creating TXT report...")

    report_lines = create_report_header(zabbix_url)
    report_lines = add_global_macros_to_report(report_lines, global_macros)
    report_lines = add_host_template_macros_to_report(report_lines, host_template_macros)

    report_lines.append("=" * 100)
    report_lines.append("END OF REPORT".center(100))
    report_lines.append("=" * 100)

    save_report_to_file(report_lines, output_file)

    zabbix_logout(api_url, auth_token)

    print("[+] Logged out from Zabbix API.")
    print(f"[+] Report saved successfully: {output_file}")
    print("[+] Script finished successfully.")


#====================================================================================================
# Start Script
#====================================================================================================

if __name__ == "__main__":
    main()

#====================================================================================================
#End