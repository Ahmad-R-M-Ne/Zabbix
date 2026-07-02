####################################################################################################
# Name: Zabbix _ Get Host Full Info                                                                #
# Job: Get full information about a host from Zabbix using Zabbix API.                             #
#      - Compatible with Zabbix Version 5.0.4                                                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-06-30                                                                                 #
####################################################################################################

import requests
import json
import getpass
import sys

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

def zabbix_api_request(api_url, method, params, auth_token=None, request_id=1):
    """
    This function sends a JSON-RPC request to the Zabbix API.
    Zabbix API uses JSON-RPC 2.0 format.
    Every request must include:
        jsonrpc
        method
        params
        id
        auth  -> except login
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

    # In Zabbix 5.0.4, auth is not sent for user.login
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
            timeout=15
        )

        response.raise_for_status()
        result = response.json()

    except requests.exceptions.RequestException as error:
        print(f"[ERROR] Connection error: {error}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON response from Zabbix server.")
        sys.exit(1)

    # Check if Zabbix API returned an error
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
# Get Host Information
#====================================================================================================

def get_host_information(api_url, auth_token, host_name):
    """
    Get host information from Zabbix.
    This function searches by technical hostname first.
    If not found, it tries visible name.
    """

    # First try: search by real Zabbix hostname
    params = {
        "output": [
            "hostid",
            "host",
            "name",
            "description",
            "status"
        ],
        "filter": {
            "host": [host_name]
        },
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
        "selectParentTemplates": [
            "templateid",
            "host",
            "name"
        ]
    }

    hosts = zabbix_api_request(
        api_url=api_url,
        method="host.get",
        params=params,
        auth_token=auth_token,
        request_id=2
    )

    # Second try: search by visible name
    if not hosts:
        params["filter"] = {
            "name": [host_name]
        }

        hosts = zabbix_api_request(
            api_url=api_url,
            method="host.get",
            params=params,
            auth_token=auth_token,
            request_id=3
        )

    return hosts

#====================================================================================================
# Convert Interface Type Number to Human-Readable Name
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
# Convert SNMP Version Number to Human-Readable Name
#====================================================================================================

def snmp_version_to_name(version):

    versions = {
        "1": "SNMPv1",
        "2": "SNMPv2c",
        "3": "SNMPv3"
    }

    return versions.get(str(version), "Unknown")

#====================================================================================================
# Print Host Information
#====================================================================================================

def print_host_information(host):

    print("\n" + "=" * 100)
    print("                                      HOST INFORMATION")
    print("=" * 100)
    print(f"Host ID       : {host.get('hostid')}")
    print(f"Hostname      : {host.get('host')}")
    print(f"Visible Name  : {host.get('name')}")

    status = host.get("status")
    if status == "0":
        print("Status        : Enabled")
    elif status == "1":
        print("Status        : Disabled")
    else:
        print(f"Status        : Unknown ({status})")

    description = host.get("description")
    if description:
        print(f"Description   : {description}")
    else:
        print("Description   : No description configured")

    print("-" * 100)
    print("INTERFACES")
    print("-" * 100)

    interfaces = host.get("interfaces", [])

    if not interfaces:
        print("No interface configured.")
    else:
        for interface in interfaces:
            interface_type = interface_type_to_name(interface.get("type"))
            main_status = "Yes" if interface.get("main") == "1" else "No"

            use_ip = interface.get("useip")
            ip = interface.get("ip")
            dns = interface.get("dns")
            port = interface.get("port")

            if use_ip == "1":
                connect_to = ip
            else:
                connect_to = dns

            print(f"Interface ID  : {interface.get('interfaceid')}")
            print(f"Type          : {interface_type}")
            print(f"Main          : {main_status}")
            print(f"IP Address    : {ip}")
            print(f"DNS Name      : {dns}")
            print(f"Connect To    : {connect_to}")
            print(f"Port          : {port}")

            # SNMP-specific information
            if interface.get("type") == "2":
                details = interface.get("details", {})

                snmp_version = details.get("version")
                snmp_community = details.get("community")

                print(f"SNMP Version  : {snmp_version_to_name(snmp_version)}")

                if snmp_community:
                    print(f"SNMP Community: {snmp_community}")
                else:
                    print("SNMP Community: Not configured / SNMPv3 does not use community")

    print("-" * 100)
    print("ASSIGNED TEMPLATES")
    print("-" * 100)

    templates = host.get("parentTemplates", [])

    if not templates:
        print("No template assigned.")
    else:
        for template in templates:
            print(f"Template ID   : {template.get('templateid')}")
            print(f"Template Name : {template.get('name')}")
            print(f"Template Host : {template.get('host')}")
            
    print("=" * 100)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API Host Information Collector")
    print("[+] Compatible with Zabbix Server 5.0.4\n")

    # Ask user for Zabbix connection information
    zabbix_url = input("Enter Zabbix URL, example http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    # Ask user for host name
    host_name = input("Enter hostname or visible name: ")

    # Prepare API URL
    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    # Login to Zabbix
    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print("[+] Searching host information...")

    # Get host information
    hosts = get_host_information(api_url, auth_token, host_name)

    if not hosts:
        print(f"\n[!] Host not found: {host_name}")
        zabbix_logout(api_url, auth_token)
        sys.exit(1)

    # If multiple hosts are returned, print all of them
    for host in hosts:
        print_host_information(host)

    # Logout
    zabbix_logout(api_url, auth_token)

    print("\n[+] Logged out from Zabbix API.")
    print("[+] Script finished successfully.")

#====================================================================================================
# Start Script
#====================================================================================================

if __name__ == "__main__":
    main()
    
#====================================================================================================
#End

