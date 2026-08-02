####################################################################################################
# Name: Zabbix _ User Update                                                                       #
# Job: Updates user information in Zabbix Server (compatible with Zabbix 7.x+).                    #
#      Supports updating: first name, last name, password, and user groups.                        #
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
def authenticate(username, password):
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": username,
            "password": password
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
        return data.get("result")
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error: {e}")
        sys.exit(1)

#====================================================================================================
# GET USERID FUNCTION
#====================================================================================================
def get_userid(auth_token, username):
    """
    Retrieve userid by username.
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
# UPDATE USER FUNCTION
#====================================================================================================
def update_user(auth_token, userid, name=None, surname=None, password=None, group_ids=None):
    """
    Update user information. Provide only the fields you want to update.
    """
    params = {"userid": userid}

    if name:
        params["name"] = name
    if surname:
        params["surname"] = surname
    if password:
        params["passwd"] = password
    if group_ids:
        params["usrgrps"] = [{"usrgrpid": str(gid)} for gid in group_ids]

    return api_call(auth_token, "user.update", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Zabbix User Update Script")
    admin_user = input("Admin username: ").strip()
    admin_pass = input("Admin password: ").strip()
    token = authenticate(admin_user, admin_pass)

    target_user = input("Enter username to update: ").strip()
    userid = get_userid(token, target_user)

    print("Press Enter to skip a field.")
    name = input("New first name: ").strip() or None
    surname = input("New last name: ").strip() or None
    password = input("New password: ").strip() or None
    group_input = input("New user group IDs (comma-separated): ").strip()
    group_ids = [int(gid.strip()) for gid in group_input.split(",")] if group_input else None

    updated = update_user(token, userid, name, surname, password, group_ids)
    if updated:
        print(f"[*] User '{target_user}' updated successfully.")
    else:
        print("[!] Failed to update the user.")

if __name__ == "__main__":
    main()

#====================================================================================================
#End