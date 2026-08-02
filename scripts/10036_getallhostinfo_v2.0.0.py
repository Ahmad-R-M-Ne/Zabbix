####################################################################################################
# Name: Zabbix _ Get All Host Info                                                                 #
# Job: Collect Partial information about all hosts from Zabbix using Zabbix API.                   #
#      - Compatible with Zabbix Version 5.0.4                                                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-07-02                                                                                 #
####################################################################################################

import requests
import json
import getpass
import sys
import os
from datetime import datetime

#====================================================================================================
# Normalize Zabbix API URL
#====================================================================================================

def normalize_zabbix_url(url):         # Convert normal Zabbix frontend URL to Zabbix API URL.

    url = url.strip().rstrip("/")

    if url.endswith("api_jsonrpc.php"):
        return url

    return url + "/api_jsonrpc.php"

#====================================================================================================
# Send Request to Zabbix API
#====================================================================================================

def zabbix_api_request(api_url, method, params, auth_token=None, request_id=1):
    """
    Send JSON-RPC request to Zabbix API.
    Zabbix API uses JSON-RPC 2.0.
    """

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
            timeout=60
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
        "user": username,                        # "user" in zabbix version 5.0.4 API
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

def zabbix_logout(api_url, auth_token):          # Logout from Zabbix API and invalidate the authentication token.

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
# Convert Host Status
#====================================================================================================

def host_status_to_name(status):
    """
    Zabbix host status:

        0 = Enabled / Monitored
        1 = Disabled / Not monitored
    """
    statuses = {
        "0": "Enabled",
        "1": "Disabled"
    }

    return statuses.get(str(status), "Unknown")

#====================================================================================================
# Convert Interface Type
#====================================================================================================

def interface_type_to_name(interface_type):

    interface_types = {
        "1": "Agent",
        "2": "SNMP",
        "3": "IPMI",
        "4": "JMX"
    }

    return interface_types.get(str(interface_type), "Unknown")

#====================================================================================================
# Convert SNMP Version
#====================================================================================================

def snmp_version_to_name(version):

    versions = {
        "1": "SNMPv1",
        "2": "SNMPv2c",
        "3": "SNMPv3"
    }

    return versions.get(str(version), "Unknown")

#====================================================================================================
# Convert SNMPv3 Security Level
#====================================================================================================

def snmpv3_security_level_to_name(level):

    levels = {
        "0": "noAuthNoPriv",
        "1": "authNoPriv",
        "2": "authPriv"
    }

    return levels.get(str(level), "Unknown")

#====================================================================================================
# Convert Macro Type
#====================================================================================================

def macro_type_to_name(macro_type):

    macro_types = {
        "0": "Text",
        "1": "Secret"
    }

    return macro_types.get(str(macro_type), "Unknown")

#====================================================================================================
# Get All Hosts Full Information
#====================================================================================================

def get_all_hosts_information(api_url, auth_token):
    """
    Get full information about all Zabbix hosts.

    This uses host.get and selects related objects:
        - interfaces
        - groups
        - templates
        - macros
        - inventory
    """

    params = {
        "output": [
            "hostid",
            "host",
            "name",
            "status",
            "description",
            "proxy_hostid",
            "maintenance_status",
            "maintenance_type",
            "maintenanceid",
            "inventory_mode"
        ],

        "selectInterfaces": [
            "interfaceid",
            "type",
            "main",
            "useip",
            "ip",
            "dns",
            "port",
            "details"
        ],

        "selectGroups": [
            "groupid",
            "name"
        ],

        "selectParentTemplates": [
            "templateid",
            "host",
            "name",
            "description"
        ],

        "selectMacros": [
            "hostmacroid",
            "macro",
            "value",
            "description",
            "type"
        ],

        "selectInventory": "extend",

        "sortfield": "host",
        "sortorder": "ASC"
    }

    hosts = zabbix_api_request(
        api_url=api_url,
        method="host.get",
        params=params,
        auth_token=auth_token,
        request_id=2
    )

    return hosts

#====================================================================================================
# Get Primary Interface IP
#====================================================================================================

def get_primary_ip(host):
    """
    Return the main interface IP address of the host.
    """

    interfaces = host.get("interfaces", [])

    for interface in interfaces:
        if interface.get("main") == "1":
            if interface.get("useip") == "1":
                return interface.get("ip", "")
            else:
                return interface.get("dns", "")

    if interfaces:
        interface = interfaces[0]

        if interface.get("useip") == "1":
            return interface.get("ip", "")
        else:
            return interface.get("dns", "")

    return "N/A"

#====================================================================================================
# Create Report Header
#====================================================================================================

def create_report_header(zabbix_url, total_hosts):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("#" * 100)
    lines.append("#" + "ZABBIX ALL HOSTS INFORMATION REPORT".center(98) + "#")
    lines.append("#" * 100)
    lines.append(f"Report Date       : {now}")
    lines.append(f"Zabbix URL        : {zabbix_url}")
    lines.append(f"Compatibility     : Zabbix Server 5.0.4")
    lines.append(f"Collection Method : host.get")
    lines.append(f"Total Hosts       : {total_hosts}")
    lines.append("=" * 100)

    return lines

#====================================================================================================
# Build TXT Report
#====================================================================================================

def build_report(zabbix_url, hosts):                       # Build final TXT report for all hosts.

    lines = create_report_header(
        zabbix_url=zabbix_url,
        total_hosts=len(hosts)
    )
    
    for index, host in enumerate(hosts, start=1):

        lines.append(f"{host.get('hostid', '')},{get_primary_ip(host)},{host.get('name', '')}")

    lines.append("")
    lines.append("=" * 100)
    lines.append("END OF REPORT".center(100))
    lines.append("=" * 100)

    return lines


#====================================================================================================
# Save Report to TXT File
#====================================================================================================

def save_report_to_file(lines, output_file):               # Save report to TXT file.

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

    except OSError as error:
        print(f"[ERROR] Could not write report file: {error}")
        sys.exit(1)

#====================================================================================================
# Print Short Summary
#====================================================================================================

def print_short_summary(hosts, output_file):               # Print only short summary to terminal.

    enabled_count = 0
    disabled_count = 0
    snmp_hosts = 0
    agent_hosts = 0

    for host in hosts:
        if host.get("status") == "0":
            enabled_count += 1
        elif host.get("status") == "1":
            disabled_count += 1

        interfaces = host.get("interfaces", [])

        has_snmp = False
        has_agent = False

        for interface in interfaces:
            if interface.get("type") == "2":
                has_snmp = True
            elif interface.get("type") == "1":
                has_agent = True

        if has_snmp:
            snmp_hosts += 1

        if has_agent:
            agent_hosts += 1

    print("")
    print("=" * 100)
    print("ZABBIX ALL HOSTS INFORMATION SUMMARY".center(100))
    print("=" * 100)
    print(f"Total Hosts        : {len(hosts)}")
    print(f"Enabled Hosts      : {enabled_count}")
    print(f"Disabled Hosts     : {disabled_count}")
    print(f"Hosts with SNMP    : {snmp_hosts}")
    print(f"Hosts with Agent   : {agent_hosts}")
    print(f"Output File        : {output_file}")
    print("=" * 100)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API All Hosts Information Collector (Compact)")
    print("[+] Compatible with Zabbix Server 5.0.4")
    print("[+] Short host information will be saved to a TXT report.\n")

    zabbix_url = input("Enter Zabbix URL, example: http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    output_dir = input("Enter output directory, default current directory: ").strip()

    if output_dir == "":
        output_dir = "."

    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as error:
        print(f"[ERROR] Could not create output directory: {error}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        output_dir,
        f"Zabbix_All_Hosts_Short_Information_{timestamp}.txt"
    )

    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print("[+] Getting all hosts information...")

    hosts = get_all_hosts_information(api_url, auth_token)

    print(f"[+] Total hosts collected: {len(hosts)}")
    print("[+] Building TXT report...")

    report_lines = build_report(zabbix_url, hosts)

    save_report_to_file(report_lines, output_file)

    zabbix_logout(api_url, auth_token)

    print_short_summary(hosts, output_file)

    print("\n[+] Logged out from Zabbix API.")
    print("[+] Script finished successfully.")

#====================================================================================================
# Start Script
#====================================================================================================

if __name__ == "__main__":
    main()
    
#====================================================================================================
#End