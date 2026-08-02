####################################################################################################
# Name: Zabbix _ Remove User                                                                       #
# Job: Deletes a User from Zabbix Server.                                                          #
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
# GET USER FUNCTION
#====================================================================================================
def get_user(auth_token, username):
    """
    Retrieve user details to get userid by username.
    """
    params = {
        "output": ["userid", "username"],
        "filter": {"username": username}
    }
    users = api_call(auth_token, "user.get", params)
    if not users:
        print(f"[!] No user found with username '{username}'")
        sys.exit(1)
    return users[0]["userid"]

#====================================================================================================
# DELETE USER FUNCTION
#====================================================================================================
def delete_user(auth_token, userid):
    """
    Delete user by userid.
    """
    return api_call(auth_token, "user.delete", [userid])

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    token = authenticate()
    username = input("Enter the username to delete: ").strip()

    userid = get_user(token, username)
    confirm = input(f"Are you sure you want to delete user '{username}' (ID: {userid})? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("[*] Deletion canceled.")
        return

    deleted = delete_user(token, userid)
    if deleted:
        print(f"[*] User '{username}' deleted successfully.")
    else:
        print("[!] Failed to delete the user.")

if __name__ == "__main__":
    main()

#====================================================================================================
#End
