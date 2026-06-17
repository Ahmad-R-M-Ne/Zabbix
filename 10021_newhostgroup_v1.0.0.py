####################################################################################################
# Name: Zabbix _ Create New Host Group                                                             #
# Job: This Script Creates a New Host Group in Zabbix Server,                                      #
#      With a Check to Avoid Creating Duplicates.                                                  #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-11-08                                                                                 #
####################################################################################################

import json
import requests
import sys

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"
ZABBIX_USER = ""
ZABBIX_PASS = ""

#====================================================================================================
# API CALL FUNCTION
#====================================================================================================
def api_call(auth_token, method, params):
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
        return data.get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error: {e}")
        sys.exit(1)

#====================================================================================================
# AUTHENTICATION
#====================================================================================================
def authenticate():
    """
    Authenticate using fixed admin credentials.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"username": ZABBIX_USER, "password": ZABBIX_PASS},
        "id": 1,
        "auth": None
    }
    try:
        response = requests.post(ZABBIX_URL, headers={'Content-Type': 'application/json-rpc'}, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            print(f"[!] Authentication failed: {data['error']['data']}")
            sys.exit(1)
        return data.get("result")
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error: {e}")
        sys.exit(1)

#====================================================================================================
# CHECK HOST GROUP EXISTENCE
#====================================================================================================
def hostgroup_exists(auth_token, group_name):
    """
    Check if a host group with the given name already exists in Zabbix.
    """
    params = {"filter": {"name": group_name}}
    result = api_call(auth_token, "hostgroup.get", params)
    return len(result) > 0

#====================================================================================================
# CREATE HOST GROUP FUNCTION
#====================================================================================================
def create_hostgroup(auth_token, group_name):
    """
    Create a new host group in Zabbix Server.
    """
    params = {"name": group_name}
    return api_call(auth_token, "hostgroup.create", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Zabbix Host Group Creation Script")
    token = authenticate()

    group_name = input("Enter new host group name: ").strip()
    if not group_name:
        print("[!] Host group name cannot be empty.")
        sys.exit(1)

    if hostgroup_exists(token, group_name):
        print(f"[!] Host group '{group_name}' already exists. Skipping creation.")
        sys.exit(0)

    result = create_hostgroup(token, group_name)
    if result:
        print(f"[*] Host group '{group_name}' created successfully with ID: {result['groupids'][0]}")
    else:
        print("[!] Failed to create host group.")

if __name__ == "__main__":
    main()

#====================================================================================================
#End
