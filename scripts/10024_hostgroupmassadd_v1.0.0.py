####################################################################################################
# Name: Zabbix _ Host Group Mass Add                                                               #
# Job: This Script Adds Multiple Hosts to Host Groups in Zabbix Server.                            #
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
# HOSTGROUP MASSADD FUNCTION
#====================================================================================================
def hostgroup_massadd(auth_token, host_ids, group_ids):
    """
    Add multiple hosts to multiple host groups.
    :param host_ids: List of host IDs to add
    :param group_ids: List of host group IDs to add hosts into
    """
    params = {"hosts": [{"hostid": hid} for hid in host_ids],
              "groups": [{"groupid": gid} for gid in group_ids]}
    return api_call(auth_token, "hostgroup.massadd", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Zabbix HostGroup Mass Add Script")
    token = authenticate()

    host_ids_input = input("Enter host IDs to add (comma-separated): ").strip()
    group_ids_input = input("Enter host group IDs (comma-separated): ").strip()

    if not host_ids_input or not group_ids_input:
        print("[!] Host IDs and Host Group IDs cannot be empty.")
        sys.exit(1)

    host_ids = [hid.strip() for hid in host_ids_input.split(",") if hid.strip().isdigit()]
    group_ids = [gid.strip() for gid in group_ids_input.split(",") if gid.strip().isdigit()]

    if not host_ids or not group_ids:
        print("[!] Invalid host IDs or group IDs provided.")
        sys.exit(1)

    result = hostgroup_massadd(token, host_ids, group_ids)
    if result:
        print(f"[*] Successfully added hosts {host_ids} to host groups {group_ids}.")
    else:
        print("[!] Failed to add hosts to host groups.")

if __name__ == "__main__":
    main()

#====================================================================================================
#End