####################################################################################################
# Name: Zabbix _ Get User Group                                                                    #
# Job: Retrieves Details of User Groups from Zabbix Server.                                        #
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
    """Perform a JSON-RPC call to the Zabbix API."""
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
    """Authenticate with Zabbix API and return auth token."""
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
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    token = authenticate()
    params = {
        "output": ["usrgrpid", "name", "users_status"]
    }
    user_groups = api_call(token, "usergroup.get", params)

    if not user_groups:
        print("[*] No user groups found.")
        return

    print(f"[*] Retrieved {len(user_groups)} user group(s):\n")
    for group in user_groups:
        print(f"ID: {group['usrgrpid']} | Name: {group['name']} | Status: {group.get('users_status', 'N/A')}")

if __name__ == "__main__":
    main()
    
#====================================================================================================
#End