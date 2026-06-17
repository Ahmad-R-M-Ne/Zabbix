####################################################################################################
# Name: Zabbix _ Remove Host Group                                                                 #
# Job: This Script Deletes a Host Group in Zabbix Server.                                          #
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
# GET HOST GROUP ID
#====================================================================================================
def get_hostgroup_id(auth_token, group_name):
    """
    Retrieve the host group ID for a given host group name.
    """
    params = {"filter": {"name": group_name}}
    result = api_call(auth_token, "hostgroup.get", params)
    if result:
        return result[0]['groupid']
    return None

#====================================================================================================
# DELETE HOST GROUP FUNCTION
#====================================================================================================
def delete_hostgroup(auth_token, group_id):
    """
    Delete a host group by ID in Zabbix Server.
    """
    return api_call(auth_token, "hostgroup.delete", [group_id])

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Zabbix Host Group Deletion Script")
    token = authenticate()

    group_name = input("Enter the host group name to delete: ").strip()
    if not group_name:
        print("[!] Host group name cannot be empty.")
        sys.exit(1)

    group_id = get_hostgroup_id(token, group_name)
    if not group_id:
        print(f"[!] Host group '{group_name}' does not exist.")
        sys.exit(0)

    result = delete_hostgroup(token, group_id)
    if result:
        print(f"[*] Host group '{group_name}' deleted successfully with ID: {group_id}")
    else:
        print("[!] Failed to delete host group.")

if __name__ == "__main__":
    main()

#====================================================================================================
#End
