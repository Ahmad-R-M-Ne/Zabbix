####################################################################################################
# Name: Zabbix _ Create New User                                                                   #
# Job: Creates a New User in Zabbix Server.                                                        #
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
# CREATE USER FUNCTION
#====================================================================================================
def create_user(auth_token, username, password, surname=None, usrgrps=None):
    """
    Create a new user in Zabbix 7.x with internal authentication.
    """
    if not usrgrps:
        print("[!] User must belong to at least one group.")
        return None

    usrgrps_list = [{"usrgrpid": str(g)} for g in usrgrps]

    params = {
        "username": username,   # Login name
        "passwd": password,     # Required for internal auth
        "surname": surname or "",
        "usrgrps": usrgrps_list
    }

    return api_call(auth_token, "user.create", params)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    token = authenticate()

    print("Enter details for the new user:")
    username = input("Username (login name): ").strip()
    password = input("Password: ").strip()
    surname = input("Surname (optional): ").strip() or None
    usrgrps_input = input("User group IDs (comma-separated): ").strip()
    usrgrps = [g.strip() for g in usrgrps_input.split(",") if g.strip()]

    # Create the user with password
    created = create_user(token, username, password, surname, usrgrps)
    if not created or "userids" not in created:
        print("[!] Failed to create user.")
        sys.exit(1)

    userid = created["userids"][0]
    print(f"[*] User '{username}' created successfully with ID: {userid}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End