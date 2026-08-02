####################################################################################################
# Name: Zabbix _ Get Host Group                                                                    #
# Job: This Script Retrieves all Host Groups from Zabbix Server.                                   #
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
# GET HOST GROUPS FUNCTION
#====================================================================================================
def get_hostgroups(auth_token):
    """
    Retrieve all host groups from Zabbix Server.
    """
    params = {"output": ["groupid", "name"]}
    return api_call(auth_token, "hostgroup.get", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Zabbix Host Groups Retrieval Script")
    token = authenticate()

    hostgroups = get_hostgroups(token)
    if not hostgroups:
        print("[*] No host groups found in Zabbix.")
        sys.exit(0)

    print("[*] Host Groups in Zabbix:")
    for hg in hostgroups:
        print(f"ID: {hg['groupid']} | Name: {hg['name']}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End
