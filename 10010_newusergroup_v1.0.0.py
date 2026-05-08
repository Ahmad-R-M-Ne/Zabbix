####################################################################################################
# Name: Zabbix _ Create New User Group                                                             #
# Job: This Script makes an API to add a new User Group in Zabbix-server.                          #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-11-08                                                                                 #
####################################################################################################

import json
import requests
import sys
import os

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASS = "zabbix"

#====================================================================================================
# HELPER FUNCTIONS
#====================================================================================================
def api_call(auth_token, method, params):
    """Send JSON-RPC request to Zabbix API"""
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": auth_token
    }

    try:
        response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f"\n[!] Zabbix API Error: {data['error']['data']}\n")
            sys.exit(1)

        return data["result"]

    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error: {e}")
        sys.exit(1)


def authenticate():
    """Authenticate and get API token"""
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": ZABBIX_USER,
            "password": ZABBIX_PASS
        },
        "id": 1,
        "auth": None
    }

    try:
        response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f"[!] Authentication failed: {data['error']['data']}")
            sys.exit(1)

        return data["result"]

    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error: {e}")
        sys.exit(1)

#====================================================================================================
# MAIN LOGIC
#====================================================================================================
def main():
    print("\n=== Phoenix Automation Project ===")
    print(">>> Create New Zabbix User Group <<<\n")

    group_name = input("Enter new Zabbix User Group name: ").strip()
    host_group = input("Enter target Host Group name: ").strip()

    access_input = input("Access level (read-write / read / deny): ").strip().lower()
    if access_input not in ["read-write", "read", "deny"]:
        print("[!] Invalid access level. Must be: read-write / read / deny")
        sys.exit(1)

    access_map = {
        "deny": 0,
        "read": 2,
        "read-write": 3
    }
    permission_level = access_map[access_input]

    token = authenticate()
    print("[+] Authentication successful.\n")

    # Get Host Group ID
    hg_result = api_call(token, "hostgroup.get", {"filter": {"name": host_group}})
    if not hg_result:
        print(f"[!] Host group '{host_group}' not found.")
        sys.exit(1)

    hostgroupid = hg_result[0]["groupid"]

    # Create User Group
    params = {
        "name": group_name,
        "rights": [
            {
                "id": hostgroupid,
                "permission": permission_level
            }
        ]
    }

    result = api_call(token, "usergroup.create", params)

    new_group_id = result["usrgrpids"][0]

    print(f"[+] User Group '{group_name}' created successfully.")
    print(f"    → Group ID: {new_group_id}")
    print(f"    → Host Group: {host_group}")
    print(f"    → Access: {access_input}")

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Script interrupted by user.")
        sys.exit(0)

#====================================================================================================
#End
