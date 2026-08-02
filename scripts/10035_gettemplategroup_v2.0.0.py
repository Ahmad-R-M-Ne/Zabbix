####################################################################################################
# Name: Zabbix _ Get Template Group                                                                #
# Job: Get and list all Zabbix template groups using Zabbix API.                                   #
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
    Send JSON-RPC request to Zabbix API.
    Zabbix API format:
        jsonrpc
        method
        params
        auth
        id
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
    """
    Logout from Zabbix API.
    """

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
# Get Template Groups
#====================================================================================================

def get_template_groups(api_url, auth_token):
    """
    Get all host groups that contain templates.
    In Zabbix 5.0.4:
        There is no separate templategroup.get method.
    Correct method:
        hostgroup.get
    Important parameters:
        templated_hosts = 1
            Return only groups that contain templates.
        selectTemplates
            Return templates inside each group.
    """
    params = {
        "output": [
            "groupid",
            "name",
            "internal"
        ],

        # Return only groups that contain templates
        "templated_hosts": 1,

        # Return templates assigned to each group
        "selectTemplates": [
            "templateid",
            "host",
            "name"
        ],

        "sortfield": "name",
        "sortorder": "ASC"
    }

    groups = zabbix_api_request(
        api_url=api_url,
        method="hostgroup.get",
        params=params,
        auth_token=auth_token,
        request_id=2
    )

    return groups

#====================================================================================================
# Print Template Groups
#====================================================================================================

def print_template_groups(groups):                         # Print all template groups and their assigned templates.

    print("\n" + "=" * 100)
    print("                                  ZABBIX TEMPLATE GROUPS")
    print("=" * 100)

    if not groups:
        print("[!] No template groups found.")
        print("=" * 100)
        return

    print(f"Total Template Groups Found: {len(groups)}")
    print("=" * 100)

    for group in groups:
        group_id = group.get("groupid")
        group_name = group.get("name")
        internal = group.get("internal")
        templates = group.get("templates", [])

        print(f"\nGroup ID       : {group_id}")
        print(f"Group Name     : {group_name}")
        print(f"Internal Group : {'Yes' if internal == '1' else 'No'}")
        print(f"Templates      : {len(templates)}")

        print("-" * 100)

        if not templates:
            print("No templates inside this group.")
        else:
            for template in templates:
                print(f"Template ID    : {template.get('templateid')}")
                print(f"Template Host  : {template.get('host')}")
                print(f"Template Name  : {template.get('name')}")
                print("-" * 100)

    print("\n" + "=" * 100)
    print("                              END OF TEMPLATE GROUP LIST")
    print("=" * 100)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API Template Groups Collector")
    print("[+] Compatible with Zabbix Server 5.0.4\n")

    zabbix_url = input("Enter Zabbix URL, example http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print("[+] Getting template groups...")

    groups = get_template_groups(api_url, auth_token)

    print_template_groups(groups)

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