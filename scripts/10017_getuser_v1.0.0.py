####################################################################################################
# Name: Zabbix _ Get User                                                                          #
# Job: Retrieves User Details from Zabbix Server.                                                  #
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
# GET USER DETAILS
#====================================================================================================
def get_user(auth_token, username=None):
    """
    Retrieve details of a user from Zabbix 7.x+.
    If username is None, retrieves all users.
    """
    params = {
        "output": ["userid", "username", "name", "surname", "usrgrps", "type", "gui_access"]
    }
    if username:
        params["filter"] = {"username": username}

    return api_call(auth_token, "user.get", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    token = authenticate()

    username = input("Enter username to retrieve (leave empty to list all users): ").strip() or None
    users = get_user(token, username)

    if not users:
        print("[*] No users found.")
        return

    for user in users:
        print("\n--------------------------------------------")
        print(f"UserID       : {user.get('userid')}")
        print(f"Username     : {user.get('username')}")
        print(f"Name         : {user.get('name')}")
        print(f"Surname      : {user.get('surname')}")
        print(f"User Type    : {user.get('type')}")
        print(f"GUI Access   : {user.get('gui_access')}")
        usrgrps = user.get("usrgrps", [])
        groups = ", ".join([g.get("name", "") for g in usrgrps])
        print(f"User Groups  : {groups}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End