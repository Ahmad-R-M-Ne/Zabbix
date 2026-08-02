####################################################################################################
# Name: Zabbix _ Remove User Group                                                                 #
# Job: This Script Deletes an Existing User Group in the Zabbix Server.                            #
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
ZABBIX_USER = ""
ZABBIX_PASS = ""

#====================================================================================================
# HELPER FUNCTIONS
#====================================================================================================

def api_call(auth_token, method, params):
    """Send a JSON-RPC request to Zabbix API"""
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
            print(f"[!] Zabbix API Error: {data['error']['data']}")
            sys.exit(1)
        return data["result"]
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error: {e}")
        sys.exit(1)


def authenticate():
    """Authenticate to Zabbix and return an auth token"""
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
    print(">>> Delete Zabbix User Group <<<\n")

    group_name = input("Enter the User Group name to delete: ").strip()

    # Authenticate to Zabbix
    token = authenticate()
    print("[+] Authentication successful.")

    # Get the User Group ID by name
    groups = api_call(token, "usergroup.get", {"filter": {"name": group_name}})
    if not groups:
        print(f"[!] User Group '{group_name}' not found in Zabbix.")
        sys.exit(1)

    usrgrpid = groups[0]["usrgrpid"]
    print(f"[+] Found User Group '{group_name}' (ID: {usrgrpid}).")

    confirm = input(f"Are you sure you want to DELETE this group '{group_name}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("[*] Operation cancelled by user.")
        sys.exit(0)

    # Perform deletion
    result = api_call(token, "usergroup.delete", [usrgrpid])
    if result:
        print(f"[+] User Group '{group_name}' deleted successfully.")
    else:
        print(f"[!] Failed to delete User Group '{group_name}'.")

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