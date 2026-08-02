####################################################################################################
# Name: Zabbix _ User Group Update                                                                 #
# Job: Updates Details of an Existing User Group in Zabbix Server.                                 #
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
# UPDATE USER GROUP FUNCTION
#====================================================================================================
def update_user_group(auth_token, group_id, new_name=None, new_status=None):
    """
    Update a Zabbix user group.
    
    :param auth_token: Auth token from Zabbix API
    :param group_id: User group ID to update
    :param new_name: New name of the user group (optional)
    :param new_status: New status (0=enabled, 1=disabled) (optional)
    :return: API response
    """
    params = {"usrgrpid": group_id}
    if new_name:
        params["name"] = new_name
    if new_status is not None:
        params["status"] = new_status

    if len(params) == 1:
        print("[!] Nothing to update. Provide new_name and/or new_status.")
        return None

    return api_call(auth_token, "usergroup.update", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    token = authenticate()
    
    # Example usage: update group ID 7
    group_id = input("Enter the User Group ID to update: ").strip()
    new_name = input("Enter new name (leave blank to skip): ").strip() or None
    new_status_input = input("Enter new status (0=enabled, 1=disabled, leave blank to skip): ").strip()
    new_status = int(new_status_input) if new_status_input else None

    result = update_user_group(token, group_id, new_name, new_status)
    if result:
        print(f"[*] User Group {group_id} updated successfully: {result}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End